/**
 * Phase 8: hash-chained development-mission queue (owner-authored, chat intake).
 *
 * The chat assistant cannot write code. When the owner asks for engineering work
 * (new features, the university, operationalizing agents, …) the assistant
 * proposes recording it as a development mission; the owner confirms with
 * «تایید <code>» exactly like the paper commands (chat_actions.ts), and only then
 * is one line appended here with status QUEUED. Nothing is ever executed by this
 * module: it is a queue that the (future) engineering/mission-controller layer is
 * expected to read. Recording a mission is not doing the work, and no reply may
 * ever claim the work is done.
 *
 * Storage: an append-only JSONL file (default
 * `<AHOS data dir>/dev_missions/dev_missions.jsonl`), never a database. Every line
 * is a full record linked to the previous one by prev_hash/entry_hash (sha256 over
 * canonical JSON), so edits, deletions and reordering are detectable by verify().
 * A keyless chain cannot detect a whole-file rewrite: record `head_hash`
 * somewhere outside the file (handoff doc, commit) to anchor it.
 *
 * Privacy: the raw user message is never stored. Only the cleaned mission summary
 * the owner confirmed, plus the channel and a *hash* of the sender id. Secret-like
 * substrings in the summary are redacted before hashing, so they never reach disk.
 *
 * Not an authority: grants nothing, unlocks no gate, is imported by no
 * decision/trading code. PAPER_ONLY is unaffected.
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import {
  GENESIS_HASH,
  FileAuditSink,
  canonicalJson,
  hashId,
  sha256Hex,
  verifyAuditLines,
} from "./chat_control_gate";

export const DEV_MISSION_SCHEMA = "ahos.dev_missions.v1";
export const DEV_MISSION_STATUS = "QUEUED" as const;
export const MAX_SUMMARY_LEN = 280;
export const MAX_TITLE_LEN = 60;

export type DevMissionRecord = {
  schema: string;
  seq: number;
  ts: string;
  kind: "MISSION";
  /** Stable, human-readable id: DM-000001. Unique within the file (seq + 1). */
  id: string;
  /** The 6-char confirm code of the chat action that created this entry (audit link). */
  confirmCode: string | null;
  titleFa: string;
  summaryFa: string;
  status: typeof DEV_MISSION_STATUS;
  channelClaimed: string;
  userIdHash: string;
  prev_hash: string;
  entry_hash: string;
};

/** Persian view of one queued mission, for the read tool / dashboard. */
export type DevMissionView = {
  id: string;
  titleFa: string;
  statusFa: string;
  queuedAgoFa: string;
};

export interface DevMissionReader {
  /** Queued missions, newest first. Chain is verified; a broken chain yields []. */
  queued(now?: Date): DevMissionView[];
}

// ------------------------------------------------------------------ secrets --

const SECRET_RULES: Array<[string, RegExp]> = [
  ["PRIVATE_KEY_BLOCK", /-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?(-----END [A-Z0-9 ]*PRIVATE KEY-----|$)/],
  ["TELEGRAM_BOT_TOKEN", /\b\d{8,12}:[A-Za-z0-9_-]{30,50}\b/],
  ["GOOGLE_API_KEY", /\bAIza[0-9A-Za-z_-]{30,}/],
  ["ANTHROPIC_KEY", /\bsk-ant-[A-Za-z0-9_-]{16,}/],
  ["OPENAI_STYLE_KEY", /\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}/],
  ["GITHUB_TOKEN", /\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}/],
  ["JWT", /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}/],
  ["EVM_PRIVATE_KEY", /\b0x[0-9a-fA-F]{64}\b/],
  ["URL_CREDENTIALS", /(?:[a-z][a-z0-9+.-]*:\/\/)[^/\s:@]+:[^/\s@]+@/i],
  ["BEARER", /\bbearer\s+[A-Za-z0-9._~+/=-]{12,}/i],
  [
    "ASSIGNED_SECRET",
    /\b([A-Z0-9_]*(?:api[_-]?key|secret|token|passw(?:or)?d|private[_-]?key|credential)[A-Z0-9_]*)\s*[:=]\s*(['"]?)(?!\[REDACTED)([^\s'\",;]{6,})/i,
  ],
];

/** Redact secret-looking substrings before anything is hashed or written. */
export function redactMissionSecrets(text: string): string {
  let out = String(text ?? "");
  for (const [name, pat] of SECRET_RULES) {
    out = out.replace(pat, (m, ...args: unknown[]) => {
      // The marker never carries any of the matched secret text (not even a prefix).
      if (name === "ASSIGNED_SECRET") return `${String(args[0] ?? "")} [REDACTED:${name}]`;
      if (name === "URL_CREDENTIALS") return `${String(args[0] ?? "")}[REDACTED:${name}]@`;
      return `[REDACTED:${name}]`;
    });
  }
  return out;
}

// ------------------------------------------------------------------ summary --

/**
 * The mission summary shown back to the owner and stored in the queue. It is the
 * owner's own request, cleaned up: one line, no zero-width/bidi artefacts, no
 * leading greetings, truncated. Never the raw chat row.
 */
export function cleanSummaryFa(text: string): string {
  const t = String(text ?? "")
    .normalize("NFKC")
    .replace(/[​-‏‪-‮⁠-⁤⁦-⁩﻿­ـ]/g, "")
    .replace(/‌/g, " ")
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/\s+/g, " ")
    .trim();
  const stripped = t.replace(/^(?:سلام|درود|hello|hi|hey|hey)[\s!.،,؟?]*/i, "").trim();
  const one = (stripped || t).replace(/\s*[\n\r]+/g, " ").trim();
  if (one.length <= MAX_SUMMARY_LEN) return one;
  return one.slice(0, MAX_SUMMARY_LEN - 1).trimEnd() + "…";
}

