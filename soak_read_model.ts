/**
 * M13 soak read model — the presentation layer's view of the local paper soak.
 *
 * The runner that actually cycles on this host is not the Node engine; it is
 * `scripts/m13_gold_soak.py`, a Python alarm clock that trades a fictional
 * $10 000 bankroll against corroborated XAU prices and writes
 * `reports/grok/M13_SOAK/soak_status.json` after every cycle. The dashboard's
 * telemetry strips show UNKNOWN while that file is the only live telemetry in
 * the building, so this module reads it the same way `canonical_read_model.ts`
 * reads Python's canonical decisions: as an artifact the app *presents* and
 * never as one it joins, scores, or decides from.
 *
 * What this module is allowed to do: parse the file, note its age, hand the
 * strips the numbers the runner already recorded. What it is not allowed to do
 * is anything else. The soak is PAPER_ONLY structurally, in the modules the
 * runner calls — not because a flag here says so — and no value below is derived
 * from anything but the file's own fields. A missing, unreadable, corrupt or
 * empty file is UNAVAILABLE, and an old one is STALE with its age on it; neither
 * is ever filled in with a plausible number, because `UNKNOWN > fabricated`.
 *
 * Staleness is measured in the soak's own cadence: the runner writes every
 * `cycle_interval_sec`, so a last cycle older than three intervals (clamped, so
 * a misconfigured interval cannot make a live soak look dead or a dead one look
 * live) is STALE rather than AVAILABLE.
 */
import { readFile } from "fs/promises";
import path from "path";

export const SOAK_READ_MODEL_VERSION = "m13-soak-read-model-v1";

export type SoakReadStatus = "AVAILABLE" | "STALE" | "UNAVAILABLE";

/** The minimum staleness window, so a tiny interval cannot make age vanish. */
const MIN_STALE_SEC = 1800;
/** The maximum, so a huge interval cannot keep a long-dead soak "live". */
const MAX_STALE_SEC = 86_400;
/** Fallback cadence when the file does not say how often it writes. */
const DEFAULT_INTERVAL_SEC = 900;
/** How many intervals of silence before the reading is STALE. */
const STALE_INTERVALS = 3;

export type SoakRunView = {
  running: boolean;
  cyclesOk: number | null;
  cyclesFailed: number | null;
  lastCycleAt: string | null;
  lastCycleOk: boolean | null;
  lastCycleDurationS: number | null;
  witnessState: string | null;
  witnessReason: string | null;
  priceUsd: number | null;
  spreadPct: number | null;
};

export type SoakGatesView = {
  day: string | null;
  tier: string | null;
  promoted: boolean | null;
  measurablePassed: number | null;
  measurableTotal: number | null;
  unmeasurableCount: number | null;
  readyForOwnerReview: boolean | null;
  openQuestions: string[];
  gateMd: string | null;
};

export type SoakLedgerView = {
  market: string | null;
  bankrollUsd: number | null;
  equityUsd: number | null;
  realizedPnlUsd: number | null;
  cumulativeRealizedPnlUsd: number | null;
  closedTrades: number | null;
  positionOpen: boolean;
  openUnpriced: boolean;
  exitCard: string | null;
  entryPrice: number | null;
  execPrice: number | null;
  lastPrice: number | null;
  qty: number | null;
  notionalUsd: number | null;
  openExposurePct: number | null;
  drawdownPct: number | null;
  breakerState: string | null;
  breakerAllowed: boolean | null;
  witnessState: string | null;
  witnessReason: string | null;
  spreadPct: number | null;
};

export type SoakReadModel = {
  version: string;
  status: SoakReadStatus;
  reason: string | null;
  soak: string | null;
  paperOnly: boolean;
  startedHint: string | null;
  intervalSec: number | null;
  plannedDays: number | null;
  lastCycleAt: string | null;
  /** Age of the last cycle in seconds, for the strips' STALE copy. */
  ageSec: number | null;
  run: SoakRunView | null;
  gates: SoakGatesView | null;
  ledger: SoakLedgerView | null;
  stale: boolean;
  no_invented_evidence: true;
};

export function soakStatusPath(): string {
  const env = (process.env.AHOS_SOAK_STATUS || "").trim();
  if (env) return env;
  return path.join(/* turbopackIgnore: true */ process.cwd(), "reports", "grok", "M13_SOAK", "soak_status.json");
}

export function unavailableSoak(reason: string): SoakReadModel {
  return {
    version: SOAK_READ_MODEL_VERSION,
    status: "UNAVAILABLE",
    reason,
    soak: null,
    paperOnly: true,
    startedHint: null,
    intervalSec: null,
    plannedDays: null,
    lastCycleAt: null,
    ageSec: null,
    run: null,
    gates: null,
    ledger: null,
    stale: false,
    no_invented_evidence: true,
  };
}

