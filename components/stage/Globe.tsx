/**
 * M-D6.1 — the point globe: the observatory's centrepiece, hanging above the
 * shamseh floor.
 *
 * What it is: a field of gold dots on a Fibonacci lattice (see
 * `globeGeometry.ts`), wrapped around a dark lacquer body, with a fresnel
 * atmosphere (`Atmosphere.tsx`) that puts a warm halo along the silhouette.
 * Everything is generated in code except one 111 KB land mask (see below), so
 * §0.5's "zero external requests at runtime" holds — the mask is served from
 * the app's own origin as `/geo/earth_specular_1k.png` — and §1's "generated
 * procedurally (no copied art)" holds with it, the mask being public-domain
 * *data* about where the land is rather than art.
 *
 * What it deliberately is not: a *data* globe. The continents it traces
 * (M-D6.3) are ornament — they carry no values, they do not light up on a
 * verdict, and a token's result is never expressed by brightening a region. The
 * truth badge in the DOM says what the evidence said. Everything here is still
 * one glow only — the brand gold — because spec §2.3 forbids status colours as
 * decoration.
 *
 * Geography, where it appears, comes from licensed-free Natural Earth polygons
 * via `world-atlas` + `topojson-client`, bundled rather than fetched, and from
 * the NASA Black Marble water mask in `public/geo/` (public domain, copied from
 * the owner's vendor kit per the 18:00 rule). Both stay ornament: if land ever
 * has to mean something, the values must arrive through `/api/command` as
 * labelled data — never as a colour change here.
 *
 * Tiers. Spec §11's ladder sets the density; the counts stay under the 30k the
 * owner's list caps a point globe at (T3 is 24 000 dust + 4 800 land), and T1
 * costs two draw calls with no postprocessing. The fresnel rim is one overdrawn
 * shell, not a bloom pass — at T2/T3 the real bloom chain arrives with M-D5.6's
 * pipeline and may replace it.
 */
"use client";

