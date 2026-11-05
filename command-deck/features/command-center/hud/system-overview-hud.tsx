"use client";

import { Gauge } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { HudCard } from "./hud-card";
import { StatusBadge } from "@/components/status/status-badge";
import { Badge } from "@/components/ui/badge";
import { POSITIONS } from "@/lib/data/positions";
import { NEWS_EVENTS } from "@/lib/data/intelligence";
import { DESKS } from "@/lib/data/desks";
import { DATASET } from "@/lib/data/config";
import { localizeDigits } from "@/lib/formatters/numbers";
import type { ReactNode } from "react";

interface Row {
  icon: ReactNode;
  label: string;
  value: string;
  status: ReactNode;
}

/**
 * Honest SYSTEM OVERVIEW: measured app configuration + sample dataset facts.
 * Never claims an "Operational" state — the badge is PAPER-ONLY.
 */
export function SystemOverviewHud({ className }: { className?: string }) {
  const { dict, locale } = useLocale();

  const rows: Row[] = [
    {
      icon: "◆",
      label: dict.command.activeDesks,
      value: `${localizeDigits(String(DESKS.length), locale)}/${localizeDigits(String(DESKS.length), locale)}`,
      status: <StatusBadge status="MEASURED" size="sm" />,
    },
    {
      icon: "◆",
      label: dict.positions.title.replace(" — نمونه", ""),
      value: localizeDigits(String(POSITIONS.length), locale),
      status: <StatusBadge status="SAMPLE" size="sm" />,
    },
    {
      icon: "◆",
      label: dict.intelligence.title.split(" و ")[1] ?? dict.intelligence.title,
      value: localizeDigits(String(NEWS_EVENTS.length), locale),
      status: <StatusBadge status="SAMPLE" size="sm" />,
    },
    {
      icon: "◆",
      label: dict.strip.api,
      value: "—",
      status: <StatusBadge status="NOT_CONNECTED" size="sm" />,
    },
    {
      icon: "◆",
      label: dict.strip.soakWindow,
      value: "—",
      status: <StatusBadge status="NOT_MEASURED" size="sm" />,
    },
  ];

  return (
    <HudCard
      icon={Gauge}
      title="System Overview"
      titleFa={dict.command.kpiTitle}
      className={className}
      badge={
        <Badge variant="default" className="shrink-0 text-[9px]">
          {dict.common.paperOnly}
        </Badge>
      }
    >
      <ul className="flex flex-col gap-2">
        {rows.map((row, i) => (
          <li key={i} className="flex items-center gap-2.5 text-[11px]">
            <span aria-hidden className="text-[8px] text-primary/60">{row.icon}</span>
            <span className="min-w-0 flex-1 truncate text-muted-foreground">{row.label}</span>
            <span className="tnum text-sm font-extrabold text-foreground">
              {row.value}
            </span>
            {row.status}
          </li>
        ))}
      </ul>
      <p className="mt-2.5 border-t border-border/50 pt-2 font-mono text-[9px] text-subtle" dir="ltr">
        {DATASET.id} · {DATASET.asOf.slice(11, 16)} UTC
      </p>
    </HudCard>
  );
}
