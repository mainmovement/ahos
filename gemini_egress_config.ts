/**
 * Mission 9.6 (MN-4): explicit, file-backed owner approval for Gemini egress.
 *
 * Both reviews flagged that the phraser and the chat agent send data to Gemini
 * by default (opt-out env only). The owner has opted in, so the default stays
 * ON — but the approval is now an explicit committed record rather than an
 * implicit absence of an env var, and egress fails closed without it.
 *
 * `config/gemini_egress.json` (overridable with AHOS_GEMINI_EGRESS_CONFIG) is
 * the approval record: it names what is approved, when, by whom, and holds no
 * secret of any kind. Egress for a channel is enabled only when ALL of:
 *   - the record exists, parses and matches the schema,
 *   - `approved` is true and `revokedAt` is null,
 *   - the channel is listed in `scope`,
 *   - no kill switch is set (AHOS_GEMINI_EGRESS, or the channel's own switch).
 *
 * A missing, malformed or tampered record disables egress. The record is small
 * enough to audit by hand; a sha256 of the committed file is pinned by the
 * static test so a silent substitution is caught.
 */
import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import process from "node:process";

/** Same shape as gemini_phraser.EnvMap, declared locally to keep this module
 * dependency-free (gemini_phraser imports this, not the other way round). */
export type EnvMap = Record<string, string | undefined>;

export type EgressScope = "phraser" | "chat_agent";

export type EgressRecord = {
  approved: boolean;
  approvedAt: string;
  approvedBy: string;
  scope: string[];
  recipients: string[];
  note?: string;
  revokedAt: string | null;
};

const DEFAULT_PATH = "config/gemini_egress.json";

/** Kill switches: any of these disables egress regardless of the record. */
function killed(scope: EgressScope, src: EnvMap): boolean {
  const off = (v: unknown) => ["off", "0", "false", "none"].includes(String(v ?? "").trim().toLowerCase());
  if (off(src.AHOS_GEMINI_EGRESS)) return true;
  if (scope === "phraser") return off(src.AHOS_PHRASER);
  return off(src.AHOS_CHAT_AGENT);
}

let recordPath = "";
let recordKey = "";
let cached: EgressRecord | null = null;
let cachedError: string | null = null;

function resolvePath(src: EnvMap): string {
  const p = String(src.AHOS_GEMINI_EGRESS_CONFIG ?? "").trim();
  return resolve(process.cwd(), p || DEFAULT_PATH);
}

/**
 * Reads and validates the approval record. Returns null when the record is
 * missing, unparseable, or does not match the schema — egress then fails closed.
 * The (path, size, mtime) key means an edit or a swapped file is picked up
 * immediately and a stable file costs one stat per process.
 */
export function readEgressRecord(src: EnvMap = process.env): EgressRecord | null {
  const path = resolvePath(src);
  let key = path;
  try {
    const st = statSync(path);
    key = `${path}:${st.size}:${Math.floor(st.mtimeMs)}`;
  } catch {
    cachedError = "EGRESS_RECORD_MISSING";
    return null;
  }
  if (key !== recordKey || cached === undefined) {
    recordKey = key;
    cached = null;
    cachedError = null;
    try {
      const raw = JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
      if (typeof raw.approved !== "boolean") throw new Error("approved must be boolean");
      if (typeof raw.approvedAt !== "string" || !raw.approvedAt) throw new Error("approvedAt missing");
      if (typeof raw.approvedBy !== "string" || !raw.approvedBy) throw new Error("approvedBy missing");
      if (!Array.isArray(raw.scope) || !raw.scope.every((s) => typeof s === "string")) throw new Error("scope must be a string array");
      if (!Array.isArray(raw.recipients) || !raw.recipients.every((s) => typeof s === "string")) throw new Error("recipients must be a string array");
      if (raw.revokedAt !== null && typeof raw.revokedAt !== "string") throw new Error("revokedAt must be null or a string");
      cached = raw as unknown as EgressRecord;
    } catch (e) {
      cachedError = `EGRESS_RECORD_INVALID:${(e as Error).message}`;
    }
  }
  return cached;
}

/** Why the last read failed (missing/invalid), for diagnostics and tests. */
export function egressRecordError(): string | null {
  return cachedError;
}

/** Reset the memo. Production code never needs this; tests do. */
export function resetEgressRecordCache(): void {
  recordPath = "";
  recordKey = "";
  cached = null;
  cachedError = null;
}

/**
 * True only when the owner has explicitly approved this channel AND no kill
 * switch is set. This is the single decision point for sending anything to
 * Gemini; both getDefaultPhraser and getDefaultChatAgent go through it.
 */
export function egressApproved(scope: EgressScope, src: EnvMap = process.env): boolean {
  if (killed(scope, src)) return false;
  const rec = readEgressRecord(src);
  if (!rec) return false;
  if (!rec.approved) return false;
  if (rec.revokedAt !== null) return false;
  return rec.scope.includes(scope);
}
