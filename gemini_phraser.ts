/**
 * Phase 6: Gemini implementation of the ReplyPhraser seam (response_composer.ts).
 *
 * Zero authority. It only rewrites the deterministic, grounded draft; the
 * composer's validatePhrased() still decides whether the rewrite is accepted
 * (no new numbers, no jargon, footer exactly once, length), else the
 * deterministic text is used. Locked drafts (GM-04 refusals) never reach here.
 *
 * Key handling: this module never sees the API key. It spawns the Python helper
 * `python -m architecture.ai.gemini_phraser`, which reads the key from Windows
 * Credential Manager (generic target AHOS/ai/gemini, read-only) and calls the
 * Gemini REST API itself. Only the draft text (no user id, no raw user message)
 * goes to the helper via UTF-8 stdin; JSON comes back on UTF-8 stdout.
 *
 * Config (env, read at first use):
 *   AHOS_PHRASER            "off" disables; anything else (default) = gemini
 *   AHOS_GEMINI_MODELS      comma list, max 2 used (default gemini-flash-lite-latest,gemini-3.5-flash-lite)
 *   AHOS_PHRASER_TIMEOUT_MS per-model timeout passed to the helper (default 4000, max 8000;
 *                           the helper's total budget is 9 s for at most 2 models)
 *   AHOS_PHRASER_PYTHON     python executable (default .venv\Scripts\python.exe / .venv/bin/python)
 *
 * Circuit breaker (in memory, per gateway process): 3 consecutive failures →
 * skip for 60 s; credential/quota problems (AUTH_FAILED, QUOTA_EXHAUSTED,
 * NO_CREDENTIAL, NOT_WINDOWS, ...) → skip for 10 min. While open, phrase()
 * returns null immediately (deterministic reply, no added latency).
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import type { GroundedDraft, PhrasedReply, ReplyPhraser } from "./response_composer";
import { renderPlain, REPLY_BUDGET_CHARS } from "./reply_format";

/** Plain env map (avoids NodeJS.ProcessEnv's required NODE_ENV in tests). */
export type EnvMap = Record<string, string | undefined>;

export const DEFAULT_GEMINI_MODELS: readonly string[] = Object.freeze(["gemini-flash-lite-latest", "gemini-3.5-flash-lite"]);

export type HelperRequest = {
  draft: string;
  style: string[];
  intent: string;
  models: string[];
  timeout_ms: number;
};

export type HelperResult = {
  ok: boolean;
  text: string | null;
  model: string | null;
  status: string;
  reason_code: string;
  latency_ms: number;
  attempts?: unknown[];
};

/** Runs the helper; injectable for tests. Must resolve (never reject) with a result or null. */
export type HelperRunner = (req: HelperRequest, killAfterMs: number) => Promise<HelperResult | null>;

export type PhraserStats = {
  lastStatus: string;
  lastReason: string;
  lastModel: string | null;
  lastLatencyMs: number;
  consecutiveFailures: number;
  openUntil: number;
};

const LONG_OPEN_REASONS = new Set([
  "AUTH_FAILED",
  "QUOTA_EXHAUSTED",
  "NO_CREDENTIAL",
  "EMPTY_CREDENTIAL",
  "NOT_WINDOWS",
  "READ_FAILED",
  "TARGET_NOT_ALLOWED",
  "HELPER_SPAWN_FAILED",
]);

export type GeminiPhraserOptions = {
  runner?: HelperRunner;
  now?: () => number;
  models?: string[];
  timeoutMs?: number;
  failureThreshold?: number;
  shortOpenMs?: number;
  longOpenMs?: number;
};

