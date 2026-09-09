"use client";

import { useEffect, useRef } from "react";
import type { TreeVitals } from "@/lib/engine";

/* ------------------------------------------------------------------ */
/* The Wise Tree — procedural, living botanical-tech visualization.    */
/* roots = data sources · rocks = failures · leaves = sensors          */
/* fruits = opportunities · golden fruit = exceptional opportunity     */
/* ------------------------------------------------------------------ */

type V = { x: number; y: number };

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type Branch = { pts: V[]; w: number; depth: number; side: number };
type Root = { pts: V[]; healthy: boolean; ph: number };
type Leaf = { x: number; y: number; r: number; rot: number; ph: number };
type Fruit = { x: number; y: number; r: number; golden: boolean; ph: number };
type Rock = { x: number; y: number; s: number; rot: number };

type Tree = {
  trunk: V[];
  branches: Branch[];
  roots: Root[];
  leaves: Leaf[];
  fruits: Fruit[];
  rocks: Rock[];
  groundY: number;
};

function growTree(w: number, h: number, vitals: TreeVitals): Tree {
  const rnd = mulberry32(1377);
  const groundY = h * 0.8;
  const baseX = w * 0.5;
  const topY = h * 0.16;

  /* trunk — slightly serpentine polyline */
  const segs = 10;
  const trunk: V[] = [];
  for (let i = 0; i <= segs; i++) {
    const t = i / segs;
    trunk.push({
      x: baseX + Math.sin(t * 3.1) * 7 * (1 - t) + (rnd() - 0.5) * 4,
      y: groundY - t * (groundY - topY),
    });
  }

  /* branches — one per specialist team */
  const branches: Branch[] = [];
  const count = Math.max(6, Math.min(12, vitals.branches));
  for (let i = 0; i < count; i++) {
    const t = 0.3 + (0.62 * i) / (count - 1); // height along trunk
    const idx = Math.round(t * segs);
    const start = trunk[Math.min(segs, idx)];
    const side = i % 2 === 0 ? 1 : -1;
    const len = (0.16 + rnd() * 0.22) * w * 0.5;
    const rise = (0.1 + rnd() * 0.16) * h;
    const pts: V[] = [{ ...start }];
    const steps = 4;
    for (let k = 1; k <= steps; k++) {
      const u = k / steps;
      pts.push({
        x: start.x + side * len * u * (0.6 + u * 0.6),
        y: start.y - rise * u - Math.sin(u * Math.PI) * 8 + (rnd() - 0.5) * 6,
      });
    }
    branches.push({ pts, w: 5.5 - t * 3.4, depth: i, side });
  }

  /* roots — one per provider */
  const roots: Root[] = [];
  const rc = Math.max(4, Math.min(12, vitals.roots));
  for (let i = 0; i < rc; i++) {
    const side = i % 2 === 0 ? 1 : -1;
    const reach = (0.2 + rnd() * 0.32) * w * 0.5;
    const depth = (0.09 + rnd() * 0.13) * h;
    const pts: V[] = [{ x: baseX, y: groundY }];
    const steps = 4;
    for (let k = 1; k <= steps; k++) {
      const u = k / steps;
      pts.push({
        x: baseX + side * reach * u + (rnd() - 0.5) * 14,
        y: groundY + depth * Math.sin(u * Math.PI * 0.62) + (rnd() - 0.5) * 5,
      });
    }
    roots.push({ pts, healthy: i < vitals.healthyRoots, ph: rnd() * Math.PI * 2 });
  }

  /* leaves — sensors */
  const leaves: Leaf[] = [];
  const leafCount = Math.min(110, vitals.leaves);
  for (let i = 0; i < leafCount; i++) {
    const b = branches[Math.floor(rnd() * branches.length)];
    const tip = b.pts[b.pts.length - 1];
    leaves.push({
      x: tip.x + (rnd() - 0.5) * 56,
      y: tip.y + (rnd() - 0.5) * 36 - 8,
      r: 2 + rnd() * 3.4,
      rot: rnd() * Math.PI,
      ph: rnd() * Math.PI * 2,
    });
  }

  /* fruits */
  const fruits: Fruit[] = [];
  const shuffled = [...branches].sort(() => rnd() - 0.5);
  for (let i = 0; i < vitals.fruits && i < shuffled.length; i++) {
    const tip = shuffled[i].pts[shuffled[i].pts.length - 1];
    fruits.push({ x: tip.x, y: tip.y + 8, r: 6.5, golden: false, ph: rnd() * Math.PI * 2 });
  }
  /* golden fruit crowns the tree */
  for (let i = 0; i < Math.max(1, vitals.goldenFruits); i++) {
    fruits.push({ x: baseX + (i - 0.5) * 26, y: topY - 14 - i * 20, r: 9, golden: true, ph: rnd() * Math.PI * 2 });
  }

  /* rocks — failures near the roots */
  const rocks: Rock[] = [];
  for (let i = 0; i < vitals.rocks; i++) {
    const side = i % 2 === 0 ? 1 : -1;
    rocks.push({
      x: baseX + side * (0.1 + rnd() * 0.22) * w * 0.5,
      y: groundY + 6 + rnd() * h * 0.09,
      s: 9 + rnd() * 10,
      rot: rnd() * Math.PI,
    });
  }

  return { trunk, branches, roots, leaves, fruits, rocks, groundY };
}

