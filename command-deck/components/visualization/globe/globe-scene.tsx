"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { AMBIENCE, SEASON_TINTS } from "@/lib/visualization/ambience";
import type { AmbiencePreset, SeasonPreset } from "@/lib/types";

/* ------------------------------------------------------------------ */
/* procedural helpers (deterministic — no Math.random, no wall clock)  */

function hash01(i: number): number {
  let h = (i * 2654435761) >>> 0;
  h ^= h >>> 13;
  h = (h * 1274126177) >>> 0;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

function radialTexture(softness = 0.55): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 62);
    grad.addColorStop(0, "rgba(255,255,255,1)");
    grad.addColorStop(softness, "rgba(255,255,255,0.8)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 128, 128);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** soft ring sprite for the projector platform */
function platformGlowTexture(): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createRadialGradient(128, 128, 20, 128, 128, 126);
    grad.addColorStop(0, "rgba(255,255,255,0.85)");
    grad.addColorStop(0.55, "rgba(255,255,255,0.18)");
    grad.addColorStop(0.85, "rgba(255,255,255,0.05)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 256);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const ringGeoCache = { inner: 0, outer: 0, geo: null as THREE.RingGeometry | null };
function unitRing(): THREE.RingGeometry {
  if (!ringGeoCache.geo || ringGeoCache.inner !== 0.86 || ringGeoCache.outer !== 1) {
    ringGeoCache.inner = 0.86;
    ringGeoCache.outer = 1;
    ringGeoCache.geo = new THREE.RingGeometry(0.86, 1, 96);
  }
  return ringGeoCache.geo;
}

/** lat/lon (degrees) → unit vector matching THREE.SphereGeometry equirect UVs */
function latLonToVec(lat: number, lon: number): THREE.Vector3 {
  const phi = ((lon + 180) / 360) * Math.PI * 2;
  const theta = ((90 - lat) / 180) * Math.PI;
  return new THREE.Vector3(
    -Math.cos(phi) * Math.sin(theta),
    Math.cos(theta),
    Math.sin(phi) * Math.sin(theta),
  );
}

/* final grade pass: vignette + film grain + subtle chromatic aberration */
const GRADE_SHADER = {
  uniforms: {
    tDiffuse: { value: null as THREE.Texture | null },
    uTime: { value: 0 },
    uAmount: { value: 1 },
  },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse;
    uniform float uTime;
    uniform float uAmount;
    varying vec2 vUv;
    float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7)) + uTime * 13.7) * 43758.5453); }
    void main(){
      vec2 c = vUv - 0.5;
      float r2 = dot(c, c);
      // chromatic aberration grows toward the edges
      float ab = 0.0016 * r2 * 4.0 * uAmount;
      vec3 col;
      col.r = texture2D(tDiffuse, vUv + c * ab).r;
      col.g = texture2D(tDiffuse, vUv).g;
      col.b = texture2D(tDiffuse, vUv - c * ab).b;
      // vignette
      float vig = smoothstep(0.95, 0.28, length(c) * 1.25);
      col *= mix(1.0, vig, 0.42 * uAmount);
      // film grain
      col += (hash(vUv * vec2(1920.0, 1080.0)) - 0.5) * 0.028 * uAmount;
      gl_FragColor = vec4(col, 1.0);
    }`,
};

/* ------------------------------------------------------------------ */

/**
 * Cinematic AHOS command-chamber scene (plain Three.js — no R3F).
 * Photoreal Earth (NASA Blue Marble day / Black Marble night lights / ocean
 * specular via water mask / drifting cloud shell), volumetric projector beam
 * from a light-well platform, rising embers, holo scan pulse, gyro rings,
 * orbit gates with comet trails, data packets, dust, nebulae, bloom + grade
 * pass (grain/vignette/aberration), DOM asset chips pinned to real lat/lons.
 * Decorative and simulation-labeled; drag-to-spin with inertia, pointer
 * parallax, tab-hidden pause, bounded DPR, full disposal, 2D fallback above.
 */
export default function GlobeScene({
  preset,
  season,
  onFail,
}: {
  preset: AmbiencePreset;
  season: SeasonPreset;
  onFail: () => void;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let disposed = false;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false,
        powerPreference: "high-performance",
      });
    } catch {
      onFail();
      return;
    }
    if (!renderer.getContext()) {
      onFail();
      return;
    }

    const spec = AMBIENCE[preset].three;
    const seasonSpec = SEASON_TINTS[season];
    const dpr = Math.min(window.devicePixelRatio || 1, 1.6);
    renderer.setPixelRatio(dpr);
    renderer.setClearColor(0x04060d, 1);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 120);
    camera.position.set(0, 0.34, 3.7);

    /* ---------------- lights ---------------- */
    scene.add(new THREE.AmbientLight(0x8fa3c8, 0.28));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.4);
    keyLight.position.set(3, 1.4, 3.4);
    const rimLight = new THREE.DirectionalLight(spec.rim, 1.1);
    rimLight.position.set(-4, -1.4, -3);
    scene.add(keyLight, rimLight);

    /** single sun direction shared by every shader */
    const LIGHT_DIR = new THREE.Vector3(3, 1.4, 3.4).normalize();

    /* ---------------- sky dome + stars + nebulae ---------------- */
    const skyMat = new THREE.ShaderMaterial({
      side: THREE.BackSide,
      depthWrite: false,
      uniforms: {
        uTop: { value: new THREE.Color(spec.skyTop) },
        uBottom: { value: new THREE.Color(spec.skyBottom) },
      },
      vertexShader: `varying vec3 vPos; void main(){ vPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `
        varying vec3 vPos; uniform vec3 uTop; uniform vec3 uBottom;
        void main(){
          float h = clamp(normalize(vPos).y * 0.5 + 0.5, 0.0, 1.0);
          vec3 col = mix(uBottom, uTop, pow(h, 1.3));
          gl_FragColor = vec4(col, 1.0);
        }`,
    });
    scene.add(new THREE.Mesh(new THREE.SphereGeometry(40, 32, 24), skyMat));

    const starGeo = new THREE.BufferGeometry();
    {
      const starPos: number[] = [];
      const starCol: number[] = [];
      const white = new THREE.Color(0xdfe8ff);
      const cyan = new THREE.Color(0x7fd8e8);
      const gold = new THREE.Color(0xe7c55c);
      for (let i = 0; i < 1300; i += 1) {
        const y = 1 - (i / 1299) * 2;
        const r = Math.sqrt(Math.max(0, 1 - y * y));
        const theta = i * 2.399963;
        const rad = 24 + hash01(i * 7 + 1) * 8;
        starPos.push(Math.cos(theta) * r * rad, y * rad * 0.92, Math.sin(theta) * r * rad);
        const c = hash01(i * 13 + 5) > 0.92 ? cyan : hash01(i * 17 + 9) > 0.94 ? gold : white;
        const b = 0.3 + hash01(i * 23 + 3) * 0.7;
        starCol.push(c.r * b, c.g * b, c.b * b);
      }
      starGeo.setAttribute("position", new THREE.Float32BufferAttribute(starPos, 3));
      starGeo.setAttribute("color", new THREE.Float32BufferAttribute(starCol, 3));
    }
    const stars = new THREE.Points(
      starGeo,
      new THREE.PointsMaterial({
        size: 1.6,
        sizeAttenuation: false,
        vertexColors: true,
        transparent: true,
        opacity: 0.9,
        depthWrite: false,
      }),
    );
    scene.add(stars);

    const glowTexture = radialTexture(0.35);
    const nebulae: THREE.Sprite[] = [];
    const NEBULA = [
      { dir: new THREE.Vector3(-5, 2.4, -9), scale: 17, color: 0x1d3a6e },
      { dir: new THREE.Vector3(6, -1.6, -8.4), scale: 14, color: 0x3a2a63 },
      { dir: new THREE.Vector3(0.6, 3.4, -9.6), scale: 11, color: 0x14384a },
    ];
    NEBULA.forEach((n, i) => {
      const sprite = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: glowTexture,
          color: n.color,
          transparent: true,
          opacity: 0.16 + i * 0.015,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      );
      sprite.position.copy(n.dir);
      sprite.scale.setScalar(n.scale);
      scene.add(sprite);
      nebulae.push(sprite);
    });

    /* ---------------- photoreal Earth ---------------- */
    const globe = new THREE.Group();
    globe.rotation.z = 0.1;
    scene.add(globe);

    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin("anonymous");
    let texLoads = 0;
    const dayTex = loader.load("/textures/earth-day-2048.jpg", () => void ++texLoads, undefined, () => onFail());
    const nightTex = loader.load("/textures/earth-night-2048.jpg", () => void ++texLoads, undefined, () => onFail());
    const waterTex = loader.load("/textures/earth-water-2048.png", () => void ++texLoads, undefined, () => onFail());
    const cloudTex = loader.load("/textures/clouds-2048.png", () => void ++texLoads, undefined, () => onFail());
    dayTex.colorSpace = THREE.SRGBColorSpace;
    nightTex.colorSpace = THREE.SRGBColorSpace;
    cloudTex.colorSpace = THREE.SRGBColorSpace;
    waterTex.colorSpace = THREE.NoColorSpace;
    for (const t of [dayTex, nightTex, waterTex, cloudTex]) {
      t.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
    }

    const earthMat = new THREE.ShaderMaterial({
      uniforms: {
        uDay: { value: dayTex },
        uNight: { value: nightTex },
        uWater: { value: waterTex },
        uLightDir: { value: LIGHT_DIR.clone() },
        uAtmo: { value: new THREE.Color(spec.atmosphere) },
        uTint: { value: new THREE.Color(seasonSpec.tint) },
        uTintStrength: { value: seasonSpec.strength * 0.5 },
        uSun: { value: new THREE.Color(spec.key) },
      },
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vView;
        void main(){
          vUv = uv;
          vNormal = normalize(mat3(modelMatrix) * normal);
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          vView = normalize(-mv.xyz);
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: `
        uniform sampler2D uDay;
        uniform sampler2D uNight;
        uniform sampler2D uWater;
        uniform vec3 uLightDir;
        uniform vec3 uAtmo;
        uniform vec3 uTint;
        uniform float uTintStrength;
        uniform vec3 uSun;
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vView;
        void main(){
          vec3 N = normalize(vNormal);
          vec3 V = normalize(vView);
          vec3 L = normalize(uLightDir);
          float d = dot(N, L);
          float dayMix = smoothstep(-0.14, 0.28, d);

          vec3 day = texture2D(uDay, vUv).rgb;
          vec3 nightImg = texture2D(uNight, vUv).rgb;
          float water = texture2D(uWater, vUv).r;

          // gently grade the day side toward the chamber palette
          day = mix(day, day * (uTint * 0.5 + 0.72), uTintStrength);

          // ocean sun glint (only water, only day side)
          vec3 R = reflect(-L, N);
          float spec = pow(max(dot(R, V), 0.0), 42.0) * water * dayMix;
          day += uSun * spec * 0.55;

          // night side: near-black + warm city lights
          float lights = dot(nightImg, vec3(0.35, 0.45, 0.2));
          vec3 city = vec3(1.0, 0.72, 0.34) * pow(lights, 1.35) * 1.5;
          vec3 night = vec3(0.012, 0.02, 0.045) + city;

          vec3 col = mix(night, day, dayMix);

          // atmospheric rim (stronger on the lit limb)
          float fres = pow(1.0 - max(dot(N, V), 0.0), 2.6);
          col += uAtmo * fres * (0.35 + 0.45 * dayMix);

          // faint terminator warm band
          float term = smoothstep(0.22, 0.0, abs(d)) * 0.14;
          col += vec3(0.9, 0.55, 0.25) * term;

          gl_FragColor = vec4(col, 1.0);
        }`,
    });
    globe.add(new THREE.Mesh(new THREE.SphereGeometry(1, 96, 96), earthMat));

    /* drifting cloud shell */
    const cloudMat = new THREE.MeshLambertMaterial({
      map: cloudTex,
      transparent: true,
      opacity: 0.34,
      depthWrite: false,
    });
    const clouds = new THREE.Mesh(new THREE.SphereGeometry(1.016, 72, 72), cloudMat);
    scene.add(clouds);

    /* holographic scan band travelling across the globe */
    const scanMat = new THREE.MeshBasicMaterial({
      color: 0x7fd8e8,
      transparent: true,
      opacity: 0.28,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const scan = new THREE.Mesh(new THREE.TorusGeometry(1, 0.006, 8, 128), scanMat);
    scan.rotation.x = Math.PI / 2;
    scene.add(scan);

    /* ---------------- atmosphere shells ---------------- */
    const atmosphereMat = new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: new THREE.Color(spec.atmosphere) },
        uLightDir: { value: LIGHT_DIR.clone() },
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vWorld;
        void main(){
          vNormal = normalize(mat3(modelMatrix) * normal);
          vWorld = normalize(position);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }`,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vWorld;
        uniform vec3 uColor;
        uniform vec3 uLightDir;
        void main(){
          float i = pow(0.72 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 3.2);
          float lit = 0.5 + 0.5 * dot(normalize(vWorld), normalize(uLightDir));
          gl_FragColor = vec4(uColor, 1.0) * i * (0.16 + 0.22 * lit);
        }`,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false,
    });
    scene.add(new THREE.Mesh(new THREE.SphereGeometry(1.12, 64, 64), atmosphereMat));

    const innerAtmoMat = new THREE.ShaderMaterial({
      uniforms: { uColor: { value: new THREE.Color(spec.atmosphere) } },
      vertexShader: `
        varying vec3 vNormal; varying vec3 vView;
        void main(){
          vNormal = normalize(normalMatrix * normal);
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          vView = normalize(-mv.xyz);
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: `
        varying vec3 vNormal; varying vec3 vView; uniform vec3 uColor;
        void main(){
          float fres = pow(1.0 - max(dot(normalize(vNormal), normalize(vView)), 0.0), 3.4);
          gl_FragColor = vec4(uColor, fres * 0.22);
        }`,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    scene.add(new THREE.Mesh(new THREE.SphereGeometry(1.035, 64, 64), innerAtmoMat));

    /* ---------------- sun glow ---------------- */
    const sunSprite = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: glowTexture,
        color: spec.key,
        transparent: true,
        opacity: 0.3,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    );
    sunSprite.position.copy(LIGHT_DIR).multiplyScalar(14);
    sunSprite.scale.setScalar(5);
    scene.add(sunSprite);

    /* ---------------- projector platform + volumetric beam ---------------- */
    const platform = new THREE.Group();
    platform.position.y = -1.36;
    scene.add(platform);

    // glossy light-well disc
    const wellTexture = platformGlowTexture();
    const well = new THREE.Mesh(
      new THREE.CircleGeometry(1.18, 72),
      new THREE.MeshBasicMaterial({ map: wellTexture, color: 0xd4af37, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false }),
    );
    well.rotation.x = -Math.PI / 2;
    platform.add(well);

    const pRings: Array<{ mesh: THREE.Mesh; mat: THREE.MeshBasicMaterial; speed: number }> = [];
    const P_RINGS = [
      { scale: 0.92, color: 0xd4af37, opacity: 0.3, speed: 0.24 },
      { scale: 0.66, color: 0x22d3ee, opacity: 0.4, speed: -0.36 },
      { scale: 1.3, color: 0x8b5cf6, opacity: 0.16, speed: 0.12 },
    ];
    P_RINGS.forEach((r) => {
      const mat = new THREE.MeshBasicMaterial({
        color: r.color, transparent: true, opacity: r.opacity, blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide, depthWrite: false,
      });
      const mesh = new THREE.Mesh(unitRing(), mat);
      mesh.rotation.x = Math.PI / 2;
      mesh.scale.setScalar(r.scale);
      platform.add(mesh);
      pRings.push({ mesh, mat, speed: r.speed });
    });

    const pGlow = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: glowTexture, color: 0xd4af37, transparent: true, opacity: 0.16,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }),
    );
    pGlow.scale.setScalar(1.9);
    platform.add(pGlow);

    // volumetric beam (fresnel-faded, noise-flickered)
    const beamMat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor: { value: new THREE.Color(0x6fd8ec) },
      },
      vertexShader: `
        varying vec3 vNormal; varying vec3 vView; varying vec2 vUvB;
        void main(){
          vUvB = uv;
          vNormal = normalize(normalMatrix * normal);
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          vView = normalize(-mv.xyz);
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: `
        varying vec3 vNormal; varying vec3 vView; varying vec2 vUvB;
        uniform float uTime; uniform vec3 uColor;
        float hash(vec2 p){ return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }
        void main(){
          float edge = pow(abs(dot(normalize(vNormal), normalize(vView))), 1.4);
          float fall = smoothstep(0.0, 0.42, vUvB.y) * smoothstep(1.0, 0.62, vUvB.y);
          float flick = 0.82 + 0.18 * sin(uTime * 2.1 + vUvB.y * 9.0)
                      + 0.06 * (hash(vec2(floor(uTime * 14.0), vUvB.y * 4.0)) - 0.5);
          float a = edge * fall * flick * 0.16;
          vec3 col = mix(uColor, vec3(1.0, 0.86, 0.5), (1.0 - vUvB.y) * 0.45);
          gl_FragColor = vec4(col, a);
        }`,
      transparent: true,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 1.06, 1.42, 64, 1, true), beamMat);
    beam.position.y = -0.66;
    scene.add(beam);

    /* ---------------- rising embers near the platform ---------------- */
    const EMBERS = 70;
    const emberGeo = new THREE.BufferGeometry();
    const emberSeed: number[] = [];
    {
      const pos: number[] = [];
      for (let i = 0; i < EMBERS; i += 1) {
        pos.push(0, 0, 0);
        emberSeed.push(hash01(i * 71 + 3) * Math.PI * 2, 0.05 + hash01(i * 97 + 11) * 0.12, hash01(i * 131 + 7));
      }
      emberGeo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    }
    const embers = new THREE.Points(
      emberGeo,
      new THREE.PointsMaterial({
        size: 0.035, map: glowTexture, color: 0xf3d27a, transparent: true, opacity: 0.85,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }),
    );
    scene.add(embers);

    /* ---------------- gyro rings ---------------- */
    const circlePoints = (radius: number, segments = 160, y = 0) =>
      Array.from({ length: segments }, (_, i) => {
        const a = (i / segments) * Math.PI * 2;
        return new THREE.Vector3(Math.cos(a) * radius, y, Math.sin(a) * radius);
      });
    const gyro1 = new THREE.LineLoop(
      new THREE.BufferGeometry().setFromPoints(circlePoints(2.06)),
      new THREE.LineBasicMaterial({ color: 0xd4af37, transparent: true, opacity: 0.26 }),
    );
    gyro1.rotation.x = 1.2;
    scene.add(gyro1);
    const gyro2 = new THREE.LineLoop(
      new THREE.BufferGeometry().setFromPoints(circlePoints(2.24)),
      new THREE.LineBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.2 }),
    );
    gyro2.rotation.set(0.42, 0, 0.95);
    scene.add(gyro2);

    /* ---------------- orbit gates + comet trails ---------------- */
    interface Ring {
      group: THREE.Group;
      node: THREE.Mesh;
      glow: THREE.Sprite;
      trailGeo: THREE.BufferGeometry;
      speed: number;
      angle: number;
      radius: number;
      mat: THREE.LineBasicMaterial;
    }
    const ringSpecs = [
      { r: 1.38, tilt: [0.5, 0, 0], color: 0xd4af37, speed: 0.4, nodeColor: 0xf3d27a },
      { r: 1.56, tilt: [-0.32, 0, 0.42], color: 0x22d3ee, speed: 0.27, nodeColor: 0x7fd8e8 },
      { r: 1.78, tilt: [0.14, 0, -0.62], color: 0x8b5cf6, speed: 0.19, nodeColor: 0xc4b5fd },
    ] as const;
    const TRAIL_LEN = 26;
    const dotTexture = radialTexture(0.55);
    const rings: Ring[] = ringSpecs.map((rs, ringIdx) => {
      const group = new THREE.Group();
      group.rotation.set(rs.tilt[0], rs.tilt[1], rs.tilt[2]);
      const mat = new THREE.LineBasicMaterial({ color: rs.color, transparent: true, opacity: spec.ringOpacity });
      group.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(circlePoints(rs.r, 180)), mat));

      const node = new THREE.Mesh(
        new THREE.SphereGeometry(0.02, 12, 12),
        new THREE.MeshBasicMaterial({ color: rs.nodeColor }),
      );
      group.add(node);

      const glow = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: glowTexture, color: rs.nodeColor, transparent: true, opacity: 0.7,
          blending: THREE.AdditiveBlending, depthWrite: false,
        }),
      );
      glow.scale.setScalar(0.09);
      group.add(glow);

      const trailGeo = new THREE.BufferGeometry();
      const trailPos = new Float32Array(TRAIL_LEN * 3);
      const trailCol = new Float32Array(TRAIL_LEN * 3);
      const nc = new THREE.Color(rs.nodeColor);
      for (let i = 0; i < TRAIL_LEN; i += 1) {
        const fade = Math.pow(1 - i / TRAIL_LEN, 2.4) * (ringIdx === 0 ? 1 : 0.8);
        trailCol[i * 3] = nc.r * fade;
        trailCol[i * 3 + 1] = nc.g * fade;
        trailCol[i * 3 + 2] = nc.b * fade;
      }
      trailGeo.setAttribute("position", new THREE.BufferAttribute(trailPos, 3).setUsage(THREE.DynamicDrawUsage));
      trailGeo.setAttribute("color", new THREE.BufferAttribute(trailCol, 3));
      group.add(new THREE.Points(trailGeo, new THREE.PointsMaterial({
        size: 0.028, map: dotTexture, vertexColors: true, transparent: true,
        blending: THREE.AdditiveBlending, depthWrite: false,
      })));

      scene.add(group);
      return { group, node, glow, trailGeo, speed: rs.speed, angle: (ringIdx + 1) * 2.1, radius: rs.r, mat };
    });

    /* ---------------- connection arcs + packets ---------------- */
    const ARC_ANCHORS = [
      latLonToVec(51.5, -0.12), latLonToVec(40.7, -74.0), latLonToVec(35.7, 51.4),
      latLonToVec(1.35, 103.8), latLonToVec(-33.9, 151.2), latLonToVec(55.8, 37.6),
      latLonToVec(-23.5, -46.6), latLonToVec(19.4, -99.1), latLonToVec(28.6, 77.2),
      latLonToVec(-1.3, 36.8), latLonToVec(37.6, 126.9), latLonToVec(52.5, 13.4),
    ];
    interface Arc {
      curve: THREE.QuadraticBezierCurve3;
      mat: THREE.LineBasicMaterial;
    }
    const arcs: Arc[] = [];
    const packets: Array<{ curve: THREE.QuadraticBezierCurve3; offset: number; speed: number }> = [];
    const packetPos: number[] = [];
    const packetCol: number[] = [];
    const packetCyan = new THREE.Color(0x9be8f5);
    const packetGold = new THREE.Color(0xf3d27a);
    let packetIndex = 0;
    for (let i = 0; i < ARC_ANCHORS.length / 2; i += 1) {
      const a = ARC_ANCHORS[i * 2];
      const b = ARC_ANCHORS[(i * 2 + 3) % ARC_ANCHORS.length];
      const start = a.clone().multiplyScalar(1.005);
      const end = b.clone().multiplyScalar(1.005);
      const mid = start.clone().add(end).multiplyScalar(0.5).normalize().multiplyScalar(1 + start.distanceTo(end) * 0.45);
      const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
      const mat = new THREE.LineBasicMaterial({ color: 0x35c8de, transparent: true, opacity: 0.2 });
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(56)), mat));
      arcs.push({ curve, mat });

      for (let p = 0; p < 2; p += 1) {
        const c = packetIndex % 2 === 0 ? packetCyan : packetGold;
        packetPos.push(0, 0, 0);
        packetCol.push(c.r, c.g, c.b);
        packets.push({ curve, offset: hash01(i * 31 + p * 7) * 2, speed: 0.14 + hash01(i * 13 + p) * 0.2 });
        packetIndex += 1;
      }
    }
    const packetGeo = new THREE.BufferGeometry();
    packetGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(packetPos), 3).setUsage(THREE.DynamicDrawUsage));
    packetGeo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(packetCol), 3));
    scene.add(new THREE.Points(packetGeo, new THREE.PointsMaterial({
      size: 0.05, map: dotTexture, vertexColors: true, transparent: true, opacity: 0.95,
      blending: THREE.AdditiveBlending, depthWrite: false,
    })));

    /* ---------------- ambient dust ---------------- */
    const dustGeo = new THREE.BufferGeometry();
    {
      const dustPos: number[] = [];
      for (let i = 0; i < 170; i += 1) {
        const y = 1 - (i / 169) * 2;
        const r = Math.sqrt(Math.max(0, 1 - y * y));
        const theta = i * 2.399963 + hash01(i * 29) * 0.5;
        const rad = 2.3 + hash01(i * 37 + 3) * 1.1;
        dustPos.push(Math.cos(theta) * r * rad, y * rad * 0.75, Math.sin(theta) * r * rad);
      }
      dustGeo.setAttribute("position", new THREE.Float32BufferAttribute(dustPos, 3));
    }
    const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({
      size: 0.012, map: dotTexture, color: 0x9db4d8, transparent: true, opacity: 0.32,
      blending: THREE.AdditiveBlending, depthWrite: false,
    }));
    scene.add(dust);

    /* ---------------- DOM asset chips at real lat/lons ---------------- */
    const chipLayer = document.createElement("div");
    chipLayer.setAttribute("aria-hidden", "true");
    chipLayer.style.cssText = "position:absolute;inset:0;overflow:hidden;pointer-events:none;";
    container.appendChild(chipLayer);

    const CHIP_DEFS = [
      { label: "XAU", color: "#D4AF37", lat: 51.5, lon: -0.12 },
      { label: "BTC", color: "#22D3EE", lat: 37.77, lon: -122.42 },
      { label: "ETH", color: "#8B5CF6", lat: 52.52, lon: 13.4 },
      { label: "SOL", color: "#22C55E", lat: 1.35, lon: 103.82 },
    ];
    const chips = CHIP_DEFS.map((def) => {
      const el = document.createElement("div");
      el.className = "scene-chip";
      el.innerHTML = `<span style="background:${def.color}"></span>${def.label}`;
      el.style.opacity = "0";
      chipLayer.appendChild(el);
      return { dir: latLonToVec(def.lat, def.lon).multiplyScalar(1.012), el };
    });

    /* ---------------- post-processing: bloom + grade ---------------- */
    let composer: EffectComposer | null = null;
    let bloomPass: UnrealBloomPass | null = null;
    let gradePass: ShaderPass | null = null;
    try {
      composer = new EffectComposer(renderer);
      composer.setPixelRatio(dpr);
      composer.addPass(new RenderPass(scene, camera));
      bloomPass = new UnrealBloomPass(new THREE.Vector2(1, 1), spec.bloom, 0.5, 0.58);
      composer.addPass(bloomPass);
      gradePass = new ShaderPass(GRADE_SHADER);
      composer.addPass(gradePass);
    } catch {
      composer = null; // graceful: direct rendering without post FX
    }

    /* ---------------- interactions ---------------- */
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    let velY = 0;
    let velX = 0;
    const targetRot = { x: 0, y: 0 };
    const onPointerDown = (e: PointerEvent) => {
      dragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      container.style.cursor = "grabbing";
    };
    const onPointerUp = () => {
      dragging = false;
      container.style.cursor = "grab";
    };
    const onPointerMove = (e: PointerEvent) => {
      const rect = container.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width - 0.5;
      const ny = (e.clientY - rect.top) / rect.height - 0.5;
      if (dragging) {
        velY = (e.clientX - lastX) * 0.0035;
        velX = (e.clientY - lastY) * 0.0022;
        lastX = e.clientX;
        lastY = e.clientY;
      } else {
        targetRot.x = ny * 0.16;
        targetRot.y = nx * 0.22;
      }
    };
    container.style.cursor = "grab";
    container.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUp);
    container.addEventListener("pointermove", onPointerMove);

    /* ---------------- sizing / lifecycle ---------------- */
    const resize = () => {
      const w = container.clientWidth || 1;
      const h = container.clientHeight || 1;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      composer?.setSize(w, h);
      bloomPass?.setSize(w, h);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    const applyPreset = (p: AmbiencePreset, s: SeasonPreset) => {
      const amb = AMBIENCE[p].three;
      const seas = SEASON_TINTS[s];
      rimLight.color.setHex(amb.rim);
      atmosphereMat.uniforms.uColor.value.setHex(amb.atmosphere);
      innerAtmoMat.uniforms.uColor.value.setHex(amb.atmosphere);
      earthMat.uniforms.uAtmo.value.setHex(amb.atmosphere);
      earthMat.uniforms.uSun.value.setHex(amb.key);
      earthMat.uniforms.uTint.value.setHex(seas.tint);
      earthMat.uniforms.uTintStrength.value = seas.strength * 0.5;
      skyMat.uniforms.uTop.value.setHex(amb.skyTop);
      skyMat.uniforms.uBottom.value.setHex(amb.skyBottom);
      sunSprite.material.color.setHex(amb.key);
      rings.forEach((ring, idx) => {
        ring.mat.color.setHex(ringSpecs[idx].color);
        ring.mat.opacity = amb.ringOpacity;
      });
      if (bloomPass) bloomPass.strength = amb.bloom;
      renderer.setClearColor(amb.skyTop, 1);
    };
    applyPreset(preset, season);

    let raf = 0;
    let running = true;
    let lastFrame = performance.now();
    let elapsed = 0;
    const onVisibility = () => {
      running = document.visibilityState === "visible";
      if (running) lastFrame = performance.now();
    };
    document.addEventListener("visibilitychange", onVisibility);

    const tmpVec = new THREE.Vector3();
    const tmpWorld = new THREE.Vector3();
    const tmpCam = new THREE.Vector3();
    const animate = () => {
      raf = requestAnimationFrame(animate);
      if (!running || disposed) return;
      const now = performance.now();
      const dt = Math.min((now - lastFrame) / 1000, 0.05);
      lastFrame = now;
      elapsed += dt;
      const t = elapsed;

      // earth spin + drag inertia + parallax tilt
      globe.rotation.y += dt * 0.045 + velY;
      velY *= 0.93;
      globe.rotation.x += (targetRot.x - globe.rotation.x) * 0.04 + velX;
      velX *= 0.9;
      clouds.rotation.y = globe.rotation.y * 1.12 + t * 0.004; // clouds drift slightly faster
      clouds.rotation.x = globe.rotation.x;

      // cinematic camera dolly
      camera.position.z = 3.7 + Math.sin(t * 0.07) * 0.16;
      camera.position.y = 0.34 + Math.sin(t * 0.11) * 0.05;
      camera.lookAt(0, -0.05, 0);

      stars.rotation.y += dt * 0.004;
      dust.rotation.y -= dt * 0.012;
      sunSprite.material.opacity = 0.24 + Math.sin(t * 0.8) * 0.05;

      // scan band travels the globe latitude range
      const scanY = Math.sin(t * 0.3) * 0.92;
      scan.position.y = scanY;
      const sr = Math.sqrt(Math.max(0.02, 1 - scanY * scanY));
      scan.scale.setScalar(sr * 1.008);
      scanMat.opacity = 0.1 + (Math.sin(t * 1.7) * 0.5 + 0.5) * 0.12;

      // platform + beam life
      pRings.forEach((r) => {
        r.mesh.rotation.z += dt * r.speed;
      });
      pGlow.material.opacity = 0.12 + (Math.sin(t * 1.4) * 0.5 + 0.5) * 0.05;
      beamMat.uniforms.uTime.value = t;

      // embers rise from the light-well
      const emberAttr = emberGeo.getAttribute("position") as THREE.BufferAttribute;
      for (let i = 0; i < EMBERS; i += 1) {
        const phase = emberSeed[i * 3];
        const speed = emberSeed[i * 3 + 1];
        const seed = emberSeed[i * 3 + 2];
        const life = (t * speed + seed) % 1;
        const x = Math.cos(phase + life * 2.4) * (0.28 + life * 0.85);
        const z = Math.sin(phase + life * 2.4) * (0.28 + life * 0.85);
        emberAttr.setXYZ(i, x, -1.34 + life * 1.15, z);
      }
      emberAttr.needsUpdate = true;

      // gyro + orbits
      gyro1.rotation.y += dt * 0.1;
      gyro2.rotation.y -= dt * 0.07;
      rings.forEach((ring, idx) => {
        ring.group.rotation.y += dt * (idx % 2 === 0 ? 0.05 : -0.04);
        ring.angle += dt * ring.speed;
        const cos = Math.cos(ring.angle);
        const sin = Math.sin(ring.angle);
        ring.node.position.set(cos * ring.radius, 0, sin * ring.radius);
        ring.glow.position.copy(ring.node.position);
        const posAttr = ring.trailGeo.getAttribute("position") as THREE.BufferAttribute;
        for (let i = 0; i < TRAIL_LEN; i += 1) {
          const a = ring.angle - i * 0.05;
          posAttr.setXYZ(i, Math.cos(a) * ring.radius, 0, Math.sin(a) * ring.radius);
        }
        posAttr.needsUpdate = true;
      });

      // packets along arcs
      const packetAttr = packetGeo.getAttribute("position") as THREE.BufferAttribute;
      packets.forEach((packet, i) => {
        const u = (t * packet.speed + packet.offset) % 1;
        packet.curve.getPoint(u, tmpVec);
        packetAttr.setXYZ(i, tmpVec.x, tmpVec.y, tmpVec.z);
      });
      packetAttr.needsUpdate = true;
      arcs.forEach((arc, i) => {
        arc.mat.opacity = 0.12 + (Math.sin(t * 0.6 + i * 0.9) * 0.5 + 0.5) * 0.14;
      });

      // chips follow the rotating globe (screen space)
      const rect = container.getBoundingClientRect();
      for (const chip of chips) {
        tmpWorld.copy(chip.dir).applyEuler(globe.rotation).multiplyScalar(1.0);
        tmpCam.copy(camera.position).sub(tmpWorld).normalize();
        const facing = tmpWorld.clone().normalize().dot(tmpCam);
        tmpVec.copy(tmpWorld).project(camera);
        const x = Math.min(Math.max((tmpVec.x * 0.5 + 0.5) * rect.width, 36), rect.width - 36);
        const y = Math.min(Math.max((-tmpVec.y * 0.5 + 0.5) * rect.height, 44), rect.height - 30);
        chip.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -130%)`;
        chip.el.style.opacity = facing > 0.28 && tmpVec.z < 1 ? "1" : "0";
      }

      if (gradePass) gradePass.uniforms.uTime.value = t % 10;

      if (composer) composer.render();
      else renderer.render(scene, camera);
    };
    animate();

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      ro.disconnect();
      container.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      container.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("visibilitychange", onVisibility);
      chipLayer.remove();
      composer?.dispose();
      [dayTex, nightTex, waterTex, cloudTex, dotTexture, glowTexture, wellTexture].forEach((t) => t.dispose());
      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh || obj instanceof THREE.Points || obj instanceof THREE.Line) {
          obj.geometry.dispose();
          const mat = obj.material as THREE.Material | THREE.Material[];
          if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
          else mat.dispose();
        }
        if (obj instanceof THREE.Sprite) obj.material.dispose();
      });
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preset, season]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full cursor-grab active:cursor-grabbing"
      role="img"
      aria-label="Simulated Earth with intelligence orbits — decorative visualization"
    />
  );
}
