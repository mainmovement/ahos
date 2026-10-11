"use client";

/**
 * M-D5.2 / M-D6.1 — the gold-lit lacquer observatory, centred in the RTL shell.
 *
 * M-D5.2 shipped this deliberately *empty*: a lazily-imported R3F island inside
 * the Next shell, lit in the spec's tokens, tier-aware, and able to lose its
 * WebGL context without losing anything else — the pipeline proven before any
 * content was placed on it. M-D6.1 sets the centrepiece on it, `Globe`: a point
 * globe above the shamseh, its density and rotation drawn from the same motion
 * budget the floor reads. The rings and beads (M-D6) and the tower (M-D8) arrive
 * onto a stage whose lighting, palette and fallbacks already work.
 *
 * Procedural only (M-D5.1's verdict). No textures, no models, no HDR fetch —
 * REFERENCE_BOARD ref 9: drei `Environment preset=` loads an HDRI from
 * raw.githack.com, which breaks spec §0.5's "zero external requests at runtime"
 * and M-D2's CSP. The metal here reflects a PMREM environment built from two
 * emissive quads in code, so gold reads as gold with nothing downloaded.
 *
 * The shamseh floor engraving is generated from geometry, per spec §1: "one
 * 10-fold shamseh (sun rosette) … generated procedurally (no copied art)."
 * The {10/3} decagram is drawn by index arithmetic, not traced from art.
 */
import { useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

import { useStageStore, motionBudget } from "@/components/stage/store";
import { edgeColor, goldEmissive, rimLight, stageColors } from "@/components/stage/themeColors";
import type { TierVerdict } from "@/components/stage/quality";
import Globe from "@/components/stage/Globe";

const FLOOR_RADIUS = 6;
const RING_RADIUS = 5.2;

/**
 * A 10-fold shamseh (sun rosette) as line geometry: two concentric decagons and
 * the {10/3} decagram between them, plus a hairline band. Pure arithmetic on a
 * fixed count — deterministic by construction, so the engraving is identical on
 * every machine and every reload, which is also what makes a screenshot
 * comparable between runs.
 */
function shamsehGeometry(radius: number, segments: number = 10): THREE.BufferGeometry {
  const pts: number[] = [];
  const push = (a: number, r: number) => {
    const t = (a / segments) * Math.PI * 2 - Math.PI / 2;   // point up at the top
    pts.push(Math.cos(t) * r, 0, Math.sin(t) * r);
  };
  // outer decagon
  for (let i = 0; i < segments; i++) {
    push(i, radius);
    push(i + 1, radius);
  }
  // {10/3} decagram: connect every third vertex of the outer decagon
  for (let i = 0; i < segments; i++) {
    push(i, radius);
    push(i + 3, radius);
  }
  // inner decagon
  const inner = radius * 0.62;
  for (let i = 0; i < segments; i++) {
    push(i, inner);
    push(i + 1, inner);
  }
  // hairline band between the two
  for (let i = 0; i < segments; i++) {
    push(i, radius * 0.97);
    push(i, inner * 1.03);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  return geo;
}

/**
 * A PMREM environment built from emissive quads: warm gold low on one side, a
 * cooler fill on the other. Gives metal something to reflect without a single
 * fetch. The result is cached on the renderer so a re-render does not rebuild it.
 */
function useProceduralEnv(): THREE.Texture | null {
  const gl = useThree((s) => s.gl);
  return useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#0B0709");
    const mk = (color: string, x: number, z: number, w: number, intensity: number) => {
      const mesh = new THREE.Mesh(
        new THREE.PlaneGeometry(w, w),
        new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity) }),
      );
      mesh.position.set(x, 1.5, z);
      mesh.lookAt(0, 0, 0);
      scene.add(mesh);
    };
    mk("#F1D58E", -4.5, -3.5, 5, 1.1);   // warm key, stage-right
    mk("#E8834A", 4.5, -3.5, 4, 0.7);    // ember rim, stage-left
    mk("#3A2A1C", 0, 4.5, 6, 0.4);       // overhead fill
    const tex = pmrem.fromScene(scene, 0.04).texture;
    pmrem.dispose();
    return tex;
  }, [gl]);
}

