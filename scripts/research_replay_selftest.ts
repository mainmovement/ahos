import assert from "node:assert/strict";
import test from "node:test";
import { buildResearchFromReplay } from "../src/features/missions-b2/lib/research-replay.ts";

const SAMPLE = `
| Gold daily | 0.86 | 0.55 | **NO PROVEN EDGE · NO PROVEN EDGE** |
| Oil daily | 0.36 | 0.25 | **NO PROVEN EDGE · NO PROVEN EDGE** |
`;

test("research replay: parses NO PROVEN EDGE rows honestly", () => {
  const s = buildResearchFromReplay(SAMPLE, "2026-10-21T12:00:00Z");
  assert.ok(s);
  assert.equal(s!.demo, false);
  assert.equal(s!.hypotheses.length, 2);
  assert.ok(s!.hypotheses.every((h) => h.status === "REJECTED"));
  assert.equal(s!.weeklyExam?.itemsPassedUnseen, 0);
});
