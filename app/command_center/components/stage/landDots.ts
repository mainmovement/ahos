/**
 * M-D6.3 — the globe's land dots, pure and headless.
 *
 * The owner's 00:20 next steps ask for Natural Earth land dots on the globe, and
 * pre-approve exactly the packages that make this honest: `world-atlas` (ISC)
 * ships Natural Earth polygons as TopoJSON, and `topojson-client` (ISC) turns
 * them back into GeoJSON. Both are bundled, not fetched — §0.5's "zero external
 * requests at runtime" still holds, and the globe still carries no copied art.
 *
 * The dots stay ornament. They are all brand gold, because spec §2.3 is explicit
 * that status colours are never decoration: a token's verdict is not expressed by
 * lighting a continent, and the truth badge in the DOM is what says what the
 * evidence said. If land ever has to carry data it must come through
 * `/api/command` as labelled values, not as a change of colour here.
 *
 * Layout: the land is not sampled independently — that would clump in Europe and
 * go sparse over Siberia. A Fibonacci lattice over the whole sphere is filtered
 * to the points that fall inside a land polygon, then subsampled evenly, so the
 * dots are spread *within* the continents at the same density the dust field has
 * over the ocean. The whole sphere is still the input, which is why the poles
 * stay reached: Antarctica and the Arctic Ocean are in the data, not clipped away
 * to save a polygon.
 *
 * Everything here is deterministic and free of `window`, `document` and
 * `WebGLRenderingContext`, so the land can be asserted on a machine with no GPU —
 * the only way "the dots are on the continents" can be proven rather than
 * eyeballed.
 */

// 55 KB, bundled. `land-110m` is the coarsest Natural Earth cut; as a *mask* for
// dots at this scale its coastlines are finer than the dots themselves, so the
// 50m and 10m cuts would cost 10×–60× the bytes for nothing an eye can see.
//
// The import attribute is what bare Node's ESM loader requires for JSON; the
// bundler accepts it too, so one import works in both places.
//
// Relative, not the `@/` alias: the selftest runs this under bare Node with no
// tsconfig path mapping, and the module is pure either way.
import land110m from "world-atlas/land-110m.json" with { type: "json" };
import { feature } from "topojson-client";

import {
  fibonacciSphere,
  GLOBE_RADIUS,
  pointShades,
} from "./globeGeometry.ts";

/** Land dots sit a hair above the dust field, so they read as a layer over it. */
export const LAND_DOTS_RADIUS = GLOBE_RADIUS * 1.004;

/**
 * The polygon machinery below (`POLYGONS`, `isLand`) is the selftest's
 * independent second source: it says where land is, so the NASA mask's
 * continents can be pinned against named geography rather than against
 * themselves. Two sources, one answer — the two-source rule, applied to a map.
 * Nothing in the render path calls it; `landDots` places dots everywhere and the
 * mask selects.
 */
/** A GeoJSON position, as `[lon, lat]` in degrees. */
type Position = number[];
/** A closed ring of positions. */
type Ring = Position[];
/**
 * A polygon: its outer ring first, then its holes. Either may be empty if the
 * atlas is degenerate, which the tests below tolerate rather than throw on.
 */
type Polygon = Ring[];

/**
 * The land polygons in degrees, decoded once. `feature()` applies the TopoJSON
 * transform and quantization, so what lands here is ordinary lon/lat rings.
 *
 * `world-atlas`'s `land` ships as a GeometryCollection holding one dissolved
 * MultiPolygon; `countries` would be a collection of single Polygons. Both are
 * accepted here, so the atlas can be swapped for a finer cut without touching
 * this module — and neither branch is a guess, the selftest pins which one is
 * in use by checking known geography.
 */
const POLYGONS: Polygon[] = (() => {
  const object = land110m.objects.land;
  const geometries = object.geometries ?? [object];
  const polygons: Polygon[] = [];
  for (const geometry of geometries) {
    const decoded = feature(land110m, geometry);
    polygons.push(...asPolygons(decoded.geometry));
  }
  return polygons;
})();

/**
 * Pull the rings out of one decoded geometry. A `Polygon` is one ring list; a
 * `MultiPolygon` is a list of them. Anything else contributes nothing, which
 * keeps a malformed atlas from taking the render down with it.
 */
