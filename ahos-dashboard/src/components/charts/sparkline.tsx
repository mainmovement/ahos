import { useId } from "react";
import { cn } from "@/lib/utils";

interface SparklineProps {
  data: readonly number[];
  className?: string;
  /** stroke colour token (CSS var) — defaults to the data cyan */
  color?: string;
  area?: boolean;
  baseline?: boolean;
  strokeWidth?: number;
  label?: string;
  height?: number;
}

/**
 * Lightweight SVG sparkline (no chart library) for dense KPI cards.
 * Time always flows left→right, also in RTL.
 */
export function Sparkline({ data, className, color = "var(--color-data-400)", area = true, baseline = false, strokeWidth = 1.5, label, height = 36 }: SparklineProps) {
  const id = useId().replace(/:/g, "");
  const w = 120;
  const h = height;
  if (data.length < 2) {
    return (
      <svg viewBox={`0 0 ${w} ${h}`} className={cn("block w-full", className)} style={{ height }} role="img" aria-label={label ?? "no data"}>
        <line x1="0" x2={w} y1={h / 2} y2={h / 2} stroke="var(--color-fg-5)" strokeDasharray="3 4" />
      </svg>
    );
  }
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const pad = 3;
  const pts = data.map((v, i) => [(i / (data.length - 1)) * w, pad + (1 - (v - min) / span) * (h - pad * 2)] as const);
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
  const last = pts[pts.length - 1]!;
  const first = pts[0]!;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className={cn("block w-full overflow-visible", className)} style={{ height }} role="img" aria-label={label}>
      <defs>
        <linearGradient id={`sg-${id}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.32" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {baseline && <line x1="0" x2={w} y1={first[1]} y2={first[1]} stroke="var(--color-fg-5)" strokeDasharray="2 3" vectorEffect="non-scaling-stroke" />}
      {area && <path d={`${line} L${w},${h} L0,${h} Z`} fill={`url(#sg-${id})`} />}
      <path d={line} fill="none" stroke={color} strokeWidth={strokeWidth} vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={last[0]} cy={last[1]} r="2.2" fill={color} vectorEffect="non-scaling-stroke" />
      <circle cx={last[0]} cy={last[1]} r="5" fill={color} opacity="0.18" />
    </svg>
  );
}
