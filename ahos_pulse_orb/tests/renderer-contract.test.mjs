import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../components/PulseOrb.tsx", import.meta.url), "utf8");
const browserTest = await readFile(new URL("../scripts/capture-screens.mjs", import.meta.url), "utf8");

test("scene/GPGPU initializer is not keyed to changing data props and exposes a counter", () => {
  assert.match(source, /\/\/ --- main init effect ---[\s\S]*?\}, \[webglOk, reduced\]\);/);
  assert.match(source, /__pulseOrbRendererCreations/);
  assert.match(source, /dataset\.rendererCreations/);
  assert.doesNotMatch(source, /\}, \[webglOk, reduced, (?:health|signals|departments|gate|calm)/);
});

test("Playwright harness changes props 50 times and compares renderer counts", () => {
  assert.match(browserTest, /50 prop updates \(test\)/);
  assert.match(browserTest, /counter !== afterChurn/);
});
