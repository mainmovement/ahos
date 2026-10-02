/**
 * GM-04: chat/Telegram operational-control capability gate.
 * This is the conservative form: it can only take capability away.
 *
 * Every /api/chat caller authenticates with the same bearer token, and the
 * `channel` field is supplied by the client. So the chat path cannot prove that
 * a message came from the local dashboard (see
 * reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md, option 3(b)).
 * Because of that, ENGINE_CONTROL (start/stop) and PAPER_WRITE (paper_buy) are
 * REFUSED on the chat path for EVERY channel, including "web".
 * The dashboard's dedicated buttons (/api/engine, /api/paper) are unchanged.
 *
 * `channel` is recorded in the audit as `channel_claimed` and is never used as
 * a grant. No new secret is needed.
 *
 * Audit: an append-only JSONL with a hash chain and hashed ids. It never
 * stores the raw message or the raw user id. If the audit write fails, the
 * request stays refused (fail-closed) and the chat keeps working.
 *
 * Pure apart from the default file writer. Run: npm run test:chat-control-gate
 */
import { createHash } from "node:crypto";
import { appendFileSync, closeSync, existsSync, fstatSync, mkdirSync, openSync, readSync } from "node:fs";
import { dirname, join } from "node:path";

export const CONTROL_AUDIT_SCHEMA = "ahos.chat_control_audit.v1";
export const GENESIS_HASH = "0".repeat(64);

export type Capability = "ENGINE_CONTROL" | "PAPER_WRITE";
export const CONTROL_INTENTS: Readonly<Record<string, Capability>> = Object.freeze({
  start: "ENGINE_CONTROL",
  stop: "ENGINE_CONTROL",
  paper_buy: "PAPER_WRITE",
});

// ---------------------------------------------------------------- matching --

const ZERO_WIDTH = /[\u200B\u200D\u200E\u200F\u202A-\u202E\u2060-\u2064\u2066-\u2069\uFEFF\u00AD]/g; // ZWNJ (U+200C) handled below

