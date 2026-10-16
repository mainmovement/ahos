import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { buildMapTargets, particleTextureSize } from "../lib/mapTargets.ts";

const world = JSON.parse(await readFile(new URL("../public/geo/world.geo.json", import.meta.url), "utf8"));

test("quality maps to exact fixed GPGPU texture dimensions", () => {
  assert.equal(particleTextureSize("low"), 64);
  assert.equal(particleTextureSize("medium"), 128);
  assert.equal(particleTextureSize("high"), 256);
  assert.equal(64 ** 2, 4096);
  assert.equal(128 ** 2, 16384);
  assert.equal(256 ** 2, 65536);
});

test("map targets sample bundled outlines and filled countries, including Iran", () => {
  const result = buildMapTargets(world, 128);
  assert.equal(result.sampledPoints, 16384);
  assert.equal(result.data.length, 16384 * 4);
  assert.ok(result.featuresWithPaths >= 170, `country path count ${result.featuresWithPaths}`);
  assert.ok(result.iranPoints > 0, "expected gold-marked Iran map targets");
  for (let i = 0; i < result.data.length; i += 4) {
    assert.ok(result.data[i] >= -2.21 && result.data[i] <= 2.21);
    assert.ok(result.data[i + 1] >= -1.42 && result.data[i + 1] <= 1.42);
    assert.ok(result.data[i + 2] === 0);
  }
});
