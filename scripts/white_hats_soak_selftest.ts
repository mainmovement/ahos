import test from "node:test";
import assert from "node:assert/strict";
import { buildSoakWhiteHatsSnapshot } from "../src/features/white-hats/lib/soak-snapshot.ts";

test("soak snapshot is never demo and stays PAPER_ONLY", () => {
  const snap = buildSoakWhiteHatsSnapshot({
    soak: {
      last_cycle: { ts: "2026-10-20T12:00:00Z", witness_state: "VERIFIED", witness_reason: "ok" },
      ledger_state: { breaker: { state: "ARMED", drawdown_pct: 0.1, open_exposure_pct: 5 } },
      last_m42_reconcile: { ts: "2026-10-20T12:00:00Z", verdict: "CLEAN", head_hash: "abc123" },
    },
    judgeText: "Verdict: CLEAN",
    reconcileText: "Verdict: CLEAN",
    generatedAt: "2026-10-20T12:00:00Z",
    sourceLabel: "test",
  });
  assert.equal(snap.demo, false);
  assert.equal(snap.realTrading, false);
  assert.equal(snap.executionMode, "PAPER_ONLY");
  assert.ok(snap.inspectors.length >= 2);
  assert.equal(snap.decisions.length, 0);
});
