/**
 * M-D6.1 — the globe's geometry, pure and headless.
 *
 * The observatory's centrepiece is a *point* globe: a field of dots laid out on
 * a sphere, each one a single vertex. The owner's 19:42 list (item 3) names the
 * form — "a dotted or hex-point globe (instanced points, under 30k)" — and the
 * reason it is dots rather than a mapped surface is §0.5's "zero external
 * requests at runtime": a texture map would be a fetch, and a shaded continent
 * globe would be art this project has no license to copy. Points generated from
 * arithmetic are neither.
 *
 * The layout is a Fibonacci lattice rather than random placement or a latitude
 * grid. Random clumps and leaves gaps; a lat/long grid piles points at the poles
 * and visibly rows at the equator. The golden-angle spiral is the standard
 * answer when the requirement is "as even as possible for a given count", and it
 * is even at *any* count — so the T1, T2 and T3 densities all look like the same
 * globe seen at different resolutions, not three different objects.
 *
 * Everything here is deterministic and free of `window`, `document` and
 * `WebGLRenderingContext`, so the layout can be asserted on a machine with no
 * GPU at all — which is the only way a claim like "the dots are evenly spread"
 * can be proven rather than eyeballed.
 */

/** The globe's radius in stage units. The dots sit exactly on it. */
export const GLOBE_RADIUS = 1.1;

/**
 * Lay `count` points on a sphere of `radius` using the golden-angle spiral.
 *
 * Returns a flat `[x, y, z]` attribute, three floats per point. Deterministic by
 * construction: the same count is byte-identical on every machine and every
 * reload, which is also what makes a screenshot comparable between runs.
 */
export function fibonacciSphere(count: number, radius: number = GLOBE_RADIUS): Float32Array {
  const n = Math.max(0, Math.floor(count));
  const out = new Float32Array(n * 3);
  if (n === 0) return out;
  const golden = Math.PI * (Math.sqrt(5) - 1);
  const denom = Math.max(1, n - 1);
  for (let i = 0; i < n; i++) {
    // y walks from the top pole to the bottom; r is the ring's radius at that
    // height, so the points stay on the sphere by construction.
    const y = 1 - (i / denom) * 2;
    const r = Math.sqrt(Math.max(0, 1 - y * y));
    const theta = golden * i;
    const at = i * 3;
    out[at] = Math.cos(theta) * r * radius;
    out[at + 1] = y * radius;
    out[at + 2] = Math.sin(theta) * r * radius;
  }
  return out;
}

/**
 * A deterministic per-point brightness in [0.72, 1.0], so the field reads as
 * filed gold dust rather than a uniform grid of identical dots.
 *
 * A fixed irrational hash, not `Math.random()`: the pattern must not flicker
 * between renders, and two machines must see the same globe.
 */
export function pointShades(count: number): Float32Array {
  const n = Math.max(0, Math.floor(count));
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const h = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
    out[i] = 0.72 + 0.28 * (h - Math.floor(h));
  }
  return out;
}
