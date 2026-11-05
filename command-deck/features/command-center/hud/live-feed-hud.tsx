"use client";

import { Radio } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { HudCard } from "./hud-card";
import { StatusBadge } from "@/components/status/status-badge";
import { NEWS_EVENTS } from "@/lib/data/intelligence";
import { DESKS } from "@/lib/data/desks";
import { formatDaysAgoShort } from "@/lib/formatters/dates";
import type { NewsEvent } from "@/lib/types";

/** Latest sample intelligence events — live-styled, honestly labeled SAMPLE. */
export function LiveFeedHud({ className }: { className?: string }) {
  const { dict, locale } = useLocale();

  const dated = NEWS_EVENTS.filter((e): e is NewsEvent & { at: string } => e.at !== null);
  dated.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
  const latest = dated.slice(0, 4);

  return (
    <HudCard
      icon={Radio}
      title="Live Feed"
      titleFa={dict.intelligence.title}
      className={className}
      badge={<StatusBadge status="SAMPLE" size="sm" />}
    >
      <ul className="flex flex-col gap-2.5">
        {latest.map((event) => {
          const tone =
            event.impact === "HIGH"
              ? "bg-danger"
              : event.impact === "MEDIUM"
                ? "bg-warning"
                : "bg-accent";
          return (
            <li key={event.id} className="flex items-start gap-2.5">
              <span aria-hidden className={`mt-1.5 inline-block size-1.5 shrink-0 rounded-full ${tone}`} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[11px] font-bold leading-relaxed">{event.title[locale]}</p>
                <p className="mt-0.5 flex items-center gap-1.5 text-[9px] text-muted-foreground">
                  <span className="truncate">
                    {DESKS.find((d) => d.id === event.desks[0])?.name[locale] ?? event.desks[0]}
                  </span>
                  <span aria-hidden>·</span>
                  <time className="tnum shrink-0">{formatDaysAgoShort(event.at, locale)}</time>
                </p>
              </div>
              <StatusBadge status={event.provenance.status} size="sm" />
            </li>
          );
        })}
      </ul>
    </HudCard>
  );
}
