import assert from "node:assert/strict";
import test from "node:test";
import { buildScienceRadarFromSoak } from "../src/features/missions-b4/lib/science-radar-soak.ts";
import { buildWeeklyExamFromSoak } from "../src/features/missions-b4/lib/weekly-exam-soak.ts";

const STATUS = {
  last_cycle: {
    ts: "2026-10-21T12:00:00Z",
    witness_state: "VERIFIED",
    witness_reason: "min_sources_met (2 independent: ['goldapi_spot', 'yahoo_gc_futures']), spread 0.3%",
  },
  last_tier_gate: {
    kind: "tier_gate",
    day: "2026-10-21",
    ok: true,
    tier: "T0",
    measurable_passed: 4,
    measurable_total: 10,
    open_questions: ["M-REGIME-4: owner act needed"],
    ready_for_owner_review: false,
  },
};

test("soak bindings: radar witnesses and tier gate exam are non-demo PARTIAL sources", () => {
  const radar = buildScienceRadarFromSoak(STATUS, "2026-10-21T12:00:00Z");
  assert.ok(radar);
  assert.equal(radar!.demo, false);
  assert.equal(radar!.items.length, 2);
  const exam = buildWeeklyExamFromSoak(STATUS, "2026-10-21T12:00:00Z");
  assert.ok(exam);
  assert.equal(exam!.runs.length, 1);
  assert.equal(exam!.runs[0].demo, false);
  assert.equal(exam!.runs[0].state, "PARTIAL");
});
