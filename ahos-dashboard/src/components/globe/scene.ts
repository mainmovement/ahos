/**
 * AHOS 3D Earth — framework-free three.js scene (client only).
 *
 *  - three-globe for layers (Iran polygon/path, rings, points, arcs, atmosphere)
 *  - custom day/night ShaderMaterial driven by the real sun position
 *  - procedural, offline textures (textures.ts)
 *  - OrbitControls (drag/zoom), camera fly-to, auto-rotate with pause
 *  - pauses when off-screen / tab hidden, FPS cap per quality profile
 *  - full disposal of GPU resources on dispose()
 */
import * as THREE from "three";
import ThreeGlobe from "three-globe";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { geoContains } from "d3-geo";
import type { FinancialCenter } from "@/lib/api/types";
import type { QualityBudget } from "@/lib/settings/types";
import { sunPosition } from "@/lib/astro/solar";
import { loadIran, outerRings, type IranFeature } from "./geo-data";
import { createDayNightMaterial } from "./material";
import { generateGlobeCanvases } from "./textures";
import { TEHRAN } from "./scene-constants";

export { TEHRAN };

export interface GlobeLayers {
  labels: boolean;
  atmosphere: boolean;
  markers: boolean;
  links: boolean;
}

export interface GlobeLabel {
  id: string;
  lat: number;
  lng: number;
  kind: "iran" | "center" | "sun";
}

export interface SceneOptions {
  budget: QualityBudget;
  /** Start position of the camera (deep links start focused, no flight needed). */
  initialView: "global" | "iran";
  reducedMotion: boolean;
  autoRotate: boolean;
  layers: GlobeLayers;
  centers: FinancialCenter[];
  links: { from: string; to: string }[];
  ariaLabel: string;
  getLabels: () => GlobeLabel[];
  getLabelEls: () => (HTMLElement | null)[];
  onIranClick: () => void;
  onIranHover: (hover: boolean) => void;
  onRenderingChange: (rendering: boolean) => void;
  onTexturesReady: () => void;
  onError: (err: unknown) => void;
}

export interface GlobeScene {
  flyTo(target: "iran" | "global"): void;
  zoom(factor: number): void;
  setLayers(layers: GlobeLayers): void;
  setAutoRotate(on: boolean): void;
  setReducedMotion(reduced: boolean): void;
  dispose(): void;
}

export const IRAN_VIEW = { lat: 32.4, lng: 53.7, dist: 178 };
export const GLOBAL_VIEW = { lat: 24, lng: 44, dist: 318 };

const GOLD = "#e6bf5f";
const GOLD_LIGHT = "#f7e3a1";
const DATA = "#45d0e6";

interface Flight {
  fromDir: THREE.Vector3;
  toDir: THREE.Vector3;
  fromDist: number;
  toDist: number;
  start: number;
  dur: number;
}

const easeInOutCubic = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

function v3(c: { x: number; y: number; z: number }) {
  return new THREE.Vector3(c.x, c.y, c.z);
}

