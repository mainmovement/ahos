import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("message-hub and self-eval snapshot routes exist", () => {
  const root = join(import.meta.dirname, "..", "app", "api");
  assert.ok(readFileSync(join(root, "message-hub", "snapshot", "route.ts"), "utf8").includes("readMessageHub"));
  assert.ok(readFileSync(join(root, "self-evaluation", "snapshot", "route.ts"), "utf8").includes("readSelfEvaluation"));
  assert.ok(readFileSync(join(root, "portable", "snapshot", "route.ts"), "utf8").includes("readPortable"));
  assert.ok(readFileSync(join(root, "ops", "stack", "route.ts"), "utf8").includes("probe(3200)"));
});
