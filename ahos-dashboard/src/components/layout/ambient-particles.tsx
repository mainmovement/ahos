"use client";

import { useEffect, useRef } from "react";
import { useSettings } from "@/lib/settings/provider";

/**
 * Gold dust drifting behind the shell. Count comes from the quality profile;
 * disabled for LOW and for reduced motion; pauses when the tab is hidden.
 */
export function AmbientParticles() {
  const { budget, reducedMotion } = useSettings();
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || reducedMotion || budget.particles === 0) {
      if (canvas) canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    let w = 0;
    let h = 0;
    const resize = () => {
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const parts = Array.from({ length: budget.particles }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 0.4 + Math.random() * 1.3,
      vx: (Math.random() - 0.5) * 0.06,
      vy: -0.03 - Math.random() * 0.08,
      a: 0.12 + Math.random() * 0.45,
      ph: Math.random() * Math.PI * 2,
    }));
    let raf = 0;
    let last = performance.now();
    const loop = (t: number) => {
      const dt = Math.min(64, t - last);
      last = t;
      ctx.clearRect(0, 0, w, h);
      for (const p of parts) {
        p.x += p.vx * dt * 0.06 * 16;
        p.y += p.vy * dt * 0.06 * 16;
        if (p.y < -10) {
          p.y = h + 10;
          p.x = Math.random() * w;
        }
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        const tw = 0.6 + 0.4 * Math.sin(t * 0.0012 + p.ph);
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
        g.addColorStop(0, `rgba(240, 210, 126, ${p.a * tw})`);
        g.addColorStop(1, "rgba(240, 210, 126, 0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(loop);
    };
    const start = () => {
      if (!raf) {
        last = performance.now();
        raf = requestAnimationFrame(loop);
      }
    };
    const stop = () => {
      cancelAnimationFrame(raf);
      raf = 0;
    };
    const onVis = () => (document.hidden ? stop() : start());
    start();
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", onVis);
    return () => {
      stop();
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVis);
      ctx.clearRect(0, 0, w, h);
    };
  }, [budget.particles, reducedMotion]);

  return <canvas ref={ref} aria-hidden className="pointer-events-none fixed inset-0 z-0 opacity-80" />;
}