/** Short title: first clause, or the whole summary when it is already short. */
export function titleFromSummaryFa(summaryFa: string): string {
  const s = String(summaryFa ?? "").trim();
  const first = s.split(/[.۔!؟?،,؛;:]/)[0].trim() || s;
  if (first.length <= MAX_TITLE_LEN) return first;
  return first.slice(0, MAX_TITLE_LEN - 1).trimEnd() + "…";
}

// -------------------------------------------------------------------- store --

export type AppendInput = {
  summaryFa: string;
  confirmCode?: string | null;
  channel?: string | null;
  userId?: string | null;
};

export class DevMissionStore implements DevMissionReader {
  readonly path: string;
  private readonly sink: FileAuditSink;
  private readonly now: () => Date;

  constructor(path: string, opts: { now?: () => Date; sink?: FileAuditSink } = {}) {
    this.path = path;
    this.sink = opts.sink ?? new FileAuditSink(path);
    this.now = opts.now ?? (() => new Date());
  }

  /** Parse every line and verify the chain. Returns [] on any tamper/break. */
  records(): DevMissionRecord[] {
    if (!existsSync(this.path)) return [];
    const raw = readFileSync(this.path, "utf8");
    const lines = raw.split("\n").filter((l) => l.trim());
    if (verifyAuditLines(lines) !== -1) return [];
    return lines.map((l) => JSON.parse(l) as DevMissionRecord);
  }

  verify(): { ok: boolean; entries: number; headHash: string; firstBadLine: number } {
    const lines = existsSync(this.path) ? readFileSync(this.path, "utf8").split("\n").filter((l) => l.trim()) : [];
    const bad = verifyAuditLines(lines);
    const last = lines.length ? (JSON.parse(lines[lines.length - 1]) as DevMissionRecord).entry_hash : GENESIS_HASH;
    return { ok: bad === -1, entries: lines.length, headHash: last, firstBadLine: bad };
  }

  /** Append one QUEUED mission. Refuses an empty summary; never throws. */
  append(input: AppendInput): DevMissionRecord | null {
    const summary = cleanSummaryFa(input.summaryFa);
    if (!summary) return null;
    const seq = this.records().length;
    const body = {
      schema: DEV_MISSION_SCHEMA,
      seq,
      ts: this.now().toISOString(),
      kind: "MISSION" as const,
      id: `DM-${String(seq + 1).padStart(6, "0")}`,
      confirmCode: input.confirmCode ?? null,
      titleFa: titleFromSummaryFa(summary),
      summaryFa: redactMissionSecrets(summary),
      status: DEV_MISSION_STATUS,
      channelClaimed: String(input.channel ?? "unspecified").slice(0, 32).replace(/[^\w.-]/g, "_") || "unspecified",
      userIdHash: hashId("user", input.userId),
      prev_hash: this.sink.lastHash(),
    };
    const rec: DevMissionRecord = { ...body, entry_hash: sha256Hex(canonicalJson(body)) };
    try {
      this.sink.append(canonicalJson(rec) + "\n");
    } catch {
      return null;
    }
    return rec;
  }

  queued(now: Date = new Date()): DevMissionView[] {
    return this.records()
      .slice()
      .reverse()
      .map((r) => ({
        id: r.id,
        titleFa: r.titleFa,
        statusFa: "در صف",
        queuedAgoFa: faAgo(r.ts, now),
      }));
  }
}

export function faAgo(iso: string, now: Date): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "نامشخص";
  const mins = Math.max(0, Math.round((now.getTime() - d.getTime()) / 60000));
  if (mins < 1) return "همین الان";
  if (mins < 60) return `${faDigits(mins)} دقیقه پیش`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${faDigits(hrs)} ساعت پیش`;
  return `${faDigits(Math.round(hrs / 24))} روز پیش`;
}

function faDigits(n: number): string {
  return String(n).replace(/[0-9]/g, (c) => "۰۱۲۳۴۵۶۷۸۹"[Number(c)]);
}

export function defaultDevMissionsPath(env: Record<string, string | undefined> = process.env): string {
  const explicit = (env.AHOS_DEV_MISSIONS_PATH || "").trim();
  if (explicit) return explicit;
  const dataDir = (env.AHOS_DATA_DIR || "").trim() || join(process.cwd(), "data");
  return join(dataDir, "dev_missions", "dev_missions.jsonl");
}

let defaultStore: DevMissionStore | null = null;
/** Process-wide store (in memory handle only; the file is the state). */
export function getDevMissionStore(env: Record<string, string | undefined> = process.env): DevMissionStore {
  if (!defaultStore) defaultStore = new DevMissionStore(defaultDevMissionsPath(env));
  return defaultStore;
}
