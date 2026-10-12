"use client";

/**
 * M-D6.5 — the chain rings, the observatory's orbits around the globe.
 *
 * This is the vendor kit's reference (`vendor_assets/globe/reference/ChainRingsR3F.tsx`,
 * three + drei `Line`, MIT), copied into the app per the owner's 18:00 rule and
 * adapted in three ways: the rings sit outside the globe's atmosphere rather
 * than around a unit sphere, the palette comes from the stage's own tokens so
 * the rings cannot drift off the unified look, and the budget is the same one
 * the globe and the floor read — so one tier decision moves the whole stage
 * together instead of leaving the rings at full cost on a low tier.
 *
 * What they are not: data. Nothing here is a market, an asset or a verdict. The
 * rings are the observatory's ornament — a centrepiece that reads as machinery
 * without claiming to *be* machinery. The vendor reference calls these "orbit
 * rings with optional moving nodes", and the nodes carry no labels and respond
 * to nothing. The truth badge in the DOM says what the evidence said.
 *
 * Tiering follows the vendor reference's own note: T1 draws low-segment rings
 * with no nodes and no travel, T3 goes to 256 segments with up to 8 nodes. The
 * `speed` is multiplied by the budget's `rotate`, which is already 0 under
 * reduced motion and under T0, so this component never has to ask what tier it
 * is in to know whether it may move.
 */
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import * as THREE from "three";

import { GLOBE_RADIUS } from "@/components/stage/globeGeometry";

/**
 * The rings' radii, in the globe's own units. The atmosphere reaches
 * `GLOBE_RADIUS * 1.15` and the globe's visible surface is at
 * `GLOBE_RADIUS * SCALE`, so these start clear of the halo and step outward —
 * the inner ring is a close orbit, the outer is the wide one the eye reads as
 * the observatory's armature.
 */
const RING_RADII = [1.32, 1.52, 1.74];

/**
 * Three different planes. Identical tilts would make the rings read as one
 * flattened hoop; three axes read as an orrery. Chosen so no ring is edge-on to
 * the camera (which would collapse it to a line) and no two are parallel.
 */
const RING_TILTS: [number, number, number][] = [
  [0.42, 0.0, 0.12],
  [-0.3, 0.22, 0.28],
  [0.14, -0.38, 0.05],
];

/** The travelling nodes' own spin, in radians per second at `rotate` 1. */
const NODE_SPEED = 0.16;
/** A ring's own slow precession, so the orbits are not frozen relative to each other. */
const RING_SPEED = 0.03;

export interface ChainRingsProps {
  /** Line segments per ring, from the tier's budget. Zero renders nothing. */
  segments: number;
  /** Travelling nodes per ring, from the tier's budget. */
  nodes: number;
  /** The motion multiplier the rest of the stage already uses; 0 stills everything. */
  rotate: number;
  /** The rings' gold, from `goldEmissive` — the one colour allowed to glow. */
  color: THREE.ColorRepresentation;
  /** A muted tone for the outer rings, so the inner ring is the figure. */
  muted: THREE.ColorRepresentation;
}

export function ChainRings({ segments, nodes, rotate, color, muted }: ChainRingsProps) {
  if (segments <= 0) return null;

  return (
    <>
      {RING_RADII.map((radius, i) => (
        <OneRing
          key={i}
          radius={radius * GLOBE_RADIUS}
          tilt={RING_TILTS[i]}
          segments={segments}
          nodes={nodes}
          rotate={rotate}
          // The inner ring is the gold one; the outer two are the muted armature,
          // which keeps the globe's own gold from competing with a bright hoop.
          color={i === 0 ? color : muted}
        />
      ))}
    </>
  );
}

function OneRing({
  radius,
  tilt,
  segments,
  nodes,
  rotate,
  color,
}: {
  radius: number;
  tilt: [number, number, number];
  segments: number;
  nodes: number;
  rotate: number;
  color: THREE.ColorRepresentation;
}) {
  // The vendor reference builds its points from `EllipseCurve` in the XZ plane;
  // kept as-is, since rotating the group is how the tilt is expressed.
  const points = useMemo(
    () =>
      new THREE.EllipseCurve(0, 0, radius, radius, 0, Math.PI * 2)
        .getPoints(segments)
        .map((p) => new THREE.Vector3(p.x, 0, p.y)),
    [radius, segments],
  );

  const spin = useRef<THREE.Group>(null!);
  useFrame((_, delta) => {
    if (rotate <= 0 || !spin.current) return;
    spin.current.rotation.y += delta * NODE_SPEED * rotate;
    spin.current.parent!.rotation.y += delta * RING_SPEED * rotate;
  });

  return (
    <group rotation={tilt}>
      <Line points={points} color={color} lineWidth={1} transparent opacity={0.6} />
      {nodes > 0 ? (
        <group ref={spin}>
          {Array.from({ length: nodes }, (_, k) => {
            const a = (k / nodes) * Math.PI * 2;
            return (
              <mesh key={k} position={[Math.cos(a) * radius, 0, Math.sin(a) * radius]}>
                <sphereGeometry args={[0.016, 8, 8]} />
                <meshBasicMaterial color={color} />
              </mesh>
            );
          })}
        </group>
      ) : null}
    </group>
  );
}
