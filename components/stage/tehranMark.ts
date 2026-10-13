/**
 * M-D6.6 — the Tehran mark, pure and headless.
 *
 * The M-D6 spec names one place on the globe: "Tehran mark". Not as data — the
 * observatory is Persian, the shell is RTL, and a single gold bead on the globe
 * says where the room is looking from without claiming anything about a market.
 * Spec §2.3 still holds: this bead is ornament in brand gold, it is not a
 * verdict, and it never lights up to signal one. The truth badge in the DOM says
 * what the evidence said.
 *
 * The coordinates come from the same atlas the land layer uses (Natural Earth;
 * `scripts/land_selftest.ts` already asserts `isLand(TEHRAN_LON, TEHRAN_LAT)`).
 * The position is the exact inverse of `landDots.ts`' convention —
 * `lat = asin(y / r)`, `lon = atan2(z, x)` — so the bead lands on the very point
 * the atlas calls Tehran rather than on a meridian-flipped or pole-swapped
 * lookalike. A sign error here would still render a plausible bead on a globe;
 * only the round-trip assertion can catch it, which is why this module is pure
 * and asserts without a GPU.
 *
 * Free of `window`, `document` and `WebGLRenderingContext`, like the rest of the
 * stage's geometry modules.
 */
// Relative, not the `@/` alias: the selftest runs this under bare Node with no
// tsconfig path mapping, and the module is pure either way. Same convention as
// `landDots.ts`.
import { GLOBE_RADIUS } from "./globeGeometry.ts";
import { LAND_DOTS_RADIUS } from "./landDots.ts";

/**
 * Where the atlas puts Tehran. Tehran 35.69° N, 51.39° E — the GeoJSON
 * convention the whole stage uses: longitude east-positive, latitude
 * north-positive, both in degrees.
 */
export const TEHRAN_LON = 51.39;
export const TEHRAN_LAT = 35.69;

/**
 * The bead's own radius, in the globe's units. It sits just outside the land-dot
 * layer (`GLOBE_RADIUS * 1.004`) so the dots never cap it, and well inside the
 * atmosphere shell (`GLOBE_RADIUS * 1.15`) so it is part of the globe rather
 * than one of the chain rings' orbits.
 */
export const MARK_RADIUS = GLOBE_RADIUS * 1.016;

/**
 * Degrees → the globe's own cartesian frame. The inverse of the convention
 * `landDots.ts` decodes with, kept here so a mark and the dots beneath it cannot
 * disagree about which way is east.
 *
 * lon 0, lat 0 lands on the +x axis; +z is east, +y is north. This is the frame
 * `sun.ts` and `globeGeometry.ts` already assume, so the sun's terminator and
 * the bead are on one globe, not two.
 */
export function geoToPosition(
  lon: number,
  lat: number,
  radius: number,
): [number, number, number] {
  const lonRad = (lon * Math.PI) / 180;
  const latRad = (lat * Math.PI) / 180;
  const cosLat = Math.cos(latRad);
  return [
    radius * cosLat * Math.cos(lonRad),
    radius * Math.sin(latRad),
    radius * cosLat * Math.sin(lonRad),
  ];
}

/** Tehran's position on a globe of the given radius, or `MARK_RADIUS` by default. */
export function tehranMarkPosition(
  radius: number = MARK_RADIUS,
): [number, number, number] {
  return geoToPosition(TEHRAN_LON, TEHRAN_LAT, radius);
}