/** NFKC, Arabic->Persian letters, strip zero-width/bidi marks, collapse space, lower. */
export function normalizeCommandText(text: string): string {
  return String(text ?? "")
    .normalize("NFKC")
    .replace(ZERO_WIDTH, "")
    .replace(/\u200C/g, " ")
    .replace(/[\u064A\u0649]/g, "ی")
    .replace(/\u0643/g, "ک")
    .replace(/[\u064B-\u065F\u0670]/g, "") // harakat
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

const START_PHRASES = [
  "start", "start engine", "start the engine", "engine start",
  "شروع", "شروع کن", "استارت", "استارت کن", "روشن", "روشن کن", "روشنش کن",
  "موتور رو روشن کن", "موتور را روشن کن", "شروع موتور", "موتور روشن",
];
const STOP_PHRASES = [
  "stop", "stop engine", "stop the engine", "engine stop",
  "توقف", "توقف کن", "استاپ", "استاپ کن", "خاموش", "خاموش کن", "خاموشش کن",
  "موتور رو خاموش کن", "موتور را خاموش کن", "توقف موتور", "موتور خاموش",
];
const POLITE = /^(?:لطفا|لطفاً|please|pls)\s+|\s+(?:لطفا|لطفاً|please|pls)$/g;
const TRAILING_PUNCT = /[\s.!?؟،,؛;:…]+$/;

function commandCore(text: string): string {
  let t = normalizeCommandText(text).replace(TRAILING_PUNCT, "");
  t = t.replace(/^\/([a-z_]+)(?:@[a-z0-9_]{3,64})?/, "$1");          // /stop@SomeBot -> stop
  t = t.replace(POLITE, "").replace(POLITE, "").replace(TRAILING_PUNCT, "").trim();
  return t;
}

/**
 * Whole-message command match only. "stop loss", "stoploss", "start-up",
 * "restart", "nonstop", "قیمت توقف ضرر" never match.
 */
export function detectControlCommand(text: string): "start" | "stop" | null {
  const core = commandCore(text);
  if (START_PHRASES.includes(core)) return "start";
  if (STOP_PHRASES.includes(core)) return "stop";
  return null;
}

/** paper_buy needs an explicit phrase; a bare "paper" (e.g. "paper trading چیه") is not a buy. */
export function looksLikePaperBuy(text: string): boolean {
  const t = normalizeCommandText(text);
  return /(خریدم|خرید کاغذی|ثبت خرید|\bpaper[ -]?buy\b)/i.test(t);
}

// ------------------------------------------------------------------- gate --

export type GateInput = {
  intent: string;
  text: string;
  channelClaimed?: string | null;
  userId?: string | null;
};

export type GateDecision = {
  controlled: boolean;
  allowed: boolean;
  capability: Capability | null;
  reason: string;
  replyFa: string | null;
};

// User-facing text: short, no internal ids. Behaviour (always refuse) is unchanged.
const REFUSE_FA: Record<Capability, string> = {
  ENGINE_CONTROL:
    "⛔ کنترل موتور از طریق گفتگو غیرفعال است.\n" +
    "برای روشن یا خاموش کردن، از دکمه‌های داشبورد محلی استفاده کن. هیچ تغییری اعمال نشد.",
  PAPER_WRITE:
    "⛔ ثبت خرید کاغذی از طریق گفتگو غیرفعال است.\n" +
    "ثبت کاغذی فقط از داشبورد محلی انجام می‌شود و خرید واقعی هرگز انجام نمی‌شود. هیچ تغییری اعمال نشد.",
};

/** Chat-path decision. Deny-by-default for every control capability, every channel. */
export function gateChatControl(input: GateInput): GateDecision {
  const capability = Object.prototype.hasOwnProperty.call(CONTROL_INTENTS, input.intent)
    ? CONTROL_INTENTS[input.intent]
    : null;
  if (!capability) {
    return { controlled: false, allowed: true, capability: null, reason: "NOT_A_CONTROL_INTENT", replyFa: null };
  }
  return {
    controlled: true,
    allowed: false,
    capability,
    reason: "CHAT_PATH_CANNOT_PROVE_LOCAL_DASHBOARD",
    replyFa: REFUSE_FA[capability],
  };
}

// ------------------------------------------------------------------ audit --

export function sha256Hex(s: string): string {
  return createHash("sha256").update(s, "utf8").digest("hex");
}

export function hashId(kind: string, value: string | null | undefined): string {
  const v = String(value ?? "").trim();
  return v ? sha256Hex(`ahos:${kind}:${v}`).slice(0, 16) : "UNKNOWN";
}

function canonicalJson(v: unknown): string {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return `[${v.map(canonicalJson).join(",")}]`;
  const o = v as Record<string, unknown>;
  return `{${Object.keys(o).sort().map((k) => `${JSON.stringify(k)}:${canonicalJson(o[k])}`).join(",")}}`;
}

export type ControlAuditRecord = {
  schema: string;
  ts: string;
  surface: "chat" | "engine_api";
  intent: string;
  capability: Capability | null;
  decision: "ALLOWED" | "REFUSED";
  reason: string;
  channel_claimed: string;
  user_id_hash: string;
  message_sha256: string | null;
  message_len: number | null;
  prev_hash: string;
  entry_hash: string;
};

export interface AuditSink {
  lastHash(): string;
  append(line: string): void;
}

export class MemoryAuditSink implements AuditSink {
  lines: string[] = [];
  lastHash(): string {
    if (!this.lines.length) return GENESIS_HASH;
    return (JSON.parse(this.lines[this.lines.length - 1]) as ControlAuditRecord).entry_hash;
  }
  append(line: string): void {
    this.lines.push(line);
  }
}

export class FileAuditSink implements AuditSink {
  readonly path: string;
  constructor(path: string) {
    this.path = path; // explicit field: node strip-types mode rejects parameter properties
  }
  lastHash(): string {
    if (!existsSync(this.path)) return GENESIS_HASH;
    const fd = openSync(this.path, "r");
    try {
      const size = fstatSync(fd).size;
      if (size === 0) return GENESIS_HASH;
      const len = Math.min(size, 16384);
      const buf = Buffer.alloc(len);
      readSync(fd, buf, 0, len, size - len);
      const lines = buf.toString("utf8").split("\n").filter((l) => l.trim());
      const last = lines[lines.length - 1];
      try {
        return (JSON.parse(last) as ControlAuditRecord).entry_hash || GENESIS_HASH;
      } catch {
        return sha256Hex(last); // torn/garbage tail: chain onto its hash, never rewrite
      }
    } finally {
      closeSync(fd);
    }
  }
  append(line: string): void {
    mkdirSync(dirname(this.path), { recursive: true });
    let prefix = "";
    if (existsSync(this.path)) {
      const fd = openSync(this.path, "r");
      try {
        const size = fstatSync(fd).size;
        if (size > 0) {
          const b = Buffer.alloc(1);
          readSync(fd, b, 0, 1, size - 1);
          if (b[0] !== 0x0a) prefix = "\n"; // isolate a torn tail; never rewrite it
        }
      } finally {
        closeSync(fd);
      }
    }
    appendFileSync(this.path, prefix + line, { encoding: "utf8", mode: 0o600 });
  }
}

export function defaultAuditPath(env: Record<string, string | undefined> = process.env): string {
  const explicit = (env.AHOS_CONTROL_AUDIT_PATH || "").trim();
  if (explicit) return explicit;
  const dataDir = (env.AHOS_DATA_DIR || "").trim() || join(process.cwd(), "data");
  return join(dataDir, "control_audit", "chat_control_audit.jsonl");
}

export function buildAuditRecord(
  p: {
    surface: "chat" | "engine_api";
    intent: string;
    capability: Capability | null;
    decision: "ALLOWED" | "REFUSED";
    reason: string;
    channelClaimed?: string | null;
    userId?: string | null;
    text?: string | null;
  },
  prevHash: string,
  now: Date = new Date(),
): ControlAuditRecord {
  const body = {
    schema: CONTROL_AUDIT_SCHEMA,
    ts: now.toISOString(),
    surface: p.surface,
    intent: p.intent,
    capability: p.capability,
    decision: p.decision,
    reason: p.reason,
    channel_claimed: String(p.channelClaimed ?? "unspecified").slice(0, 32).replace(/[^\w.-]/g, "_") || "unspecified",
    user_id_hash: hashId("user", p.userId),
    message_sha256: p.text == null ? null : sha256Hex(String(p.text)),
    message_len: p.text == null ? null : String(p.text).length,
    prev_hash: prevHash,
  };
  return { ...body, entry_hash: sha256Hex(canonicalJson(body)) };
}

/** Append one audit record; never throws (returns null on failure). */
export function recordControlAudit(
  p: Parameters<typeof buildAuditRecord>[0],
  sink: AuditSink = new FileAuditSink(defaultAuditPath()),
  now?: Date,
): ControlAuditRecord | null {
  try {
    const rec = buildAuditRecord(p, sink.lastHash(), now);
    sink.append(canonicalJson(rec) + "\n");
    return rec;
  } catch {
    return null;
  }
}

/** Verify a chain of JSONL audit lines. Returns index of first bad line, or -1. */
export function verifyAuditLines(lines: string[]): number {
  let prev = GENESIS_HASH;
  for (let i = 0; i < lines.length; i++) {
    let rec: ControlAuditRecord;
    try {
      rec = JSON.parse(lines[i]) as ControlAuditRecord;
    } catch {
      return i;
    }
    if (rec.prev_hash !== prev) return i;
    const { entry_hash, ...body } = rec;
    if (sha256Hex(canonicalJson(body)) !== entry_hash) return i;
    prev = entry_hash;
  }
  return -1;
}
