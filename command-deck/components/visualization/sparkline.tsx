"use client";

import { cn } from "@/lib/utils";

/** Tiny inline SVG sparkline — deterministic, dependency-free. */
export function Sparkline({
  values,
  className,
  stroke = "rgb(var(--chart-1))",
  fill = false,
}: {
  values: readonly number[];
  className?: string;
  stroke?: string;
  fill?: boolean;
}) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = 100 / (values.length - 1);
  const pts = values.map((v, i) => `${(i * step).toFixed(2)},${(30 - ((v - min) / range) * 26).toFixed(2)}`);
  const line = `M${pts.join(" L")}`;
  const area = `${line} L100,32 L0,32 Z`;
  const gradId = `spark-${values.length}-${Math.round(min)}-${Math.round(max)}`;

  return (
    <svg viewBox="0 0 100 32" preserveAspectRatio="none" className={cn("h-10 w-full", className)} aria-hidden>
      {fill ? (
        <>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity="0.25" />
              <stop offset="100%" stopColor={stroke} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={area} fill={`url(#${gradId})`} />
        </>
      ) : null}
      <path d={line} fill="none" stroke={stroke} strokeWidth="1.6" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
    </svg>
  );
}
