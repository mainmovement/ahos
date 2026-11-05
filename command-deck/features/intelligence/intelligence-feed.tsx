"use client";

import { useMemo, useState } from "react";
import { ArrowDownRight, ArrowUpRight, CircleDashed, Minus, Newspaper } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { Panel, PanelContent, PanelHeader, PanelTitle, PanelDescription } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/status/status-badge";
import { EmptyState } from "@/components/status/empty-state";
import { MARKET_DRIVERS, NEWS_EVENTS } from "@/lib/data/intelligence";
import { DESKS } from "@/lib/data/desks";
import { localizeDigits, formatNumber } from "@/lib/formatters/numbers";
import { formatDateTime } from "@/lib/formatters/dates";
import type { ImpactLevel, NewsCategory } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORIES: NewsCategory[] = [
  "geopolitics",
  "central_banks",
  "macroeconomics",
  "whale_activity",
  "onchain",
  "exchanges",
  "regulatory",
  "commodity_supply",
];

export function IntelligenceFeed() {
  const { dict, locale } = useLocale();
  const [category, setCategory] = useState<"all" | NewsCategory>("all");
  const [impact, setImpact] = useState<"all" | ImpactLevel>("all");

  const events = useMemo(
    () =>
      NEWS_EVENTS.filter((e) => {
        if (category !== "all" && e.category !== category) return false;
        if (impact !== "all" && e.impact !== impact) return false;
        return true;
      }),
    [category, impact],
  );

  const driverDesks = useMemo(() => {
    const desks = new Map<string, typeof MARKET_DRIVERS>();
    for (const driver of MARKET_DRIVERS) {
      const list = desks.get(driver.deskId) ?? [];
      list.push(driver);
      desks.set(driver.deskId, list);
    }
    return [...desks.entries()];
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* filters */}
      <div className="flex flex-wrap items-center gap-2">
        <Select value={category} onValueChange={(v) => setCategory(v as typeof category)}>
          <SelectTrigger className="h-9 w-44" aria-label={dict.intelligence.filterAllCategories}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{dict.intelligence.filterAllCategories}</SelectItem>
            {CATEGORIES.map((c) => (
              <SelectItem key={c} value={c}>
                {dict.intelligence.categories[c]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={impact} onValueChange={(v) => setImpact(v as typeof impact)}>
          <SelectTrigger className="h-9 w-36" aria-label={dict.intelligence.filterAllImpacts}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{dict.intelligence.filterAllImpacts}</SelectItem>
            <SelectItem value="HIGH">{dict.intelligence.impactHigh}</SelectItem>
            <SelectItem value="MEDIUM">{dict.intelligence.impactMedium}</SelectItem>
            <SelectItem value="LOW">{dict.intelligence.impactLow}</SelectItem>
          </SelectContent>
        </Select>
        <p aria-live="polite" className="tnum ms-auto text-[11px] text-muted-foreground">
          {localizeDigits(String(events.length), locale)} {dict.intelligence.eventsCount}
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        {/* events */}
        <div className="flex min-w-0 flex-col gap-3">
          {events.length === 0 ? (
            <Panel>
              <EmptyState icon={Newspaper} title={dict.positions.emptyTitle} body={dict.positions.emptyBody} />
            </Panel>
          ) : (
            events.map((ev) => (
              <Panel key={ev.id} className="transition-shadow hover:shadow-panel-hover">
                <PanelContent className="flex flex-col gap-2.5">
                  <div className="flex flex-wrap items-center gap-2 text-[10px]">
                    <Badge variant="outline">{dict.intelligence.categories[ev.category]}</Badge>
                    <ImpactMeter level={ev.impact} />
                    <time className="tnum text-muted-foreground" dateTime={ev.at ?? undefined}>
                      {ev.at ? formatDateTime(ev.at, locale) : dict.intelligence.noTime}
                    </time>
                    <span className="ms-auto flex items-center gap-1.5">
                      <span className="text-muted-foreground">{dict.intelligence.evidenceLabel}:</span>
                      <StatusBadge status={ev.provenance.status} size="sm" />
                    </span>
                  </div>
                  <h3 className="text-sm font-bold leading-relaxed">{ev.title[locale]}</h3>
                  <p className="text-xs leading-relaxed text-muted-foreground">{ev.summary[locale]}</p>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-border/60 pt-2.5 text-[10px]">
                    <span className="flex flex-wrap items-center gap-1">
                      <span className="text-muted-foreground">{dict.intelligence.affectedDesks}:</span>
                      {ev.desks.map((d) => (
                        <Badge key={d} variant="muted" className="px-1.5">
                          {DESKS.find((desk) => desk.id === d)?.name[locale] ?? d}
                        </Badge>
                      ))}
                    </span>
                    <span className="ms-auto truncate font-mono text-subtle" dir="ltr">
                      {dict.intelligence.sourceLabel}: {ev.sourceLabel}
                    </span>
                  </div>
                </PanelContent>
              </Panel>
            ))
          )}
        </div>

        {/* driver board */}
        <div className="flex min-w-0 flex-col gap-4">
          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.intelligence.driversTitle}</PanelTitle>
              <PanelDescription>{dict.intelligence.driversNote}</PanelDescription>
            </PanelHeader>
            <PanelContent className="flex flex-col gap-4">
              {driverDesks.map(([deskId, drivers]) => (
                <div key={deskId}>
                  <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-subtle" dir="ltr">
                    {DESKS.find((d) => d.id === deskId)?.name.en ?? deskId}
                  </p>
                  <ul className="flex flex-col gap-2">
                    {drivers.map((driver) => (
                      <li key={driver.id} className="rounded-xl border border-border/60 bg-muted/20 p-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-[11px] font-bold leading-relaxed">{driver.name[locale]}</p>
                          <DriverDir dir={driver.direction} />
                        </div>
                        <div className="mt-1.5 flex items-center justify-between gap-2 text-[10px]">
                          <span className="text-muted-foreground">{dict.intelligence.weight}:</span>
                          {driver.weight.value !== null ? (
                            <span className="tnum font-bold" dir="ltr">
                              {formatNumber(driver.weight.value, "en", 2)}
                            </span>
                          ) : (
                            <StatusBadge status={driver.weight.provenance.status} size="sm" />
                          )}
                        </div>
                        <div className="mt-1.5 flex items-center justify-between gap-2 text-[10px]">
                          <span className="text-muted-foreground">{dict.intelligence.reading}:</span>
                          {driver.reading.value !== null ? (
                            <span className="tnum font-bold" dir="ltr">
                              {formatNumber(driver.reading.value, "en", 2)}
                              {driver.unit ? ` ${driver.unit}` : ""}
                            </span>
                          ) : (
                            <StatusBadge status={driver.reading.provenance.status} size="sm" />
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </PanelContent>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function ImpactMeter({ level }: { level: ImpactLevel }) {
  const { dict } = useLocale();
  const cls = level === "HIGH" ? "bg-danger" : level === "MEDIUM" ? "bg-warning" : "bg-accent";
  const label = level === "HIGH" ? dict.intelligence.impactHigh : level === "MEDIUM" ? dict.intelligence.impactMedium : dict.intelligence.impactLow;
  const filled = level === "HIGH" ? 3 : level === "MEDIUM" ? 2 : 1;
  return (
    <span className="inline-flex items-center gap-1" aria-label={`${dict.intelligence.impactLabel}: ${label}`}>
      <span aria-hidden className="flex items-center gap-0.5">
        {[1, 2, 3].map((i) => (
          <span key={i} className={cn("size-1.5 rounded-full", i <= filled ? cls : "bg-border-strong")} />
        ))}
      </span>
      <span className="font-bold text-muted-foreground">{label}</span>
    </span>
  );
}

function DriverDir({ dir }: { dir: "UP" | "DOWN" | "FLAT" | "UNKNOWN" }) {
  const { dict } = useLocale();
  if (dir === "UP") return <ArrowUpRight className="size-4 shrink-0 text-success" aria-label={dict.intelligence.dirUp} />;
  if (dir === "DOWN") return <ArrowDownRight className="size-4 shrink-0 text-danger" aria-label={dict.intelligence.dirDown} />;
  if (dir === "FLAT") return <Minus className="size-4 shrink-0 text-muted-foreground" aria-label={dict.intelligence.dirFlat} />;
  return <CircleDashed className="size-4 shrink-0 text-muted-foreground" aria-label={dict.intelligence.dirUnknown} />;
}
