import test from "node:test";
import assert from "node:assert/strict";
import { computeStrictness } from "../lib/gate.ts";

test("computeStrictness from counts", () => {
  assert.equal(computeStrictness({ absorbed: 3, dissipated: 1 }), 0.25);
  assert.equal(computeStrictness({ absorbed: 0, dissipated: 0 }), 0.5);
});

test("computeStrictness uses provided strictness", () => {
  assert.equal(computeStrictness({ absorbed: 1, dissipated: 9, strictness: 0.42 }), 0.42);
});

test("computeStrictness clamps", () => {
  assert.equal(computeStrictness({ absorbed: 0, dissipated: 0, strictness: 2 }), 1);
});