function asPolygons(geometry: unknown): Polygon[] {
  if (!geometry || typeof geometry !== "object") return [];
  const coords = (geometry as { coordinates?: unknown }).coordinates;
  if (!Array.isArray(coords)) return [];
  const type = (geometry as { type?: unknown }).type;
  if (type === "Polygon") return [coords as unknown as Polygon];
  if (type === "MultiPolygon") {
    return (coords as unknown as Polygon[]).filter((poly) => Array.isArray(poly));
  }
  return [];
}

/**
 * Ray-casting point-in-polygon in equirectangular space. Coastlines here are
 * already split at ±180°, so no ring crosses the antimeridian and the planar
 * test is exact enough for ornament. A candidate that lands exactly on a
 * coastline resolves one way or the other — deterministically, so it never
 * flickers between renders.
 */
function pointInRing(lon: number, lat: number, ring: Ring): boolean {
  let inside = false;
  const m = ring.length;
  for (let i = 0, j = m - 1; i < m; j = i++) {
    const xi = ring[i]![0]!;
    const yi = ring[i]![1]!;
    const xj = ring[j]![0]!;
    const yj = ring[j]![1]!;
    const intersects = yi > lat !== yj > lat;
    if (intersects && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

/** Inside the polygon, accounting for its holes (lakes, enclaves). */
function pointInPolygon(lon: number, lat: number, rings: Ring[]): boolean {
  if (rings.length === 0) return false;
  if (!pointInRing(lon, lat, rings[0]!)) return false;
  for (let h = 1; h < rings.length; h++) {
    if (pointInRing(lon, lat, rings[h]!)) return false;
  }
  return true;
}

/**
 * Is this point on the sphere over land? Exposed for the selftest, which has to
 * be able to ask the same question the sampler asks.
 */
export function isLand(lon: number, lat: number): boolean {
  for (const rings of POLYGONS) {
    if (pointInPolygon(lon, lat, rings)) return true;
  }
  return false;
}

/**
 * `count` dots over the *whole* sphere, as a flat `[x, y, z]` attribute.
 *
 * Owner QA 2026-10-13: the dots were patchy and the continents were not
 * recognizable, because the sampler was subsampling to a small budget
 * (`LAND_FRACTION` 0.2 of the dust count) and even an even subsample of ~4 800
 * dots over the world's land leaves too few per continent to trace a coastline.
 * The fix is the owner's: place at *full* density and let the NASA water mask
 * decide which dots show. That is also the cobe model the vendor kit points at —
 * cobe samples a land-mask texture per dot on a Fibonacci sphere and multiplies
 * the mask into the dot's alpha (`Globe.tsx`'s `LAND_FRAG` already does this).
 *
 * So `landDots` is now a plain Fibonacci lattice over the whole sphere — every
 * candidate, no filtering — and *where land is* is a rendering decision made by
 * the mask, not a geometry decision made here. A dot over the open ocean is
 * still in the buffer; the shader gives it alpha 0 and it costs vertex time, not
 * fill. The count is therefore a *candidate* budget, and only ~29% of it (the
 * earth's land fraction) is visible.
 *
 * Deterministic by construction: the lattice is deterministic, so the same count
 * is the same sphere on every machine.
 *
 * The polygon machinery below (`POLYGONS`, `isLand`) stays for the selftest: it
 * is the independent second source that says where land is, so the mask's
 * continents can be pinned against named geography rather than against
 * themselves. Two sources, one answer — the two-source rule, applied to a map.
 */
export function landDots(
  count: number,
  radius: number = LAND_DOTS_RADIUS,
): Float32Array {
  const n = Math.max(0, Math.floor(count));
  if (n === 0) return new Float32Array(0);
  return fibonacciSphere(n, radius);
}

/**
 * Brighter shading than the dust field (`pointShades` bottoms out at 0.72): the
 * land layer reads as the figure over the ground without needing a second colour.
 * The hash is reused, not duplicated, so this is the same distribution rescaled —
 * one deterministic pattern for the whole globe.
 */
export function landShades(count: number): Float32Array {
  const out = pointShades(count);
  for (let i = 0; i < out.length; i++) {
    out[i] = 0.88 + 0.12 * ((out[i]! - 0.72) / 0.28);
  }
  return out;
}
