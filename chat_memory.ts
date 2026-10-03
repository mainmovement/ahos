/**
 * Phase 7b: short per-conversation memory for the chat agent.
 * In-memory only (local gateway process), last N turns, secrets redacted,
 * expires after inactivity. Keys are hashed identities (never raw ids).
 */
import { createHash } from "node:crypto";

export type Turn = { role: "user" | "assistant"; content: string; at: number };

const SECRET_PATTERNS: RegExp[] = [
  /\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}/g,
  /\bAIza[0-9A-Za-z_-]{20,}/g,
  /\b(?:gsk|xai|ghp|gho|github_pat|glpat|xox[abpr])[-_][A-Za-z0-9_-]{12,}/g,
  /\b\d{6,12}:[A-Za-z0-9_-]{30,}\b/g, // telegram bot token
  /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}/g, // JWT
  /\b0x[a-fA-F0-9]{64}\b/g, // EVM private key
  /\bBearer\s+[A-Za-z0-9._~+/=-]{12,}/gi,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
  /\b[A-Za-z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*[=:]\s*\S+/gi,
];

export function redactSecrets(text: string): string {
  let t = String(text ?? "");
  for (const re of SECRET_PATTERNS) t = t.replace(re, "[REDACTED]");
  return t;
}

/**
 * Mission 9.5 m4: strip live one-time confirm codes (and their Persian/English
 * cancel words) so a «تایید ABCD12» never rides from memory into the next
 * Gemini request or the `chat_messages` DB. Only whole-message confirmations are
 * matched — the same anchor chat_actions.parseConfirmation uses — so a sentence
 * that merely contains the word «تایید» is untouched.
 */
const CONFIRM_CODE_WORDS = "(?:تایید|تأیید|تائید|لغو|کنسل|انصراف|confirm|cancel|yes)";
const CONFIRM_CODE_RE = new RegExp(`\\b${CONFIRM_CODE_WORDS}\\s+[A-Z0-9]{6}\\b`, "giu");

export function stripConfirmCodes(text: string): string {
  return String(text ?? "").replace(CONFIRM_CODE_RE, "[کد حذف شد]");
}

export function memoryKey(channel: string | null | undefined, userId: string | null | undefined): string {
  // Mission 9.5 m2: no default to an owner channel. A dashboard caller is keyed
  // by its per-session id, so two browsers never share memory or pending codes;
  // an anonymous caller gets its own anonymous key.
  const raw = `${String(channel ?? "anonymous").toLowerCase()}|${String(userId ?? "")}`;
  return createHash("sha256").update(raw, "utf8").digest("hex").slice(0, 32);
}

export class ConversationMemory {
  private readonly map = new Map<string, Turn[]>();
  private readonly maxTurns: number;
  private readonly ttlMs: number;
  private readonly maxKeys: number;
  private readonly now: () => number;

  constructor(opts: { maxTurns?: number; ttlMs?: number; maxKeys?: number; now?: () => number } = {}) {
    this.maxTurns = opts.maxTurns ?? 10;
    this.ttlMs = opts.ttlMs ?? 6 * 60 * 60 * 1000;
    this.maxKeys = opts.maxKeys ?? 200;
    this.now = opts.now ?? Date.now;
  }

  get(key: string): Turn[] {
    const turns = this.map.get(key) ?? [];
    const last = turns[turns.length - 1];
    if (last && this.now() - last.at > this.ttlMs) {
      this.map.delete(key);
      return [];
    }
    return [...turns];
  }

  /** Store one exchange (user + assistant). Content is redacted, confirm codes
   * are stripped and it is capped — what is remembered is what may leave the
   * process (e.g. for the Gemini helper on a later turn). */
  append(key: string, user: string, assistant: string): void {
    const t = this.now();
    const turns = this.get(key);
    turns.push({ role: "user", content: stripConfirmCodes(redactSecrets(user)).slice(0, 1500), at: t });
    turns.push({ role: "assistant", content: stripConfirmCodes(redactSecrets(assistant)).slice(0, 2000), at: t });
    const keep = turns.slice(-this.maxTurns * 2);
    this.map.delete(key);
    this.map.set(key, keep);
    while (this.map.size > this.maxKeys) {
      const oldest = this.map.keys().next().value;
      if (oldest === undefined) break;
      this.map.delete(oldest);
    }
  }

  clear(key: string): void {
    this.map.delete(key);
  }
}

let defaultMemory: ConversationMemory | null = null;
export function getConversationMemory(): ConversationMemory {
  if (!defaultMemory) defaultMemory = new ConversationMemory();
  return defaultMemory;
}
