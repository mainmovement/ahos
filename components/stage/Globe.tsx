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
 * What it deliberately is not: a map. No continents, no coastlines, no
 * implied geography, because the globe carries *no data*. It is the observatory's
 * ornament, and ornament in this system may use exactly one glow — the brand
 * gold (`themeColors.goldEmissive`) — never a status colour (spec §2.3: status
 * colours are never decoration). A token's verdict is not expressed by lighting a
 * continent; the truth badge in the DOM says what the evidence said.
 *
 * Tiers. Spec §11's ladder sets the density; the counts stay under the 30k the
 * owner's list caps a point globe at, and T1 keeps a single draw call with no
 * postprocessing. The fresnel rim is one overdrawn shell, not a bloom pass — at
 * T2/T3 the real bloom chain arrives with M-D5.6's pipeline and may replace it.
 */
"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

import { useStageStore } from "@/components/stage/store";
import { goldEmissive, stageColors } from "@/components/stage/themeColors";
import { fibonacciSphere, GLOBE_RADIUS, pointShades } from "@/components/stage/globeGeometry";

/**
 * Spec §8.1: idle motion is 0.5°/s. The budget scales it per tier and zeroes it
 * under reduced motion, so a still screenshot is a still globe.
 */
const IDLE_RAD_PER_SEC = (0.5 * Math.PI) / 180;
/** An aesthetic axial tilt, so the globe reads as a planet and not a ball bearing. */
const TILT = 0.31;
/** Where the globe hangs, above the floor's shamseh. */
const POSITION: [number, number, number] = [0, 1.42, 0];

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
  /** How many dots, from the tier's budget. Zero renders the body and rim only. */
  points: number;
  /** The rotation rate the tier allows; 0 is a static globe. */
  rotate: number;
}

export default function Globe({ points, rotate }: GlobeProps) {
  const ref = useRef<THREE.Group>(null);
  const colors = stageColors(useStageStore((s) => s.theme));
  const gold = goldEmissive(colors);

  // A procedural environment gives the lacquer body something to reflect; the
  // floor builds the same one, and reusing the PMREM cache is M-D6.2's job, so
  // this shell's own env is omitted and the body reads by light alone.
  const dotPositions = useMemo(() => fibonacciSphere(points), [points]);
  const dotShades = useMemo(() => pointShades(points), [points]);
  const dotColors = useMemo(() => {
    const arr = new Float32Array(points * 3);
    for (let i = 0; i < points; i++) {
      const s = dotShades[i]!;
      arr[i * 3] = gold.r * s;
      arr[i * 3 + 1] = gold.g * s;
      arr[i * 3 + 2] = gold.b * s;
    }
    return new THREE.BufferAttribute(arr, 3);
  }, [dotShades, gold, points]);

  const dotGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(dotPositions, 3));
    geo.setAttribute("color", dotColors);
    return geo;
  }, [dotPositions, dotColors]);

  const pointTexture = useMemo(() => softPointTexture(), []);

  const rimMaterial = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: RIM_VERT,
        fragmentShader: RIM_FRAG,
        uniforms: {
          uColor: { value: gold.clone() },
          uPower: { value: 3.0 },
          uIntensity: { value: 1.35 },
        },
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide,
      }),
    [gold],
  );

  useFrame((_, delta) => {
    if (ref.current && rotate > 0) {
      ref.current.rotation.y += delta * IDLE_RAD_PER_SEC * rotate;
    }
  });

  return (
    <group ref={ref} position={POSITION} rotation={[0, 0, TILT]}>
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
            size={0.062}
            sizeAttenuation
            vertexColors
            transparent
            opacity={0.95}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </points>
      ) : null}
      {/* The fresnel rim shell. */}
      <mesh material={rimMaterial}>
        <sphereGeometry args={[GLOBE_RADIUS * 1.035, 64, 48]} />
      </mesh>
    </group>
  );
}