function str(v: unknown): string | null {
  return typeof v === "string" && v.trim() !== "" ? v : null;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function booleanish(v: unknown): boolean | null {
  return typeof v === "boolean" ? v : null;
}

function iso(v: unknown): string | null {
  const s = str(v);
  if (!s) return null;
  return Number.isFinite(Date.parse(s)) ? s : null;
}

/**
 * The staleness window, in the soak's own cadence. Three intervals of silence,
 * clamped to a half hour and a day so the interval the file reports cannot by
 * itself make the age reading dishonest.
 */
export function soakStaleAfterSec(intervalSec: number | null): number {
  const interval = num(intervalSec) ?? DEFAULT_INTERVAL_SEC;
  return Math.min(MAX_STALE_SEC, Math.max(MIN_STALE_SEC, STALE_INTERVALS * interval));
}

export function parseSoakStatus(
  raw: unknown,
  nowMs = Date.now(),
  staleAfterSec?: number,
): SoakReadModel {
  if (!raw || typeof raw !== "object") return unavailableSoak("corrupt_soak_status");

  const obj = raw as Record<string, unknown>;
  const intervalSec = num(obj.cycle_interval_sec);
  const lastCycle = obj.last_cycle;
  const lastCycleAt =
    lastCycle && typeof lastCycle === "object" ? iso((lastCycle as Record<string, unknown>).ts) : null;

  if (!lastCycleAt) {
    // A status file with no cycle yet is honest about that, and the strips say
    // UNAVAILABLE rather than showing a zeroed run that never happened.
    return unavailableSoak("no_cycle_recorded");
  }

  const ageSec = (nowMs - Date.parse(lastCycleAt)) / 1000;
  const limit = staleAfterSec ?? soakStaleAfterSec(intervalSec);
  const stale = ageSec > limit;
  const status: SoakReadStatus = stale ? "STALE" : "AVAILABLE";

  const lc = lastCycle as Record<string, unknown>;
  const ledgerRaw = obj.ledger_state;
  const ledger = (ledgerRaw && typeof ledgerRaw === "object" ? ledgerRaw : null) as Record<string, unknown> | null;
  const gateRaw = obj.last_tier_gate;
  const gate = (gateRaw && typeof gateRaw === "object" ? gateRaw : null) as Record<string, unknown> | null;
  const witness = (ledger && typeof ledger.witness === "object" ? ledger.witness : null) as Record<string, unknown> | null;
  const breaker = (ledger && typeof ledger.breaker === "object" ? ledger.breaker : null) as Record<string, unknown> | null;
  const position = (ledger && typeof ledger.position === "object" ? ledger.position : null) as Record<string, unknown> | null;

  const cyclesOk = num(obj.cycles_ok);
  const cyclesFailed = num(obj.cycles_failed);
  const positionOpen = booleanish(lc.position_open) ?? false;

  const run: SoakRunView = {
    // The runner writes after every cycle, so a fresh last cycle is the evidence
    // that it is still cycling — and `cycles_ok` is the count it recorded.
    running: !stale && cyclesOk !== null && cyclesOk > 0,
    cyclesOk,
    cyclesFailed,
    lastCycleAt,
    lastCycleOk: booleanish(lc.ok),
    lastCycleDurationS: num(lc.duration_s),
    witnessState: str(lc.witness_state),
    witnessReason: str(lc.witness_reason),
    priceUsd: num(lc.price_usd),
    spreadPct: num(lc.spread_pct),
  };

  const gates: SoakGatesView | null = gate
    ? {
        day: str(gate.day),
        tier: str(gate.tier),
        promoted: booleanish(gate.promoted),
        measurablePassed: num(gate.measurable_passed),
        measurableTotal: num(gate.measurable_total),
        unmeasurableCount: Array.isArray(gate.unmeasurable) ? gate.unmeasurable.length : null,
        readyForOwnerReview: booleanish(gate.ready_for_owner_review),
        openQuestions: Array.isArray(gate.open_questions)
          ? gate.open_questions.filter((q): q is string => typeof q === "string")
          : [],
        gateMd: str(gate.gate_md),
      }
    : null;

  const ledgerView: SoakLedgerView | null = ledger
    ? {
        market: str(ledger.market),
        bankrollUsd: num(ledger.bankroll_usd),
        equityUsd: num(ledger.equity_usd),
        realizedPnlUsd: num(ledger.realized_pnl_usd),
        cumulativeRealizedPnlUsd: num(ledger.cumulative_realized_pnl_usd),
        closedTrades: num(ledger.closed_trades),
        positionOpen,
        openUnpriced: booleanish(ledger.open_unpriced) ?? false,
        exitCard: str(ledger.exit_card),
        entryPrice: position ? num(position.entry_price) : null,
        execPrice: position ? num(position.exec_price) : null,
        lastPrice: num(ledger.price_usd),
        qty: position ? num(position.qty_oz) : null,
        notionalUsd: position ? num(position.notional_usd) : null,
        openExposurePct: breaker ? num(breaker.open_exposure_pct) : null,
        drawdownPct: breaker ? num(breaker.drawdown_pct) : null,
        breakerState: breaker ? str(breaker.state) : null,
        breakerAllowed: breaker ? booleanish(breaker.allowed) : null,
        witnessState: witness ? str(witness.state) : null,
        witnessReason: witness ? str(witness.reason) : null,
        spreadPct: witness ? num(witness.spread_pct) : null,
      }
    : null;

  return {
    version: SOAK_READ_MODEL_VERSION,
    status,
    reason: stale ? "stale_soak_status" : null,
    soak: str(obj.soak),
    paperOnly: booleanish(obj.paper_only) ?? true,
    startedHint: iso(obj.started_hint),
    intervalSec,
    plannedDays: num(obj.planned_days),
    lastCycleAt,
    ageSec,
    run,
    gates,
    ledger: ledgerView,
    stale,
    no_invented_evidence: true,
  };
}

export async function loadSoakReadModel(nowMs = Date.now()): Promise<SoakReadModel> {
  try {
    const raw = await readFile(soakStatusPath(), "utf8");
    return parseSoakStatus(JSON.parse(raw), nowMs);
  } catch {
    // Missing file, unreadable path, or a half-written cycle: the soak writes
    // this file in place, so a torn read is a real possibility and the honest
    // answer for all of them is UNAVAILABLE, never a last-known-good guess.
    return unavailableSoak("missing_soak_status");
  }
}
