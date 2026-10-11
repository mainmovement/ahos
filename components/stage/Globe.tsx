/**
 * M-D6.1 — the point globe: the observatory's centrepiece, hanging above the
 * shamseh floor.
 *
 * What it is: a field of gold dots on a Fibonacci lattice (see
 * `globeGeometry.ts`), wrapped around a dark lacquer body, with a fresnel rim
 * that puts a hot gold edge along the silhouette. Everything is generated in
 * code — no textures fetched, no models loaded, no HDR — so §0.5's "zero
 * external requests at runtime" holds, and §1's "generated procedurally (no
 * copied art)" holds with it.
 *
 * What it deliberately is not: a *data* globe. The continents it now traces
 * (M-D6.3) are ornament — they carry no values, they do not light up on a
 * verdict, and a token's result is never expressed by brightening a region. The
 * truth badge in the DOM says what the evidence said. Everything here is still
 * one glow only — the brand gold — because spec §2.3 forbids status colours as
 * decoration.
 *
 * Geography, where it appears, comes from licensed-free Natural Earth polygons
 * via `world-atlas` + `topojson-client`, bundled rather than fetched, so §0.5's
 * "zero external requests at runtime" still holds and §1's "no copied art" holds
 * with it. If land ever has to mean something, the values must arrive through
 * `/api/command` as labelled data — never as a colour change here.
 *
 * Tiers. Spec §11's ladder sets the density; the counts stay under the 30k the
 * owner's list caps a point globe at (T3 is 24 000 dust + 4 800 land), and T1
 * costs two draw calls with no postprocessing. The fresnel rim is one overdrawn
 * shell, not a bloom pass — at T2/T3 the real bloom chain arrives with M-D5.6's
 * pipeline and may replace it.
 */
"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

import { useStageStore } from "@/components/stage/store";
import { stageColors } from "@/components/stage/themeColors";
import { fibonacciSphere, GLOBE_RADIUS, pointShades } from "@/components/stage/globeGeometry";
import { landDots, landShades, LAND_DOTS_RADIUS } from "@/components/stage/landDots";

/** Spec §8.1: idle motion is 0.5°/s — one full turn in twelve minutes. */
const IDLE_RAD_PER_SEC = (0.5 * Math.PI) / 180;
/** An aesthetic axial tilt, so the globe reads as a planet and not a ball bearing. */
const TILT = 0.31;
/**
 * Owner QA 00:24: the globe was too small and floating above the floor ring. 1.6×
 * fills the ring the way the owner asked, and as a side effect it spreads the same
 * dot count over ~2.56× the screen area, which is most of why the rim stopped
 * stacking into hot spots — see `RIM_*` and the dot opacity below.
 */
const SCALE = 1.6;
/**
 * Where the globe hangs. The floor's ring surface sits at y = -0.5 + 0.002, and
 * the globe is a sphere of `SCALE * GLOBE_RADIUS`, so seating it on the ring is
 * `ringY + SCALE * GLOBE_RADIUS`. The tilt does not enter that arithmetic — a
 * sphere's extent is the same in every orientation.
 */
const POSITION: [number, number, number] = [0, -0.498 + SCALE * GLOBE_RADIUS, 0];

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
 * The fresnel rim: a shell slightly larger than the globe, rendered from the
 * inside, additive, brightest where the surface turns away from the camera. That
 * is the "gold rim light" the owner's list asks for, and it costs one triangle
 * shell rather than a postprocessing pass — which is why T1 may have it too.
 *
 * Owner QA 00:24 tuned the falloff: `uPower` 3.0 made the rim a broad flat band
 * that read as a cartoon outline, so it is narrowed, the intensity is brought
 * back so the edge glows rather than paints, and the shell is pulled in to hug
 * the dot field instead of floating around it.
 *
 * The shader is two lines of fresnel arithmetic; `precision` is set because a
 * WebGL1 context is still possible at T1 and the default there is not guaranteed.
 */
