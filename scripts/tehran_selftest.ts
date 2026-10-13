/**
 * M-D6.6 Tehran-mark selftest — the bead is where the atlas says Tehran is.
 *
 * Run: npm run test:tehran
 * Self-test, not independent verification.
 *
 * The land selftest proves the *layer* decodes geography correctly. This one
 * proves the thing that is new: that one named place, rendered as a bead, lands
 * where the atlas puts it rather than on a mirror image. A wrong bead is still a
 * plausible bead on a plausible globe — an `atan2` sign error puts it on the
 * opposite meridian and nothing in the render breaks — so the assertions are
 * geometric round-trips and geographic facts, and they run with no GPU.
 *
 * Runs without a GPU, without `window`, and without three.js.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isLand,
  landDots,
  LAND_DOTS_RADIUS,
} from "../components/stage/landDots.ts";
import { GLOBE_RADIUS } from "../components/stage/globeGeometry.ts";
import {
  geoToPosition,
  MARK_RADIUS,
  TEHRAN_LAT,
  TEHRAN_LON,
  tehranMarkPosition,
} from "../components/stage/tehranMark.ts";

/** The decoder the land layer uses, inverted back to lon/lat — the arbiter. */
function decode(p: [number, number, number], r: number): [number, number] {
  const [x, y, z] = p;
  const lat = (Math.asin(y / r) * 180) / Math.PI;
  const lon = (Math.atan2(z, x) * 180) / Math.PI;
  return [lon, lat];
}

describe("M-D6.6: the mark is where the atlas says Tehran is", () => {
  it("round-trips through the land layer's own decoder, on both hemispheres", () => {
    // If `geoToPosition` and `landDots.ts` disagreed about which way is east, or
    // whether +y is north, this would come back as the antipode or a mirror.
    for (const [name, lon, lat] of [
      ["Tehran", TEHRAN_LON, TEHRAN_LAT],
      ["Quito", -78.47, -0.18],          // west, on the equator
      ["Wellington", 174.78, -41.29],    // the antipodes, date-line-adjacent
      ["Murmansk", 33.08, 68.97],        // high north, where a lat bug bites
      ["McMurdo", 166.67, -77.85],       // deep south, likewise
    ] as const) {
      const r = 3.7;                      // any radius; the frame is scale-free
      const back = decode(geoToPosition(lon, lat, r), r);
      assert.ok(Math.abs(back[0] - lon) < 1e-9, `${name}: lon came back as ${back[0]}`);
      assert.ok(Math.abs(back[1] - lat) < 1e-9, `${name}: lat came back as ${back[1]}`);
    }
  });

  it("is land under the bead, so the mark is not anchored to an ocean", () => {
    // The same atlas the dots are filtered by. If this ever flips to false the
    // bead would float in the Caspian or the Indian Ocean, which is a worse lie
    // than no bead at all.
    assert.equal(isLand(TEHRAN_LON, TEHRAN_LAT), true);
  });

  it("sits on the northern and eastern half of the globe, as Tehran is", () => {
    const [x, y, z] = tehranMarkPosition();
    // +y is north, +z is east, and a 51° E longitude is on the +x/+z quadrant.
    assert.ok(y > 0, `Tehran is north of the equator, got y=${y}`);
    assert.ok(z > 0, `Tehran is east of Greenwich, got z=${z}`);
    assert.ok(x > 0, `a 51° E longitude is on the +x/+z quadrant, got x=${x}`);
  });

  it("never lands on a land dot, and never leaves the atmosphere", () => {
    // Outside the dot layer so the dots cannot cap the bead; inside the shell so
    // it reads as part of the globe rather than as a fourth chain ring.
    assert.ok(
      MARK_RADIUS > LAND_DOTS_RADIUS,
      `the mark at ${MARK_RADIUS} must clear the dots at ${LAND_DOTS_RADIUS}`,
    );
    assert.ok(
      MARK_RADIUS < GLOBE_RADIUS * 1.15,
      `the mark at ${MARK_RADIUS} is outside the atmosphere at ${GLOBE_RADIUS * 1.15}`,
    );
    // And it is planted in the middle of the dot field, not at its edge: inland
    // Iran, not the coast. A bead marooned from every dot would look like a star.
    const pos = tehranMarkPosition();
    const dots = landDots(4000, LAND_DOTS_RADIUS);   // flat [x,y,z]*n
    let nearest = Infinity;
    for (let i = 0; i < dots.length; i += 3) {
      nearest = Math.min(
        nearest,
        Math.hypot(dots[i]! - pos[0], dots[i + 1]! - pos[1], dots[i + 2]! - pos[2]),
      );
    }
    assert.ok(
      nearest < GLOBE_RADIUS * 0.08,
      `the bead is too far from the nearest land dot (${nearest})`,
    );
  });

  it("is deterministic, so the bead does not flicker between renders", () => {
    const a = tehranMarkPosition();
    const b = tehranMarkPosition();
    assert.deepEqual(a, b);
  });

  it("follows the radius it is given, so it scales with the globe", () => {
    const at = (r: number) => tehranMarkPosition(r);
    assert.deepEqual(at(MARK_RADIUS * 2)[0], at(MARK_RADIUS)[0] * 2);
    assert.deepEqual(at(MARK_RADIUS * 2)[1], at(MARK_RADIUS)[1] * 2);
    assert.deepEqual(at(MARK_RADIUS * 2)[2], at(MARK_RADIUS)[2] * 2);
  });
});
