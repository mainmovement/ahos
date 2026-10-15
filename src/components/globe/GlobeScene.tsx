"use client";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import ThreeGlobe from "three-globe";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Language, Quality } from "../../lib/navigation";
import {
  countryRings,
  referenceCities,
  tehran,
  type CountryCollection,
} from "../../lib/geography";
import { solarPosition } from "../../lib/solar";
import {
  makeEarthMaterial,
  makeEarthTextures,
  type GlobePalette,
} from "./textures";
export type GlobeOptions = {
  paused: boolean;
  atmosphere: boolean;
  markers: boolean;
  labels: boolean;
  view: "global" | "iran";
  zoom: number;
  reset: number;
  language: Language;
  reducedMotion: boolean;
};
type Props = {
  countries: CountryCollection;
  quality: Quality;
  options: GlobeOptions;
  onIran: () => void;
  onFailure: () => void;
  onReady: () => void;
};
export default function GlobeScene({
  countries,
  quality,
  options,
  onIran,
  onFailure,
  onReady,
}: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const latest = useRef(options);
  const controller = useRef<{
    apply: (previous: GlobeOptions, next: GlobeOptions) => void;
  } | null>(null);
  useEffect(() => {
    const previous = latest.current;
    latest.current = options;
    controller.current?.apply(previous, options);
  }, [options]);
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let renderer: THREE.WebGLRenderer | undefined;
    let globe: ThreeGlobe | undefined;
    let controls: OrbitControls | undefined;
    let frame = 0;
    let disposed = false;
    let visible = true;
    let lastFrame = 0;
    let resizeObserver: ResizeObserver | undefined;
    let intersection: IntersectionObserver | undefined;
    const scene = new THREE.Scene();
    const textures: THREE.Texture[] = [];
    const materials = new Set<THREE.Material>();
    const geometries = new Set<THREE.BufferGeometry>();
    const labels: {
      element: HTMLButtonElement;
      position: THREE.Vector3;
      city: typeof tehran;
    }[] = [];
    let camera: THREE.PerspectiveCamera;
    let fly: { from: THREE.Vector3; to: THREE.Vector3; start: number } | null =
      null;
    const style = getComputedStyle(document.documentElement);
    const token = (key: string) => style.getPropertyValue(`--ah-${key}`).trim();
    const palette: GlobePalette = {
      ocean: token("globe-ocean"),
      land: token("globe-land"),
      line: token("globe-line"),
      night: token("globe-night"),
      light: token("globe-night-light"),
      gold: token("gold"),
      atmosphere: token("globe-atmosphere"),
    };
    const zoomTarget = () => (latest.current.view === "iran" ? 210 : 330);
    const cleanObjects = () => {
      scene.traverse((object) => {
        const mesh = object as THREE.Mesh;
        if (mesh.geometry) geometries.add(mesh.geometry);
        if (mesh.material)
          (Array.isArray(mesh.material)
            ? mesh.material
            : [mesh.material]
          ).forEach((material) => materials.add(material));
      });
      geometries.forEach((geometry) => geometry.dispose());
      materials.forEach((material) => material.dispose());
      textures.forEach((texture) => texture.dispose());
    };
    const visibility = () => {
      if (document.hidden || !visible) {
        cancelAnimationFrame(frame);
        frame = 0;
        globe?.pauseAnimation();
      } else if (!disposed && !frame) {
        frame = requestAnimationFrame(render);
      }
    };
    const contextLost = (event: Event) => {
      event.preventDefault();
      if (!disposed) onFailure();
    };
    let pointerStart = { x: 0, y: 0 };
    const pointerDown = (event: PointerEvent) => {
      pointerStart = { x: event.clientX, y: event.clientY };
      fly = null;
    };
    const pointerUp = (event: PointerEvent) => {
      if (
        !renderer ||
        Math.hypot(
          event.clientX - pointerStart.x,
          event.clientY - pointerStart.y,
        ) > 5
      )
        return;
      const rect = renderer.domElement.getBoundingClientRect();
      const ray = new THREE.Raycaster();
      ray.setFromCamera(
        new THREE.Vector2(
          ((event.clientX - rect.left) / rect.width) * 2 - 1,
          (-(event.clientY - rect.top) / rect.height) * 2 + 1,
        ),
        camera,
      );
      const hit = ray.ray.intersectSphere(
        new THREE.Sphere(new THREE.Vector3(), 100),
        new THREE.Vector3(),
      );
      if (!hit || !globe) return;
      const geo = globe.toGeoCoords(hit);
      const iran = countries.features.find(
        (country) => country.properties.iso === "IRN",
      );
      if (
        iran &&
        countryRings(iran).some((ring) => {
          let inside = false;
          for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            const [xi, yi] = ring[i],
              [xj, yj] = ring[j];
            if (
              yi > geo.lat !== yj > geo.lat &&
              geo.lng < ((xj - xi) * (geo.lat - yi)) / (yj - yi) + xi
            )
              inside = !inside;
          }
          return inside;
        })
      )
        onIran();
    };
    let earthMaterial: THREE.ShaderMaterial;
    let iranPulse: THREE.Mesh;
    let markerGroup: THREE.Group;
    let particles: THREE.Points;
    let sunUpdated = 0;
    const projected = new THREE.Vector3();
    function render(now: number) {
      frame = 0;
      if (
        disposed ||
        document.hidden ||
        !visible ||
        !renderer ||
        !globe ||
        !controls
      )
        return;
      const interval =
        quality === "high"
          ? 1000 / 60
          : quality === "low"
            ? 1000 / 20
            : 1000 / 30;
      if (now - lastFrame >= interval) {
        const delta = Math.min((now - lastFrame) / 1000, 0.1);
        lastFrame = now;
        const config = latest.current;
        controls.autoRotate =
          !config.paused &&
          !config.reducedMotion &&
          config.view === "global" &&
          !fly;
        if (fly) {
          const t = config.reducedMotion
            ? 1
            : Math.min(1, (now - fly.start) / 1100);
          const ease = t * t * (3 - 2 * t);
          camera.position.lerpVectors(fly.from, fly.to, ease);
          if (t === 1) fly = null;
        }
        controls.update(delta);
        if (now - sunUpdated > 30000 || sunUpdated === 0) {
          const sun = solarPosition(new Date());
          earthMaterial.uniforms.sunDirection.value
            .copy(
              new THREE.Vector3().copy(
                globe.getCoords(sun.latitude, sun.longitude, 0),
              ),
            )
            .normalize();
          sunUpdated = now;
        }
        if (iranPulse) {
          const pulse =
            config.reducedMotion || config.paused
              ? 1
              : 1 + 0.12 * Math.sin(now / 500);
          iranPulse.scale.setScalar(pulse);
        }
        for (const label of labels) {
          const facing =
            label.position
              .clone()
              .normalize()
              .dot(camera.position.clone().sub(label.position).normalize()) >
            0.12;
          label.element.hidden = !config.labels || !facing;
          if (facing && config.labels) {
            projected.copy(label.position).project(camera);
            label.element.style.transform = `translate(-50%,-50%) translate(${(projected.x * 0.5 + 0.5) * host!.clientWidth}px,${(-projected.y * 0.5 + 0.5) * host!.clientHeight}px)`;
          }
        }
        renderer.render(scene, camera);
      }
      frame = requestAnimationFrame(render);
    }
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: quality !== "low",
        alpha: true,
        powerPreference: "low-power",
      });
      renderer.setClearColor(0, 0);
      renderer.setPixelRatio(
        Math.min(
          window.devicePixelRatio,
          quality === "high" ? 2 : quality === "low" ? 0.8 : 1.25,
        ),
      );
      renderer.domElement.setAttribute(
        "aria-label",
        "Interactive 3D Earth. Use the adjacent labeled controls for keyboard navigation.",
      );
      renderer.domElement.setAttribute("role", "img");
      host.appendChild(renderer.domElement);
      camera = new THREE.PerspectiveCamera(42, 1, 0.1, 2000);
      camera.position.set(220, 140, 205);
      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.06;
      controls.enablePan = false;
      controls.minDistance = 155;
      controls.maxDistance = 480;
      controls.autoRotateSpeed = 0.23;
      controls.rotateSpeed = 0.45;
      globe = new ThreeGlobe({ animateIn: false, waitForGlobeReady: false })
        .showAtmosphere(latest.current.atmosphere)
        .atmosphereColor(palette.atmosphere)
        .atmosphereAltitude(0.14)
        .globeCurvatureResolution(quality === "low" ? 5 : 3);
      // No internal globe animations: this module owns scheduling and visibility suspension.
      globe.pauseAnimation();
      scene.add(globe);
      const textureSet = makeEarthTextures(
        countries,
        palette,
        quality === "high" ? 4096 : quality === "low" ? 1024 : 2048,
      );
      textures.push(textureSet.dayTexture, textureSet.nightTexture);
      earthMaterial = makeEarthMaterial(
        textureSet.dayTexture,
        textureSet.nightTexture,
      );
      materials.add(globe.globeMaterial());
      globe.globeMaterial(earthMaterial);
      scene.add(new THREE.AmbientLight(palette.gold, 0.6));
      const iran = countries.features.find(
        (feature) => feature.properties.iso === "IRN",
      );
      if (iran)
        countryRings(iran).forEach((ring) => {
          const points = ring.map(([lng, lat]) =>
            new THREE.Vector3().copy(globe!.getCoords(lat, lng, 0.006)),
          );
          const geometry = new THREE.BufferGeometry().setFromPoints(points);
          const line = new THREE.Line(
            geometry,
            new THREE.LineBasicMaterial({
              color: palette.gold,
              transparent: true,
              opacity: 0.95,
            }),
          );
          scene.add(line);
          const halo = new THREE.Line(
            geometry,
            new THREE.LineBasicMaterial({
              color: palette.gold,
              transparent: true,
              opacity: 0.12,
            }),
          );
          halo.scale.setScalar(1.006);
          scene.add(halo);
        });
      markerGroup = new THREE.Group();
      scene.add(markerGroup);
      for (const city of referenceCities) {
        const marker = new THREE.Mesh(
          new THREE.SphereGeometry(city.name === "TEHRAN" ? 1.25 : 0.55, 8, 8),
          new THREE.MeshBasicMaterial({ color: palette.gold }),
        );
        marker.position.copy(globe.getCoords(city.lat, city.lng, 0.014));
        markerGroup.add(marker);
      }
      iranPulse = new THREE.Mesh(
        new THREE.RingGeometry(2.3, 2.7, 40),
        new THREE.MeshBasicMaterial({
          color: palette.gold,
          transparent: true,
          opacity: 0.8,
          side: THREE.DoubleSide,
        }),
      );
      iranPulse.position.copy(globe.getCoords(tehran.lat, tehran.lng, 0.018));
      iranPulse.lookAt(iranPulse.position.clone().multiplyScalar(2));
      markerGroup.add(iranPulse);
      referenceCities.slice(0, 7).forEach((city) => {
        const element = document.createElement("button");
        element.className = `dc-globe-label ${city.name === "TEHRAN" ? "dc-globe-label-iran" : ""}`;
        element.textContent =
          latest.current.language === "fa" ? city.fa : city.name;
        element.tabIndex = city.name === "TEHRAN" ? 0 : -1;
        element.disabled = city.name !== "TEHRAN";
        if (city.name === "TEHRAN") element.addEventListener("click", onIran);
        host.appendChild(element);
        labels.push({
          element,
          position: new THREE.Vector3().copy(
            globe!.getCoords(city.lat, city.lng, 0.06),
          ),
          city,
        });
      });
      const starPositions: number[] = [];
      const count = quality === "high" ? 200 : quality === "low" ? 0 : 70;
      for (let i = 0; i < count; i++) {
        const azimuth = i * 2.39996;
        const y = 1 - (2 * (i + 0.5)) / count;
        const radius = Math.sqrt(1 - y * y);
        starPositions.push(
          Math.cos(azimuth) * radius * 650,
          y * 650,
          Math.sin(azimuth) * radius * 650,
        );
      }
      const starGeometry = new THREE.BufferGeometry();
      starGeometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(starPositions, 3),
      );
      particles = new THREE.Points(
        starGeometry,
        new THREE.PointsMaterial({
          color: palette.atmosphere,
          size: 0.8,
          transparent: true,
          opacity: 0.45,
        }),
      );
      scene.add(particles);
      const flyTo = (config: GlobeOptions) => {
        if (!globe) return;
        const target =
          config.view === "iran"
            ? globe.getCoords(32.4, 53.7, 0)
            : globe.getCoords(25, 37, 0);
        const distance = Math.max(
          155,
          Math.min(480, zoomTarget() - config.zoom * 25),
        );
        const to = new THREE.Vector3()
          .copy(target)
          .normalize()
          .multiplyScalar(distance);
        fly = { from: camera.position.clone(), to, start: performance.now() };
      };
      controller.current = {
        apply: (previous, next) => {
          globe?.showAtmosphere(next.atmosphere && quality !== "low");
          markerGroup.visible = next.markers;
          particles.visible = !next.reducedMotion && quality !== "low";
          labels.forEach((label) => {
            label.element.textContent =
              next.language === "fa" ? label.city.fa : label.city.name;
          });
          if (previous.view !== next.view || previous.reset !== next.reset)
            flyTo(next);
          else if (previous.zoom !== next.zoom) {
            const distance = Math.max(
              155,
              Math.min(
                480,
                camera.position.length() - (next.zoom - previous.zoom) * 25,
              ),
            );
            fly = {
              from: camera.position.clone(),
              to: camera.position.clone().normalize().multiplyScalar(distance),
              start: performance.now(),
            };
          }
        },
      };
      controller.current.apply(latest.current, latest.current);
      flyTo(latest.current);
      const resize = () => {
        if (!renderer || !host) return;
        const width = host.clientWidth;
        const height = host.clientHeight;
        if (width < 1 || height < 1) return;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        globe?.rendererSize(new THREE.Vector2(width, height));
      };
      resizeObserver = new ResizeObserver(resize);
      resizeObserver.observe(host);
      resize();
      intersection = new IntersectionObserver(
        (entries) => {
          visible = entries[0]?.isIntersecting ?? true;
          visibility();
        },
        { threshold: 0.01 },
      );
      intersection.observe(host);
      renderer.domElement.addEventListener("webglcontextlost", contextLost);
      renderer.domElement.addEventListener("pointerdown", pointerDown);
      renderer.domElement.addEventListener("pointerup", pointerUp);
      document.addEventListener("visibilitychange", visibility);
      frame = requestAnimationFrame(render);
      onReady();
    } catch {
      onFailure();
    }
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      controller.current = null;
      document.removeEventListener("visibilitychange", visibility);
      resizeObserver?.disconnect();
      intersection?.disconnect();
      controls?.dispose();
      if (renderer) {
        renderer.domElement.removeEventListener(
          "webglcontextlost",
          contextLost,
        );
        renderer.domElement.removeEventListener("pointerdown", pointerDown);
        renderer.domElement.removeEventListener("pointerup", pointerUp);
      }
      labels.forEach(({ element }) => {
        element.removeEventListener("click", onIran);
        element.remove();
      });
      cleanObjects();
      globe?._destructor();
      renderer?.renderLists.dispose();
      renderer?.dispose();
      renderer?.forceContextLoss();
      renderer?.domElement.remove();
      scene.clear();
    };
  }, [countries, quality, onIran, onFailure, onReady]);
  return <div className="dc-globe-host" ref={hostRef} />;
}
