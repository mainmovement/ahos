"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GPUComputationRenderer } from "three/examples/jsm/misc/GPUComputationRenderer.js";
import { computeStrictness } from "@/lib/gate";
import { ringLayout, ringRotationDelta } from "@/lib/rings";
import { buildMapTargets, particleTextureSize } from "@/lib/mapTargets";
import { selectCalmHighlights, selectSignalParticles } from "@/lib/attention";
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

export interface GateState {
  absorbed: number;
  dissipated: number;
  strictness?: number;
}

export interface PulseOrbProps {
  health: Health;
  departments: Department[];
  signals: Signal[];
  gate?: GateState;
  calm?: boolean;
  quality?: "low" | "medium" | "high";
  onMorph?: (morphed: boolean) => void;
  morphed?: boolean;
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

interface RingHandle {
  mesh: THREE.Mesh;
  mat: THREE.ShaderMaterial;
  label: HTMLSpanElement;
  queue: number;
}

export default function PulseOrb(props: PulseOrbProps) {
  const {
    health,
    departments,
    signals,
    gate,
    calm = true,
    quality = "medium",
    onMorph,
    morphed: controlledMorphed,
  } = props;

  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const labelsRef = useRef<HTMLDivElement>(null);

  const [webglOk, setWebglOk] = useState(true);
  const [reduced, setReduced] = useState(false);
  const [morphed, setMorphed] = useState(false);
  const isMorphed = controlledMorphed ?? morphed;
  const [collapsedCount, setCollapsedCount] = useState(0);
  const selectedDepartmentIdsRef = useRef<Set<string>>(new Set());
  const [gateRatio, setGateRatio] = useState(0.5);

  // refs for latest props
  const healthRef = useRef(health);
  const departmentsRef = useRef(departments);
  const signalsRef = useRef(signals);
  const gateRef = useRef(gate);
  const calmRef = useRef(calm);
  const morphedRef = useRef(false);
  const morphProgressRef = useRef(0);

  // scene refs
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const ringGroupRef = useRef<THREE.Group | null>(null);
  const ringsRef = useRef<RingHandle[]>([]);
  const pointsRef = useRef<THREE.Points | null>(null);
  const particleMatRef = useRef<THREE.ShaderMaterial | null>(null);
  const gpgpuRef = useRef<GPUComputationRenderer | null>(null);
  const posVarRef = useRef<{ material: { uniforms: Record<string, { value: unknown }> } } | null>(null);
  const posTexRef = useRef<THREE.DataTexture | null>(null);
  const metaTexRef = useRef<THREE.DataTexture | null>(null);
  const targetTexRef = useRef<THREE.DataTexture | null>(null);
  const activeSignalsRef = useRef<Signal[]>([]);
  const sizeRef = useRef(128);
  const gateMatRef = useRef<THREE.ShaderMaterial | null>(null);
  const coreMatRef = useRef<THREE.MeshStandardMaterial | null>(null);
  const sphereMatRef = useRef<THREE.ShaderMaterial | null>(null);
  const hoveredRingRef = useRef<number>(-1);
  const focusedRingRef = useRef<number>(-1);
  const rendererCreationsRef = useRef(0);

  useEffect(() => {
    setWebglOk(hasWebGL());
    setReduced(prefersReducedMotion());
  }, []);

  // sync refs
  useEffect(() => { healthRef.current = health; }, [health]);
  useEffect(() => { departmentsRef.current = departments; syncDepartments(); }, [departments]);
  useEffect(() => { signalsRef.current = signals; syncParticles(); }, [signals]);
  useEffect(() => { gateRef.current = gate; updateGate(); }, [gate]);
  useEffect(() => { calmRef.current = calm; syncParticles(); }, [calm]);
  useEffect(() => { morphedRef.current = isMorphed; }, [isMorphed]);

  // One shared calm-mode attention budget across department and signal breaches.
  useEffect(() => {
    const selection = selectCalmHighlights(departments, signals, health, 7);
    selectedDepartmentIdsRef.current = selection.departmentIds;
    setCollapsedCount(calm ? selection.overflow : 0);
    syncParticles();
  }, [departments, signals, health, calm]);

  // gate ratio from props
  useEffect(() => {
    const strictness = computeStrictness(gate);
    setGateRatio(strictness);
    updateGate();
  }, [gate, signals]);

  const toggleMorph = () => {
    const next = !isMorphed;
    setMorphed(next);
    morphedRef.current = next;
    onMorph?.(next);
  };

  const sizeForQuality = particleTextureSize(quality);

  // --- sync functions ---
  function syncDepartments() {
    const group = ringGroupRef.current;
    if (!group) return;
    const deps = departmentsRef.current;
    // remove extra
    while (ringsRef.current.length > deps.length) {
      const r = ringsRef.current.pop()!;
      group.remove(r.mesh);
      r.mesh.geometry.dispose();
      r.mat.dispose();
      r.label.remove();
    }
    // add missing
    while (ringsRef.current.length < deps.length) {
      const i = ringsRef.current.length;
      const dept = deps[i] ?? deps[deps.length - 1];
      const layout = ringLayout(i);
      const tube = 0.012 + clamp(dept.queue, 0, 12) * 0.0025;
      const geo = new THREE.TorusGeometry(layout.radius, tube, 8, 96);
      const mat = new THREE.ShaderMaterial({
        uniforms: {
          uColor: { value: GOLD.clone() },
          uOpacity: { value: 0.7 },
          uPattern: { value: patternForStatus(dept.status) },
          uFog: { value: 0 },
        },
        vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
        fragmentShader: `varying vec2 vUv; uniform vec3 uColor; uniform float uOpacity; uniform int uPattern; uniform float uFog;
          void main(){
            float t=vUv.x*40.0; float a=1.0;
            if(uPattern==1) a=step(0.5,fract(t*0.25));
            else if(uPattern==2){ float d=length(fract(vec2(t*0.15,vUv.y*6.0))-0.5); a=1.0-smoothstep(0.08,0.18,d);}
            else if(uPattern==3) a=step(0.5,fract(t*0.25+vUv.y*4.0));
            vec3 col=mix(uColor, vec3(0.4,0.4,0.4), uFog*0.6);
            gl_FragColor=vec4(col, uOpacity*(1.0-uFog*0.5)*a);
          }`,
        transparent: true,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.set(layout.tiltX, layout.tiltY, layout.tiltZ);
      group.add(mesh);

      const label = document.createElement("span");
      label.textContent = dept.nameFa;
      label.style.position = "absolute";
      label.style.pointerEvents = "none";
      label.style.fontSize = "11px";
      label.style.color = "#d4af37";
      label.style.background = "rgba(0,0,0,0.6)";
      label.style.padding = "2px 6px";
      label.style.borderRadius = "4px";
      label.style.display = "none";
      label.style.whiteSpace = "nowrap";
      labelsRef.current?.appendChild(label);

      ringsRef.current.push({ mesh, mat, label, queue: dept.queue });
    }
    // update existing
    deps.forEach((dept, i) => {
      const ring = ringsRef.current[i];
      if (!ring) return;
      const age = ageSeconds(dept.lastDataAt);
      const fog = clamp(age / 60, 0, 1);
      const conf = clamp(dept.confidence, 0, 1);
      const col = GOLD.clone().lerp(GREY, 1 - conf);
      ring.mat.uniforms.uColor.value = col;
      ring.mat.uniforms.uOpacity.value = 0.85 - fog * 0.55;
      ring.mat.uniforms.uPattern.value = patternForStatus(dept.status);
      ring.mat.uniforms.uFog.value = fog;
      ring.label.textContent = dept.nameFa;
      // thickness update: recreate geometry if queue changed
      const layout = ringLayout(i);
      const tube = 0.012 + clamp(dept.queue, 0, 12) * 0.0025;
      const newGeo = new THREE.TorusGeometry(layout.radius, tube, 8, 96);
      ring.mesh.geometry.dispose();
      ring.mesh.geometry = newGeo;
      ring.mesh.rotation.set(layout.tiltX, layout.tiltY, layout.tiltZ);
    });
  }

  function syncParticles() {
    const size = sizeRef.current;
    const metaTex = metaTexRef.current;
    const posTex = posTexRef.current;
    if (!metaTex || !posTex) return;
    const metaArr = metaTex.image.data as Float32Array;
    const posArr = posTex.image.data as Float32Array;
    const deps = departmentsRef.current;
    const sigs = selectSignalParticles(
      deps,
      signalsRef.current,
      healthRef.current,
      calmRef.current,
      size * size,
    );
    activeSignalsRef.current = sigs;
    const n = Math.min(sigs.length, size * size);

    // A fixed-size texture is always present; unassigned particles remain ambient dust.
    for (let i = 0; i < size * size; i++) {
      const ix = i * 4;
      metaArr[ix] = 0;
      metaArr[ix + 1] = 0;
      metaArr[ix + 2] = 0;
      metaArr[ix + 3] = -1;
      posArr[ix + 3] = 1;
    }
    for (let i = 0; i < n; i++) {
      const sig = sigs[i];
      const found = deps.findIndex((d) => d.id === sig.deptId);
      const deptIndex = Math.max(0, found);
      const layout = ringLayout(deptIndex % Math.max(1, deps.length));
      const baseAngle = (deptIndex / Math.max(1, deps.length)) * Math.PI * 2;
      const ox = Math.cos(baseAngle) * layout.radius;
      const oz = Math.sin(baseAngle) * layout.radius;
      const ix = i * 4;
      posArr[ix] = ox;
      posArr[ix + 1] = 0;
      posArr[ix + 2] = oz;
      posArr[ix + 3] = 0;
      metaArr[ix] = ox;
      metaArr[ix + 1] = 0;
      metaArr[ix + 2] = oz;
      metaArr[ix + 3] = outcomeCode(sig.outcome);
    }
    metaTex.needsUpdate = true;
    posTex.needsUpdate = true;
  }

  function updateGate() {
    const mat = gateMatRef.current;
    if (!mat) return;
    const strictness = computeStrictness(gateRef.current ?? undefined);
    setGateRatio(strictness);
    mat.uniforms.uRatio.value = strictness;
  }

  // --- main init effect ---
  useEffect(() => {
    if (!webglOk || reduced) return;
    const container = containerRef.current;
    if (!container) return;

    rendererCreationsRef.current += 1;
    if (typeof window !== "undefined") {
      const counterWindow = window as Window & { __pulseOrbRendererCreations?: number };
      counterWindow.__pulseOrbRendererCreations = (counterWindow.__pulseOrbRendererCreations ?? 0) + 1;
      container.dataset.rendererCreations = String(counterWindow.__pulseOrbRendererCreations);
    }

    const size = sizeForQuality;
    sizeRef.current = size;
    container.dataset.particleTexture = `${size}x${size}`;

    const scene = new THREE.Scene();
    sceneRef.current = scene;
    const camera = new THREE.PerspectiveCamera(45, Math.max(1, container.clientWidth) / Math.max(1, container.clientHeight), 0.1, 100);
    camera.position.set(0, 0, 8.5);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setSize(container.clientWidth || 300, container.clientHeight || 300);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const ambient = new THREE.AmbientLight(0xffffff, 0.25);
    scene.add(ambient);
    const point = new THREE.PointLight(0xd4af37, 1.2, 20);
    point.position.set(2, 2, 4);
    scene.add(point);

    // glass sphere
    const sphereGeo = new THREE.SphereGeometry(1.5, 64, 64);
    const sphereMat = new THREE.ShaderMaterial({
      uniforms: { uTime: { value: 0 }, uGold: { value: GOLD.clone() }, uIntensity: { value: 0.25 } },
      vertexShader: `varying vec3 vNormal; varying vec3 vView; void main(){ vNormal=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.0); vView=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
      fragmentShader: `varying vec3 vNormal; varying vec3 vView; uniform vec3 uGold; uniform float uIntensity; void main(){ float fres=pow(1.0-max(dot(vNormal,vView),0.0),2.4); vec3 base=vec3(0.012,0.014,0.02); vec3 rim=uGold*fres*0.9*uIntensity; float hatch=step(0.92,fract(vNormal.x*12.0+vNormal.y*7.0)); rim+=uGold*hatch*0.15; gl_FragColor=vec4(base+rim,0.85); }`,
      transparent: true,
      depthWrite: false,
    });
    sphereMatRef.current = sphereMat;
    const sphere = new THREE.Mesh(sphereGeo, sphereMat);
    scene.add(sphere);

    // core
    const coreGeo = new THREE.SphereGeometry(0.32, 32, 32);
    const coreMat = new THREE.MeshStandardMaterial({ color: 0xd4af37, emissive: 0xd4af37, emissiveIntensity: 0.7, roughness: 0.3, metalness: 0.8 });
    coreMatRef.current = coreMat;
    const core = new THREE.Mesh(coreGeo, coreMat);
    core.name = "core";
    scene.add(core);

    // rings
    const ringGroup = new THREE.Group();
    ringGroupRef.current = ringGroup;
    scene.add(ringGroup);

    // gate
    const gateRadius = 1.9;
    const gateGeo = new THREE.TorusGeometry(gateRadius, 0.01, 6, 64, Math.PI * 2);
    const gateMat = new THREE.ShaderMaterial({
      uniforms: { uRatio: { value: 0.5 }, uOpacity: { value: 0.6 } },
      vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
      fragmentShader: `varying vec2 vUv; uniform float uRatio; uniform float uOpacity; void main(){ float ang=vUv.x; vec3 gold=vec3(0.83,0.69,0.22); vec3 grey=vec3(0.42,0.42,0.42); vec3 col = ang < uRatio ? gold : grey; gl_FragColor=vec4(col,uOpacity); }`,
      transparent: true,
      depthWrite: false,
    });
    gateMatRef.current = gateMat;
    const gateMesh = new THREE.Mesh(gateGeo, gateMat);
    gateMesh.rotation.x = Math.PI / 2;
    scene.add(gateMesh);

    // GPGPU
    const gpgpu = new GPUComputationRenderer(size, size, renderer);
    try { gpgpu.setDataType(THREE.HalfFloatType); } catch { /* ignore */ }
    gpgpuRef.current = gpgpu;

    const posTex = gpgpu.createTexture();
    const metaTex = gpgpu.createTexture();
    const targetTex = gpgpu.createTexture();
    posTexRef.current = posTex;
    metaTexRef.current = metaTex;
    targetTexRef.current = targetTex;

    const posArr = posTex.image.data as Float32Array;
    const metaArr = metaTex.image.data as Float32Array;
    const targetArr = targetTex.image.data as Float32Array;
    for (let i = 0; i < size * size; i++) {
      const ix = i * 4;
      posArr[ix + 3] = 1;
      metaArr[ix + 3] = -1;
      targetArr[ix + 3] = 0;
    }

    const posShader = `
      uniform sampler2D metaTexture;
      uniform sampler2D targetTexture;
      uniform float uDelta;
      uniform float uSpeed;
      uniform float uMorph;
      uniform float uTime;
      void main() {
        vec2 uv = gl_FragCoord.xy / resolution.xy;
        vec4 p = texture2D(posTexture, uv);
        vec4 m = texture2D(metaTexture, uv);
        vec4 t = texture2D(targetTexture, uv);
        if (m.w < 0.0) {
          float idx = (gl_FragCoord.x - 0.5) + (gl_FragCoord.y - 0.5) * resolution.x;
          float ang = idx * 0.61803398875 * 6.28318;
          float r = 1.64 + 0.10 * sin(uTime*0.2 + idx);
          float y = 0.32 * sin(idx*1.7 + uTime*0.16);
          vec3 dust = vec3(cos(ang + uTime*0.035)*r, y, sin(ang + uTime*0.035)*r);
          gl_FragColor = vec4(mix(dust, t.xyz, uMorph), 1.0);
          return;
        }
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
    posVar.material.uniforms.uMorph = { value: 0 };
    posVar.material.uniforms.uTime = { value: 0 };
    posVarRef.current = posVar as unknown as { material: { uniforms: Record<string, { value: unknown }> } };

    const err = gpgpu.init();
    if (err) console.error("GPGPU init error:", err);

    // particle material
    const particleGeo = new THREE.BufferGeometry();
    const indices = new Float32Array(size * size);
    for (let i = 0; i < size * size; i++) indices[i] = i;
    particleGeo.setAttribute("aIndex", new THREE.BufferAttribute(indices, 1));
    particleGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(size * size * 3), 3));

    const particleMat = new THREE.ShaderMaterial({
      uniforms: {
        uPosTex: { value: gpgpu.getCurrentRenderTarget(posVar).texture },
        uMetaTex: { value: metaTex },
        uTargetTex: { value: targetTex },
        uTexSize: { value: size },
        uPointSize: { value: quality === "low" ? 2.0 : 3.0 },
        uGold: { value: GOLD.clone() },
        uGrey: { value: GREY.clone() },
        uMorph: { value: 0 },
      },
      vertexShader: `
        attribute float aIndex;
        uniform sampler2D uPosTex;
        uniform sampler2D uMetaTex;
        uniform sampler2D uTargetTex;
        uniform float uTexSize;
        uniform float uPointSize;
        varying float vProgress;
        varying float vOutcome;
        varying float vIran;
        void main() {
          float x = mod(aIndex, uTexSize);
          float y = floor(aIndex / uTexSize);
          vec2 uv = (vec2(x, y) + 0.5) / uTexSize;
          vec4 p = texture2D(uPosTex, uv);
          vec4 m = texture2D(uMetaTex, uv);
          vec4 t = texture2D(uTargetTex, uv);
          if (m.w < 0.0) {
            // ambient dust still rendered
          }
          vec3 pos = p.xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = uPointSize;
          vProgress = p.w;
          vOutcome = m.w;
          vIran = t.w;
        }
      `,
      fragmentShader: `
        varying float vProgress;
        varying float vOutcome;
        varying float vIran;
        uniform vec3 uGold;
        uniform vec3 uGrey;
        uniform float uMorph;
        void main() {
          vec2 c = gl_PointCoord - 0.5;
          if (dot(c, c) > 0.25) discard;
          vec3 color = uGold;
          float alpha = 0.9;
          if (vOutcome < -0.5) {
            color = vec3(0.55, 0.55, 0.6);
            alpha = 0.22;
          } else if (vOutcome > 0.5 && vOutcome < 1.5) {
            color = uGrey;
            if (vProgress >= 0.65) alpha = (1.0 - vProgress) * 2.0;
          } else if (vOutcome > 1.5) {
            color = uGold;
            alpha = 0.6 * (1.0 - vProgress * 0.5);
          }
          if (uMorph > 0.5 && vIran > 0.5) {
            color = uGold;
            alpha = 0.95;
          }
          if (vOutcome < 0.5 && vOutcome > -0.5 && vProgress > 0.98) {
            color = vec3(1.0, 0.92, 0.55);
            alpha = 1.0;
          }
          gl_FragColor = vec4(color, clamp(alpha, 0.0, 1.0));
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    particleMatRef.current = particleMat;

    const points = new THREE.Points(particleGeo, particleMat);
    pointsRef.current = points;
    scene.add(points);

    // raycaster for ring hover
    const raycaster = new THREE.Raycaster();

    // pointer handlers
    const onPointerMove = (e: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const ndc = new THREE.Vector2(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
      raycaster.setFromCamera(ndc, camera);
      const ringMeshes = ringsRef.current.map((r) => r.mesh);
      const hits = raycaster.intersectObjects(ringMeshes);
      if (hits.length) {
        const idx = ringMeshes.indexOf(hits[0].object as THREE.Mesh);
        hoveredRingRef.current = idx;
      } else {
        hoveredRingRef.current = -1;
      }
      // tooltip for particles
      const phits = raycaster.intersectObject(points);
      if (phits.length && typeof phits[0].index === "number") {
        const idx = phits[0].index as number;
        if (idx < activeSignalsRef.current.length) {
          const sig = activeSignalsRef.current[idx];
          if (tooltipRef.current) {
            tooltipRef.current.style.display = "block";
            tooltipRef.current.style.left = e.clientX - rect.left + 12 + "px";
            tooltipRef.current.style.top = e.clientY - rect.top + 12 + "px";
            tooltipRef.current.textContent = sig.reason ?? sig.outcome;
          }
          return;
        }
      }
      if (tooltipRef.current) tooltipRef.current.style.display = "none";
    };
    const onPointerLeave = () => {
      hoveredRingRef.current = -1;
      if (tooltipRef.current) tooltipRef.current.style.display = "none";
    };
    renderer.domElement.addEventListener("pointermove", onPointerMove);
    renderer.domElement.addEventListener("pointerleave", onPointerLeave);

    // sync rings/particles with current props
    syncDepartments();
    syncParticles();
    updateGate();

    // Build one target per fixed particle from actual country geometry.
    let disposed = false;
    fetch("/geo/world.geo.json")
      .then((response) => {
        if (!response.ok) throw new Error(`GeoJSON request failed: ${response.status}`);
        return response.json() as Promise<FeatureCollection>;
      })
      .then((geo) => {
        if (disposed || !targetTexRef.current) return;
        const result = buildMapTargets(geo, size);
        const targetData = targetTexRef.current.image.data as Float32Array;
        targetData.set(result.data);
        targetTexRef.current.needsUpdate = true;
        console.info("PulseOrb map targets", {
          particleCount: result.sampledPoints,
          iranHighlighted: result.iranPoints,
          countryPaths: result.featuresWithPaths,
        });
      })
      .catch((error: unknown) => console.error("PulseOrb map target load failed", error));

    // animation
    const clock = new THREE.Clock();
    let raf = 0;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      if (document.hidden) return;
      const dt = Math.min(clock.getDelta(), 0.05);
      const t = clock.elapsedTime;
      const h = healthRef.current;
      const calmNow = calmRef.current;

      const breach =
        departmentsRef.current.some((d) => d.status !== "LIVE") ||
        signalsRef.current.some((s) => s.outcome === "pending" || s.outcome === "dissipated") ||
        h.stale ||
        h.jitterMs > 200;
      const intensity = calmNow ? (breach ? 1.0 : 0.22) : 1.0;

      // Calm heartbeat is slower and dimmer unless a breach needs attention.
      let pulse = 0;
      if (!h.stale && h.bpm > 0) {
        const bpmScale = calmNow && !breach ? 0.35 : 1;
        const phase = t * (h.bpm * bpmScale / 60) * Math.PI * 2 + Math.sin(t * 7.3) * (h.jitterMs / 1000);
        pulse = (calmNow && !breach ? 0.025 : 0.12) * (0.5 + 0.5 * Math.sin(phase));
      }
      if (coreMatRef.current) {
        coreMatRef.current.emissiveIntensity = (calmNow && !breach ? 0.08 : 0.6) + pulse * 3;
      }
      const core = scene.getObjectByName("core") as THREE.Mesh | undefined;
      if (core) core.scale.setScalar(1 + pulse);

      if (sphereMatRef.current) {
        sphereMatRef.current.uniforms.uTime.value = t;
        sphereMatRef.current.uniforms.uIntensity.value = intensity;
      }

      // rings
      departmentsRef.current.forEach((dept, i) => {
        const ring = ringsRef.current[i];
        if (!ring) return;
        const age = ageSeconds(dept.lastDataAt);
        const fog = clamp(age / 60, 0, 1);
        const conf = clamp(dept.confidence, 0, 1);
        const selectedHighlight = selectedDepartmentIdsRef.current.has(dept.id);
        const calmDim = calmNow && !selectedHighlight ? (dept.status === "LIVE" ? 0.46 : 0.18) : 1;
        const col = GOLD.clone().lerp(GREY, 1 - conf);
        if (calmNow && dept.status !== "LIVE" && !selectedHighlight) col.lerp(FOG_GREY, 0.75);
        ring.mat.uniforms.uColor.value = col;
        ring.mat.uniforms.uOpacity.value = (0.85 - fog * 0.55) * (0.4 + intensity * 0.6) * calmDim;
        ring.mat.uniforms.uFog.value = fog;
        ring.mat.uniforms.uPattern.value = patternForStatus(dept.status);
        const stalled = dept.status === "STALE" || dept.rate <= 0;
        if (!morphedRef.current) {
          ring.mesh.rotation.z += ringRotationDelta(dept.rate, dt, intensity, stalled);
        }
        // label visibility
        const showLabel = hoveredRingRef.current === i || focusedRingRef.current === i;
        ring.label.style.display = showLabel ? "block" : "none";
        // project label position
        ring.mesh.updateMatrixWorld();
        const v = new THREE.Vector3(ringLayout(i).radius, 0, 0).applyMatrix4(ring.mesh.matrixWorld);
        v.project(camera);
        const rect = renderer.domElement.getBoundingClientRect();
        const lx = (v.x * 0.5 + 0.5) * rect.width;
        const ly = (-v.y * 0.5 + 0.5) * rect.height;
        ring.label.style.left = lx + "px";
        ring.label.style.top = ly + "px";
      });

      // gate
      if (gateMatRef.current) {
        const strictness = computeStrictness(gateRef.current ?? undefined);
        gateMatRef.current.uniforms.uRatio.value = strictness;
        gateMatRef.current.uniforms.uOpacity.value = 0.3 + intensity * 0.4;
      }

      // morph progress
      const targetMorph = morphedRef.current ? 1 : 0;
      morphProgressRef.current += (targetMorph - morphProgressRef.current) * Math.min(1, dt * 2.5);

      // gpgpu
      const pv = posVarRef.current;
      if (pv && gpgpuRef.current) {
        pv.material.uniforms.uDelta.value = dt;
        pv.material.uniforms.uSpeed.value = 0.6 + intensity * 0.6;
        pv.material.uniforms.uMorph.value = morphProgressRef.current;
        pv.material.uniforms.uTime.value = t;
        gpgpuRef.current.compute();
        const pv2 = posVarRef.current as unknown as { /* noop */ } | null;
        if (particleMatRef.current && pv2) {
          particleMatRef.current.uniforms.uPosTex.value = gpgpuRef.current.getCurrentRenderTarget(
            pv2 as never,
          ).texture;
          particleMatRef.current.uniforms.uMorph.value = morphProgressRef.current;
        }
      }

      // scene rotation
      scene.rotation.y += 0.02 * dt * intensity;

      renderer.render(scene, camera);
    };
    animate();

    // resize
    const handleResize = () => {
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
      scene.traverse((obj) => {
        const mesh = obj as THREE.Mesh;
        if (mesh.geometry) mesh.geometry.dispose();
        const mat = mesh.material as THREE.Material | THREE.Material[];
        if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
        else if (mat) mat.dispose();
      });
      ringsRef.current.forEach((r) => r.label.remove());
      ringsRef.current = [];
      ringGroupRef.current = null;
      gpgpuRef.current?.dispose?.();
      gpgpuRef.current = null;
      posVarRef.current = null;
      renderer.dispose();
      if (renderer.domElement.parentNode === container) container.removeChild(renderer.domElement);
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      pointsRef.current = null;
      particleMatRef.current = null;
    };
  }, [webglOk, reduced]);

  // sync particles when signals/departments change (without rebuild)
  // already called via effects; ensure initial
  useEffect(() => {
    syncParticles();
  }, [signals, departments]);

  useEffect(() => {
    syncDepartments();
  }, [departments]);

  if (!webglOk || reduced) {
    return <SvgFallback departments={departments} signals={signals} health={health} gate={gate} calm={calm} />;
  }

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      <div ref={labelsRef} className="pointer-events-none absolute inset-0 overflow-hidden" />
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
            aria-label={isMorphed ? "بازگشت به اورب" : "نمایش نقشه جهان"}
          >
            {isMorphed ? "اورب" : "نقشه"}
          </button>
        </div>
        <div className="pointer-events-auto rounded bg-black/40 px-3 py-1 text-xs text-amber-200 backdrop-blur">
              سخت‌گیری دروازه: {Math.round(gateRatio * 100)}%
        </div>
      </div>
      {collapsedCount > 0 && (
        <div className="absolute bottom-4 left-4 rounded bg-black/50 px-2 py-1 text-xs text-stone-300">
          +{collapsedCount} مورد دیگر
        </div>
      )}
      <div className="sr-only">
        {departments.map((d, i) => (
          <button
            key={d.id}
            tabIndex={0}
            aria-label={`بخش ${d.nameFa} وضعیت ${d.status}`}
            onFocus={() => { focusedRingRef.current = i; }}
            onBlur={() => { focusedRingRef.current = -1; }}
          >
            {d.nameFa}
          </button>
        ))}
        {signals.map((s) => (
          <button key={s.id} tabIndex={0} aria-label={`سیگنال ${s.id} ${s.outcome} ${s.reason ?? ""}`}>
            {s.id}
          </button>
        ))}
      </div>
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
          <li key={s.id}>{s.id} {s.deptId} {s.outcome} {s.reason ?? ""}</li>
        ))}
      </ul>
    </div>
  );
}

function SvgFallback({ departments, signals, health, gate, calm }: { departments: Department[]; signals: Signal[]; health: Health; gate?: GateState; calm: boolean }) {
  const strictness = computeStrictness(gate);
  const selection = selectCalmHighlights(departments, signals, health, 7);
  const signalIds = new Set((calm ? selection.signals : signals).map((signal) => signal.id));
  return (
    <div className="relative flex h-full w-full items-center justify-center" role="group" aria-label="نمای ساده اورب">
      <svg viewBox="0 0 400 400" className="h-full w-full max-w-2xl" aria-hidden="true">
        <defs>
          <radialGradient id="orb-glass"><stop offset="0" stopColor="#16130b"/><stop offset="0.72" stopColor="#08090d"/><stop offset="1" stopColor="#d4af37" stopOpacity=".38"/></radialGradient>
          <filter id="soft-glow"><feGaussianBlur stdDeviation="2.5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>
        <circle cx="200" cy="200" r="34" fill="#d4af37" fillOpacity=".18" stroke="#d4af37" strokeOpacity=".55" />
        <circle cx="200" cy="200" r="26" fill="url(#orb-glass)" />
        {departments.slice(0, 12).map((d, i) => {
          const radius = 48 + i * 6.2;
          const age = Math.max(0, (Date.now() - new Date(d.lastDataAt).getTime()) / 60000);
          const fog = clamp(age, 0, 1);
          const dash = d.status === "STALE" ? "6 4" : d.status === "UNKNOWN" ? "1 5" : d.status === "DEMO" ? "5 2 1 2" : "none";
          const selected = selection.departmentIds.has(d.id);
          const calmDim = calm && d.status !== "LIVE" && !selected ? 0.18 : calm && !selected ? 0.55 : 1;
          const opacity = Math.max(0.08, (d.status === "LIVE" ? 0.66 : 0.9) * (1 - fog * 0.65) * calmDim);
          return (
            <ellipse
              key={d.id}
              cx="200"
              cy="200"
              rx={radius}
              ry={radius * (0.52 + (i % 3) * 0.08)}
              transform={`rotate(${i * 15 - 80} 200 200)`}
              fill="none"
              stroke={d.confidence < 0.4 ? "#777" : "#d4af37"}
              strokeWidth={1 + clamp(d.queue, 0, 8) * 0.32}
              strokeOpacity={opacity}
              strokeDasharray={dash}
            />
          );
        })}
            {signals.filter((signal) => signalIds.has(signal.id)).map((signal, i) => {
          const angle = (i / Math.max(1, Math.min(signals.length, 7))) * Math.PI * 2;
          return <circle key={signal.id} cx={200 + Math.cos(angle) * 35} cy={200 + Math.sin(angle) * 35} r="2.5" fill={signal.outcome === "absorbed" ? "#d4af37" : "#8b8b8b"} filter="url(#soft-glow)" />;
        })}
        <circle cx="200" cy="200" r="133" fill="none" stroke="#777" strokeOpacity=".5" strokeWidth="3" />
        <circle cx="200" cy="200" r="133" fill="none" stroke="#d4af37" strokeOpacity=".9" strokeWidth="3" pathLength="100" strokeDasharray={`${strictness * 100} 100`} transform="rotate(-90 200 200)" />
        <text x="200" y="380" textAnchor="middle" fill="#aaa" fontSize="12">BPM {health.bpm} {health.stale ? "(stale)" : ""}</text>
      </svg>
      {calm && selection.overflow > 0 && <div className="absolute bottom-3 left-3 rounded bg-black/60 px-2 py-1 text-xs text-stone-300">+{selection.overflow} مورد دیگر</div>}
      <div className="absolute right-3 top-3 rounded bg-amber-400/20 px-2 py-0.5 text-xs text-amber-200">DEMO</div>
      <table className="sr-only">
        <caption>داده‌های اورب</caption>
        <thead><tr><th>بخش</th><th>وضعیت</th><th>نرخ</th><th>صف</th><th>اعتماد</th></tr></thead>
        <tbody>{departments.map((d) => <tr key={d.id}><td>{d.nameFa}</td><td>{d.status}</td><td>{d.rate}</td><td>{d.queue}</td><td>{d.confidence}</td></tr>)}</tbody>
      </table>
      <table className="sr-only">
        <caption>سیگنال‌ها</caption>
        <thead><tr><th>شناسه</th><th>بخش</th><th>نتیجه</th><th>دلیل</th></tr></thead>
        <tbody>{signals.map((signal) => <tr key={signal.id}><td>{signal.id}</td><td>{signal.deptId}</td><td>{signal.outcome}</td><td>{signal.reason ?? ""}</td></tr>)}</tbody>
      </table>
    </div>
  );
}
