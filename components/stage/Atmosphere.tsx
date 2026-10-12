"use client";

/**
 * M-D6.4 — the globe's atmosphere, replacing the hand-rolled fresnel rim.
 *
 * This is the fresnel shell from the owner's vendor kit
 * (`vendor_assets/globe/reference/AtmosphereR3F.tsx`), itself adapted from
 * three-globe's atmosphere / three-glow-mesh (MIT, Vasco Asturiano; cited via
 * three-globe because three-glow-mesh's upstream repo has no LICENSE file — see
 * `vendor_assets/globe/licenses/three-glow-mesh-NOTE.txt`). Copied into the app
 * per the owner's 18:00 rule: build nothing from scratch when `vendor_assets`
 * already has it.
 *
 * What it is: a sphere slightly larger than the globe, rendered *from the
 * inside* (`BackSide` — only the far hemisphere's back faces draw), additive,
 * never writing depth. The fresnel term is `pow(coefficient + dot(normal,
 * direction-to-camera), power)`, which on a back-facing shell is a genuine
 * gradient and not a constant: the dot product is ~0.1 at the shell's own limb
 * (where the surface turns across the view) and ~1.0 at the far pole. The far
 * pole is behind the occluding body, so what is actually visible is the band
 * between the body's silhouette and the shell's limb — and in that band the
 * intensity *rises toward the globe*, which is the "atmosphere hugging the
 * planet" look rather than a painted ring at the edge.
 *
 * Why it replaced the old rim (owner QA 02:48, item 3, and the M-D6.4
 * glow-spot hunt): the old shell was also a `BackSide` additive shell, but its
 * shader, its sprite-free claim and its tuned `uPower`/`uIntensity` were three
 * separate knobs that had to agree, and two of them were inert for a
 * back-facing fragment (see the `abs(dot)` note that the old shader carried).
 * This shell has two knobs that both work, no point sprite at all, and the
 * gradient is the shader's only behaviour — so there is no constant-brightness
 * annulus to stack with the additive dots at the silhouette.
 *
 * Everything is in world space (`modelMatrix` for the vertex, `cameraPosition`
 * for the camera), so the shell is correct inside the globe's tilted, scaled,
 * spinning group without the component having to know about any of it.
 */
import * as THREE from "three";
import { useMemo } from "react";

const VERT = /* glsl */ `
  varying vec3 vVertexWorldPosition;
  varying vec3 vVertexNormal;
  void main() {
    vVertexNormal = normalize(normalMatrix * normal);
    vVertexWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;
// `precision` is set because a WebGL1 context is still possible at T1 and the
// default there is not guaranteed — the old rim shader carried the same line.
const FRAG = /* glsl */ `
  precision mediump float;
  uniform vec3 uColor;
  uniform float uCoefficient;
  uniform float uPower;
  varying vec3 vVertexNormal;
  varying vec3 vVertexWorldPosition;
  void main() {
    vec3 worldCameraToVertex = vVertexWorldPosition - cameraPosition;
    vec3 viewCameraToVertex = normalize((viewMatrix * vec4(worldCameraToVertex, 0.0)).xyz);
    float intensity = pow(uCoefficient + dot(vVertexNormal, viewCameraToVertex), uPower);
    gl_FragColor = vec4(uColor * intensity, intensity);
  }
`;

export interface AtmosphereProps {
  /** The radius the shell is based on — normally the globe's own radius. */
  radius: number;
  /** The shell reaches `radius * scale`. 1.05 hugs the dot field; 1.2 is a wide halo. */
  scale?: number;
  /** Fresnel bias. Higher pushes the whole shell brighter; see `power` for the falloff. */
  coefficient?: number;
  /** Fresnel exponent. Higher folds the glow tighter against the globe. */
  power?: number;
  color?: THREE.ColorRepresentation;
  /** The shell's subdivision. T1 uses 32, T2/T3 64. */
  segments?: number;
}

export function Atmosphere({
  radius,
  scale = 1.05,
  coefficient = 0.4,
  power = 2.0,
  color = "#D4AF5A",
  segments = 48,
}: AtmosphereProps) {
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: VERT,
        fragmentShader: FRAG,
        uniforms: {
          uColor: { value: new THREE.Color(color) },
          uCoefficient: { value: coefficient },
          uPower: { value: power },
        },
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide,
      }),
    [color, coefficient, power],
  );

  return (
    <mesh scale={radius * scale} material={material} renderOrder={1}>
      <sphereGeometry args={[1, segments, segments]} />
    </mesh>
  );
}