import { Suspense, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { useTexture } from "@react-three/drei";

import { useStageStore } from "@/components/stage/store";
import { stageColors } from "@/components/stage/themeColors";
import { fibonacciSphere, GLOBE_RADIUS, pointShades } from "@/components/stage/globeGeometry";
import { landDots, landShades, LAND_DOTS_RADIUS } from "@/components/stage/landDots";
import { LAND_MASK_URL } from "@/components/stage/landMask";
import { sunDirection, terminatorWeight } from "@/components/stage/sun";
import { Atmosphere } from "@/components/stage/Atmosphere";

/** Spec §8.1: idle motion is 0.5°/s — one full turn in twelve minutes. */
const IDLE_RAD_PER_SEC = (0.5 * Math.PI) / 180;

/** An aesthetic axial tilt, so the globe reads as a planet and not a ball bearing. */
const TILT = 0.31;
/**
 * Owner QA 00:24: the globe was too small and floating above the floor ring. 1.6x
 * fills the ring the way the owner asked, and as a side effect it spreads the same
 * dot count over ~2.56x the screen area, which is most of why the silhouette
 * stopped stacking into hot spots — see the dot opacity below.
 */
const SCALE = 1.6;

/**
 * Where the globe's group sits, and how large it is. Exported so the rings
 * (M-D6.5) can be seated on the *same* centre and scale without re-deriving
 * either — the two must agree exactly or the orbits drift off the planet.
 *
 * The floor's ring surface sits at y = -0.5 + 0.002, and the globe is a sphere
 * of `SCALE * GLOBE_RADIUS`, so seating it on the ring is
 * `ringY + SCALE * GLOBE_RADIUS`. The tilt does not enter that arithmetic — a
 * sphere's extent is the same in every orientation.
 */
export const GLOBE_POSITION: [number, number, number] = [0, -0.498 + SCALE * GLOBE_RADIUS, 0];
export const GLOBE_SCALE = SCALE;

/**
 * M-D6.4: the night side keeps a floor rather than going black. A globe that is
 * half invisible reads as broken, and the dust field is what makes the globe read
 * as a globe at all — so at night it dims to a low ember instead of vanishing.
 * Land stays brighter than dust at night, because the continents are the layer
 * the eye follows across the terminator.
 *
 * Owner QA 04:16: the night side read as a second, dimmer day rather than as
 * night, at T1 as well as T3. Measured on a frozen sun so the two captures sit
 * on the same terminator, the floors were the cause: at T3 the brightest night
 * stacks read 248.9 and at T1 248.5, i.e. the same white-gold as the day side,
 * because a dot's base is multiplied by the floor and the additive ones above it
 * still saturate. Bringing both floors down keeps the ordering (land above dust)
 * while letting the night hemisphere go properly dark: the same pair now reads
 * 164.1 at T3 and 200.4 at T1, and every luminance band above 32 dropped at
 * both tiers. The floors were halved rather than removed — the night side must
 * still be a globe, not a hole.
 */
const DUST_NIGHT = 0.07;
const LAND_NIGHT = 0.16;

/**
 * The atmosphere's tuning is the vendor kit's own defaults (see
 * `Atmosphere.tsx`): `scale` 1.15, `coefficient` 0.1, `power` 3.5. These are
 * taken as-is rather than hand-tuned — the old rim went through two rounds of
 * exponent tuning that changed nothing, because two of its three knobs were
 * inert on a back-facing fragment. Only the shell's subdivision is ours, and it
 * follows the tier so T1's halo is a 32×32 and T2/T3's a 64×64.
 */
const SHELL_SEGMENTS_T3 = 64;
/**
 * How often the terminator is recomputed. The sun moves at 15°/hour and the
 * globe's idle spin is 0.5°/s, so a second is half a degree of travel — well
 * inside the dot spacing, which makes the refresh invisible while keeping the
 * per-frame cost off the render loop.
 */
const TERMINATOR_REFRESH_S = 1.0;

/** Rotation axes, allocated once for the per-second sun transform. */
const UP_Y = new THREE.Vector3(0, 1, 0);
const AXIS_Z = new THREE.Vector3(0, 0, 1);

/**
 * The sun in the globe's own frame. The group's transform is `Ry(spin) * Rz(tilt)`,
 * so the inverse — applied right-to-left — is `Rz(-tilt) * Ry(-spin)`. Doing it to
 * the *sun* rather than to every dot is what keeps the terminator at one vector
 * per refresh instead of a matrix per dot, and it is exact, not an approximation.
 */
function sunLocalFor(spin: number, date: Date): THREE.Vector3 {
  const [x, y, z] = sunDirection(date);
  return new THREE.Vector3(x, y, z)
    .applyAxisAngle(UP_Y, -spin)
    .applyAxisAngle(AXIS_Z, -TILT)
    .normalize();
}

/**
 * One dot field's colours, lit by a sun already in the globe's frame. Pure: the
 * same base, positions and sun give the same buffer, which is what makes the
 * mount-time lighting and the per-second refresh provably agree.
 */
function litColors(
  base: Float32Array,
  positions: Float32Array,
  invR: number,
  sun: THREE.Vector3,
  night: number,
): THREE.BufferAttribute {
  const arr = new Float32Array(base.length);
  const n = base.length / 3;
  const [sx, sy, sz] = [sun.x, sun.y, sun.z];
  for (let i = 0; i < n; i++) {
    const at = i * 3;
    const w = terminatorWeight(
      [positions[at]! * invR, positions[at + 1]! * invR, positions[at + 2]! * invR],
      [sx, sy, sz],
    );
    const lit = night + (1 - night) * w;
    arr[at] = base[at]! * lit;
    arr[at + 1] = base[at + 1]! * lit;
    arr[at + 2] = base[at + 2]! * lit;
  }
  return new THREE.BufferAttribute(arr, 3);
}

/**
 * Re-light an existing attribute in place, as the world turns. Mutating the
 * attribute's own array is what avoids rebuilding 28 800 dots' worth of geometry
 * every second; `needsUpdate` is what makes the change reach the card.
 */
function relight(
  base: Float32Array,
  attribute: THREE.BufferAttribute,
  positions: Float32Array,
  invR: number,
  sun: THREE.Vector3,
  night: number,
): void {
  const arr = attribute.array as Float32Array;
  if (arr.length !== base.length) return;
  const n = base.length / 3;
  const [sx, sy, sz] = [sun.x, sun.y, sun.z];
  for (let i = 0; i < n; i++) {
    const at = i * 3;
    const w = terminatorWeight(
      [positions[at]! * invR, positions[at + 1]! * invR, positions[at + 2]! * invR],
      [sx, sy, sz],
    );
    const lit = night + (1 - night) * w;
    arr[at] = base[at]! * lit;
    arr[at + 1] = base[at + 1]! * lit;
    arr[at + 2] = base[at + 2]! * lit;
  }
  attribute.needsUpdate = true;
}

/**
 * A soft round point, painted on a canvas at startup so no image is fetched.
 * A square point at this density reads as a grid of pixels; a soft one reads as
 * dust, which is the whole look.
 */
function softPointTexture(): THREE.Texture {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const g = ctx.createRadialGradient(
      size / 2, size / 2, 0,
      size / 2, size / 2, size / 2,
    );
    g.addColorStop(0, "rgba(255,255,255,1)");
    g.addColorStop(0.32, "rgba(255,255,255,0.72)");
    g.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

/**
 * The land layer's shaders, ported from cobe (MIT, ~5 kB WebGL dotted globe;
 * see `vendor_assets/globe/reference/cobe-2.0.1`). cobe samples a land-mask
 * texture per dot and shades each dot in the fragment shader, at a *fixed*
 * alpha with no distance fade — and it is the fade that makes a sparse,
 * low-tier dot field read as faint: the old soft radial sprite was at full
 * alpha only in its centre few pixels, so a dot whose visible core is one or
 * two pixels contributes almost nothing additively over a dark body.
 *
 * The disc is therefore hard-edged and a fixed screen size. `uPxSize` is in
 * framebuffer pixels and is multiplied by the renderer's pixel ratio in JS, so
 * a dot covers the same *screen* area at every tier and every DPR, and a dot at
 * the globe's limb is exactly as large as one dead centre — no perspective
 * attenuation, which is the other half of "faint at the edges".
 *
 * The mask term keeps the continents honest at the coast: the polygon sampler
 * in `landDots.ts` decides where a dot goes, and the NASA water mask decides
 * how much of it shows, so a dot straddling a shoreline is dimmed by the
 * fraction of it that is water. Interior land is at the fixed alpha, which is
 * the cobe look the owner's kit points at.
 *
 * The day/night terminator is *not* re-derived here: the colour attribute
 * already carries it (see `litColors`/`relight`), so this shader only shapes
 * the dot and weights it by the mask, and M-D6.4's verified sun wiring stays
 * the single place the sun is applied.
 *
 * `precision` is set because a WebGL1 context is still possible at T1 and the
 * default there is not guaranteed. `vertexColors: true` on the material makes
 * three declare `attribute vec3 color`, so it is not redeclared here.
 */
const LAND_VERT = /* glsl */ `
  varying vec3 vDir;
  varying vec3 vColor;
  uniform float uPxSize;
  void main() {
    vColor = color;
    // The dot's own direction from the globe's centre, in the geometry's frame —
    // the same frame landDots.ts used for its lon/lat, so the mask's continents
    // land where the sampler put the dots.
    vDir = normalize(position);
    gl_PointSize = uPxSize;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;
const LAND_FRAG = /* glsl */ `
  precision mediump float;
  uniform sampler2D uMask;
  uniform float uAlpha;
  uniform float uFeather;
  varying vec3 vDir;
  varying vec3 vColor;
  void main() {
    // A hard-edged disc, not a soft sprite: uFeather is a third of the radius,
    // so the dot is solid out to two thirds of its edge and fades over the rest.
    // Widening this is not a coverage lever — see the sweep table on landDotPx.
    float r = length(gl_PointCoord - vec2(0.5)) * 2.0;
    float disc = 1.0 - smoothstep(1.0 - uFeather, 1.0, r);
    // lon/lat from the dot's direction — the arithmetic in landMask.ts's
    // landMaskUV, in GLSL, pinned against the same named geography.
    float lon = atan(vDir.z, vDir.x);
    float lat = asin(clamp(vDir.y, -1.0, 1.0));
    vec2 uv = vec2(0.5 + lon * 0.15915494309189535, 0.5 - lat * 0.3183098861837907);
    float land = 1.0 - texture2D(uMask, uv).r;
    gl_FragColor = vec4(vColor, disc * uAlpha * land);
  }
`;

/**
 * The land dot's screen size, and why it is not a constant. It ramps with the
 * count the tier actually draws, and the reason is arithmetic: the land is a
 * fixed 20% of the dots at every tier, so a tier with a quarter of the budget
 * draws a quarter as many discs over the *same* sphere. T1's 1 200 do not
 * overlap, and at a fixed 5.5 px each they leave gaps a coastline falls through —
 * which is owner QA 02:48's item 6, "the continents do not read at T1", and it is
 * a *sparsity* problem, not a brightness one. Backing the whole layer off to fix
 * the dense tiers' stacking was what made it appear (see 2550aae, and its
 * regression at bfab049, which reverted the ramp and left the flat value).
 *
 * So both the size and the alpha ramp as the field thins, and *together* rather
 * than in the direction 2550aae used. The discs are hard-edged, so a hard look at
 * 2550aae's own ramp (alpha 0.62 -> 0.95 at a fixed size) was measured before it
 * was copied: at 0.95 a T1 coastline stacked to L=195.0, rgb(255,249,59) — a
 * saturated yellow-white worse than the L=134 clearcoat spot the M-D6.4 fix had
 * just removed, because a hard disc adds its full alpha where two of them meet,
 * where 2550aae's soft radial sprite tailed off at the edges. Brightness is not
 * what T1 was missing; coverage was.
 *
 * The ramp therefore runs the other way: the discs get *wider* and *dimmer* as
 * the tier thins. The arithmetic of why that is the only efficient direction was
 * established by a sweep on `land_legibility.mjs`, and it is not obvious, so here
 * it is. A disc's contribution to a threshold-25 continent core scales with its
 * area, r², times its alpha — and its additive stack at a dense coastline scales
 * with exactly the same product. Coverage and stacking are the same knob, which
 * means there is no free lunch in either parameter alone:
 *
 *   T1 (1 200 dots), canvas band box   core px   mean L   core share   peak L
 *     5.5 px / 0.85  (dense, = base)    10 532    59.6      34.0%       111.8
 *     5.5 px / 0.85 / feather 0.60       9 570    55.1      31.6%        91.0
 *     7.0 px / 0.85                    11 220    68.5      35.8%       153.7
 *     8.25 px / 0.85                   12 197    75.5      37.9%       185.6
 *     9.5 px / 0.50                    12 394    65.6      38.0%       165.0
 *     8.25 px / 0.55  (SHIPPED)        12 115    61.6      37.4%       146.6
 *
 * Widening at a fixed alpha is the worst trade on the table: 7.0 px buys +6.5%
 * core for +41.9 peak, and 8.25 px / 0.85 buys +15.8% for +73.8. Widening *and*
 * dimming is the only direction that buys coverage cheaply — 8.25 px / 0.55 gets
 * +15.0% core for +34.8 peak, and 9.5 px / 0.50's extra +2.2% core costs another
 * +18.4 peak, so the shipped pair is the knee. A wider feather was tried as a
 * third lever and is a pure dimmer — it shrinks the disc's solid core, so at
 * 5.5 px / feather 0.60 both the core count *and* the peak fall together.
 *
 * 2550aae's accepted-PARTIAL figures (23.2% of the disc, mean 40.6, 27.1k core)
 * are deliberately *not* compared against this table: they were measured on the
 * pre-M-D7 layout, where the globe spanned y 135..731 against today's 305 px
 * canvas band, and "23.2% of the disc" is a different denominator from the
 * core-share-of-lit column. Only the within-layout delta above is a like-for-like
 * measurement. What the shipped pair gives up is peak: 146.6 against the base's
 * 111.8, on the same dense day-side coastline that T3 renders at L=233 — so T1
 * is still below its own accepted high-tier rendering of that feature, but the
 * margin is narrower than it was, and this is the knee of what the hard-disc
 * layer can do for itself. Item 6 stays PARTIAL pending owner QA — see the
 * M-D6.4 README.
 *
 * Both ramps' dense ends are pinned to the constants the cobe port shipped (5.5
 * px, 0.85), so T3 renders bit-identically and the M-D6.4 spot attribution
 * awaiting owner QA is not perturbed by this fix — item 6 is deliberately not
 * tied to the spots.
 */
const LAND_PX_DENSE = 5.5;
const LAND_PX_SPARSE = 8.25;
/** The counts the ramp runs between: T1's 1 200 land dots and T3's 4 800. */
const LAND_COUNT_SPARSE = 1200;
const LAND_COUNT_DENSE = 4800;
/** Where the tier's count sits on the sparse-to-dense ramp, in [0, 1]. */
function landDensity(count: number): number {
  if (count <= LAND_COUNT_SPARSE) return 0;
  if (count >= LAND_COUNT_DENSE) return 1;
  return (count - LAND_COUNT_SPARSE) / (LAND_COUNT_DENSE - LAND_COUNT_SPARSE);
}
function landDotPx(count: number): number {
  const t = landDensity(count);
  return LAND_PX_SPARSE + (LAND_PX_DENSE - LAND_PX_SPARSE) * t;
}
/**
 * cobe's dots sit at a fixed alpha with no fade; the catch on a *point* globe is
 * that a hard, fully-opaque disc stacks additively at the silhouette, which is
 * how the globe's hot spots were born (see the 4f51c21 fix). The dense end stays
 * a hair under 1 so two overlapping discs do not saturate, and the sparse end
 * trades brightness for area — see the sweep table on `landDotPx`.
 */
const LAND_ALPHA_DENSE = 0.85;
const LAND_ALPHA_SPARSE = 0.55;
function landDotAlpha(count: number): number {
  const t = landDensity(count);
  return LAND_ALPHA_SPARSE + (LAND_ALPHA_DENSE - LAND_ALPHA_SPARSE) * t;
}
/** The disc's edge feather, as a fraction of its radius. */
const LAND_DOT_FEATHER = 0.32;

export interface GlobeProps {
  /** How many dust dots, from the tier's budget. Zero renders the body and rim only. */
  points: number;
  /** The rotation rate the tier allows; 0 is a static globe. */
  rotate: number;
}

/**
 * The land layer's budget. It is proportional rather than fixed so every tier
 * shows the same globe at a different resolution: the continents keep their
 * shape and their dot density relative to the dust as the ladder climbs.
 *
 * 20% keeps the two highest tiers together under the owner's 30k cap (T3 is
 * 24 000 dust + 4 800 land) while making the continents legible at T1's 1 200.
 */
const LAND_FRACTION = 0.2;

export default function Globe({ points, rotate }: GlobeProps) {
  const ref = useRef<THREE.Group>(null);
  const colors = stageColors(useStageStore((s) => s.theme));
  // Owner QA 00:24: the token's `goldHi` (#F1D58E) is the pale gold used where
  // something must *glow*, but on the globe it read as lemon/neon rather than
  // warm gold. The deep token `gold` (#D4AF5A) is still brand gold — never a
  // status colour, §2.3 — and it is the warm one, so the dots and the rim take
  // it from the same token table and no hex is invented here.
  const warmGold = colors.gold;

  // A procedural environment gives the lacquer body something to reflect; the
  // floor builds the same one, and reusing the PMREM cache is M-D6.2's job, so
  // this shell's own env is omitted and the body reads by light alone.
  const dotPositions = useMemo(() => fibonacciSphere(points), [points]);
  const dotShades = useMemo(() => pointShades(points), [points]);
  // The base gold of each dot, before the sun. Kept unlit so the terminator can
  // be re-applied to it as the world turns — the lit value is `base * night`
  // on the dark side and `base` in full day.
  const dotBase = useMemo(() => {
    const arr = new Float32Array(points * 3);
    for (let i = 0; i < points; i++) {
      const s = dotShades[i]!;
      arr[i * 3] = warmGold.r * s;
      arr[i * 3 + 1] = warmGold.g * s;
      arr[i * 3 + 2] = warmGold.b * s;
    }
    return arr;
  }, [dotShades, warmGold, points]);
  // The dust sits on `GLOBE_RADIUS`; the inverse is the normal, precomputed once
  // so the per-second terminator pass is one divide-free dot product per dot.
  const dotInvR = 1 / GLOBE_RADIUS;
  const dotColors = useMemo(
    () => litColors(dotBase, dotPositions, dotInvR, sunLocalFor(0, new Date()), DUST_NIGHT),
    [dotBase, dotPositions, dotInvR],
  );

  const dotGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(dotPositions, 3));
    geo.setAttribute("color", dotColors);
    return geo;
  }, [dotPositions, dotColors]);

  const pointTexture = useMemo(() => softPointTexture(), []);

  // M-D6.3: the land dots. Natural Earth polygons from `world-atlas`, decoded by
  // `topojson-client`, sampled from the same kind of lattice the dust uses — see
  // `landDots.ts`. They sit a hair above the dust field and read as the figure
  // over its ground: brighter, larger, and all of them still brand gold.
  const landCount = Math.round(points * LAND_FRACTION);
  const landPositions = useMemo(() => landDots(landCount), [landCount]);
  const landBase = useMemo(() => {
    const shades = landShades(landCount);
    const arr = new Float32Array(shades.length * 3);
    for (let i = 0; i < shades.length; i++) {
      const s = shades[i]!;
      arr[i * 3] = warmGold.r * s;
      arr[i * 3 + 1] = warmGold.g * s;
      arr[i * 3 + 2] = warmGold.b * s;
    }
    return arr;
  }, [warmGold, landCount]);
  const landInvR = 1 / LAND_DOTS_RADIUS;
  const landColors = useMemo(
    () => litColors(landBase, landPositions, landInvR, sunLocalFor(0, new Date()), LAND_NIGHT),
    [landBase, landPositions, landInvR],
  );
  const landGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(landPositions, 3));
    geo.setAttribute("color", landColors);
    return geo;
  }, [landPositions, landColors]);

  // The atmosphere's shell. Its tuning is the vendor kit's defaults — see
  // Atmosphere.tsx — instead of the old rim's three knobs, one of which was
  // inert. The segments follow the tier: T1's shell is a 32×32, T2/T3 a 64×64,
  // matching the globe body's own subdivision ladder.
  const shellSegments = points >= 10000 ? SHELL_SEGMENTS_T3 : 32;

  // The land layer's mask, loaded from the app's own origin. `useTexture`
  // suspends, so the layer is mounted inside a <Suspense> below and the rest of
  // the globe renders immediately rather than waiting on the 111 KB image.
  // No colour space is set: it is a data mask, not a colour texture, and a
  // loader-made `Texture` is already `NoColorSpace` by construction (three's
  // own default, three.core.js:7311), so the shoreline ramp samples as the
  // bytes it is without the component having to mutate the object.
  const landMask = useTexture(LAND_MASK_URL);

  const gl = useThree((state) => state.gl);
  const landMaterial = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: LAND_VERT,
        fragmentShader: LAND_FRAG,
        uniforms: {
          uMask: { value: landMask },
          uAlpha: { value: landDotAlpha(landCount) },
          uFeather: { value: LAND_DOT_FEATHER },
          // three's own points shader multiplies the size by the pixel ratio
          // (`material.size * pixelRatio`); a fixed screen size has to do the
          // same or the dots shrink on a high-DPR panel.
          uPxSize: { value: landDotPx(landCount) * gl.getPixelRatio() },
        },
        transparent: true,
        depthWrite: false,
        vertexColors: true,
        blending: THREE.AdditiveBlending,
      }),
    [landMask, gl, landCount],
  );

  const lastSun = useRef(0);

  useFrame((_, delta) => {
    if (!ref.current) return;
    if (rotate > 0) {
      // §8.1's idle rate is the centrepiece's rate at every tier: one slow turn
      // in twelve minutes. The budget's multiplier scales the loose particles and
      // the drift, not the one object the eye is on — at T1's 0.5 the turn was
      // 0.25°/s, which is not perceptible as motion at all (owner QA 00:24).
      // `rotate` still gates this, so reduced motion keeps a still globe.
      ref.current.rotation.y += delta * IDLE_RAD_PER_SEC;
    }
    // M-D6.4: the terminator follows the real sun and the globe's own spin. It
    // refreshes on a timer rather than every frame: the sun moves 15°/hour and
    // the spin is 0.5°/s, so a second is half a degree — inside the dot spacing,
    // which makes the refresh invisible. This runs even when `rotate` is 0,
    // because a still globe still has a real day and night.
    const now = performance.now() / 1000;
    if (now - lastSun.current >= TERMINATOR_REFRESH_S) {
      lastSun.current = now;
      const sun = sunLocalFor(ref.current.rotation.y, new Date());
      relight(dotBase, dotColors, dotPositions, dotInvR, sun, DUST_NIGHT);
      if (landColors.array.length === landBase.length) {
        relight(landBase, landColors, landPositions, landInvR, sun, LAND_NIGHT);
      }
    }
  });

  return (
    <group ref={ref} position={GLOBE_POSITION} scale={GLOBE_SCALE} rotation={[0, 0, TILT]}>
      {/* The body: dark lacquer, clearcoat, lit by the stage's gold point light.
          Opaque and depth-writing, so it occludes the dots on the far side and
          the globe reads as a solid object rather than a dust cloud. */}
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS * 0.965, 64, 48]} />
        {/* M-D6.4: the clearcoat's specular from the directional key was the
            globe's second hot spot — a tight highlight that read L=134.0 at one
            pixel (rgb(206,120,61)) and fell to L≈14 only 20 px away, and being a
            clearcoat it did not move while the globe turned under it. Broadening
            the clearcoat rather than the base roughness keeps the lacquer sheen
            and leaves the stage's dusk key alone: this spreads the same energy
            over more pixels instead of dimming the light that also lights the
            floor ring M-D6.2 already QA'd. Measured, not assumed: the same pixel
            reads L=32.3 and its 10 px neighbourhood flattened from 62–88 to
            27–37 — see ccr_t3.png. */}
        <meshPhysicalMaterial
          color={colors.panel}
          metalness={0.45}
          roughness={0.5}
          clearcoat={1}
          clearcoatRoughness={0.5}
        />
      </mesh>
      {/* The dots. Additive over the body, so a dense field reads as glow without
          a bloom pass; depth-tested, so the far side stays hidden behind it. */}
      {points > 0 ? (
        <points geometry={dotGeometry}>
          <pointsMaterial
            map={pointTexture}
            size={0.056}
            sizeAttenuation
            vertexColors
            transparent
            // Owner QA 00:24: the two hot spots were additive overexposure —
            // dots near the silhouette stack in screen space, and at opacity 0.95
            // three of them saturate to pure white-gold. Backed off, and with the
            // 1.6× scale spreading the field, the rim reads as dust again.
            opacity={0.78}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </points>
      ) : null}
      {/* The land. M-D6.3 placed it with Natural Earth polygons; M-D6.4 shades
          it the cobe way — a fixed-size, fixed-alpha disc weighted by the NASA
          water mask — so the continents are legible at T1's 1 200 dots without
          gaining a reason to stack at T3's 4 800. Suspended on the mask load:
          the globe renders at once and the land appears when the image lands. */}
      {landCount > 0 ? (
        <Suspense fallback={null}>
          <points geometry={landGeometry} material={landMaterial} />
        </Suspense>
      ) : null}
      {/* M-D6.4: the fresnel atmosphere, replacing the hand-rolled rim shell.
          Slightly larger than the dot field, so its glow sits over the outer dust
          rather than at the silhouette itself. Tuning is the vendor kit's own
          defaults; see Atmosphere.tsx. */}
      <Atmosphere
        radius={GLOBE_RADIUS}
        color={warmGold}
        segments={shellSegments}
      />
    </group>
  );
}
