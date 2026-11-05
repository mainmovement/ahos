"use client";

import { Activity } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { HudCard } from "./hud-card";
import { StatusBadge } from "@/components/status/status-badge";

/**
 * SYSTEM HEALTH — three instrument rings that honestly report NOT MEASURED.
 * The rings are drawn as empty instrument tracks (no percentage, no value):
 * unknown health is never rendered as healthy.
 */
export function HealthRingsHud({ className }: { className?: string }) {
  const { dict } = useLocale();

  const rings = [
    { label: dict.strip.api, seed: 0.2 },
    { label: dict.strip.soakWindow, seed: 0.55 },
    { label: dict.health.resourcesTitle, seed: 0.8 },
  ];
  const R = 26;
  const C = 2 * Math.PI * R;

  return (
    <HudCard
      icon={Activity}
      title="System Health"
      titleFa={dict.command.healthTitle}
      className={className}
    >
      <div className="grid grid-cols-3 gap-2">
        {rings.map((ring) => (
          <div key={ring.label} className="flex flex-col items-center gap-1.5">
            <div className="relative">
              <svg viewBox="0 0 64 64" className="size-16 -rotate-90" aria-hidden>
                <circle
                  cx="32"
                  cy="32"
                  r={R}
                  fill="none"
                  stroke="rgb(148 163 184 / 0.22)"
                  strokeWidth="4"
                  strokeDasharray={`${C * ring.seed * 0.72} ${C}`}
                  strokeLinecap="round"
                  className="text-muted-foreground"
                />
                <circle
                  cx="32"
                  cy="32"
                  r={R}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="4"
                  strokeDasharray="2 5"
                  opacity="0.5"
                  className="text-subtle"
                />
              </svg>
              <span
                className="absolute inset-0 grid place-items-center font-latin text-sm font-extrabold text-muted-foreground"
                dir="ltr"
              >
                —
              </span>
            </div>
            <span className="line-clamp-2 text-center text-[9px] leading-tight text-muted-foreground">
              {ring.label}
            </span>
            <span className="sr-only">{dict.status.NOT_MEASURED}</span>
          </div>
        ))}
      </div>
      <p className="mt-2 flex items-start gap-1.5 border-t border-border/50 pt-2 text-[9px] leading-relaxed text-subtle">
        <StatusBadge status="NOT_MEASURED" size="sm" />
        <span>{dict.health.ramBody}</span>
      </p>
    </HudCard>
  );
}
