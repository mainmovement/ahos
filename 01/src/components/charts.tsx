"use client";

import { useEffect, useId, useRef, useState } from "react";
import { cx, TONE, type Tone } from "@/lib/ui";

/* ============================ ScoreRing ============================ */

export function ScoreRing({
  value, size = 120, stroke = 8, tone = "jade", label, sub,
}: {
  value: number; size?: number; stroke?: number; tone?: Tone; label?: string; sub?: string;
}) {
  const id = useId().replace(/:/g, "");
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(0);
  const hex = TONE[tone].hex;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf = 0;
    const io = new IntersectionObserver(
      (entries) => {
        if (!entries[0].isIntersecting) return;
        io.disconnect();
        const t0 = performance.now();
        const dur = 1400;
        const tick = (t: number) => {
          const p = Math.min(1, (t - t0) / dur);
          setShown(Math.round(value * (1 - Math.pow(1 - p, 3))));
          if (p < 1) raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => { io.disconnect(); cancelAnimationFrame(raf); };
  }, [value]);

  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - shown / 100);

  return (
    <div ref={ref} className="relative inline-grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={`sg-${id}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.9" />
            <stop offset="0.35" stopColor={hex} />
            <stop offset="1" stopColor={hex} stopOpacity="0.55" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={`url(#sg-${id})`} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={off}
          style={{ filter: `drop-shadow(0 0 10px ${hex}88)`, transition: "stroke-dashoffset 0.1s linear" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="num font-black" style={{ fontSize: size * 0.26 }}>{shown}</div>
          {label ? <div className="text-[10px] font-medium text-mist">{label}</div> : null}
          {sub ? <div className="text-[9px] text-mist/70">{sub}</div> : null}
        </div>
      </div>
    </div>
  );
}

/* ============================ Sparkline ============================ */

export function Sparkline({
  data, w = 132, h = 40, className,
}: {
  data: number[]; w?: number; h?: number; className?: string;
}) {
  const id = useId().replace(/:/g, "");
  if (!data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const pts = data.map((v, i) => [
    (i / (data.length - 1)) * w,
    h - ((v - min) / span) * (h - 6) - 3,
  ]);
  const up = data[data.length - 1] >= data[0];
  const hex = up ? "#34d399" : "#fb7185";
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className={cx("overflow-visible", className)} aria-hidden>
      <defs>
        <linearGradient id={`sa-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={hex} stopOpacity="0.35" />
          <stop offset="1" stopColor={hex} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${line} L${w},${h} L0,${h} Z`} fill={`url(#sa-${id})`} />
      <path d={line} fill="none" stroke={hex} strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="2.4" fill={hex}>
        <animate attributeName="opacity" values="1;0.3;1" dur="1.8s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

/* ============================ Radar ============================ */

export function Radar({ axes, size = 260 }: { axes: { label: string; value: number }[]; size?: number }) {
  const id = useId().replace(/:/g, "");
  const n = axes.length;
  const cx0 = size / 2;
  const cy0 = size / 2;
  const R = size / 2 - 44;
  const pt = (i: number, v: number) => {
    const a = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx0 + Math.cos(a) * R * (v / 100), cy0 + Math.sin(a) * R * (v / 100)];
  };
  const poly = (v: number) =>
    axes.map((_, i) => pt(i, v).map((x) => x.toFixed(1)).join(",")).join(" ");
  const valuePoly = axes.map((a, i) => pt(i, a.value).map((x) => x.toFixed(1)).join(",")).join(" ");
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="radar" className="mx-auto">
      <defs>
        <radialGradient id={`rg-${id}`}>
          <stop offset="0" stopColor="#34d399" stopOpacity="0.35" />
          <stop offset="1" stopColor="#34d399" stopOpacity="0.04" />
        </radialGradient>
      </defs>
      {[25, 50, 75, 100].map((v) => (
        <polygon key={v} points={poly(v)} fill="none" stroke="rgba(140,190,165,0.14)" strokeWidth="1" />
      ))}
      {axes.map((_, i) => {
        const [x, y] = pt(i, 100);
        return <line key={i} x1={cx0} y1={cy0} x2={x} y2={y} stroke="rgba(140,190,165,0.12)" strokeWidth="1" />;
      })}
      <polygon points={valuePoly} fill={`url(#rg-${id})`} stroke="#34d399" strokeWidth="1.8" strokeLinejoin="round" style={{ filter: "drop-shadow(0 0 8px rgba(52,211,153,0.4))" }} />
      {axes.map((a, i) => {
        const [x, y] = pt(i, a.value);
        return <circle key={i} cx={x} cy={y} r="3" fill="#6ee7b7" />;
      })}
      {axes.map((a, i) => {
        const ang = (Math.PI * 2 * i) / n - Math.PI / 2;
        const lx = cx0 + Math.cos(ang) * (R + 26);
        const ly = cy0 + Math.sin(ang) * (R + 26);
        return (
          <text
            key={i} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
            className="fill-mist" fontSize="10" fontWeight="600"
          >
            {a.label}
            <tspan x={lx} dy="11" className="fill-frost/80 num" fontSize="9.5">{a.value}</tspan>
          </text>
        );
      })}
    </svg>
  );
}

/* ============================ Equity area chart ============================ */

export function EquityChart({ points, w = 640, h = 220 }: { points: number[]; w?: number; h?: number }) {
  const id = useId().replace(/:/g, "");
  const data = [0, ...points];
  const min = Math.min(...data, 0);
  const max = Math.max(...data, 0);
  const span = max - min || 1;
  const padY = 14;
  const X = (i: number) => (i / (data.length - 1)) * w;
  const Y = (v: number) => padY + (1 - (v - min) / span) * (h - padY * 2);
  const line = data.map((v, i) => `${i === 0 ? "M" : "L"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");
  const zeroY = Y(0);
  const last = data[data.length - 1];
  const hex = last >= 0 ? "#34d399" : "#fb7185";
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" role="img" aria-label="equity curve">
      <defs>
        <linearGradient id={`eq-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={hex} stopOpacity="0.3" />
          <stop offset="1" stopColor={hex} stopOpacity="0.01" />
        </linearGradient>
      </defs>
      {[0.25, 0.5, 0.75].map((f) => (
        <line key={f} x1="0" x2={w} y1={h * f} y2={h * f} stroke="rgba(140,190,165,0.08)" strokeDasharray="3 6" />
      ))}
      <line x1="0" x2={w} y1={zeroY} y2={zeroY} stroke="rgba(236,245,239,0.25)" strokeWidth="1" />
      <path d={`${line} L${w},${h} L0,${h} Z`} fill={`url(#eq-${id})`} />
      <path d={line} fill="none" stroke={hex} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" style={{ filter: `drop-shadow(0 0 10px ${hex}66)` }} />
      {data.map((v, i) => (
        <circle key={i} cx={X(i)} cy={Y(v)} r={i === data.length - 1 ? 4 : 2.5} fill={i === data.length - 1 ? "#f5b73f" : hex} />
      ))}
    </svg>
  );
}
