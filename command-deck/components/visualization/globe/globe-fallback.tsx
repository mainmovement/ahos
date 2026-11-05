"use client";

import { cn } from "@/lib/utils";
import { Emblem } from "@/components/brand/emblem";
import { Skeleton } from "@/components/ui/misc";

/**
 * 2D fallback for the command-center scene: static, dependency-free SVG with
 * CSS-only orbital motion (disabled under reduced motion). The command center
 * must remain fully useful when WebGL is unavailable or the scene is off.
 */
export function GlobeFallback({ reduced, skeleton = false }: { reduced: boolean; skeleton?: boolean }) {
  if (skeleton) {
    return (
      <div className="flex h-full items-center justify-center">
        <Skeleton className="size-64 rounded-full" />
      </div>
    );
  }

  return (
    <div
      className={cn("flex h-full items-center justify-center", reduced && "[&_*]:!animate-none")}
      role="img"
      aria-label="AHOS command visualization (static fallback)"
    >
      <svg viewBox="0 0 400 400" className="h-full max-h-[430px] w-full max-w-[430px]">
        <defs>
          <radialGradient id="fb-core" cx="50%" cy="42%" r="65%">
            <stop offset="0%" stopColor="#15203A" />
            <stop offset="100%" stopColor="#0B1020" />
          </radialGradient>
        </defs>

        <circle cx="200" cy="200" r="118" fill="url(#fb-core)" stroke="#24345C" strokeWidth="1" />
        {/* latitude hints */}
        <ellipse cx="200" cy="200" rx="118" ry="38" fill="none" stroke="#344E74" strokeWidth="0.8" opacity="0.6" />
        <ellipse cx="200" cy="200" rx="96" ry="30" fill="none" stroke="#344E74" strokeWidth="0.6" opacity="0.4" />
        <ellipse cx="200" cy="200" rx="38" ry="118" fill="none" stroke="#344E74" strokeWidth="0.8" opacity="0.6" />

        {/* orbital rings */}
        <g className={reduced ? undefined : "origin-center animate-[spin_46s_linear_infinite]"} style={{ transformBox: "fill-box" }}>
          <ellipse cx="200" cy="200" rx="168" ry="60" fill="none" stroke="#D4AF37" strokeWidth="1.1" opacity="0.5" strokeDasharray="3 6" />
          <circle cx="368" cy="200" r="3.5" fill="#D4AF37" />
        </g>
        <g className={reduced ? undefined : "fb-spin-rev"} style={{ transformOrigin: "200px 200px" }}>
          <ellipse cx="200" cy="200" rx="150" ry="140" fill="none" stroke="#22D3EE" strokeWidth="1" opacity="0.4" strokeDasharray="2 7" />
          <circle cx="200" cy="60" r="3" fill="#22D3EE" />
        </g>
        <g className={reduced ? undefined : "origin-center animate-[spin_70s_linear_infinite]"} style={{ transformBox: "fill-box" }}>
          <ellipse cx="200" cy="200" rx="184" ry="104" fill="none" stroke="#8B5CF6" strokeWidth="1" opacity="0.35" strokeDasharray="1 8" />
          <circle cx="16" cy="200" r="2.5" fill="#8B5CF6" />
        </g>

        {/* intelligence nodes */}
        {[
          [140, 150], [238, 132], [176, 236], [262, 222], [128, 208], [216, 172],
        ].map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="2.4" fill="#22D3EE" opacity="0.9" />
            <circle cx={x} cy={y} r="5.5" fill="none" stroke="#22D3EE" strokeWidth="0.6" opacity="0.35" />
          </g>
        ))}
        <path d="M140 150 L216 172 L262 222" fill="none" stroke="#22D3EE" strokeWidth="0.7" opacity="0.35" />
        <path d="M238 132 L176 236 L128 208" fill="none" stroke="#D4AF37" strokeWidth="0.7" opacity="0.3" />

        <foreignObject x="152" y="152" width="96" height="96">
          <Emblem className="size-24" animated={false} />
        </foreignObject>
      </svg>

      <style jsx>{`
        .fb-spin-rev {
          animation: fb-rev 38s linear infinite;
        }
        @keyframes fb-rev {
          from { transform: rotate(360deg); }
          to { transform: rotate(0deg); }
        }
      `}</style>
    </div>
  );
}