function ObservatoryFloor({ rotate }: { rotate: number }) {
  const ref = useRef<THREE.Group>(null);
  const colors = stageColors(useStageStore((s) => s.theme));
  const env = useProceduralEnv();

  const shamseh = useMemo(() => shamsehGeometry(RING_RADIUS * 0.92), []);
  // Owner QA 00:24: the ring was a 0.09-unit tube that read as a thick flat
  // neon-yellow band. Thinned to a hairline — §14 asks for a "gold rim", and a
  // rim is a line, not a tyre — and its materials below are taken off the pale
  // `goldHi` token for the same reason the globe's were.
  const ringGeo = useMemo(() => new THREE.RingGeometry(RING_RADIUS - 0.02, RING_RADIUS, 128), []);

  useFrame((_, delta) => {
    if (ref.current && rotate > 0) {
      // Spec §8.1: idle motion is 0.5°/s for the globe; the floor engraving
      // turns at a fraction of that so it reads as the same slow clock.
      ref.current.rotation.y += delta * 0.05 * rotate;
    }
  });

  return (
    <group ref={ref} position={[0, -0.5, 0]}>
      {/* The lacquer disc: dark, glossy, clearcoat. */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow={false}>
        <circleGeometry args={[FLOOR_RADIUS, 128]} />
        <meshPhysicalMaterial
          color={colors.panel}
          metalness={0.35}
          roughness={0.55}
          clearcoat={1}
          clearcoatRoughness={0.25}
          envMap={env}
          envMapIntensity={0.55}
        />
      </mesh>
      {/* The gold edge ring, §14's "gold rim (metalness 1, roughness 0.28)". The
          warm `gold` token rather than `goldHi` (owner QA 00:24) and the env/em
          turned down so the metal reflects the room instead of painting itself
          flat neon. */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.002, 0]}>
        <primitive object={ringGeo} attach="geometry" />
        <meshStandardMaterial
          color={colors.gold}
          metalness={1}
          roughness={0.28}
          emissive={colors.gold}
          emissiveIntensity={0.1}
          envMap={env}
          envMapIntensity={0.7}
        />
      </mesh>
      {/* The faint shamseh engraving, drawn as hairlines just above the lacquer. */}
      <lineSegments geometry={shamseh} position={[0, 0.004, 0]}>
        <lineBasicMaterial
          color={edgeColor(colors)}
          transparent
          opacity={0.42}
        />
      </lineSegments>
    </group>
  );
}

function StageLights() {
  const colors = stageColors(useStageStore((s) => s.theme));
  const rim = rimLight(colors);
  return (
    <>
      <ambientLight intensity={0.22} color={colors.textMuted} />
      {/* Warm key from stage-right — the dusk the Imperial concept is lit by. */}
      <directionalLight position={[-5, 3, 2]} intensity={1.1} color={rim} />
      {/* Gold point light above the globe's crown. Owner QA 00:24: at intensity 9
          on the old, smaller globe the crown sat ~1.5 units from the bulb and
          blew out to flat gold. The globe is larger now and the bulb is higher
          and softer, so the top reads as lit lacquer rather than a hot patch. */}
      <pointLight position={[0, 5.6, 0]} intensity={3.6} distance={16} color={goldEmissive(colors)} />
      {/* A low cool fill so the shadow side is not flat black. */}
      <pointLight position={[0, -1.5, 5]} intensity={2.4} distance={12} color={colors.bg} />
    </>
  );
}

/**
 * Reports the first frame and the context-loss event upward. M-D5.4: a
 * `webglcontextlost` must drop the app to the 2D layout with a Persian notice,
 * not crash it, and no data is lost — the shell's panels are DOM and survive.
 */
function StageLifecycle({ onContextLost }: { onContextLost: () => void }) {
  const gl = useThree((s) => s.gl);
  const setReady = useStageStore((s) => s.setReady);
  useEffect(() => {
    setReady(true);
    const el = gl.domElement;
    const handleLost = (e: Event) => {
      e.preventDefault();        // let the app recover rather than the tab
      onContextLost();
    };
    el.addEventListener("webglcontextlost", handleLost as EventListener);
    return () => {
      el.removeEventListener("webglcontextlost", handleLost as EventListener);
      setReady(false);
    };
  }, [gl, onContextLost, setReady]);
  return null;
}

export interface StageProps {
  verdict: TierVerdict | null;
  onContextLost?: () => void;
}

/**
 * The stage is T0-blind: at T0 the three.js chunk is never downloaded (spec
 * §11), so the shell does not mount this component at all. If it is mounted, a
 * tier of at least T1 is implied and the canvas runs.
 */
export default function Stage({ verdict, onContextLost }: StageProps) {
  const reducedMotion = useStageStore((s) => s.reducedMotion);
  const tier = verdict?.tier ?? "T1";
  const budget = motionBudget(tier, reducedMotion);
  const colors = stageColors(useStageStore((s) => s.theme));

  return (
    <Canvas
      // §11 Low-power: render only on change. With an empty stage and no motion
      // budget this draws one frame and stops — near-zero idle GPU cost.
      frameloop={budget.rotate > 0 ? "always" : "demand"}
      camera={{ position: [0, 3.4, 7.6], fov: 42 }}
      dpr={[1, tier === "T3" ? 1.5 : tier === "T2" ? 1.25 : 1]}
      gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
      onCreated={({ gl }) => {
        gl.setClearColor(colors.bg, 1);
      }}
    >
      <StageLights />
      <ObservatoryFloor rotate={budget.rotate} />
      {/* M-D6.1: the centrepiece. Density and rotation come from the same budget
          the floor reads, so one tier decision moves the whole stage together. */}
      <Globe points={budget.globePoints} rotate={budget.rotate} />
      <StageLifecycle onContextLost={onContextLost ?? (() => undefined)} />
    </Canvas>
  );
}
