import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { buildSkillMarketFromProposals } from "../src/features/missions-b4/lib/skill-market-proposals.ts";

test("skill-market: proposals map to non-demo PARTIAL entries", () => {
  const dir = mkdtempSync(join(tmpdir(), "ahos-prop-"));
  writeFileSync(
    join(dir, "prop_test_1.json"),
    JSON.stringify({
      proposal_id: "prop_test_1",
      created_ts: 1_700_000_000,
      diagnosis: "sample architecture note",
      current_stage: "PROPOSED",
      requires_human: true,
      redteam_verdict: "NEEDS_MORE_DATA",
    }),
    "utf8",
  );
  const snap = buildSkillMarketFromProposals(dir);
  assert.ok(snap);
  assert.equal(snap!.demo, false);
  assert.equal(snap!.entries.length, 1);
  assert.equal(snap!.entries[0].demo, false);
  assert.equal(snap!.entries[0].installState, "BLOCKED");
});