/** Remove anything resembling the footer and markdown noise from model output. */
export function cleanModelText(text: string, footer: string): string {
  const core = footer.replace(/[.。]\s*$/, "");
  return String(text ?? "")
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .filter((l) => !(core && l.includes(core)))
    .map((l) => l.replace(/^\s*#{1,6}\s+/, "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/^\s*[*-]\s+/, "• ").trimEnd())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export class GeminiPhraser implements ReplyPhraser {
  readonly name = "gemini";
  private readonly runner: HelperRunner;
  private readonly now: () => number;
  private readonly models: string[];
  private readonly timeoutMs: number;
  private readonly failureThreshold: number;
  private readonly shortOpenMs: number;
  private readonly longOpenMs: number;
  readonly stats: PhraserStats = {
    lastStatus: "UNSET",
    lastReason: "UNSET",
    lastModel: null,
    lastLatencyMs: 0,
    consecutiveFailures: 0,
    openUntil: 0,
  };

  constructor(opts: GeminiPhraserOptions = {}) {
    this.runner = opts.runner ?? spawnHelperRunner;
    this.now = opts.now ?? Date.now;
    this.models = (opts.models && opts.models.length ? opts.models : [...DEFAULT_GEMINI_MODELS]).slice(0, 2);
    this.timeoutMs = Math.max(500, Math.min(opts.timeoutMs ?? 4000, 8000));
    this.failureThreshold = opts.failureThreshold ?? 3;
    this.shortOpenMs = opts.shortOpenMs ?? 60_000;
    this.longOpenMs = opts.longOpenMs ?? 600_000;
  }

  isOpen(): boolean {
    return this.now() < this.stats.openUntil;
  }

  private fail(status: string, reason: string, latency: number): null {
    const s = this.stats;
    s.lastStatus = status;
    s.lastReason = reason;
    s.lastModel = null;
    s.lastLatencyMs = latency;
    s.consecutiveFailures += 1;
    if (LONG_OPEN_REASONS.has(reason) || LONG_OPEN_REASONS.has(status)) {
      s.openUntil = this.now() + this.longOpenMs;
    } else if (s.consecutiveFailures >= this.failureThreshold) {
      s.openUntil = this.now() + this.shortOpenMs;
    }
    return null;
  }

  async phrase(draft: GroundedDraft, _deterministic: { plain: string; html: string }, style: readonly string[]): Promise<PhrasedReply | null> {
    if (draft.locked) return null;
    if (this.isOpen()) {
      this.stats.lastReason = "CIRCUIT_OPEN";
      return null;
    }
    // Links (news sources) are kept verbatim by the deterministic text; an LLM
    // rewrite could drop or alter URLs, so such drafts are not phrased.
    if (draft.blocks.some((b) => b.kind === "bullet" && b.link)) {
      this.stats.lastReason = "SKIPPED_HAS_LINKS";
      return null;
    }
    const body = renderPlain(draft.blocks, undefined, REPLY_BUDGET_CHARS).trim();
    if (!body) return null;
    const started = this.now();
    let res: HelperResult | null = null;
    try {
      res = await this.runner(
        { draft: body, style: [...style], intent: draft.intent, models: this.models, timeout_ms: this.timeoutMs },
        Math.min(this.timeoutMs * this.models.length, 9000) + 3000,
      );
    } catch {
      res = null;
    }
    const latency = Math.max(0, this.now() - started);
    if (!res) return this.fail("UNAVAILABLE", "HELPER_NO_RESULT", latency);
    if (!res.ok || !res.text) return this.fail(String(res.status || "UNAVAILABLE"), String(res.reason_code || "UNKNOWN"), latency);
    const cleaned = cleanModelText(res.text, draft.footer);
    if (!cleaned) return this.fail("DEGRADED", "EMPTY_AFTER_CLEAN", latency);
    const s = this.stats;
    s.lastStatus = "READY";
    s.lastReason = "OK";
    s.lastModel = res.model;
    s.lastLatencyMs = latency;
    s.consecutiveFailures = 0;
    s.openUntil = 0;
    return { plain: `${cleaned}\n\n— ${draft.footer}` };
  }
}

/** Minimal environment for the helper: no DATABASE_URL, no web/Telegram tokens. */
export function helperEnv(src: EnvMap = process.env): EnvMap {
  const keep = [
    "SystemRoot", "SYSTEMROOT", "windir", "PATH", "Path", "PATHEXT", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA",
    "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy", "ALL_PROXY", "all_proxy",
    "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE",
  ];
  const env: EnvMap = {};
  for (const k of keep) if (src[k] !== undefined) env[k] = src[k];
  env.PYTHONIOENCODING = "utf-8";
  env.PYTHONUTF8 = "1";
  env.PYTHONDONTWRITEBYTECODE = "1";
  return env;
}

export function resolvePython(cwd: string = process.cwd(), src: EnvMap = process.env): string {
  const override = (src.AHOS_PHRASER_PYTHON || "").trim();
  if (override) return override;
  const win = join(cwd, ".venv", "Scripts", "python.exe");
  const posix = join(cwd, ".venv", "bin", "python");
  if (process.platform === "win32") return existsSync(win) ? win : "python";
  return existsSync(posix) ? posix : "python3";
}

const HELPER_MODULES = new Set(["architecture.ai.gemini_phraser", "architecture.ai.gemini_chat"]);

/**
 * Spawn a whitelisted Python helper module (no shell, fixed argv), send UTF-8
 * JSON on stdin, parse UTF-8 JSON from stdout, hard-kill after `killAfterMs`.
 * Resolves (never rejects) with the parsed object or a synthetic failure.
 */
export function spawnPythonJson<T extends object>(module: string, req: unknown, killAfterMs: number): Promise<T | null> {
  return new Promise((resolve) => {
    const fail = (reason: string, latency = 0) =>
      ({ ok: false, text: null, parts: [], model: null, status: "UNAVAILABLE", reason_code: reason, latency_ms: latency }) as unknown as T;
    if (!HELPER_MODULES.has(module)) {
      resolve(fail("HELPER_NOT_ALLOWED"));
      return;
    }
    let settled = false;
    const done = (v: T | null) => {
      if (!settled) {
        settled = true;
        resolve(v);
      }
    };
    let child: ReturnType<typeof spawn>;
    try {
      child = spawn(resolvePython(), ["-m", module], {
        cwd: process.cwd(),
        env: helperEnv() as NodeJS.ProcessEnv,
        shell: false,
        windowsHide: true,
        stdio: ["pipe", "pipe", "ignore"],
      });
    } catch {
      done(fail("HELPER_SPAWN_FAILED"));
      return;
    }
    const chunks: Buffer[] = [];
    let size = 0;
    const timer = setTimeout(() => {
      try {
        child.kill();
      } catch {
        /* ignore */
      }
      done(fail("HELPER_TIMEOUT", killAfterMs));
    }, killAfterMs);
    child.on("error", () => {
      clearTimeout(timer);
      done(fail("HELPER_SPAWN_FAILED"));
    });
    child.stdout?.on("data", (c: Buffer) => {
      size += c.length;
      if (size <= 512 * 1024) chunks.push(c);
    });
    child.on("close", () => {
      clearTimeout(timer);
      try {
        const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8")) as T;
        done(parsed && typeof parsed === "object" ? parsed : null);
      } catch {
        done(null);
      }
    });
    child.stdin?.on("error", () => {
      /* helper exited early; close handler reports */
    });
    child.stdin?.end(Buffer.from(JSON.stringify(req), "utf8"));
  });
}

/** Default phraser runner. */
export const spawnHelperRunner: HelperRunner = (req, killAfterMs) =>
  spawnPythonJson<HelperResult>("architecture.ai.gemini_phraser", req, killAfterMs);

let singleton: GeminiPhraser | null | undefined;

/** Process-wide phraser (null when AHOS_PHRASER=off). */
export function getDefaultPhraser(src: EnvMap = process.env): GeminiPhraser | null {
  if (singleton !== undefined) return singleton;
  const mode = (src.AHOS_PHRASER || "").trim().toLowerCase();
  if (mode === "off" || mode === "0" || mode === "false" || mode === "none") {
    singleton = null;
    return singleton;
  }
  const models = (src.AHOS_GEMINI_MODELS || "")
    .split(",")
    .map((m) => m.trim())
    .filter((m) => /^[A-Za-z0-9._-]{1,80}$/.test(m));
  const t = Number(src.AHOS_PHRASER_TIMEOUT_MS);
  singleton = new GeminiPhraser({ models, timeoutMs: Number.isFinite(t) && t > 0 ? t : undefined });
  return singleton;
}