const RIM_VERT = /* glsl */ `
  varying vec3 vNormalView;
  varying vec3 vViewDir;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vNormalView = normalize(normalMatrix * normal);
    vViewDir = normalize(-mv.xyz);
    gl_Position = projectionMatrix * mv;
  }
`;
const RIM_FRAG = /* glsl */ `
  precision mediump float;
  uniform vec3 uColor;
  uniform float uPower;
  uniform float uIntensity;
  varying vec3 vNormalView;
  varying vec3 vViewDir;
  void main() {
    float fresnel = 1.0 - max(dot(vNormalView, vViewDir), 0.0);
    float rim = pow(fresnel, uPower);
    gl_FragColor = vec4(uColor * rim * uIntensity, rim);
  }
`;

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
  const dotColors = useMemo(() => {
    const arr = new Float32Array(points * 3);
    for (let i = 0; i < points; i++) {
      const s = dotShades[i]!;
      arr[i * 3] = warmGold.r * s;
      arr[i * 3 + 1] = warmGold.g * s;
      arr[i * 3 + 2] = warmGold.b * s;
    }
    return new THREE.BufferAttribute(arr, 3);
  }, [dotShades, warmGold, points]);

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
  const landColors = useMemo(() => {
    const shades = landShades(landCount);
    const arr = new Float32Array(shades.length * 3);
    for (let i = 0; i < shades.length; i++) {
      const s = shades[i]!;
      arr[i * 3] = warmGold.r * s;
      arr[i * 3 + 1] = warmGold.g * s;
      arr[i * 3 + 2] = warmGold.b * s;
    }
    return new THREE.BufferAttribute(arr, 3);
  }, [warmGold, landCount]);
  const landGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(landPositions, 3));
    geo.setAttribute("color", landColors);
    return geo;
  }, [landPositions, landColors]);

  const rimMaterial = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: RIM_VERT,
        fragmentShader: RIM_FRAG,
        uniforms: {
          uColor: { value: warmGold.clone() },
          // Narrowed from 3.0 and softened from 1.35 (owner QA 00:24): the rim
          // is now a thin hot edge that falls off quickly, not a flat band.
          uPower: { value: 6.0 },
          uIntensity: { value: 0.72 },
        },
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide,
      }),
    [warmGold],
  );

  useFrame((_, delta) => {
    if (ref.current && rotate > 0) {
      // §8.1's idle rate is the centrepiece's rate at every tier: one slow turn
      // in twelve minutes. The budget's multiplier scales the loose particles and
      // the drift, not the one object the eye is on — at T1's 0.5 the turn was
      // 0.25°/s, which is not perceptible as motion at all (owner QA 00:24).
      // `rotate` still gates this, so reduced motion keeps a still globe.
      ref.current.rotation.y += delta * IDLE_RAD_PER_SEC;
    }
  });

  return (
    <group ref={ref} position={POSITION} scale={SCALE} rotation={[0, 0, TILT]}>
      {/* The body: dark lacquer, clearcoat, lit by the stage's gold point light.
          Opaque and depth-writing, so it occludes the dots on the far side and
          the globe reads as a solid object rather than a dust cloud. */}
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS * 0.965, 64, 48]} />
        <meshPhysicalMaterial
          color={colors.panel}
          metalness={0.45}
          roughness={0.5}
          clearcoat={1}
          clearcoatRoughness={0.28}
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
      {/* The land. M-D6.3: brighter and larger than the dust, on its own shell
          a hair above it, so the continents read as a layer over the field rather
          than a denser patch of it. One more draw call at every tier. */}
      {landCount > 0 ? (
        <points geometry={landGeometry}>
          <pointsMaterial
            map={pointTexture}
            size={0.088}
            sizeAttenuation
            vertexColors
            transparent
            opacity={0.95}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </points>
      ) : null}
      {/* The fresnel rim shell, pulled in to hug the dot field. */}
      <mesh material={rimMaterial}>
        <sphereGeometry args={[GLOBE_RADIUS * 1.014, 64, 48]} />
      </mesh>
    </group>
  );
}
