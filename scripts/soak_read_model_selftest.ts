/**
 * soak_read_model selftest.
 *
 * Pins the properties that make the soak read model safe to wire to the
 * dashboard: a missing or corrupt file is UNAVAILABLE and never a guess, a stale
 * one is STALE with an age, a live one maps the runner's own fields without
 * inventing any, and the soak's paper-only status is carried rather than
 * upgraded into anything actionable.
 */
import assert from "node:assert/strict";
import test from "node:test";

import {
  parseSoakStatus,
  soakStaleAfterSec,
  unavailableSoak,
} from "../soak_read_model.ts";

const NOW_MS = Date.parse("2026-10-13T14:31:00Z");
const CYCLE_AT = "2026-10-13T14:30:54Z";

/** The shape the runner actually writes, reduced to the fields this model reads. */
function realish(over: Record<string, unknown> = {}) {
  return {
    soak: "M13-GOLD-PAPER",
    paper_only: true,
    started_hint: "2026-10-13T14:30:57Z",
    cycle_interval_sec: 900.0,
    planned_days: 6.872,
    cycles_ok: 150,
    cycles_failed: 0,
    last_cycle: {
      ts: CYCLE_AT,
      kind: "cycle",
      ok: true,
      cycle: 169,
      witness_state: "VERIFIED",
      witness_reason: "min_sources_met (2 independent)",
      price_usd: 4178.6,
      spread_pct: 0.4845867818159966,
      equity_usd: 9993.808,
      position_open: true,
      recorded: true,
      duration_s: 2.93,
    },
    last_tier_gate: {
      day: "2026-10-13",
      tier: "T0",
      promoted: false,
      measurable_passed: 1,
      measurable_total: 4,
      unmeasurable: ["regime_coverage", "cost_model", "sharpe"],
      ready_for_owner_review: false,
      open_questions: ["M-REGIME-4: ...", "M-DD-BACKTEST: ..."],
      gate_md: "reports/grok/M13_SOAK/2026-10-13_tier_gate.md",
    },
    ledger_state: {
      bankroll_usd: 10000.0,
      closed_trades: 1,
      cumulative_realized_pnl_usd: -6.191974941486933,
      cycle: 169,
      equity_usd: 9993.808,
      exit_card: "PT-X1-v1",
      market: "gold",
      open_unpriced: false,
      paper_only: true,
      price_usd: 4178.6,
      realizable_equity_usd: 9990.533,
      settled_trades: 1,
      position: {
        cycle: 64,
        entry_price: 4183.949951,
        exec_price: 4188.1339,
        notional_usd: 1000.0,
        qty_oz: 0.2387698253326929,
      },
      breaker: {
        allowed: true,
        daily_loss_pct: 0.0,
        drawdown_pct: 0.061919749414864785,
        open_exposure_pct: 10.006195811372361,
        reasons: [],
        state: "ARMED",
        weekly_loss_pct: 0.06195811372362918,
      },
      witness: {
        reason: "min_sources_met (2 independent)",
        spread_pct: 0.4845867818159966,
        state: "VERIFIED",
        tolerance_pct: 1.0,
      },
    },
    ...over,
  } as Record<string, unknown>;
}

test("missing or corrupt status is unavailable and invents nothing", () => {
  const missing = unavailableSoak("missing_soak_status");
  assert.equal(missing.status, "UNAVAILABLE");
  assert.equal(missing.run, null);
  assert.equal(missing.ledger, null);
  assert.equal(missing.gates, null);
  assert.equal(missing.paperOnly, true);
  assert.equal(missing.no_invented_evidence, true);

  assert.equal(parseSoakStatus(null).status, "UNAVAILABLE");
  assert.equal(parseSoakStatus("not json").status, "UNAVAILABLE");
  assert.equal(parseSoakStatus({}).status, "UNAVAILABLE");
  assert.equal(parseSoakStatus({ cycles_ok: 5 }).status, "UNAVAILABLE");
});

