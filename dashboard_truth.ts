/**
 * GM-03 - dashboard truthfulness helpers (presentation only).
 *
 * Pure functions, no I/O, no authority. They only decide how honestly a
 * value is DISPLAYED:
 *   - evidence older than its freshness limit is STALE, not OK;
 *   - a missing timestamp is UNKNOWN, not OK;
 *   - when the browser's last refresh failed (or the snapshot it holds is
 *     too old) every previously-green status is shown as STALE and the run
 *     pill stops claiming "running".
 * Nothing here can create or upgrade a canonical decision (AGENTS.md TS rule).
 * Run: npm run test:dashboard-truth
 */

export type TruthStatus = "OK" | "STALE" | "UNKNOWN" | "VIOLATION";

/** Evidence may lag the engine interval; anything beyond this is STALE. */
export const MIN_EVIDENCE_FRESHNESS_MS = 10 * 60_000;
/** Multiple of the engine interval tolerated before evidence is STALE. */
export const EVIDENCE_INTERVAL_MULTIPLIER = 3;
/** A browser-held snapshot older than this is STALE even without an error. */
export const VIEW_STALE_AFTER_MS = 90_000;

function toMs(ts: Date | string | number | null | undefined): number | null {
  if (ts === null || ts === undefined || ts === "") return null;
  const ms = ts instanceof Date ? ts.getTime() : typeof ts === "number" ? ts : Date.parse(ts);
  return Number.isFinite(ms) ? ms : null;
}

/** Freshness limit for engine evidence given its configured interval (sec). */
export function evidenceFreshnessLimitMs(intervalSec: number | null | undefined): number {
  const iv = typeof intervalSec === "number" && Number.isFinite(intervalSec) && intervalSec > 0 ? intervalSec : 0;
  return Math.max(MIN_EVIDENCE_FRESHNESS_MS, iv * 1000 * EVIDENCE_INTERVAL_MULTIPLIER);
}

/** OK only when a real timestamp exists and is within the limit. */
export function freshnessStatus(
  ts: Date | string | number | null | undefined,
  nowMs: number,
  maxAgeMs: number,
): TruthStatus {
  const ms = toMs(ts);
  if (ms === null) return "UNKNOWN";
  const age = nowMs - ms;
  // A timestamp from the future (>1 min skew) is not trustworthy evidence.
  if (age < -60_000) return "UNKNOWN";
  return age <= maxAgeMs ? "OK" : "STALE";
}

/**
 * Execution-mode health from the persisted system_state row, not a literal.
 * PAPER_ONLY -> OK; any other non-empty value -> VIOLATION; missing -> UNKNOWN.
 */
export function executionModeStatus(executionMode: string | null | undefined): TruthStatus {
  const m = (executionMode ?? "").trim();
  if (!m) return "UNKNOWN";
  return m === "PAPER_ONLY" ? "OK" : "VIOLATION";
}

/** Paper portfolio is only "OK" when the ledger was read AND mode is PAPER_ONLY. */
export function paperPortfolioStatus(
  executionMode: string | null | undefined,
  ledgerReadable: boolean,
): TruthStatus {
  if (!ledgerReadable) return "UNKNOWN";
  return executionModeStatus(executionMode);
}

/** Last-cycle health: SUCCESS and recent -> OK; SUCCESS but old -> STALE. */
export function lastCycleStatusHealth(
  lastCycleStatus: string | null | undefined,
  lastCycleAt: Date | string | number | null | undefined,
  nowMs: number,
  maxAgeMs: number,
): TruthStatus {
  if (lastCycleStatus !== "SUCCESS") return "UNKNOWN";
  return freshnessStatus(lastCycleAt, nowMs, maxAgeMs) === "OK" ? "OK" : "STALE";
}

export type ViewTruth = {
  stale: boolean;
  reason: "OK" | "REFRESH_FAILED" | "SNAPSHOT_TOO_OLD" | "NO_SNAPSHOT";
  ageMs: number | null;
};

/** Is the snapshot the browser is showing still trustworthy? */
export function deriveViewTruth(input: {
  generatedAt: string | null | undefined;
  lastRefreshError: string | null | undefined;
  nowMs: number;
  staleAfterMs?: number;
}): ViewTruth {
  const gen = toMs(input.generatedAt ?? null);
  const ageMs = gen === null ? null : Math.max(0, input.nowMs - gen);
  if (gen === null) return { stale: true, reason: "NO_SNAPSHOT", ageMs };
  if (input.lastRefreshError) return { stale: true, reason: "REFRESH_FAILED", ageMs };
  if ((ageMs ?? 0) > (input.staleAfterMs ?? VIEW_STALE_AFTER_MS)) {
    return { stale: true, reason: "SNAPSHOT_TOO_OLD", ageMs };
  }
  return { stale: false, reason: "OK", ageMs };
}

const GREEN = new Set(["OK", "SUCCESS", "PASS", "HIGH", "AVAILABLE"]);

/** When the view is stale, nothing may stay green. Others pass through. */
export function presentStatus(status: string, viewStale: boolean): string {
  if (viewStale && GREEN.has(status)) return "STALE";
  return status;
}

/** The run pill may only claim "running" from a fresh view. */
export function presentRunning(running: boolean, viewStale: boolean): "RUNNING" | "STOPPED" | "UNKNOWN" {
  if (viewStale) return "UNKNOWN";
  return running ? "RUNNING" : "STOPPED";
}
