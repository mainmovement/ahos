"use client";

/**
 * The department ring: one thin gold circle with twelve evenly spaced ticks, one per AHOS
 * department. A tick lights up (opacity 0.9, solid gold) only when its department needs attention;
 * otherwise it stays dim. Nothing here animates — the ring is the calm frame of the dial.
 */

import { dialSize, ringRadius, tickAngle, tickInner, tickOuter } from "./layout";
import type { Department } from "../../types/globe";

export type RingTicksProps = {
  departments: readonly Department[];
  size: number;
};

export function RingTicks({ departments, size }: RingTicksProps) {
  const dial = dialSize(size);
  const centre = dial / 2;
  const inner = tickInner(size);
  const outer = tickOuter(size);
  const count = departments.length || 12;

  return (
    <g className="ahos-ring" aria-hidden="true">
      <circle
        cx={centre}
        cy={centre}
        r={ringRadius(size)}
        fill="none"
        stroke="rgba(212, 175, 55, 0.25)"
        strokeWidth={1}
      />
      {departments.map((department, index) => {
        const angle = tickAngle(index, count);
        const radians = (angle * Math.PI) / 180;
        const cos = Math.cos(radians);
        const sin = Math.sin(radians);
        return (
          <line
            key={department.id}
            x1={centre + cos * inner}
            y1={centre + sin * inner}
            x2={centre + cos * outer}
            y2={centre + sin * outer}
            stroke={department.needsAttention ? "#f5d27a" : "rgba(212, 175, 55, 0.55)"}
            strokeWidth={department.needsAttention ? 1.6 : 1}
            strokeLinecap="round"
            opacity={department.needsAttention ? 0.9 : 0.42}
            data-attention={department.needsAttention ? "true" : "false"}
            data-freshness={department.freshness}
          />
        );
      })}
    </g>
  );
}
