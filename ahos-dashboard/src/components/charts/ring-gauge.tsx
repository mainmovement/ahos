import { useId } from "react";
import { cn } from "@/lib/utils";

interface RingGaugeProps {
  /** 0..100, null = unknown (renders a dashed ring + "—") */
  value: number | null;
  size?: number;
  stroke?: number;
  label: string;
  caption?: string;
  tone?: "gold" | "data" | "up" | "down" | "warn";
  className?: string;
  display?: string;
}

/** SVG ring gauge for scores/percentages. Unknown is visually distinct from 0. */
export function RingGauge({ value, size = 88, stroke = 7, label, caption, tone = "gold", className, display }: RingGaugeProps) {
  const gid = `ring-${useId().replace(/:/g, "")}`;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const pct = value === null ? 0 : Math.max(0, Math.min(100, value)) / 100;
  const color = { gold: `url(#${gid})`, data: "var(--color-data-400)", up: "var(--color-up)", down: "var(--color-down)", warn: "var(--color-warn)" }[tone];
  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size, height: size }} role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={value ?? undefined}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <defs>
          <linearGradient id={gid} x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--color-gold-200)" />
            <stop offset="55%" stopColor="var(--color-gold-400)" />
            <stop offset="100%" stopColor="var(--color-gold-600)" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(255 255 255 / 0.06)" strokeWidth={stroke} strokeDasharray={value === null ? "3 5" : undefined} />
        {value !== null && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${circ * pct} ${circ}`}
            style={{ filter: "drop-shadow(0 0 calc(6px * var(--glow-strength)) rgb(230 191 95 / 0.45))", transition: "stroke-dasharray var(--dur-xslow) var(--ease-out-expo)" }}
          />
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span dir="ltr" className="num text-lg font-semibold text-fg-1">
          {display ?? (value === null ? "—" : Math.round(value))}
        </span>
        {caption && <span className="text-3xs text-fg-4">{caption}</span>}
      </div>
    </div>
  );
}
