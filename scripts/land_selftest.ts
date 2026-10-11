/**
 * M-D6.3 land-dot selftest — the dots are on the continents, as an assertion.
 *
 * Run: npm run test:land
 * Self-test, not independent verification.
 *
 * The M-D6.1 selftest proves the *dust* is even. This one proves the thing that
 * is actually new: that the land layer is where the atlas says land is. A bug
 * here is invisible to any rendering check — a sign error in `atan2` still
 * produces a plausible-looking dot pattern, just on the wrong meridian — so the
 * assertions are geographic rather than geometric. Known places have known
 * answers: Paris is land, the mid-Atlantic is not, and the Sahara is land while
 * the Caspian is not.
 *
 * Runs without a GPU, without `window`, and without three.js.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  LAND_DOTS_RADIUS,
  isLand,
  landDots,
  landShades,
} from "../components/stage/landDots.ts";
import {
  GLOBE_RADIUS,
  fibonacciSphere,
} from "../components/stage/globeGeometry.ts";

describe("M-D6.3: the atlas is decoded the way GeoJSON means", () => {
  it("agrees with geography on places an atlas should not get wrong", () => {
    // lon, lat — the GeoJSON convention, east-positive and north-positive.
    for (const [name, lon, lat, expected] of [
      ["Paris", 2.35, 48.86, true],
      ["Tehran", 51.39, 35.69, true],
      ["Cape Town", 18.42, -33.93, true],
      ["mid-Atlantic", -30, 40, false],
      ["mid-Pacific", -150, 0, false],
      ["Antarctic coast", 0, -78, true],
      ["the Caspian", 51.5, 41.5, false],
      ["the Black Sea", 34, 43, false],
      ["Hudson Bay", -85, 62, false],
      ["the Bering Sea", -175, 55, false],
      ["the Sahara", 10, 24, true],
      ["the Australian outback", 132, -25, true],
      ["Greenland's north", -40, 82, true],
    ] as const) {
      assert.equal(
        isLand(lon, lat),
        expected,
        `${name} (${lon}, ${lat}) is classified wrong`,
      );
    }
  });

  it("says where the 110m cut is imprecise, instead of hiding it", () => {
    // Natural Earth at 110m carves the Caspian and the Black Sea out of the land
    // but leaves the Great Lakes in, so a dot or two lands on Lake Superior. The
    // layer is ornament with no data attached, so a dot a few hundred kilometres
    // misplaced costs nothing — but it is asserted here rather than buried, and
    // if land ever has to be geographically accurate the atlas must move to
    // `land-50m` and this test rewritten against it.
    assert.equal(isLand(-88, 47), true, "Lake Superior is no longer land in this atlas");
  });

  it("reads the whole globe, not a hemisphere or a band", () => {
    // A decoder that drops a sign or halves the range would leave half the world
    // ocean and the other half dense. Sample both halves and both hemispheres.
    const samples: Array<[string, number, number]> = [
      ["north-east", 90, 45],
      ["north-west", -90, 45],
      ["south-east", 120, -30],
      ["south-west", -120, -30],
    ];
    const counts = samples.map(([, lon, lat]) =>
      // Count land in a 20° box around each sample, at a density the sampler uses.
      boxLand(lon, lat, 20, 400),
    );
    // No quadrant is empty — land exists in all four — and none is full.
    for (let i = 0; i < counts.length; i++) {
      assert.ok(counts[i]! > 0, `${samples[i]![0]} found no land at all`);
      assert.ok(counts[i]! < 400, `${samples[i]![0]} is entirely land`);
    }
  });
});

describe("M-D6.3: the land dots sit on the sphere and on the land", () => {
  it("places every dot at the land radius", () => {
    for (const count of [200, 2000, 5000]) {
      const p = landDots(count);
      assert.equal(p.length, count * 3, `asked for ${count} dots, got another count`);
      for (let i = 0; i < p.length; i += 3) {
        const r = Math.hypot(p[i]!, p[i + 1]!, p[i + 2]!);
        assert.ok(
          Math.abs(r - LAND_DOTS_RADIUS) < 1e-5,
          `dot ${i / 3} sits at radius ${r}, not ${LAND_DOTS_RADIUS}`,
        );
        for (const c of [p[i]!, p[i + 1]!, p[i + 2]!]) {
          assert.ok(Number.isFinite(c), "a coordinate is NaN");
        }
      }
    }
  });

  it("puts every dot over land", () => {
    const p = landDots(3000);
    for (let i = 0; i < p.length; i += 3) {
      const lat = (Math.asin(p[i + 1]! / LAND_DOTS_RADIUS) * 180) / Math.PI;
      const lon = (Math.atan2(p[i + 2]!, p[i]!) * 180) / Math.PI;
      assert.ok(
        isLand(lon, lat),
        `dot ${i / 3} at (${lon.toFixed(1)}, ${lat.toFixed(1)}) is not on land`,
      );
    }
  });

  it("spreads the dots across the world rather than one continent", () => {
    // The failure mode that a land sampler actually has: taking the first N
    // inside-land points off a latitude-ordered spiral would pile them into
    // Eurasia. Spread is checked with the same band test the dust field uses, but
    // on longitude — Eurasia and Africa together span less than half of it.
    const p = landDots(4000);
    const bands = new Set<number>();
    for (let i = 0; i < p.length; i += 3) {
      const lon = (Math.atan2(p[i + 2]!, p[i]!) * 180) / Math.PI;
      bands.add(Math.round(lon / 3));
    }
    assert.ok(
      bands.size > 60,
      `only ${bands.size} distinct longitude bands — the dots are clumped on one continent`,
    );
  });

  it("reaches the polar land the data has, without clipping it away", () => {
    // Antarctica is land and Greenland nearly reaches the pole. A clip added to
    // keep the poles tidy would delete both.
    const p = landDots(4000);
    let south = Infinity;
    let north = -Infinity;
    for (let i = 0; i < p.length; i += 3) {
      const lat = (Math.asin(p[i + 1]! / LAND_DOTS_RADIUS) * 180) / Math.PI;
      south = Math.min(south, lat);
      north = Math.max(north, lat);
    }
    assert.ok(south < -70, `no land dot south of -70° (reached ${south.toFixed(1)})`);
    assert.ok(north > 70, `no land dot north of 70° (reached ${north.toFixed(1)})`);
  });

  it("is deterministic across runs", () => {
    const a = landDots(1500);
    const b = landDots(1500);
    assert.equal(a.length, b.length);
    for (let i = 0; i < a.length; i++) {
      assert.equal(a[i], b[i], "two runs disagree about a dot");
    }
  });

  it("shades every dot brighter than the dust, in range", () => {
    const s = landShades(2000);
    assert.equal(s.length, 2000);
    for (const v of s) {
      assert.ok(v >= 0.88 && v <= 1.0, `shade ${v} outside [0.88, 1.0]`);
    }
  });

  it("holds up at the largest count a tier would ask for", () => {
    // The highest tier's budget, plus headroom. This exercises the full polygon
    // pass and the subsample's arithmetic, and a NaN from the clamp or the
    // shortfall branch would surface here as a coordinate off the sphere.
    const p = landDots(24_000);
    assert.equal(p.length, 24_000 * 3);
    for (let i = 0; i < p.length; i += 3) {
      const r = Math.hypot(p[i]!, p[i + 1]!, p[i + 2]!);
      assert.ok(
        Math.abs(r - LAND_DOTS_RADIUS) < 1e-5,
        `dot ${i / 3} is at radius ${r} — the subsample emitted a zero or a NaN`,
      );
    }
  });
});

describe("M-D6.3: the two layers are distinguishable", () => {
  it("sits the land layer just outside the dust field", () => {
    assert.ok(
      LAND_DOTS_RADIUS > GLOBE_RADIUS,
      "land dots must sit above the dust or they z-fight with it",
    );
    // But not so far that the globe grows a visible shell.
    assert.ok(
      LAND_DOTS_RADIUS - GLOBE_RADIUS < GLOBE_RADIUS * 0.02,
      "the land layer is too far from the surface to read as the same globe",
    );
  });

  it("keeps the dust field complete when land is sampled from it", () => {
    // The sampler draws candidates from `fibonacciSphere` at a higher multiple;
    // it must not consume or depend on the dust field's own buffer.
    const dust = fibonacciSphere(6000);
    const before = Array.from(dust);
    landDots(1200);
    assert.deepEqual(Array.from(dust), before, "sampling land mutated the dust field");
  });
});

/** How many of `n` evenly-spread points in a box around a place are land. */
function boxLand(lon: number, lat: number, half: number, n: number): number {
  let hits = 0;
  for (let i = 0; i < n; i++) {
    const h = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
    const f = h - Math.floor(h);
    const g = Math.sin(i * 7.13 + 3.7) * 9301.37;
    const f2 = g - Math.floor(g);
    const lo = lon + (f - 0.5) * 2 * half;
    const la = lat + (f2 - 0.5) * 2 * half;
    if (isLand(lo, la)) hits++;
  }
  return hits;
}
