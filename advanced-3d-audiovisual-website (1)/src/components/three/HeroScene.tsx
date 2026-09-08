"use client";

import { Suspense, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, Float, MeshDistortMaterial, Points, PointMaterial, Line } from "@react-three/drei";
import * as THREE from "three";

function KnowledgeCore() {
  const meshRef = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.15;
      meshRef.current.rotation.x += delta * 0.04;
    }
  });
  return (
    <Float speed={1.4} rotationIntensity={0.4} floatIntensity={0.8}>
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[1.35, 4]} />
        <MeshDistortMaterial
          color="#35f0d0"
          attach="material"
          distort={0.38}
          speed={1.6}
          roughness={0.15}
          metalness={0.6}
          emissive="#8b7bff"
          emissiveIntensity={0.35}
        />
      </mesh>
    </Float>
  );
}

function OrbitRing({ radius, tilt, color, speed }: { radius: number; tilt: number; color: string; speed: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const points = useMemo(() => {
    const pts: [number, number, number][] = [];
    for (let i = 0; i <= 128; i++) {
      const a = (i / 128) * Math.PI * 2;
      pts.push([Math.cos(a) * radius, Math.sin(a) * radius * 0.28, Math.sin(a) * radius]);
    }
    return pts;
  }, [radius]);

  useFrame((_, delta) => {
    if (groupRef.current) groupRef.current.rotation.y += delta * speed;
  });

  return (
    <group ref={groupRef} rotation={[tilt, 0, tilt * 0.6]}>
      <Line points={points} color={color} transparent opacity={0.35} lineWidth={1} />
    </group>
  );
}

function DataParticles() {
  const ref = useRef<THREE.Points>(null);
  const count = 900;
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const r = 3.2 + Math.random() * 3.8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.6;
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, []);

  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.03;
  });

  return (
    <Points ref={ref} positions={positions} stride={3}>
      <PointMaterial
        transparent
        color="#8b7bff"
        size={0.028}
        sizeAttenuation
        depthWrite={false}
        opacity={0.75}
      />
    </Points>
  );
}

function Nodes() {
  const nodes = useMemo(() => {
    const arr: { pos: [number, number, number]; scale: number }[] = [];
    for (let i = 0; i < 14; i++) {
      const r = 2.4 + Math.random() * 1.6;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      arr.push({
        pos: [r * Math.sin(phi) * Math.cos(theta), r * Math.sin(phi) * Math.sin(theta) * 0.7, r * Math.cos(phi)],
        scale: 0.03 + Math.random() * 0.05,
      });
    }
    return arr;
  }, []);

  return (
    <group>
      {nodes.map((n, i) => (
        <Float key={i} speed={1 + Math.random()} floatIntensity={1.2} rotationIntensity={0}>
          <mesh position={n.pos}>
            <sphereGeometry args={[n.scale, 12, 12]} />
            <meshStandardMaterial
              color={i % 3 === 0 ? "#ff5fae" : i % 3 === 1 ? "#35f0d0" : "#ffc857"}
              emissive={i % 3 === 0 ? "#ff5fae" : i % 3 === 1 ? "#35f0d0" : "#ffc857"}
              emissiveIntensity={1.4}
            />
          </mesh>
        </Float>
      ))}
    </group>
  );
}

export function HeroScene() {
  return (
    <div className="absolute inset-0" aria-hidden="true">
      <Canvas
        camera={{ position: [0, 0.4, 6.2], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 1.75]}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <pointLight position={[5, 5, 5]} intensity={40} color="#35f0d0" />
          <pointLight position={[-5, -3, -5]} intensity={30} color="#8b7bff" />
          <KnowledgeCore />
          <Nodes />
          <DataParticles />
          <OrbitRing radius={2.8} tilt={0.35} color="#35f0d0" speed={0.09} />
          <OrbitRing radius={3.6} tilt={-0.5} color="#8b7bff" speed={-0.06} />
          <OrbitRing radius={4.3} tilt={0.15} color="#ff5fae" speed={0.045} />
          <Environment preset="night" />
        </Suspense>
      </Canvas>
    </div>
  );
}
