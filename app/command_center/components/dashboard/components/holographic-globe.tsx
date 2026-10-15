'use client'

import { useEffect, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars, Sphere, PerspectiveCamera } from '@react-three/drei'
import { PointLight } from 'three'
import { MeshPhysicalMaterial } from 'three'
import * as THREE from 'three'

const GLOBE_RADIUS = 5
const GLOBE_POINTS = 30000

interface HolographicGlobeProps {
  className?: string
}

export function HolographicGlobe({ className }: HolographicGlobeProps) {
  const groupRef = useRef<THREE.Group>(null)
  const globeRef = useRef<THREE.Mesh>(null)

  useEffect(() => {
    // Set up animation for the globe
    const animate = () => {
      if (groupRef.current) {
        groupRef.current.rotation.y += 0.002
      }
      requestAnimationFrame(animate)
    }
    animate()
  }, [])

  return (
    <div className={className}>
      <Canvas shadows dpr={[1, 2]} camera={{ position: [0, 0, 18], fov: 45 }}>
        <color attach="background" args={['#0b0b0f']} />
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#D4AF37" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#00F0FF" />

        <group ref={groupRef}>
          {/* Holographic Globe Sphere */}
          <Sphere ref={globeRef} args={[GLOBE_RADIUS, 64, 64]}>
            <MeshTransmissionMaterial
              transmission={0.9}
              roughness={0.1}
              metalness={0.9}
              thickness={2}
              ior={1.5}
              chromaticAberration={0.1}
              anisotropy={0.3}
              clearcoat={1}
              clearcoatRoughness={0.1}
              color="#D4AF37"
              temporalDistortion={0.1}
            />
          </Sphere>

          {/* Holographic Points */}
          {Array.from({ length: GLOBE_POINTS }).map((_, i) => {
            const phi = Math.acos(-1 + (2 * i) / GLOBE_POINTS)
            const theta = Math.sqrt(GLOBE_POINTS * Math.PI) * phi

            const x = GLOBE_RADIUS * Math.cos(theta) * Math.sin(phi)
            const y = GLOBE_RADIUS * Math.sin(theta) * Math.sin(phi)
            const z = GLOBE_RADIUS * Math.cos(phi)

            return (
              <pointLight
                key={i}
                position={[x, y, z]}
                intensity={0.3}
                color={i % 2 === 0 ? '#D4AF37' : '#00F0FF'}
                distance={2}
              />
            )
          })}

          {/* Holographic Rings */}
          {Array.from({ length: 3 }).map((_, i) => (
            <mesh
              key={`ring-${i}`}
              rotation={[Math.PI / 3, Math.PI / 4, 0]}
              scale={1 + i * 0.3}
            >
              <ringGeometry args={[GLOBE_RADIUS + 0.1, GLOBE_RADIUS + 0.3, 64]} />
              <meshBasicMaterial
                color={i % 2 === 0 ? '#D4AF37' : '#00F0FF'}
                transparent
                opacity={0.3}
                side={THREE.DoubleSide}
              />
            </mesh>
          ))}
        </group>

        {/* Stars Background */}
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />

        {/* Orbit Controls */}
        <OrbitControls
          enableZoom={true}
          enablePan={false}
          minDistance={12}
          maxDistance={25}
          autoRotate={true}
          autoRotateSpeed={0.5}
        />

        {/* Perspective Camera */}
        <PerspectiveCamera makeDefault position={[0, 0, 18]} />
      </Canvas>

      {/* Overlay Text */}
      <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-end pb-16">
        <div className="text-center space-y-2">
          <h3 className="text-xl font-bold text-[#D4AF37] tracking-wider">AHOS NETWORK</h3>
          <p className="text-sm text-cyan-400">Global Intelligence Mesh</p>
          <div className="mt-4 flex gap-8 justify-center">
            <div className="text-center">
              <p className="text-2xl font-bold text-white">573</p>
              <p className="text-xs text-slate-400">Active Nodes</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">12.3k</p>
              <p className="text-xs text-slate-400">Connections</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">99.9%</p>
              <p className="text-xs text-slate-400">Uptime</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