function makeStarSprite(): THREE.CanvasTexture {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const ctx = c.getContext("2d")!;
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.25, "rgba(255,244,214,0.75)");
  g.addColorStop(1, "rgba(255,244,214,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function createGlobeScene(host: HTMLElement, opts: SceneOptions): GlobeScene {
  const { budget } = opts;
  let reducedMotion = opts.reducedMotion;
  let userAutoRotate = opts.autoRotate;
  let layers = { ...opts.layers };
  let disposed = false;

  /* -------------------------------------------------------- renderer */
  const renderer = new THREE.WebGLRenderer({ antialias: budget.antialias, alpha: true, powerPreference: "high-performance" });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, budget.pixelRatioCap) * budget.renderScale);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const canvas = renderer.domElement;
  canvas.style.cssText = "position:absolute;inset:0;width:100%;height:100%;display:block;outline:none;touch-action:none;";
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", opts.ariaLabel);
  host.prepend(canvas);
  const onContextLost = (e: Event) => {
    e.preventDefault();
    opts.onError(new Error("WebGL context lost"));
  };
  canvas.addEventListener("webglcontextlost", onContextLost);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 1, 6000);

  /* ----------------------------------------------------------- globe */
  const material = createDayNightMaterial();
  // Blending happens in linear space: a small opacity already reads as a clear gold tint after sRGB encoding.
  const CAP_OPACITY = 0.035;
  const CAP_OPACITY_HOVER = 0.09;
  const capMat = new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, opacity: CAP_OPACITY, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });

  const globe = new ThreeGlobe({ waitForGlobeReady: false, animateIn: false })
    .globeMaterial(material)
    .showGraticules(false)
    .showAtmosphere(layers.atmosphere)
    .atmosphereColor("#c9a552")
    .atmosphereAltitude(0.12);
  scene.add(globe);

  scene.add(new THREE.AmbientLight(0xffffff, 2.4));
  const dirLight = new THREE.DirectionalLight(0xfff1d0, 0.8);
  scene.add(dirLight);

  const centerById = new Map(opts.centers.map((c) => [c.id, c]));

  // Rings (Tehran pulse) — static marker under reduced motion
  const applyRings = () => {
    globe
      .ringsData(layers.markers && !reducedMotion ? [{ ...TEHRAN, tier: 0 }, ...opts.centers.filter((c) => c.tier === 1 && c.id !== "tehran").map((c) => ({ lat: c.lat, lng: c.lng, tier: 1 }))] : [])
      .ringColor((d: object) => {
        const tier = (d as { tier: number }).tier;
        return (t: number) => (tier === 0 ? `rgba(247, 227, 161, ${(1 - t) * 0.95})` : `rgba(69, 208, 230, ${(1 - t) * 0.5})`);
      })
      .ringMaxRadius((d: object) => ((d as { tier: number }).tier === 0 ? 3.6 : 1.6))
      .ringPropagationSpeed((d: object) => ((d as { tier: number }).tier === 0 ? 1.5 : 0.9))
      .ringRepeatPeriod((d: object) => ((d as { tier: number }).tier === 0 ? 1150 : 2400))
      .ringAltitude(0.009);
  };

  const applyPoints = () => {
    const pts = layers.markers ? opts.centers.map((c) => ({ lat: c.lat, lng: c.lng, tier: c.tier, iran: c.id === "tehran" })) : [];
    globe
      .pointsData(pts)
      .pointLat((d: object) => (d as { lat: number }).lat)
      .pointLng((d: object) => (d as { lng: number }).lng)
      .pointColor((d: object) => ((d as { iran: boolean }).iran ? GOLD_LIGHT : DATA))
      .pointAltitude((d: object) => ((d as { iran: boolean }).iran ? 0.022 : 0.012))
      .pointRadius((d: object) => ((d as { iran: boolean }).iran ? 0.42 : (d as { tier: number }).tier === 1 ? 0.32 : 0.24))
      .pointResolution(12)
      .pointsMerge(true)
      .pointsTransitionDuration(0);
  };

  const applyArcs = () => {
    const arcs = layers.links
      ? opts.links
          .map((l) => {
            const a = centerById.get(l.from);
            const b = centerById.get(l.to);
            return a && b ? { startLat: a.lat, startLng: a.lng, endLat: b.lat, endLng: b.lng, iran: a.id === "tehran", seed: (a.lat * 13 + b.lng * 7) % 1 } : null;
          })
          .filter((x): x is NonNullable<typeof x> => x !== null)
      : [];
    globe
      .arcsData(arcs)
      .arcStartLat((d: object) => (d as { startLat: number }).startLat)
      .arcStartLng((d: object) => (d as { startLng: number }).startLng)
      .arcEndLat((d: object) => (d as { endLat: number }).endLat)
      .arcEndLng((d: object) => (d as { endLng: number }).endLng)
      .arcColor((d: object) => ((d as { iran: boolean }).iran ? ["rgba(247,227,161,0.08)", "rgba(247,227,161,0.85)", "rgba(69,208,230,0.6)"] : ["rgba(69,208,230,0.04)", "rgba(69,208,230,0.75)", "rgba(69,208,230,0.04)"]))
      .arcStroke(0.24)
      .arcAltitudeAutoScale(0.38)
      .arcDashLength(reducedMotion ? 1 : 0.38)
      .arcDashGap(reducedMotion ? 0 : 1.1)
      .arcDashInitialGap((d: object) => Math.abs((d as { seed: number }).seed) * 2)
      .arcDashAnimateTime(reducedMotion ? 0 : 4200)
      .arcsTransitionDuration(0);
  };

  let iranFeature: IranFeature | null = null;
  const applyIran = () => {
    if (!iranFeature) return;
    const rings = outerRings(iranFeature);
    globe
      .polygonsData([iranFeature])
      .polygonCapMaterial(capMat)
      // No side walls: three-globe extrudes sides from the globe centre, which would
      // show through as an opaque slab with a non-clipping custom material.
      .polygonSideColor(() => false as unknown as string)
      .polygonSideMaterial(() => null as unknown as THREE.Material)
      .polygonStrokeColor(() => GOLD_LIGHT)
      .polygonAltitude(0.0065)
      .polygonCapCurvatureResolution(2)
      .polygonsTransitionDuration(0);
    const paths = [
      ...rings.map((pts, i) => ({ pts, kind: "border" as const, i })),
      ...(reducedMotion ? [] : rings.slice(0, 1).map((pts, i) => ({ pts, kind: "comet" as const, i }))),
    ];
    globe
      .pathsData(paths)
      .pathPoints((d: object) => (d as { pts: [number, number][] }).pts)
      .pathPointLat((p: [number, number]) => p[1])
      .pathPointLng((p: [number, number]) => p[0])
      .pathPointAlt(() => 0.0075)
      .pathColor((d: object) => ((d as { kind: string }).kind === "comet" ? ["rgba(255,250,232,0.0)", "rgba(255,246,216,1)"] : ["rgba(247,227,161,0.95)", "rgba(230,191,95,0.95)"]))
      .pathStroke((d: object) => ((d as { kind: string }).kind === "comet" ? 1.4 : 0.9))
      .pathDashLength((d: object) => ((d as { kind: string }).kind === "comet" ? 0.07 : 1))
      .pathDashGap((d: object) => ((d as { kind: string }).kind === "comet" ? 0.93 : 0))
      .pathDashAnimateTime((d: object) => ((d as { kind: string }).kind === "comet" ? 7000 : 0))
      .pathTransitionDuration(0);
  };

  applyRings();
  applyPoints();
  applyArcs();
  void loadIran()
    .then((f) => {
      if (disposed) return;
      iranFeature = f;
      applyIran();
      needsRender = true;
    })
    .catch(opts.onError);

  /* ---------------------------------------------------------- stars */
  const starTex = makeStarSprite();
  const starGeo = new THREE.BufferGeometry();
  {
    const n = budget.stars;
    const pos = new Float32Array(n * 3);
    const col = new Float32Array(n * 3);
    let seed = 99991;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < n; i++) {
      const u = rnd() * 2 - 1;
      const th = rnd() * Math.PI * 2;
      const r = 1800 + rnd() * 1600;
      const s = Math.sqrt(1 - u * u);
      pos[i * 3] = r * s * Math.cos(th);
      pos[i * 3 + 1] = r * u;
      pos[i * 3 + 2] = r * s * Math.sin(th);
      const b = 0.35 + rnd() * 0.65;
      const warm = rnd() > 0.7;
      col[i * 3] = b;
      col[i * 3 + 1] = b * (warm ? 0.9 : 0.97);
      col[i * 3 + 2] = b * (warm ? 0.72 : 1);
    }
    starGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    starGeo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  }
  const starMat = new THREE.PointsMaterial({ size: 2.2, sizeAttenuation: false, map: starTex, vertexColors: true, transparent: true, depthWrite: false, opacity: 0.9 });
  const stars = new THREE.Points(starGeo, starMat);
  scene.add(stars);

  /* ----------------------------------------- decorative orbit + sat */
  const orbitGroup = new THREE.Group();
  const orbitMats: THREE.Material[] = [];
  let satellite: THREE.Mesh | null = null;
  if (budget.stars >= 1000) {
    const mkOrbit = (radius: number, tiltX: number, tiltZ: number, opacity: number) => {
      const pts = new THREE.EllipseCurve(0, 0, radius, radius, 0, Math.PI * 2).getPoints(256).map((p) => new THREE.Vector3(p.x, 0, p.y));
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineDashedMaterial({ color: GOLD, dashSize: 1.2, gapSize: 3.6, transparent: true, opacity, depthWrite: false });
      orbitMats.push(mat);
      const line = new THREE.LineLoop(geo, mat);
      line.computeLineDistances();
      line.rotation.set(tiltX, 0, tiltZ);
      orbitGroup.add(line);
      return line;
    };
    const o1 = mkOrbit(152, 0.38, -0.22, 0.16);
    const satMat = new THREE.MeshBasicMaterial({ color: "#fff3cf" });
    orbitMats.push(satMat);
    satellite = new THREE.Mesh(new THREE.SphereGeometry(0.75, 12, 12), satMat);
    o1.add(satellite);
    scene.add(orbitGroup);
  }

  /* --------------------------------------------------------- controls */
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.075;
  controls.rotateSpeed = 0.42;
  controls.zoomSpeed = 0.7;
  controls.enablePan = false;
  controls.minDistance = 132;
  controls.maxDistance = 560;
  controls.autoRotateSpeed = 0.42;
  const startView = opts.initialView === "iran" ? IRAN_VIEW : GLOBAL_VIEW;
  const startPos = v3(globe.getCoords(startView.lat, startView.lng, 0)).normalize().multiplyScalar(startView.dist);
  camera.position.copy(startPos);
  camera.lookAt(0, 0, 0);

  let interacting = false;
  let focusIran = opts.initialView === "iran";
  let resumeTimer: ReturnType<typeof setTimeout> | undefined;
  let flight: Flight | null = null;
  let needsRender = true;

  const syncAutoRotate = () => {
    controls.autoRotate = userAutoRotate && !reducedMotion && !focusIran && !interacting && !flight;
  };
  syncAutoRotate();
  controls.addEventListener("start", () => {
    interacting = true;
    clearTimeout(resumeTimer);
    syncAutoRotate();
  });
  controls.addEventListener("end", () => {
    clearTimeout(resumeTimer);
    resumeTimer = setTimeout(() => {
      interacting = false;
      syncAutoRotate();
    }, 3500);
  });
  controls.addEventListener("change", () => {
    needsRender = true;
  });

  /* ------------------------------------------------------ composer */
  let composer: EffectComposer | null = null;
  let bloom: UnrealBloomPass | null = null;
  if (budget.bloom) {
    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    bloom = new UnrealBloomPass(new THREE.Vector2(256, 256), 0.42, 0.45, 0.9);
    composer.addPass(bloom);
    composer.addPass(new OutputPass());
  }

  /* ----------------------------------------------------------- sun */
  const updateSun = () => {
    const s = sunPosition(new Date());
    const dir = v3(globe.getCoords(s.subsolarLat, s.subsolarLng, 0)).normalize();
    material.uniforms.sunDir.value.copy(dir);
    dirLight.position.copy(dir.multiplyScalar(500));
    needsRender = true;
  };
  updateSun();
  const sunTimer = setInterval(updateSun, 60_000);

  /* ------------------------------------------------------ textures */
  const gpuTextures: THREE.Texture[] = [];
  let readyStart = 0;
  void generateGlobeCanvases(budget.textureSize, budget.geoDetail, budget.cityLights)
    .then(({ day, night, mask }) => {
      if (disposed) return;
      const aniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      const mk = (c: HTMLCanvasElement, srgb: boolean) => {
        const t = new THREE.CanvasTexture(c);
        t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
        t.anisotropy = aniso;
        t.generateMipmaps = true;
        t.minFilter = THREE.LinearMipmapLinearFilter;
        gpuTextures.push(t);
        return t;
      };
      material.uniforms.dayMap.value = mk(day, true);
      material.uniforms.nightMap.value = mk(night, true);
      material.uniforms.maskMap.value = mk(mask, false);
      readyStart = performance.now();
      needsRender = true;
      opts.onTexturesReady();
    })
    .catch(opts.onError);

  /* ------------------------------------------------------- picking */
  const pickSphere = new THREE.Mesh(new THREE.SphereGeometry(100, 48, 48), new THREE.MeshBasicMaterial({ visible: false }));
  scene.add(pickSphere);
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let pendingPick = false;
  let hoverIran = false;
  let downAt: { x: number; y: number; t: number } | null = null;

  const isIranAt = (clientX: number, clientY: number): boolean => {
    if (!iranFeature) return false;
    const rect = canvas.getBoundingClientRect();
    pointer.set(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObject(pickSphere, false)[0];
    if (!hit) return false;
    const g = globe.toGeoCoords(hit.point);
    return geoContains(iranFeature, [g.lng, g.lat]);
  };
  let lastPointer = { x: 0, y: 0 };
  const onPointerMove = (e: PointerEvent) => {
    lastPointer = { x: e.clientX, y: e.clientY };
    pendingPick = true;
  };
  const onPointerDown = (e: PointerEvent) => {
    downAt = { x: e.clientX, y: e.clientY, t: performance.now() };
  };
  const onPointerUp = (e: PointerEvent) => {
    if (!downAt) return;
    const moved = Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y);
    const quick = performance.now() - downAt.t < 600;
    downAt = null;
    if (moved < 6 && quick && isIranAt(e.clientX, e.clientY)) opts.onIranClick();
  };
  const onPointerLeave = () => {
    if (hoverIran) {
      hoverIran = false;
      capMat.opacity = CAP_OPACITY;
      canvas.style.cursor = "";
      opts.onIranHover(false);
      needsRender = true;
    }
  };
  canvas.addEventListener("pointermove", onPointerMove);
  canvas.addEventListener("pointerdown", onPointerDown);
  canvas.addEventListener("pointerup", onPointerUp);
  canvas.addEventListener("pointerleave", onPointerLeave);

  /* -------------------------------------------------------- resize */
  let width = 1;
  let height = 1;
  const resize = () => {
    const rect = host.getBoundingClientRect();
    width = Math.max(1, Math.round(rect.width));
    height = Math.max(1, Math.round(rect.height));
    renderer.setSize(width, height, false);
    composer?.setSize(width, height);
    bloom?.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    globe.rendererSize(new THREE.Vector2(width, height));
    needsRender = true;
  };
  resize();
  const ro = new ResizeObserver(resize);
  ro.observe(host);

  /* ----------------------------------------------------- labels */
  const tmp = new THREE.Vector3();
  const camDir = new THREE.Vector3();
  const sizeCache = new WeakMap<HTMLElement, { w: number; h: number; at: number }>();
  let frameNo = 0;
  const placed: { x0: number; y0: number; x1: number; y1: number }[] = [];
  const updateLabels = () => {
    const labels = opts.getLabels();
    const els = opts.getLabelEls();
    frameNo++;
    placed.length = 0;
    for (let i = 0; i < labels.length; i++) {
      const el = els[i];
      const lb = labels[i];
      if (!el || !lb) continue;
      const alt = lb.kind === "sun" ? 0.02 : 0.012;
      const p = v3(globe.getCoords(lb.lat, lb.lng, alt));
      camDir.copy(camera.position).sub(p).normalize();
      const facing = tmp.copy(p).normalize().dot(camDir);
      const fade = Math.max(0, Math.min(1, (facing - 0.08) / 0.22));
      if (fade <= 0.01) {
        el.style.visibility = "hidden";
        continue;
      }
      p.project(camera);
      const x = (p.x * 0.5 + 0.5) * width;
      const y = (-p.y * 0.5 + 0.5) * height;
      // Screen-space collision culling: labels are ordered by priority.
      let sz = sizeCache.get(el);
      if (!sz || frameNo - sz.at > 90) {
        const inner = (el.firstElementChild as HTMLElement | null) ?? el;
        sz = { w: inner.offsetWidth, h: inner.offsetHeight, at: frameNo };
        sizeCache.set(el, sz);
      }
      const rect = { x0: x - sz.w / 2 - 3, x1: x + sz.w / 2 + 3, y0: y - sz.h / 2 - 2, y1: y + sz.h / 2 + 2 };
      if (placed.some((r) => r.x0 < rect.x1 && r.x1 > rect.x0 && r.y0 < rect.y1 && r.y1 > rect.y0)) {
        el.style.visibility = "hidden";
        continue;
      }
      placed.push(rect);
      el.style.visibility = "visible";
      el.style.opacity = String(fade);
      el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
    }
  };

  /* ---------------------------------------------------------- loop */
  let raf = 0;
  let running = false;
  let lastFrame = 0;
  const frameBudget = 1000 / budget.fpsCap;
  let lastTick = performance.now();

  const tick = (now: number) => {
    raf = requestAnimationFrame(tick);
    if (now - lastFrame < frameBudget - 1.5) return;
    const dt = Math.min(0.1, (now - lastTick) / 1000);
    lastTick = now;
    lastFrame = now;

    if (flight) {
      const t = flight.dur <= 0 ? 1 : Math.min(1, (now - flight.start) / flight.dur);
      const e = easeInOutCubic(t);
      const q = new THREE.Quaternion().setFromUnitVectors(flight.fromDir, flight.toDir);
      const qt = new THREE.Quaternion().slerp(q, e);
      const dir = flight.fromDir.clone().applyQuaternion(qt);
      camera.position.copy(dir.multiplyScalar(flight.fromDist + (flight.toDist - flight.fromDist) * e));
      camera.lookAt(0, 0, 0);
      needsRender = true;
      if (t >= 1) {
        flight = null;
        controls.enabled = true;
        syncAutoRotate();
      }
    }

    if (readyStart) {
      const r = Math.min(1, (now - readyStart) / (reducedMotion ? 1 : 900));
      material.uniforms.ready.value = r;
      needsRender = true;
      if (r >= 1) readyStart = 0;
    }

    if (pendingPick) {
      pendingPick = false;
      const h = isIranAt(lastPointer.x, lastPointer.y);
      if (h !== hoverIran) {
        hoverIran = h;
        capMat.opacity = h ? CAP_OPACITY_HOVER : CAP_OPACITY;
        canvas.style.cursor = h ? "pointer" : "";
        opts.onIranHover(h);
        needsRender = true;
      }
    }

    if (!flight) controls.update(dt);
    if (satellite && !reducedMotion) {
      const a = now * 0.00012;
      satellite.position.set(152 * Math.cos(a), 0, 152 * Math.sin(a));
      needsRender = true;
    }

    // Reduced motion: no ambient animation → render on demand only (controls/flight/fade set needsRender).
    const animating = !reducedMotion || controls.autoRotate;
    if (!needsRender && !animating) return;
    needsRender = false;
    if (layers.labels) updateLabels();
    if (composer) composer.render(dt);
    else renderer.render(scene, camera);
  };

  const setRunning = (on: boolean) => {
    if (on === running || disposed) return;
    running = on;
    if (on) {
      lastTick = performance.now();
      globe.resumeAnimation();
      raf = requestAnimationFrame(tick);
    } else {
      cancelAnimationFrame(raf);
      globe.pauseAnimation();
    }
    opts.onRenderingChange(on);
  };

  let inView = true;
  const io = new IntersectionObserver((entries) => {
    inView = entries.some((e) => e.isIntersecting);
    setRunning(inView && !document.hidden);
  });
  io.observe(host);
  const onVisibility = () => setRunning(inView && !document.hidden);
  document.addEventListener("visibilitychange", onVisibility);
  setRunning(!document.hidden);

  /* ------------------------------------------------------------ API */
  const flyToLatLng = (lat: number, lng: number, dist: number, dur: number) => {
    flight = {
      fromDir: camera.position.clone().normalize(),
      toDir: v3(globe.getCoords(lat, lng, 0)).normalize(),
      fromDist: camera.position.length(),
      toDist: dist,
      start: performance.now(),
      dur: reducedMotion ? 0 : dur,
    };
    controls.enabled = false;
    syncAutoRotate();
  };

  return {
    flyTo(target) {
      focusIran = target === "iran";
      if (target === "iran") flyToLatLng(IRAN_VIEW.lat, IRAN_VIEW.lng, IRAN_VIEW.dist, 1700);
      else flyToLatLng(GLOBAL_VIEW.lat, GLOBAL_VIEW.lng, GLOBAL_VIEW.dist, 1500);
    },
    zoom(factor) {
      const dir = camera.position.clone().normalize();
      const g = globe.toGeoCoords(dir.clone().multiplyScalar(100));
      const dist = Math.max(controls.minDistance, Math.min(controls.maxDistance, camera.position.length() * factor));
      flyToLatLng(g.lat, g.lng, dist, 420);
    },
    setLayers(next) {
      const prev = layers;
      layers = { ...next };
      if (prev.atmosphere !== next.atmosphere) globe.showAtmosphere(next.atmosphere);
      if (prev.markers !== next.markers) {
        applyRings();
        applyPoints();
      }
      if (prev.links !== next.links) applyArcs();
      if (!next.labels) opts.getLabelEls().forEach((el) => el && (el.style.visibility = "hidden"));
      needsRender = true;
    },
    setAutoRotate(on) {
      userAutoRotate = on;
      syncAutoRotate();
    },
    setReducedMotion(r) {
      if (r === reducedMotion) return;
      reducedMotion = r;
      applyRings();
      applyArcs();
      applyIran();
      syncAutoRotate();
      needsRender = true;
    },
    dispose() {
      disposed = true;
      running = false;
      cancelAnimationFrame(raf);
      clearInterval(sunTimer);
      clearTimeout(resumeTimer);
      ro.disconnect();
      io.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("pointerleave", onPointerLeave);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      controls.dispose();
      globe.pauseAnimation();
      globe._destructor();
      scene.traverse((obj) => {
        const mesh = obj as THREE.Mesh;
        mesh.geometry?.dispose();
        const mats = Array.isArray(mesh.material) ? mesh.material : mesh.material ? [mesh.material] : [];
        for (const m of mats) {
          for (const v of Object.values(m)) if (v instanceof THREE.Texture) v.dispose();
          m.dispose();
        }
      });
      gpuTextures.forEach((t) => t.dispose());
      [material, capMat, starMat, ...orbitMats].forEach((m) => m.dispose());
      starTex.dispose();
      starGeo.dispose();
      bloom?.dispose();
      composer?.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    },
  };
}
