"use client";

import Link from "next/link";
import { ArrowRight, ArrowLeft, Clock, Funnel } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { Panel, PanelContent } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { ProvenanceChip, StatusBadge } from "@/components/status/status-badge";
import { SignalBadge } from "@/components/status/signal-badge";
import { Sparkline } from "@/components/visualization/sparkline";
import { DESKS } from "@/lib/data/desks";
import { navHref } from "@/lib/nav";
import { cn } from "@/lib/utils";
import { formatDaysRelativeToDataset } from "@/lib/formatters/dates";
import { formatScore, localizeDigits } from "@/lib/formatters/numbers";

export function DesksGrid() {
  const { dict, locale } = useLocale();
  const isRtl = locale === "fa";

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {DESKS.map((desk) => {
        const featured = desk.priority === "PRIORITY";
        const signal = desk.signal.value ?? "UNKNOWN";
        return (
          <Panel
            key={desk.id}
            className={cn(
              "group relative flex flex-col transition-shadow hover:shadow-panel-hover",
              featured && "border-primary/35",
            )}
          >
            {featured ? (
              <span aria-hidden className="absolute inset-x-0 top-0 h-px bg-gradient-to-l from-transparent via-primary/70 to-transparent" />
            ) : null}
            <PanelContent className="flex h-full flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="truncate text-base font-extrabold">{desk.name[locale]}</h3>
                    <Badge variant={featured ? "default" : "muted"} className="shrink-0">
                      {featured ? dict.desks.priorityHigh : dict.desks.standard}
                    </Badge>
                  </div>
                  <p className="mt-1 truncate font-mono text-[10px] text-subtle" dir="ltr">
                    {desk.instruments.join(" · ")}
                  </p>
                </div>
                <SignalBadge state={signal} />
              </div>

              <div className="rounded-xl border border-border/60 bg-muted/20 p-2.5">
                {desk.sparkline.value ? (
                  <Sparkline
                    values={desk.sparkline.value}
                    stroke={featured ? "rgb(var(--chart-2))" : "rgb(var(--chart-1))"}
                    fill
                  />
                ) : (
                  <div className="flex h-10 items-center justify-start gap-2 px-1">
                    <span className="h-px w-8 bg-border-strong" aria-hidden />
                    <StatusBadge status={desk.sparkline.provenance.status} size="sm" />
                  </div>
                )}
              </div>

              <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-[11px]">
                <div>
                  <dt className="text-muted-foreground">{dict.desks.score}</dt>
                  <dd className="mt-0.5 flex items-center gap-1.5">
                    {desk.score.value ? (
                      <span className="tnum text-sm font-extrabold" dir="ltr">
                        {formatScore(desk.score.value.value, locale)}
                      </span>
                    ) : (
                      <span className="font-bold text-muted-foreground">{dict.common.valueMissing}</span>
                    )}
                    <ProvenanceChip envelope={desk.score} />
                  </dd>
                </div>
                <div>
                  <dt className="flex items-center gap-1 text-muted-foreground">
                    <Clock className="size-3" aria-hidden />
                    {dict.desks.lastObservation}
                  </dt>
                  <dd className="mt-0.5">
                    {desk.lastObservation.value ? (
                      <time className="tnum" dateTime={desk.lastObservation.value}>
                        {formatDaysRelativeToDataset(desk.lastObservation.value, locale)}
                      </time>
                    ) : (
                      <StatusBadge status={desk.lastObservation.provenance.status} size="sm" />
                    )}
                  </dd>
                </div>
              </dl>

              <div className="mt-auto flex items-center justify-between gap-2 border-t border-border/60 pt-3">
                <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <Funnel className="size-3.5" aria-hidden />
                  {dict.desks.alerts}: <span className="tnum font-bold text-foreground">{localizeDigits(String(desk.alertCount.value ?? 0), locale)}</span>
                  <ProvenanceChip envelope={desk.alertCount} />
                </span>
                <Link
                  href={navHref(locale, `/desks/${desk.id}`)}
                  className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-bold text-primary transition-colors hover:bg-primary/10"
                >
                  {dict.desks.openDesk}
                  {isRtl ? <ArrowLeft className="size-3.5" aria-hidden /> : <ArrowRight className="size-3.5" aria-hidden />}
                </Link>
              </div>
            </PanelContent>
          </Panel>
        );
      })}
    </div>
  );
}
