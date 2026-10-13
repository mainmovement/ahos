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
 * Since the 2026-10-13 rescale the render path no longer filters dots by
 * polygon: `landDots` fills the whole sphere and the NASA water mask in
 * `public/geo/` decides which dots are visible. So the layer's honesty now rests
 * on the *mask* agreeing with the atlas, and the M-D6.4 section below asserts
 * that against named continents and over a grid of the whole globe — an axis
 * flipped either way still renders plausible continents, and only a second
 * source catches it.
 *
 * Runs without a GPU, without `window`, and without three.js.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import { inflateSync } from "node:zlib";
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

  it("covers the whole sphere, because the mask — not the sampler — selects land", () => {
    // Owner QA 2026-10-13: `landDots` is now a full Fibonacci lattice and the
    // NASA water mask decides which dots render. So the honest assertion is no
    // longer "every dot is over land" — most candidates are deliberately over
    // ocean, and the shader zeroes them — but "the lattice reaches everywhere",
    // which is what lets the mask trace a coastline at any orientation.
    const p = landDots(4000);
    const bands = new Set<number>();
    for (let i = 0; i < p.length; i += 3) {
      bands.add(Math.round(dotLat(p, i) / 3));
    }
    assert.ok(bands.size > 58, `only ${bands.size} latitude bands — the lattice does not cover the globe`);
  });

  it("spreads the dots across the world rather than one continent", () => {
    // The failure mode that a land sampler actually has: taking the first N
    // inside-land points off a latitude-ordered spiral would pile them into
    // Eurasia. Spread is checked with the same band test the dust field uses, but
    // on longitude — Eurasia and Africa together span less than half of it.
    const p = landDots(4000);
    const bands = new Set<number>();
    for (let i = 0; i < p.length; i += 3) {
      bands.add(Math.round(dotLon(p, i) / 3));
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
      const lat = dotLat(p, i);
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

describe("M-D6.4: the NASA mask draws the same continents the atlas names", () => {
  // The render path no longer asks the atlas where a dot goes — `landDots` fills
  // the whole sphere and the NASA water mask decides which dots are visible. So
  // the honest question moved: not "are the dots on land" but "does the mask's
  // land agree with an independent source of where land is". A mask checked
  // against itself would pass every test and still show the continents upside
  // down, which is exactly the failure a v-axis sign error produces and exactly
  // what this section exists to catch. The atlas is the second source.
  it("puts the named continents on land in both sources", () => {
    // Deep interiors, not capitals: at 1 024 px the mask is 0.35°/px at the
    // equator, and a coastline is not a fair test of a coastline.
    for (const [name, lon, lat] of [
      ["Africa", 20, 2],
      ["southern Africa", 22, -22],
      ["Europe", 15, 50],
      ["Central Asia", 75, 45],
      ["East Asia", 112, 38],
      ["North America", -97, 42],
      ["South America", -58, -12],
      ["Australia", 133, -25],
      ["Antarctica", 0, -80],
      ["Greenland", -45, 74],
    ] as const) {
      assert.equal(isLand(lon, lat), true, `${name} is not land in the atlas`);
      assert.equal(maskLand(lon, lat), true, `${name} is water in the mask`);
    }
  });

  it("keeps the oceans and the great seas water in both sources", () => {
    for (const [name, lon, lat] of [
      ["the mid-Atlantic", -32, 38],
      ["the mid-Pacific", -155, -5],
      ["the southern Indian Ocean", 85, -35],
      ["the Arctic Ocean", 25, 86],
      ["the Coral Sea", 155, -20],
    ] as const) {
      assert.equal(isLand(lon, lat), false, `${name} is land in the atlas`);
      assert.equal(maskLand(lon, lat), false, `${name} is land in the mask`);
    }
  });

  it("agrees with the atlas over the whole globe", () => {
    // A 3° grid: coarse enough to run headless, fine enough that a flipped or
    // offset axis cannot hide. The rate is logged because the residual is real —
    // both sources are coarse, so the disagreement lives at the coastlines and
    // the number is evidence, not a pass/fail in itself.
    //
    // Measured 92.3% (2026-10-13). The residual is not spread evenly: outside the
    // south polar band it is 95.4%, and what is left there is coastline and small
    // islands — Greenland's coast, the Canadian Arctic, Madagascar, New Zealand —
    // which a 110 m atlas and a 1 024 px mask cannot both resolve. The one
    // systematic difference is the pole itself: the mask's Antarctica reaches
    // -90° and the 110 m atlas's stops short, so the mask is the more complete of
    // the two there. A meridian offset — the bug the test below guards — would
    // disagree along a whole line of longitude, not at scattered coastal points.
    const { agree, total } = compareSources(3);
    const rate = agree / total;
    console.log(`  mask/atlas agreement: ${agree}/${total} = ${(rate * 100).toFixed(1)}%`);
    // 90% leaves room for those coarsenesses while a flipped axis lands near 50%.
    assert.ok(rate >= 0.9, `mask and atlas agree on only ${(rate * 100).toFixed(1)}% of the globe`);
  });

  it("is sensitive to the axis, not passing vacuously", () => {
    // The convention above could be wrong in a way that still scores well, so
    // the inverted convention is run too and must fail: if it also agreed, the
    // test above would be proving nothing. Measured 50.7% against the shipped
    // convention's 92.3% — the two hemispheres' land is partly symmetric, so
    // an inverted axis is not a total loss, just a clear one.
    const { agree, total } = compareSources(3, { flipLatitude: true });
    const rate = agree / total;
    console.log(`  inverted v-axis agreement: ${agree}/${total} = ${(rate * 100).toFixed(1)}%`);
    assert.ok(
      rate < 0.6,
      `an inverted latitude axis still scores ${(rate * 100).toFixed(1)}% — the agreement test is not sensitive`,
    );
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

/**
 * A dot's latitude, decoded the way the layer's own convention means it. The
 * poles are clamped because the round trip through `LAND_DOTS_RADIUS` is not
 * exact: `GLOBE_RADIUS * 1.004` is not representable, so dividing a pole's
 * coordinate back by it overshoots 1 by ~3.5e-8 and `asin` is NaN outside
 * [-1, 1]. The land shader clamps for exactly this reason
 * (`clamp(vDir.y, -1.0, 1.0)` in `Globe.tsx`), and the assertions here decode
 * the same way the shader does. The full lattice the rescale ships reaches both
 * poles, which is what surfaced it — the old land-filtered sampler dropped them,
 * because a dot at a NaN latitude is in no polygon.
 */
function dotLat(p: Float32Array, i: number): number {
  const y = Math.min(1, Math.max(-1, p[i + 1]! / LAND_DOTS_RADIUS));
  return (Math.asin(y) * 180) / Math.PI;
}

/** A dot's longitude — `atan2` is finite everywhere its argument is. */
function dotLon(p: Float32Array, i: number): number {
  return (Math.atan2(p[i + 2]!, p[i]!) * 180) / Math.PI;
}

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

/**
 * The NASA water mask, decoded with no third-party help. `sharp` is only a
 * transitive dependency here, so a selftest that reached for it would be
 * asserting something about the build's internals instead of about the globe;
 * an 8-bit, non-interlaced PNG is `zlib` plus a scanline unfilter.
 *
 * Held as raw bytes in *file* row order: row 0 is the PNG's first row, i.e. the
 * top of the image as any viewer shows it, i.e. the north pole for a north-up
 * equirectangular mask.
 */
const MASK = (() => {
  let bytes: Buffer;
  try {
    bytes = fs.readFileSync(new URL("../public/geo/earth_specular_1k.png", import.meta.url));
  } catch (e) {
    throw new Error(
      "the land mask public/geo/earth_specular_1k.png is missing or unreadable; " +
        "the globe's continents cannot be asserted without it",
    );
  }
  return decodePng(bytes);
})();

/**
 * Inflate an 8-bit non-interlanced PNG into its raw samples. Anything else is a
 * format the asset does not use, and a thrown error here is better than a
 * silent wrong answer from a partial decoder.
 */
function decodePng(bytes: Buffer): {
  width: number;
  height: number;
  channels: number;
  data: Uint8Array;
} {
  for (let i = 0; i < 8; i++) {
    if (bytes[i] !== [137, 80, 78, 71, 13, 10, 26, 10][i]) {
      throw new Error("the land mask is not a PNG");
    }
  }
  const chunks: Array<[string, Buffer]> = [];
  let at = 8;
  while (at + 8 <= bytes.length) {
    const len = bytes.readUInt32BE(at);
    const type = bytes.toString("latin1", at + 4, at + 8);
    const body = bytes.subarray(at + 8, at + 8 + len);
    chunks.push([type, body]);
    at += 12 + len; // length, type, body, CRC
    if (type === "IEND") break;
  }
  const ihdr = chunks.find(([type]) => type === "IHDR")?.[1];
  if (!ihdr) throw new Error("the land mask's PNG has no IHDR");
  const width = ihdr.readUInt32BE(0);
  const height = ihdr.readUInt32BE(4);
  const bitDepth = ihdr[8];
  const colourType = ihdr[9];
  const interlace = ihdr[12];
  if (bitDepth !== 8) throw new Error(`the land mask is ${bitDepth}-bit; this decoder handles 8-bit only`);
  if (interlace !== 0) throw new Error("the land mask is interlaced; this decoder handles non-interlaced images only");
  const channels = colourType === 0 ? 1 : colourType === 2 ? 3 : colourType === 6 ? 4 : -1;
  if (channels < 0) throw new Error(`the land mask uses PNG colour type ${colourType}; this decoder handles 0, 2 and 6`);

  const raw = inflateSync(Buffer.concat(chunks.filter(([type]) => type === "IDAT").map(([, body]) => body)));
  const stride = width * channels;
  const data = new Uint8Array(height * stride);
  let src = 0;
  let prev: Uint8Array | undefined;
  for (let y = 0; y < height; y++) {
    const filter = raw[src++];
    const line = raw.subarray(src, src + stride);
    src += stride;
    const out = data.subarray(y * stride, (y + 1) * stride);
    for (let x = 0; x < stride; x++) {
      const a = x >= channels ? out[x - channels]! : 0;
      const b = prev ? prev[x]! : 0;
      const c = x >= channels && prev ? prev[x - channels]! : 0;
      let value: number;
      switch (filter) {
        case 0: value = line[x]!; break;
        case 1: value = line[x]! + a; break;
        case 2: value = line[x]! + b; break;
        case 3: value = line[x]! + Math.floor((a + b) / 2); break;
        case 4: {
          // Paeth, exactly as the PNG spec writes it.
          const p = a + b - c;
          const pa = Math.abs(p - a);
          const pb = Math.abs(p - b);
          const pc = Math.abs(p - c);
          value = line[x]! + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c);
          break;
        }
        default: throw new Error(`the land mask uses PNG filter ${filter} on row ${y}`);
      }
      out[x] = value & 0xff;
    }
    prev = out;
  }
  return { width, height, channels, data };
}

const INV_TWO_PI = 1 / (2 * Math.PI);
const INV_PI = 1 / Math.PI;
/**
 * Is the mask's land at this lon/lat? The mask is a *water* mask — bright over
 * ocean, dark over land, with a grey ramp at the shore — so land is a sample
 * below mid-grey, and the ramp is what lets a dot straddling a coast fade
 * rather than snap.
 *
 * Row 0 of the file is the north pole, and this samples the file's own rows —
 * which is the shader's convention once `three` uploads with `flipY` on and
 * puts the file's row 0 at v = 1 (see `Globe.tsx`). Sampling it the other way
 * renders the same continents upside down, Africa pointing at the sky, and the
 * agreement rate above is the only thing that says which is which.
 */
function maskLand(lon: number, lat: number, flipLatitude: boolean = false): boolean {
  const lonRad = (lon * Math.PI) / 180;
  const latRad = (lat * Math.PI) / 180;
  const u = (((lonRad * INV_TWO_PI + 0.5) % 1) + 1) % 1;
  const v = flipLatitude ? 0.5 + latRad * INV_PI : 0.5 - latRad * INV_PI;
  const col = Math.min(MASK.width - 1, Math.max(0, Math.round(u * (MASK.width - 1))));
  const row = Math.min(MASK.height - 1, Math.max(0, Math.round(v * (MASK.height - 1))));
  const sample = MASK.data![(row * MASK.width + col) * MASK.channels]!;
  return sample < 128;
}

/**
 * How often the mask and the atlas answer the same question the same way over a
 * lat/lon grid. `flipLatitude` re-samples with the v axis inverted — it is what
 * proves the agreement figure is sensitive to the axis instead of passing
 * vacuously.
 */
function compareSources(step: number, { flipLatitude = false } = {}): { agree: number; total: number } {
  let agree = 0;
  let total = 0;
  for (let lat = -90 + step / 2; lat < 90; lat += step) {
    for (let lon = -180 + step / 2; lon < 180; lon += step) {
      total++;
      if (maskLand(lon, lat, flipLatitude) === isLand(lon, lat)) agree++;
    }
  }
  return { agree, total };
}