export default function TreeCanvas({ vitals, className }: { vitals: TreeVitals; className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current as HTMLCanvasElement;
    if (!canvas) return;
    const ctx = canvas.getContext("2d") as CanvasRenderingContext2D;
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0, h = 0, dpr = 1, raf = 0, t = 0, last = performance.now();
    let tree: Tree = growTree(600, 420, vitals);
    let running = true;

    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      w = Math.max(280, rect?.width ?? 600);
      h = Math.max(320, Math.round(w * 0.62));
      dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = w * dpr; canvas.height = h * dpr;
      canvas.style.width = `${w}px`; canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      tree = growTree(w, h, vitals);
      if (reduced) draw(0.016);
    };

    const sway = (ph: number, amp: number) => Math.sin(t * 0.7 + ph) * amp;

    function draw(dt: number) {
      t += dt;
      ctx.clearRect(0, 0, w, h);

      const gy = tree.groundY;

      /* crown aura */
      const aura = ctx.createRadialGradient(w * 0.5, h * 0.32, 0, w * 0.5, h * 0.32, w * 0.42);
      aura.addColorStop(0, "rgba(52,211,153,0.10)");
      aura.addColorStop(0.6, "rgba(245,183,63,0.05)");
      aura.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = aura;
      ctx.fillRect(0, 0, w, h);

      /* ground line */
      ctx.strokeStyle = "rgba(140,190,165,0.22)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, gy);
      for (let x = 0; x <= w; x += 8) {
        ctx.lineTo(x, gy + Math.sin(x * 0.02 + 1) * 2.4);
      }
      ctx.stroke();

      /* groundwater shimmer */
      for (let i = 0; i < vitals.water; i++) {
        const px = ((i * 97.3 + (t * 14)) % (w * 0.9)) + w * 0.05;
        const py = gy + h * 0.13 + Math.sin(t * 0.8 + i) * 4;
        ctx.fillStyle = `rgba(103,232,249,${0.1 + 0.08 * Math.sin(t + i)})`;
        ctx.beginPath(); ctx.arc(px, py, 1.6, 0, Math.PI * 2); ctx.fill();
      }

      /* roots */
      for (const r of tree.roots) {
        const flow = 0.5 + 0.5 * Math.sin(t * 1.4 + r.ph);
        ctx.strokeStyle = r.healthy
          ? `rgba(52,211,153,${0.28 + flow * 0.3})`
          : "rgba(251,113,133,0.30)";
        ctx.lineWidth = r.healthy ? 2.4 : 2;
        ctx.lineCap = "round";
        ctx.beginPath();
        r.pts.forEach((p, i) => {
          const x = p.x + sway(r.ph + i, 1.2);
          i === 0 ? ctx.moveTo(x, p.y) : ctx.lineTo(x, p.y);
        });
        ctx.stroke();
        if (r.healthy) {
          const tip = r.pts[r.pts.length - 1];
          ctx.fillStyle = `rgba(110,231,183,${0.4 + flow * 0.4})`;
          ctx.beginPath(); ctx.arc(tip.x + sway(r.ph, 1), tip.y, 2.2, 0, Math.PI * 2); ctx.fill();
        }
      }

      /* rocks */
      for (const r of tree.rocks) {
        ctx.save();
        ctx.translate(r.x, r.y);
        ctx.rotate(r.rot);
        ctx.fillStyle = "rgba(90,96,100,0.75)";
        ctx.strokeStyle = "rgba(251,113,133,0.4)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
          const a = (i / 6) * Math.PI * 2;
          const rr = r.s * (0.75 + ((i * 37) % 10) / 40);
          const x = Math.cos(a) * rr, y = Math.sin(a) * rr * 0.8;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath(); ctx.fill(); ctx.stroke();
        ctx.restore();
      }

      /* trunk */
      tree.trunk.forEach((p, i) => {
        if (i === 0) return;
        const prev = tree.trunk[i - 1];
        const u = i / tree.trunk.length;
        const grad = ctx.createLinearGradient(prev.x, prev.y, p.x, p.y);
        grad.addColorStop(0, `rgba(96,74,46,${0.92 - u * 0.1})`);
        grad.addColorStop(1, `rgba(138,106,58,${0.9})`);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 14 * (1 - u) + 2.4;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(prev.x + sway(u, u * 2.2), prev.y);
        ctx.lineTo(p.x + sway(u + 0.1, u * 2.2), p.y);
        ctx.stroke();
      });

      /* branches */
      for (const b of tree.branches) {
        const breathe = sway(b.depth, 2.4);
        ctx.strokeStyle = "rgba(122,96,60,0.85)";
        ctx.lineWidth = Math.max(1.2, b.w);
        ctx.lineCap = "round";
        ctx.beginPath();
        b.pts.forEach((p, i) => {
          const u = i / (b.pts.length - 1);
          const x = p.x + breathe * u;
          i === 0 ? ctx.moveTo(x, p.y) : ctx.lineTo(x, p.y);
        });
        ctx.stroke();
      }

      /* leaves */
      for (const l of tree.leaves) {
        const pulse = 0.5 + 0.5 * Math.sin(t * 1.3 + l.ph);
        ctx.save();
        ctx.translate(l.x + sway(l.ph, 2.6), l.y + Math.cos(t * 0.9 + l.ph) * 1.4);
        ctx.rotate(l.rot + Math.sin(t * 0.6 + l.ph) * 0.2);
        ctx.fillStyle = `rgba(110,231,183,${0.16 + pulse * 0.35})`;
        ctx.beginPath();
        ctx.ellipse(0, 0, l.r * 1.7, l.r, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      /* knowledge motes rising through trunk */
      for (let i = 0; i < Math.min(16, vitals.water); i++) {
        const u = ((t * 0.06 + i * 0.11) % 1);
        const ti = Math.floor(u * (tree.trunk.length - 1));
        const p = tree.trunk[Math.min(tree.trunk.length - 1, ti)];
        ctx.fillStyle = `rgba(103,232,249,${0.55 * (1 - u)})`;
        ctx.beginPath(); ctx.arc(p.x + Math.sin(t * 2 + i) * 6, p.y, 1.8, 0, Math.PI * 2); ctx.fill();
      }

      /* fruits */
      for (const f of tree.fruits) {
        const pulse = 0.5 + 0.5 * Math.sin(t * (f.golden ? 1.8 : 1.1) + f.ph);
        const fy = f.y + sway(f.ph, 2);
        const glow = ctx.createRadialGradient(f.x, fy, 0, f.x, fy, f.r * 3.2);
        if (f.golden) {
          glow.addColorStop(0, `rgba(245,183,63,${0.4 + pulse * 0.25})`);
          glow.addColorStop(1, "rgba(245,183,63,0)");
        } else {
          glow.addColorStop(0, `rgba(52,211,153,${0.3 + pulse * 0.15})`);
          glow.addColorStop(1, "rgba(52,211,153,0)");
        }
        ctx.fillStyle = glow;
        ctx.beginPath(); ctx.arc(f.x, fy, f.r * 3.2, 0, Math.PI * 2); ctx.fill();

        const body = ctx.createRadialGradient(f.x - f.r * 0.3, fy - f.r * 0.35, 1, f.x, fy, f.r * 1.15);
        if (f.golden) {
          body.addColorStop(0, "#fff3cf");
          body.addColorStop(0.5, "#f5b73f");
          body.addColorStop(1, "#a06a10");
        } else {
          body.addColorStop(0, "#d7fff0");
          body.addColorStop(0.55, "#34d399");
          body.addColorStop(1, "#0b6b4c");
        }
        ctx.fillStyle = body;
        ctx.beginPath(); ctx.arc(f.x, fy, f.r * (f.golden ? 1 + pulse * 0.06 : 1), 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = f.golden ? "rgba(252,211,77,0.6)" : "rgba(110,231,183,0.4)";
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.arc(f.x, fy, f.r + 2.5, 0, Math.PI * 2); ctx.stroke();
      }
    }

    const io = new IntersectionObserver((es) => {
      running = es[0].isIntersecting;
      if (running && !reduced) { last = performance.now(); raf = requestAnimationFrame(loop); }
    });
    const loop = (now: number) => {
      if (!running) return;
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      draw(dt);
      if (!reduced) raf = requestAnimationFrame(loop);
    };
    io.observe(canvas);
    resize();
    window.addEventListener("resize", resize);
    if (!reduced) raf = requestAnimationFrame(loop);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      io.disconnect();
    };
  }, [vitals]);

  return (
    <div className={className}>
      <canvas ref={ref} role="img" aria-label="Wise Tree visualization" className="mx-auto block" />
    </div>
  );
}
