"use client";

import { useId } from "react";
import { cn } from "@/lib/utils";

/**
 * AHOS Lion & Sun emblem — original artwork drawn for this project.
 * A geometric heraldic lion beneath a twelve-ray sun, inside a double ring
 * with eight cardinal ticks. Metallic-gold treatment; identity, not glitter.
 */
export function Emblem({
  className,
  animated = true,
  title = "AHOS",
}: {
  className?: string;
  animated?: boolean;
  title?: string;
}) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const goldId = `g-${uid}`;
  const sunId = `s-${uid}`;
  const glowId = `gl-${uid}`;

  return (
    <svg
      viewBox="0 0 256 256"
      role="img"
      aria-label={title}
      className={cn("select-none", className)}
      focusable="false"
    >
      <defs>
        <linearGradient id={goldId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#F6E7B8" />
          <stop offset="45%" stopColor="#D4AF37" />
          <stop offset="100%" stopColor="#8C6A1F" />
        </linearGradient>
        <radialGradient id={sunId} cx="50%" cy="42%" r="65%">
          <stop offset="0%" stopColor="#FFF7DC" />
          <stop offset="55%" stopColor="#F3D27A" />
          <stop offset="100%" stopColor="#B08F2A" />
        </radialGradient>
        <filter id={glowId} x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3.2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* rings + ticks */}
      <circle cx="128" cy="128" r="122" fill="none" stroke={`url(#${goldId})`} strokeWidth="3" />
      <circle cx="128" cy="128" r="112" fill="none" stroke={`url(#${goldId})`} strokeWidth="1" opacity="0.5" />
      <g stroke={`url(#${goldId})`} strokeWidth="2" opacity="0.9">
        {Array.from({ length: 8 }, (_, i) => (
          <line key={i} x1="128" y1="8" x2="128" y2="16" transform={`rotate(${i * 45} 128 128)`} />
        ))}
      </g>

      {/* sun */}
      <g filter={animated ? `url(#${glowId})` : undefined} transform="translate(0 -4)">
        <g fill={`url(#${goldId})`}>
          {Array.from({ length: 12 }, (_, i) => (
            <path key={`l${i}`} d="M128 40 L134.5 62 L121.5 62 Z" transform={`rotate(${i * 30} 128 96)`} opacity="0.95" />
          ))}
          {Array.from({ length: 12 }, (_, i) => (
            <path key={`s${i}`} d="M128 54 L132.5 66 L123.5 66 Z" transform={`rotate(${15 + i * 30} 128 96)`} opacity="0.8" />
          ))}
        </g>
        <circle cx="128" cy="96" r="25" fill={`url(#${sunId})`} stroke="#8C6A1F" strokeWidth="1.4" />
        <circle cx="128" cy="96" r="17" fill="none" stroke="#8C6A1F" strokeWidth="0.8" opacity="0.55" />
      </g>

      {/* lion — angular heraldic silhouette, passant, facing dexter */}
      <g fill={`url(#${goldId})`} stroke={`url(#${goldId})`} strokeWidth="1" strokeLinejoin="round">
        <path d="M76 128 L88 113 L98 105 L104 111 L112 107 L120 115 L128 109 L136 117 L146 121 L160 125 L176 123 L184 129 L188 139 L184 157 L192 169 L180 173 L172 159 L160 151 L136 147 L124 151 L120 165 L126 173 L112 175 L112 159 L104 145 L96 133 L80 135 Z" />
        {/* ear notch */}
        <path d="M98 105 L103 99 L107 107 Z" fill="#0B1020" opacity="0.28" stroke="none" />
        {/* eye */}
        <circle cx="90" cy="119" r="1.6" fill="#0B1020" opacity="0.55" stroke="none" />
      </g>
      {/* tail */}
      <path
        d="M182 128 C194 120 199 106 191 95"
        fill="none"
        stroke={`url(#${goldId})`}
        strokeWidth="4.5"
        strokeLinecap="round"
      />
      <path d="M185 96 L197 88 L195 102 Z" fill={`url(#${goldId})`} />

      {/* plinth arc */}
      <path
        d="M54 196 Q128 210 202 196"
        fill="none"
        stroke={`url(#${goldId})`}
        strokeWidth="1.6"
        opacity="0.55"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** Emblem + wordmark lockup for headers and the hero. */
export function BrandLockup({
  emblemClassName,
  className,
  compact = false,
}: {
  emblemClassName?: string;
  className?: string;
  compact?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <Emblem className={cn("size-10", emblemClassName)} animated={false} />
      {!compact ? (
        <span className="flex flex-col leading-tight">
          <span className="gold-text text-lg font-extrabold tracking-wide" dir="ltr">
            AHOS
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground" dir="ltr">
            Intelligence Command Deck
          </span>
        </span>
      ) : null}
    </span>
  );
}
