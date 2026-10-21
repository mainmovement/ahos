import test from "node:test";
import assert from "node:assert/strict";
import { buildSoakNewsroomSnapshot } from "../src/features/newsroom/lib/soak-snapshot.ts";

test("soak newsroom: witness sources, no invented stories, PAPER_ONLY", () => {
  const snap = buildSoakNewsroomSnapshot({
    last_cycle: { ts: "2026-10-20T12:00:00Z", witness_state: "VERIFIED" },
    ledger_state: {
      witness: {
        state: "VERIFIED",
        quotes: [
          { provider_id: "goldapi_spot", instrument: "spot", observed_at: 1792537990 },
          { provider_id: "yahoo_gc_futures", instrument: "futures", observed_at: 1792537400 },
        ],
      },
    },
  });
  assert.ok(snap);
  assert.equal(snap!.realTrading, false);
  assert.equal(snap!.executionMode, "PAPER_ONLY");
  assert.equal(snap!.stories.length, 0);
  assert.equal(snap!.sources.length, 2);
  assert.ok(snap!.telemetry.adapter.startsWith("soak:"));
});
