import { useId } from "react";
import { cn } from "@/lib/utils";

/**
 * AHOS emblem — glossy black disc, gold rim, five-point gold star holding a
 * stylised figure (ball head + teardrop body). Pure SVG, no raster assets.
 */
export function AhosLogo({ size = 36, className, glow = true }: { size?: number; className?: string; glow?: boolean }) {
  const uid = useId().replace(/:/g, "");
  const g = (n: string) => `${n}-${uid}`;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" className={cn("shrink-0", className)} role="img" aria-label="AHOS">
      <defs>
        <radialGradient id={g("halo")} cx="50%" cy="50%" r="50%">
          <stop offset="55%" stopColor="#e6bf5f" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#e6bf5f" stopOpacity="0" />
        </radialGradient>
        <radialGradient id={g("disc")} cx="42%" cy="34%" r="70%">
          <stop offset="0%" stopColor="#23232b" />
          <stop offset="55%" stopColor="#0b0b10" />
          <stop offset="100%" stopColor="#000" />
        </radialGradient>
        <linearGradient id={g("rim")} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fff3cf" />
          <stop offset="30%" stopColor="#e6bf5f" />
          <stop offset="65%" stopColor="#8c6a25" />
          <stop offset="100%" stopColor="#f0d27e" />
        </linearGradient>
        <linearGradient id={g("star")} x1="0.2" y1="0" x2="0.8" y2="1">
          <stop offset="0%" stopColor="#fff6d8" />
          <stop offset="38%" stopColor="#f0d27e" />
          <stop offset="72%" stopColor="#c9952f" />
          <stop offset="100%" stopColor="#7a5a1c" />
        </linearGradient>
        <filter id={g("blur")} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.2" />
        </filter>
      </defs>
      {glow && <circle cx="32" cy="32" r="31" fill={`url(#${g("halo")})`} className="origin-center animate-pulse-soft motion-off:animate-none" />}
      <circle cx="32" cy="32" r="27.5" fill={`url(#${g("disc")})`} />
      <ellipse cx="29" cy="18" rx="15" ry="7" fill="#fff" opacity="0.06" />
      <circle cx="32" cy="32" r="27.5" fill="none" stroke={`url(#${g("rim")})`} strokeWidth="2.2" />
      <circle cx="32" cy="32" r="24.2" fill="none" stroke="#e6bf5f" strokeOpacity="0.28" strokeWidth="0.6" />
      {glow && (
        <path
          d="M32 15.6 L36.82 26.87 L48.17 28.25 L39.8 36.03 L41.99 47.25 L32 41.7 L22.01 47.25 L24.2 36.03 L15.83 28.25 L27.18 26.87 Z"
          fill="#f0d27e"
          opacity="0.55"
          filter={`url(#${g("blur")})`}
        />
      )}
      <path
        d="M32 15.6 L36.82 26.87 L48.17 28.25 L39.8 36.03 L41.99 47.25 L32 41.7 L22.01 47.25 L24.2 36.03 L15.83 28.25 L27.18 26.87 Z"
        fill={`url(#${g("star")})`}
        stroke="#fff3cf"
        strokeOpacity="0.55"
        strokeWidth="0.5"
        strokeLinejoin="round"
      />
      <circle cx="32" cy="27.3" r="2.65" fill="#0a0a0e" />
      <path d="M32 30.7 C35.5 34.2 35.9 38.3 32 40.6 C28.1 38.3 28.5 34.2 32 30.7 Z" fill="#0a0a0e" />
    </svg>
  );
}
