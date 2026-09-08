"use client";

import { useEffect, useRef } from "react";

export function VoidScene({ mode = "hero" }: { mode?: "hero" | "soft" }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    let disposed = false;
    let stop = () => {};

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    (async () => {
      const THREE = await import("three");
      if (disposed || !canvas) return;

      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
      renderer.setClearColor(0x000000, 0);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
      camera.position.z = mode === "hero" ? 7.2 : 8.4;

      const count = mode === "hero" ? 1800 : 900;
      const positions = new Float32Array(count * 3);
      const colors = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        const r = 4.5 + Math.random() * 8;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = r * Math.cos(phi);
        const gold = Math.random() > 0.72;
        colors[i * 3] = gold ? 0.95 : 0.43;
        colors[i * 3 + 1] = gold ? 0.83 : 0.9;
        colors[i * 3 + 2] = gold ? 0.62 : 0.97;
      }
      const pGeo = new THREE.BufferGeometry();
      pGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      pGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
      const points = new THREE.Points(
        pGeo,
        new THREE.PointsMaterial({
          size: mode === "hero" ? 0.028 : 0.02,
          vertexColors: true,
          transparent: true,
          opacity: 0.85,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      );
      scene.add(points);

      const ico = new THREE.Mesh(
        new THREE.IcosahedronGeometry(1.55, 1),
        new THREE.MeshBasicMaterial({
          color: 0xf3d5a0,
          wireframe: true,
          transparent: true,
          opacity: 0.55,
        }),
      );
      scene.add(ico);

      const torus = new THREE.Mesh(
        new THREE.TorusGeometry(2.35, 0.015, 8, 128),
        new THREE.MeshBasicMaterial({ color: 0x6ee7f9, transparent: true, opacity: 0.35 }),
      );
      torus.rotation.x = Math.PI / 2.4;
      scene.add(torus);

      const torus2 = new THREE.Mesh(
        new THREE.TorusGeometry(2.9, 0.008, 8, 160),
        new THREE.MeshBasicMaterial({ color: 0xc9a36a, transparent: true, opacity: 0.22 }),
      );
      torus2.rotation.x = Math.PI / 1.7;
      scene.add(torus2);

      const core = new THREE.Mesh(
        new THREE.SphereGeometry(0.22, 24, 24),
        new THREE.MeshBasicMaterial({ color: 0xfff1cc }),
      );
      scene.add(core);

      let mx = 0;
      let my = 0;
      const onMove = (e: PointerEvent) => {
        mx = (e.clientX / window.innerWidth) * 2 - 1;
        my = (e.clientY / window.innerHeight) * 2 - 1;
      };
      window.addEventListener("pointermove", onMove);

      const resize = () => {
        const parent = canvas.parentElement;
        const w = parent?.clientWidth || window.innerWidth;
        const h = parent?.clientHeight || window.innerHeight;
        renderer.setSize(w, h, false);
        camera.aspect = w / Math.max(h, 1);
        camera.updateProjectionMatrix();
      };
      resize();
      window.addEventListener("resize", resize);

      let raf = 0;
      const tick = () => {
        const t = performance.now() / 1000;
        if (!reduce) {
          ico.rotation.y = t * 0.12;
          ico.rotation.x = t * 0.05;
          torus.rotation.z = t * 0.08;
          torus2.rotation.z = -t * 0.05;
          points.rotation.y = t * 0.02;
          core.scale.setScalar(1 + Math.sin(t * 2) * 0.08);
        }
        camera.position.x += (mx * 0.8 - camera.position.x) * 0.04;
        camera.position.y += (-my * 0.5 - camera.position.y) * 0.04;
        camera.lookAt(0, 0, 0);
        renderer.render(scene, camera);
        raf = requestAnimationFrame(tick);
      };
      tick();

      stop = () => {
        cancelAnimationFrame(raf);
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("resize", resize);
        pGeo.dispose();
        ico.geometry.dispose();
        torus.geometry.dispose();
        torus2.geometry.dispose();
        core.geometry.dispose();
        renderer.dispose();
      };
    })();

    return () => {
      disposed = true;
      stop();
    };
  }, [mode]);

  return <canvas ref={ref} className="void-canvas" aria-hidden />;
}
