"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import * as THREE from "three";
import { GPUComputationRenderer } from "three/examples/jsm/misc/GPUComputationRenderer.js";
import type { FeatureCollection } from "geojson";

export type DeptStatus = "LIVE" | "STALE" | "UNKNOWN" | "DEMO";
export type SignalOutcome = "absorbed" | "dissipated" | "pending";

export interface Department {
  id: string;
  nameFa: string;
  rate: number;
  queue: number;
  lastDataAt: string;
  confidence: number;
  status: DeptStatus;
}

export interface Signal {
  id: string;
  deptId: string;
  at: string;
  outcome: SignalOutcome;
  reason?: string;
}

export interface Health {
  bpm: number;
  jitterMs: number;
  stale: boolean;
}

export interface PulseOrbProps {
  health: Health;
  departments: Department[];
  signals: Signal[];
  quality?: "low" | "medium" | "high";
  onMorph?: (morphed: boolean) => void;
}

const GOLD = new THREE.Color("#d4af37");
const GREY = new THREE.Color("#6b6b6b");
const FOG_GREY = new THREE.Color("#3a3a3a");

function hasWebGL(): boolean {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function clamp(v: number, a: number, b: number): number {
  return Math.max(a, Math.min(b, v));
}

function outcomeCode(o: SignalOutcome): number {
  if (o === "absorbed") return 0;
  if (o === "dissipated") return 1;
  return 2;
}

function patternForStatus(s: DeptStatus): number {
  switch (s) {
    case "LIVE":
      return 0;
    case "STALE":
      return 1;
    case "UNKNOWN":
      return 2;
    case "DEMO":
      return 3;
    default:
      return 0;
  }
}

function ageSeconds(iso: string): number {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return 9999;
  return (Date.now() - t) / 1000;
}

export default function PulseOrb(props: PulseOrbProps) {
  const { health, departments, signals, quality = "medium", onMorph } = props;
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [webglOk, setWebglOk] = useState(true);
  const [reduced, setReduced] = useState(false);
  const [morphed, setMorphed] = useState(false);
  const morphedRef = useRef(false);
  const morphProgressRef = useRef(0);
  const [highlightedCount, setHighlightedCount] = useState(0);
  const [collapsedCount, setCollapsedCount] = useState(0);
  const [gateRatio, setGateRatio] = useState(0.5);

  useEffect(() => {
    setWebglOk(hasWebGL());
    setReduced(prefersReducedMotion());
  }, []);

  const toggleMorph = () => {
    setMorphed((m) => {
      const n = !m;
      morphedRef.current = n;
      onMorph?.(n);
      return n;
    });
  };

  useEffect(() => {
    morphedRef.current = morphed;
  }, [morphed]);

  // attention budget
  useEffect(() => {
    const breaches =
      departments.filter((d) => d.status !== "LIVE").length +
      signals.filter((s) => s.outcome === "pending").length +
      (health.stale ? 1 : 0);
    const total = breaches;
    if (total <= 7) {
      setHighlightedCount(total);
      setCollapsedCount(0);
    } else {
      setHighlightedCount(7);
      setCollapsedCount(total - 7);
    }
  }, [departments, signals, health]);

  // gate ratio
  useEffect(() => {
    const a = signals.filter((s) => s.outcome === "absorbed").length;
    const d = signals.filter((s) => s.outcome === "dissipated").length;
    const total = a + d;
    setGateRatio(total === 0 ? 0.5 : a / total);
  }, [signals]);

  const maxTexSize = quality === "low" ? 64 : quality === "medium" ? 128 : 256;

  useEffect(() => {
    if (!webglOk || reduced) return;
    const container = containerRef.current;
    if (!container) return;

    let disposed = false;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      45,
      Math.max(1, container.clientWidth) / Math.max(1, container.clientHeight),
      0.1,
      100,
    );
    camera.position.set(0, 0, 6.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setSize(container.clientWidth || 300, container.clientHeight || 300);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.25);
    scene.add(ambient);
    const point = new THREE.PointLight(0xd4af37, 1.2, 20);
    point.position.set(2, 2, 4);
    scene.add(point);

    // glass sphere (Fresnel + matcap-ish)
    const sphereGeo = new THREE.SphereGeometry(1.5, 64, 64);
    const sphereMat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uGold: { value: GOLD.clone() },
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vView;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          vView = normalize(-mv.xyz);
          gl_Position = projectionMatrix * mv;
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vView;
        uniform vec3 uGold;
        void main() {
          float fres = pow(1.0 - max(dot(vNormal, vView), 0.0), 2.4);
          vec3 base = vec3(0.03, 0.035, 0.05);
          vec3 rim = uGold * fres * 0.9;
          // permanent gold edge hatching (paper-only watermark)
          float hatch = step(0.92, fract(vNormal.x * 12.0 + vNormal.y * 7.0));
          rim += uGold * hatch * 0.15;
          gl_FragColor = vec4(base + rim, 0.85);
        }
      `,
      transparent: true,
      depthWrite: false,
    });
    const sphere = new THREE.Mesh(sphereGeo, sphereMat);
    scene.add(sphere);

    // golden core
    const coreGeo = new THREE.SphereGeometry(0.32, 32, 32);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      emissive: 0xd4af37,
      emissiveIntensity: 0.7,
      roughness: 0.3,
      metalness: 0.8,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    scene.add(core);

    // rings
    const ringGroup = new THREE.Group();
    scene.add(ringGroup);
    const radius = 2.35;
    const rings: {
      dept: Department;
      mesh: THREE.Mesh;
      mat: THREE.ShaderMaterial;
      angle: number;
    }[] = [];
    departments.forEach((dept, i) => {
      const angle = (i / Math.max(1, departments.length)) * Math.PI * 2;
      const tube = 0.012 + clamp(dept.queue, 0, 20) * 0.004;
      const geo = new THREE.TorusGeometry(radius, tube, 8, 96);
      const mat = new THREE.ShaderMaterial({
        uniforms: {
          uColor: { value: GOLD.clone() },
          uOpacity: { value: 0.7 },
          uPattern: { value: patternForStatus(dept.status) },
        },
        vertexShader: `
          varying vec2 vUv;
          void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          varying vec2 vUv;
          uniform vec3 uColor;
          uniform float uOpacity;
          uniform int uPattern;
          void main() {
            float t = vUv.x * 40.0;
            float a = 1.0;
            if (uPattern == 1) {
              a = step(0.5, fract(t * 0.25));
            } else if (uPattern == 2) {
              float d = length(fract(vec2(t * 0.15, vUv.y * 6.0)) - 0.5);
              a = smoothstep(0.18, 0.08, d);
            } else if (uPattern == 3) {
              a = step(0.5, fract(t * 0.25 + vUv.y * 4.0));
            }
            gl_FragColor = vec4(uColor, uOpacity * a);
          }
        `,
        transparent: true,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(geo, mat);
      // orient ring around Y axis tilted
      mesh.rotation.x = Math.PI / 2.2;
      mesh.rotation.z = angle;
      ringGroup.add(mesh);
      rings.push({ dept, mesh, mat, angle });
    });

    // gate arc
    const gateGroup = new THREE.Group();
    scene.add(gateGroup);
    const gateRadius = 1.9;
    const gateGeo1 = new THREE.TorusGeometry(gateRadius, 0.01, 6, 64, Math.PI * 2);
    const gateMat1 = new THREE.ShaderMaterial({
      uniforms: { uRatio: { value: 0.5 }, uOpacity: { value: 0.6 } },
      vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
      fragmentShader: `varying vec2 vUv; uniform float uRatio; uniform float uOpacity; void main(){ float ang=vUv.x; vec3 gold=vec3(0.83,0.69,0.22); vec3 grey=vec3(0.42,0.42,0.42); vec3 col = ang < uRatio ? gold : grey; gl_FragColor=vec4(col,uOpacity); }`,
      transparent: true,
      depthWrite: false,
    });
    const gateMesh = new THREE.Mesh(gateGeo1, gateMat1);
    gateMesh.rotation.x = Math.PI / 2;
    gateGroup.add(gateMesh);

    // particles GPGPU
    const count = Math.max(1, signals.length);
    let size = 16;
    while (size * size < count && size < maxTexSize) size *= 2;
    if (size > maxTexSize) size = maxTexSize;

    const gpgpu = new GPUComputationRenderer(size, size, renderer);
    try {
      gpgpu.setDataType(THREE.HalfFloatType);
    } catch {
      // ignore
    }

    const posTex = gpgpu.createTexture();
    const metaTex = gpgpu.createTexture();
    const targetTex = gpgpu.createTexture();

    const posArr = posTex.image.data as Float32Array;
    const metaArr = metaTex.image.data as Float32Array;
    const targetArr = targetTex.image.data as Float32Array;

    // map projection for morph targets
    // load geo json sync? fetch at runtime from /geo/world.geo.json (same origin, no network)
    // We'll compute map targets lazily; default to a circle layout.
    const mapTargets: { x: number; y: number; z: number }[] = [];
    // placeholder until geo loaded; fill below

    departments.forEach((d) => d); // noop

    // init textures
    for (let i = 0; i < size * size; i++) {
      const ix = i * 4;
      if (i < signals.length) {
        const sig = signals[i];
        const deptIndex = Math.max(0, departments.findIndex((d) => d.id === sig.deptId));
        const baseAngle = (deptIndex / Math.max(1, departments.length)) * Math.PI * 2;
        const r = 2.35;
        const ox = Math.cos(baseAngle) * r;
        const oy = 0;
        const oz = Math.sin(baseAngle) * r;
        posArr[ix + 0] = ox;
        posArr[ix + 1] = oy;
        posArr[ix + 2] = oz;
        posArr[ix + 3] = 0; // progress
        metaArr[ix + 0] = ox;
        metaArr[ix + 1] = oy;
        metaArr[ix + 2] = oz;
        metaArr[ix + 3] = outcomeCode(sig.outcome);
        // map target placeholder
        const mt = { x: (Math.random() - 0.5) * 3, y: 0, z: (Math.random() - 0.5) * 2 };
        mapTargets[i] = mt;
        targetArr[ix + 0] = mt.x;
        targetArr[ix + 1] = mt.y;
        targetArr[ix + 2] = mt.z;
        targetArr[ix + 3] = 0;
      } else {
        posArr[ix + 3] = 1;
        metaArr[ix + 3] = -1;
        targetArr[ix + 3] = -1;
      }
    }
    posTex.needsUpdate = true;
    metaTex.needsUpdate = true;
    targetTex.needsUpdate = true;

    // try load geojson and recompute map targets
    fetch("/geo/world.geo.json")
      .then((r) => r.json())
      .then((geo: FeatureCollection) => {
        if (disposed) return;
        // build list of country centroids
        const centroids: [number, number][] = [];
        // use d3-geo
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const proj = (THREE as any); // noop
        void proj;
        // simple: use feature geometry first coordinate as point
        geo.features.forEach((f) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const g: any = f.geometry;
          if (!g) return;
          let coord: number[] | null = null;
          if (g.type === "Point") coord = g.coordinates;
          else if (g.type === "Polygon") coord = g.coordinates?.[0]?.[0];
          else if (g.type === "MultiPolygon") coord = g.coordinates?.[0]?.[0]?.[0];
          if (coord) centroids.push([coord[0], coord[1]]);
        });
        if (centroids.length === 0) return;
        // map each signal to a centroid
        for (let i = 0; i < signals.length; i++) {
          const c = centroids[i % centroids.length];
          // mercator-ish projection to 3D plane
          const lon = c[0];
          const lat = c[1];
          const x = (lon / 180) * 2.2;
          const z = (-lat / 90) * 1.4;
          const ix = i * 4;
          targetArr[ix + 0] = x;
          targetArr[ix + 1] = 0;
          targetArr[ix + 2] = z;
          mapTargets[i] = { x, y: 0, z };
        }
        targetTex.needsUpdate = true;
      })
      .catch(() => {
        // keep placeholders
      });

    const posShader = `
      uniform sampler2D metaTexture;
      uniform sampler2D targetTexture;
      uniform float uDelta;
      uniform float uSpeed;
      uniform float uMorph;
      void main() {
        vec2 uv = gl_FragCoord.xy / resolution.xy;
        vec4 p = texture2D(posTexture, uv);
        vec4 m = texture2D(metaTexture, uv);
        vec4 t = texture2D(targetTexture, uv);
        if (m.w < 0.0) { gl_FragColor = vec4(0.0,0.0,0.0,1.0); return; }
        float progress = p.w;
        float limit = 1.0;
        if (m.w > 0.5 && m.w < 1.5) limit = 0.7;
        if (progress < limit) progress = min(progress + uDelta * uSpeed, limit);
        vec3 origin = m.xyz;
        vec3 orbPos = mix(origin, vec3(0.0), progress);
        vec3 mapPos = t.xyz;
        vec3 pos = mix(orbPos, mapPos, uMorph);
        gl_FragColor = vec4(pos, progress);
      }
    `;

    const posVar = gpgpu.addVariable("posTexture", posShader, posTex);
    gpgpu.setVariableDependencies(posVar, [posVar]);
    posVar.material.uniforms.metaTexture = { value: metaTex };
    posVar.material.uniforms.targetTexture = { value: targetTex };
    posVar.material.uniforms.uDelta = { value: 0 };
    posVar.material.uniforms.uSpeed = { value: 0.8 };
    posVar.material.uniforms.uMorph = { value: morphProgressRef.current };

    const err = gpgpu.init();
    if (err) console.error("GPGPU init error:", err);

    // particle material
    const particleGeo = new THREE.BufferGeometry();
    const indices = new Float32Array(size * size);
    for (let i = 0; i < size * size; i++) indices[i] = i;
    particleGeo.setAttribute("aIndex", new THREE.BufferAttribute(indices, 1));
    const posAttr = new Float32Array(size * size * 3);
    for (let i = 0; i < size * size; i++) {
      posAttr[i * 3 + 0] = posArr[i * 4 + 0];
      posAttr[i * 3 + 1] = posArr[i * 4 + 1];
      posAttr[i * 3 + 2] = posArr[i * 4 + 2];
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(posAttr, 3));

    const particleMat = new THREE.ShaderMaterial({
      uniforms: {
        uPosTex: { value: gpgpu.getCurrentRenderTarget(posVar).texture },
        uMetaTex: { value: metaTex },
        uTexSize: { value: size },
        uPointSize: { value: quality === "low" ? 2.0 : 3.0 },
        uGold: { value: GOLD.clone() },
        uGrey: { value: GREY.clone() },
      },
      vertexShader: `
        attribute float aIndex;
        uniform sampler2D uPosTex;
        uniform sampler2D uMetaTex;
        uniform float uTexSize;
        uniform float uPointSize;
        varying float vProgress;
        varying float vOutcome;
        void main() {
          float x = mod(aIndex, uTexSize);
          float y = floor(aIndex / uTexSize);
          vec2 uv = (vec2(x, y) + 0.5) / uTexSize;
          vec4 p = texture2D(uPosTex, uv);
          vec4 m = texture2D(uMetaTex, uv);
          if (m.w < 0.0) {
            gl_Position = vec4(2.0, 2.0, 0.0, 1.0);
            gl_PointSize = 0.0;
            vProgress = 1.0;
            vOutcome = -1.0;
            return;
          }
          vec3 pos = p.xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = uPointSize;
          vProgress = p.w;
          vOutcome = m.w;
        }
      `,
      fragmentShader: `
        varying float vProgress;
        varying float vOutcome;
        uniform vec3 uGold;
        uniform vec3 uGrey;
        void main() {
          vec2 c = gl_PointCoord - 0.5;
          if (dot(c, c) > 0.25) discard;
          vec3 color = uGold;
          float alpha = 0.9;
          if (vOutcome > 0.5 && vOutcome < 1.5) {
            color = uGrey;
            // fade before reaching
            if (vProgress >= 0.65) alpha = (1.0 - vProgress) * 2.0;
          }
          if (vOutcome < 0.5 && vProgress > 0.98) {
            color = vec3(1.0, 0.92, 0.55);
            alpha = 1.0;
          }
          if (vOutcome > 1.5) {
            color = uGold;
            alpha = 0.6 * (1.0 - vProgress * 0.5);
          }
          gl_FragColor = vec4(color, clamp(alpha, 0.0, 1.0));
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const points = new THREE.Points(particleGeo, particleMat);
    scene.add(points);

    const raycaster = new THREE.Raycaster();
    const onPointerMove = (e: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const ndc = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1,
      );
      raycaster.setFromCamera(ndc, camera);
      const hits = raycaster.intersectObject(points);
      if (hits.length && typeof hits[0].index === "number") {
        const idx = hits[0].index as number;
        if (idx < signals.length) {
          const sig = signals[idx];
          if (tooltipRef.current) {
            tooltipRef.current.style.display = "block";
            tooltipRef.current.style.left = e.clientX - rect.left + 12 + "px";
            tooltipRef.current.style.top = e.clientY - rect.top + 12 + "px";
            tooltipRef.current.textContent = sig.reason ?? sig.outcome;
            tooltipRef.current.setAttribute("dir", "rtl");
          }
          return;
        }
      }
      if (tooltipRef.current) tooltipRef.current.style.display = "none";
    };
    const onPointerLeave = () => {
      if (tooltipRef.current) tooltipRef.current.style.display = "none";
    };
    renderer.domElement.addEventListener("pointermove", onPointerMove);
    renderer.domElement.addEventListener("pointerleave", onPointerLeave);

    // morph uMorph sync
    // animation
    const clock = new THREE.Clock();
    let raf = 0;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      if (document.hidden) return;
      const dt = Math.min(clock.getDelta(), 0.05);
      const t = clock.elapsedTime;
      // heartbeat
      let pulse = 0;
      if (!health.stale && health.bpm > 0) {
        const phase = t * (health.bpm / 60) * Math.PI * 2 + Math.sin(t * 7.3) * (health.jitterMs / 1000);
        pulse = 0.12 * (0.5 + 0.5 * Math.sin(phase));
      }
      core.scale.setScalar(1 + pulse);
      coreMat.emissiveIntensity = 0.6 + pulse * 3;

      // breach intensity
      const breach =
        departments.some((d) => d.status !== "LIVE") ||
        signals.some((s) => s.outcome === "pending") ||
        health.stale ||
        health.jitterMs > 200;
      const intensity = breach ? 1.0 : 0.35;

      sphereMat.uniforms.uTime.value = t;

      // rings
      rings.forEach(({ dept, mesh, mat }) => {
        const age = ageSeconds(dept.lastDataAt);
        const fog = clamp(age / 60, 0, 1);
        const conf = clamp(dept.confidence, 0, 1);
        const col = GOLD.clone().lerp(GREY, 1 - conf).lerp(FOG_GREY, fog * 0.6);
        mat.uniforms.uColor.value = col;
        mat.uniforms.uOpacity.value = (0.85 - fog * 0.55) * (0.4 + intensity * 0.6);
        mat.uniforms.uPattern.value = patternForStatus(dept.status);

        const stalled = dept.status === "STALE" || dept.rate <= 0;
        if (!stalled && !morphed) {
          mesh.rotation.z += dept.rate * dt * intensity;
        }
      });

      const a = signals.filter((s) => s.outcome === "absorbed").length;
      const d = signals.filter((s) => s.outcome === "dissipated").length;
      const total = a + d;
      const ratio = total === 0 ? 0.5 : a / total;
      (gateMat1 as THREE.ShaderMaterial).uniforms.uRatio.value = ratio;
      (gateMat1 as THREE.ShaderMaterial).uniforms.uOpacity.value = 0.3 + intensity * 0.4;
      gateMesh.rotation.z += 0.1 * dt * intensity;

      // gpgpu
      const targetMorph = morphedRef.current ? 1 : 0;
      morphProgressRef.current += (targetMorph - morphProgressRef.current) * Math.min(1, dt * 2.5);
      posVar.material.uniforms.uDelta.value = dt;
      posVar.material.uniforms.uSpeed.value = 0.6 + intensity * 0.6;
      posVar.material.uniforms.uMorph.value = morphProgressRef.current;
      gpgpu.compute();
      particleMat.uniforms.uPosTex.value = gpgpu.getCurrentRenderTarget(posVar).texture;

      // scene rotation
      ringGroup.rotation.y += 0.05 * dt * (0.3 + intensity * 0.7);
      scene.rotation.y += 0.02 * dt * intensity;

      renderer.render(scene, camera);
    };
    animate();

    // resize
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 300;
      const h = container.clientHeight || 300;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    const ro = new ResizeObserver(handleResize);
    ro.observe(container);
    window.addEventListener("resize", handleResize);

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("pointermove", onPointerMove);
      renderer.domElement.removeEventListener("pointerleave", onPointerLeave);
      // dispose
      scene.traverse((obj) => {
        const mesh = obj as THREE.Mesh;
        if (mesh.geometry) mesh.geometry.dispose();
        const mat = mesh.material as THREE.Material | THREE.Material[];
        if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
        else if (mat) mat.dispose();
      });
      gpgpu.dispose?.();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [webglOk, reduced, departments, signals, health, quality]);

  // morph notify
  useEffect(() => {
    onMorph?.(morphed);
  }, [morphed, onMorph]);

  if (!webglOk || reduced) {
    return <SvgFallback departments={departments} signals={signals} health={health} />;
  }

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      <div
        ref={tooltipRef}
        className="pointer-events-none absolute z-10 hidden max-w-xs rounded border border-amber-400/40 bg-black/80 px-2 py-1 text-xs text-amber-100 backdrop-blur"
        style={{ display: "none" }}
      />
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-between p-4">
        <div className="pointer-events-auto flex gap-2">
          <button
            onClick={toggleMorph}
            className="rounded border border-amber-400/40 bg-black/40 px-3 py-1 text-xs text-amber-200 backdrop-blur"
            aria-label={morphed ? "بازگشت به اورب" : "نمایش نقشه جهان"}
          >
            {morphed ? "اورب" : "نقشه"}
          </button>
        </div>
        <div className="pointer-events-auto rounded bg-black/40 px-3 py-1 text-xs text-amber-200 backdrop-blur">
          دروازه: {Math.round(gateRatio * 100)}% جذب
        </div>
      </div>
      {collapsedCount > 0 && (
        <div className="absolute bottom-4 left-4 rounded bg-black/50 px-2 py-1 text-xs text-stone-300">
          +{collapsedCount} مورد دیگر
        </div>
      )}
      {/* keyboard-focusable proxies for rings and signals */}
      <div className="sr-only">
        {departments.map((d) => (
          <button key={d.id} tabIndex={0} aria-label={`بخش ${d.nameFa} وضعیت ${d.status}`}>
            {d.nameFa}
          </button>
        ))}
        {signals.map((s) => (
          <button key={s.id} tabIndex={0} aria-label={`سیگنال ${s.id} ${s.outcome} ${s.reason ?? ""}`}>
            {s.id}
          </button>
        ))}
      </div>
      {/* off-canvas text table */}
      <table className="sr-only">
        <caption>داده‌های اورب</caption>
        <thead>
          <tr>
            <th>بخش</th>
            <th>وضعیت</th>
            <th>نرخ</th>
            <th>صف</th>
            <th>اعتماد</th>
          </tr>
        </thead>
        <tbody>
          {departments.map((d) => (
            <tr key={d.id}>
              <td>{d.nameFa}</td>
              <td>{d.status}</td>
              <td>{d.rate}</td>
              <td>{d.queue}</td>
              <td>{d.confidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <ul className="sr-only">
        {signals.map((s) => (
          <li key={s.id}>
            {s.id} {s.deptId} {s.outcome} {s.reason ?? ""}
          </li>
        ))}
      </ul>
    </div>
  );
}

function SvgFallback({ departments, signals, health }: { departments: Department[]; signals: Signal[]; health: Health }) {
  return (
    <div className="flex h-full w-full items-center justify-center" role="img" aria-label="نمای ساده اورب">
      <svg viewBox="0 0 400 400" className="h-full w-full max-w-md">
        <circle cx="200" cy="200" r="120" fill="none" stroke="#d4af37" strokeOpacity="0.3" />
        <circle cx="200" cy="200" r="30" fill="#d4af37" fillOpacity="0.6" />
        {departments.map((d, i) => {
          const a = (i / Math.max(1, departments.length)) * Math.PI * 2;
          const x = 200 + Math.cos(a) * 150;
          const y = 200 + Math.sin(a) * 150;
          return <circle key={d.id} cx={x} cy={y} r={4 + d.queue * 0.5} fill="#d4af37" fillOpacity={d.status === "LIVE" ? 0.8 : 0.3} />;
        })}
        <text x="200" y="380" textAnchor="middle" fill="#aaa" fontSize="12">
          BPM {health.bpm} {health.stale ? "(stale)" : ""}
        </text>
      </svg>
    </div>
  );
}
