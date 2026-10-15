/**
 * M-D6.4 — the globe's land mask, pure helpers plus the URL of the local asset.
 *
 * The land layer's shader needs to know, per dot, whether it sits on land — and
 * it asks the NASA Black Marble water mask rather than re-deriving it. The mask
 * lives at `public/geo/earth_specular_1k.png`, served from the app's own origin,
 * so no runtime request leaves the box (spec §0.5). It is public-domain NASA
 * imagery, i.e. data about where the land is, not art; see `public/geo/README.md`
 * for the provenance chain.
 *
 * Why a mask as well as `landDots.ts`: the lattice decides *where the dots go*
 * and is asserted headlessly (`scripts/land_selftest.ts`). The mask decides
 * *how bright a dot is*: its shoreline is a grey ramp, not a binary edge, so a
 * dot that straddles a coast is dimmed by the fraction of it that is water. That is the cobe model — cobe samples a land-mask texture per dot and
 * multiplies the mask value into the dot's alpha — and it is what keeps the
 * continents soft at the coast while every interior dot is at full, fixed
 * brightness. See `Globe.tsx`'s `LAND_FRAG`.
 *
 * Everything here is free of `window`, `document` and `WebGL`, so the sampling
 * convention is asserted on a machine with no GPU — the only way "the mask's
 * continents line up with the real ones" can be proven rather than eyeballed.
 * That is the mask-versus-atlas section of `scripts/land_selftest.ts`.
 */

export const LAND_MASK_URL = "/geo/earth_specular_1k.png";

const INV_TWO_PI = 1 / (2 * Math.PI);
const INV_PI = 1 / Math.PI;

/**
 * The mask's texture coordinates for a longitude/latitude in radians.
 *
 * Plain equirectangular: column 0 is longitude −180°, row 0 of the *file* is the
 * north pole. Three uploads textures with `flipY` on, which puts the file's row
 * 0 at v = 1 — so latitude enters with a + sign and the north pole samples
 * v = 1, not v = 0. A minus sign here still yields a plausible map with the
 * continents in the wrong hemisphere, which is why the axis is pinned against
 * the atlas in `scripts/land_selftest.ts` rather than eyeballed: the mask is
 * 8-bit greyscale 1 024 × 512, and the atlas agrees with it on 92.3% of a 3°
 * grid (95.4% away from the pole).
 */
export function landMaskUV(lon: number, lat: number): [number, number] {
  return [0.5 + lon * INV_TWO_PI, 0.5 + lat * INV_PI];
}

/**
 * The land weight for a mask sample: the mask is a *water* mask, black over
 * land and white over ocean, so the weight is the inverted sample. Exposed so
 * the polarity is a decision in one place rather than an assumption in two —
 * inverting it by mistake would put dots on the ocean floor and leave the
 * continents dark, and nothing in the render would say which one happened.
 */
export function landWeight(maskSample: number): number {
  return 1 - maskSample;
}