test("a live soak maps the runner's own fields, not derived ones", () => {
  const m = parseSoakStatus(realish(), NOW_MS);
  assert.equal(m.status, "AVAILABLE");
  assert.equal(m.stale, false);
  assert.equal(m.soak, "M13-GOLD-PAPER");
  assert.equal(m.paperOnly, true);
  assert.equal(m.lastCycleAt, CYCLE_AT);
  assert.equal(m.ageSec, 6);

  assert.equal(m.run?.running, true);
  assert.equal(m.run?.cyclesOk, 150);
  assert.equal(m.run?.cyclesFailed, 0);
  assert.equal(m.run?.lastCycleOk, true);
  assert.equal(m.run?.witnessState, "VERIFIED");
  assert.equal(m.run?.priceUsd, 4178.6);

  assert.equal(m.gates?.tier, "T0");
  assert.equal(m.gates?.promoted, false);
  assert.equal(m.gates?.measurablePassed, 1);
  assert.equal(m.gates?.measurableTotal, 4);
  assert.equal(m.gates?.unmeasurableCount, 3);
  assert.equal(m.gates?.readyForOwnerReview, false);
  assert.equal(m.gates?.openQuestions.length, 2);

  assert.equal(m.ledger?.market, "gold");
  assert.equal(m.ledger?.bankrollUsd, 10000.0);
  assert.equal(m.ledger?.equityUsd, 9993.808);
  assert.equal(m.ledger?.cumulativeRealizedPnlUsd, -6.191974941486933);
  assert.equal(m.ledger?.closedTrades, 1);
  assert.equal(m.ledger?.positionOpen, true);
  assert.equal(m.ledger?.openUnpriced, false);
  assert.equal(m.ledger?.exitCard, "PT-X1-v1");
  assert.equal(m.ledger?.entryPrice, 4183.949951);
  assert.equal(m.ledger?.lastPrice, 4178.6);
  assert.equal(m.ledger?.qty, 0.2387698253326929);
  assert.equal(m.ledger?.notionalUsd, 1000.0);
  assert.equal(m.ledger?.drawdownPct, 0.061919749414864785);
  assert.equal(m.ledger?.openExposurePct, 10.006195811372361);
  assert.equal(m.ledger?.breakerState, "ARMED");
  assert.equal(m.ledger?.breakerAllowed, true);
  assert.equal(m.ledger?.witnessState, "VERIFIED");
});

test("a soak older than three intervals is STALE, and still reports", () => {
  const old = "2026-10-13T10:00:00Z";
  const m = parseSoakStatus(realish({ last_cycle: { ts: old, ok: true } }), NOW_MS);
  assert.equal(m.status, "STALE");
  assert.equal(m.stale, true);
  assert.equal(m.reason, "stale_soak_status");
  // The numbers are still the runner's own — age disqualifies freshness, not the
  // reading, and the strips show the age rather than blanking to UNKNOWN.
  assert.equal(m.run?.cyclesOk, 150);
  assert.equal(m.run?.running, false);
  assert.equal(m.ledger?.equityUsd, 9993.808);
});

test("a cycle that failed is carried, not smoothed into a success", () => {
  const m = parseSoakStatus(
    realish({ last_cycle: { ts: CYCLE_AT, ok: false, witness_state: "UNRESOLVED" }, cycles_failed: 2 }),
    NOW_MS,
  );
  assert.equal(m.status, "AVAILABLE");
  assert.equal(m.run?.lastCycleOk, false);
  assert.equal(m.run?.cyclesFailed, 2);
  assert.equal(m.run?.witnessState, "UNRESOLVED");
});

test("a position held unpriced is shown as unpriced, never as priced", () => {
  const m = parseSoakStatus(
    realish({
      ledger_state: {
        open_unpriced: true,
        price_usd: null,
        position: { entry_price: 4183.949951, exec_price: 4188.1339, notional_usd: 1000.0, qty_oz: 0.2387 },
      },
    }),
    NOW_MS,
  );
  assert.equal(m.status, "AVAILABLE");
  assert.equal(m.ledger?.openUnpriced, true);
  assert.equal(m.ledger?.lastPrice, null);
  // A null price must not fall back to the entry price: pricing on one source is
  // exactly what the witness law refuses, and the display must not either. The
  // entry is still the entry — it is just not a price.
  assert.equal(m.ledger?.entryPrice, 4183.949951);
});

test("staleness is measured in the soak's own cadence, clamped", () => {
  assert.equal(soakStaleAfterSec(900), 2700);
  assert.equal(soakStaleAfterSec(10), 1800);   // a tiny interval cannot shrink the window
  assert.equal(soakStaleAfterSec(60_000), 86_400); // a huge one cannot extend it past a day
  assert.equal(soakStaleAfterSec(null), 2700);  // a file with no cadence falls back
});
