'use client'

import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export function Globe3D() {
  const containerRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const globeRef = useRef<THREE.Mesh | null>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    if (!containerRef.current) return

    // Create scene
    const scene = new THREE.Scene()
    sceneRef.current = scene

    // Create camera
    const camera = new THREE.PerspectiveCamera(
      45,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    )
    camera.position.z = 18
    camera.position.y = 5
    cameraRef.current = camera

    // Create renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true
    })
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
    containerRef.current.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // Create globe group
    const globeGroup = new THREE.Group()
    scene.add(globeGroup)
    globeRef.current = globeGroup

    // Create main globe sphere with holographic material
    const globeGeometry = new THREE.SphereGeometry(6, 64, 64)
    const globeMaterial = new THREE.MeshPhongMaterial({
      color: 0x0a0e17,
      emissive: 0x001a33,
      emissiveIntensity: 0.2,
      shininess: 100,
      transparent: true,
      opacity: 0.9,
      wireframe: false
    })
    const globe = new THREE.Mesh(globeGeometry, globeMaterial)
    globeGroup.add(globe)

    // Create holographic wireframe overlay
    const wireframeGeometry = new THREE.WireframeGeometry(globeGeometry)
    const wireframeMaterial = new THREE.LineBasicMaterial({
      color: 0xD4AF37,
      transparent: true,
      opacity: 0.15
    })
    const wireframe = new THREE.LineSegments(wireframeGeometry, wireframeMaterial)
    globeGroup.add(wireframe)

    // Create golden atmosphere glow
    const atmosphereGeometry = new THREE.SphereGeometry(6.2, 64, 64)
    const atmosphereMaterial = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.6 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
          gl_FragColor = vec4(0.83, 0.68, 0.21, 1.0) * intensity;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true
    })
    const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial)
    globeGroup.add(atmosphere)

    // Create golden glow sphere
    const glowGeometry = new THREE.SphereGeometry(6.1, 64, 64)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: 0xD4AF37,
      transparent: true,
      opacity: 0.1,
      side: THREE.BackSide
    })
    const glow = new THREE.Mesh(glowGeometry, glowMaterial)
    globeGroup.add(glow)

    // Create cyan holographic rings
    const ringGeometry = new THREE.RingGeometry(7.5, 7.8, 64)
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x00D9FF,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    })
    const ring1 = new THREE.Mesh(ringGeometry, ringMaterial)
    ring1.rotation.x = Math.PI / 2
    ring1.rotation.y = Math.PI / 8
    globeGroup.add(ring1)

    const ring2 = new THREE.Mesh(ringGeometry, ringMaterial.clone())
    ring2.material.opacity = 0.2
    ring2.rotation.x = Math.PI / 2
    ring2.rotation.y = -Math.PI / 8
    ring2.rotation.z = Math.PI / 12
    globeGroup.add(ring2)

    // Add particles
    const particleCount = 500
    const particleGeometry = new THREE.BufferGeometry()
    const particlePositions = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const r = 6.3 + Math.random() * 3

      particlePositions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      particlePositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      particlePositions[i * 3 + 2] = r * Math.cos(phi)
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3))
    const particleMaterial = new THREE.PointsMaterial({
      color: 0x00D9FF,
      size: 0.08,
      transparent: true,
      opacity: 0.8
    })
    const particles = new THREE.Points(particleGeometry, particleMaterial)
    globeGroup.add(particles)

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 2)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xD4AF37, 1)
    directionalLight.position.set(10, 10, 10)
    scene.add(directionalLight)

    const directionalLight2 = new THREE.DirectionalLight(0x00D9FF, 0.5)
    directionalLight2.position.set(-10, -10, 5)
    scene.add(directionalLight2)

    // Orbit controls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.enableZoom = true
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.8

    // Animation loop
    function animate() {
      animationRef.current = requestAnimationFrame(animate)

      // Rotate particles slowly
      if (particles) {
        particles.rotation.y += 0.001
      }

      // Pulse the rings
      const time = Date.now() * 0.001
      if (ring1) {
        ring1.rotation.z = Math.sin(time * 0.5) * 0.1
      }
      if (ring2) {
        ring2.rotation.z = Math.cos(time * 0.3) * 0.1
      }

      controls.update()
      renderer.render(scene, camera)
    }

    animate()

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current || !camera || !renderer) return

      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    }

    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (renderer && containerRef.current) {
        containerRef.current.removeChild(renderer.domElement)
        renderer.dispose()
      }
      if (scene) {
        scene.clear()
      }
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[400px] flex items-center justify-center"
      style={{
        background: 'radial-gradient(circle at center, #0a0e17 0%, #000 100%)'
      }}
    >
      {/* Holographic grid overlay */}
      <div className="absolute inset-0 pointer-events-none"
           style={{
             backgroundImage: 'radial-gradient(#D4AF37 1px, transparent 1px)',
             backgroundSize: '40px 40px',
             opacity: 0.1
           }}
      />
    </div>
  )
}
