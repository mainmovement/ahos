import assert from "node:assert/strict";
import test from "node:test";
import { parseMissionsFromSoakTierGate } from "../src/features/missions-b2/lib/missions-soak-fallback.ts";

test("missions soak fallback: tier_gate open questions become PARTIAL rows", () => {
  const parsed = parseMissionsFromSoakTierGate({
    last_tier_gate: {
      ts: "2026-10-21T12:00:00Z",
      ok: true,
      tier: "T0",
      measurable_passed: 4,
      measurable_total: 10,
      open_questions: ["M-REGIME-4: owner act needed"],
      ready_for_owner_review: false,
    },
  });
  assert.ok(parsed);
  assert.equal(parsed!.missions.length, 2);
  assert.equal(parsed!.missions[0].id, "M13-TIER-GATE");
  assert.equal(parsed!.missions[1].id, "M-REGIME-4");
  assert.equal(parsed!.missions[1].blockedOwner, true);
});
