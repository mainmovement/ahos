import test from "node:test";
import assert from "node:assert/strict";
import { ringLayout, ringRotationDelta } from "../lib/rings.ts";

test("12 department rings have individually tilted, distinct, non-overlapping radii", () => {
  const layouts = Array.from({ length: 12 }, (_, i) => ringLayout(i));
  assert.equal(new Set(layouts.map((layout) => layout.radius)).size, 12);
  assert.equal(new Set(layouts.map((layout) => layout.tiltX)).size, 12);
  for (let i = 1; i < layouts.length; i++) {
    const radialGap = layouts[i].radius - layouts[i - 1].radius;
    const maximumTubeDiameter = 2 * (0.012 + 12 * 0.0025);
    assert.ok(radialGap > maximumTubeDiameter, `ring ${i} gap ${radialGap}`);
  }
});

test("each department ring rotates at its own rate and stale rings stop", () => {
  assert.ok(Math.abs(ringRotationDelta(0.5, 0.1, 1, false) - 0.05) < 1e-12);
  assert.ok(Math.abs(ringRotationDelta(1.5, 0.1, 1, false) - 0.15) < 1e-12);
  assert.equal(ringRotationDelta(1.5, 0.1, 1, true), 0);
});
