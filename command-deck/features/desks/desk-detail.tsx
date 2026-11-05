"use client";

import Link from "next/link";
import { useMemo } from "react";
import {
  ArrowRight,
  ArrowLeft,
  CircleSlash,
  LineChart as LineChartIcon,
  CandlestickChart,
  ShieldQuestion,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useLocale } from "@/components/providers/locale-provider";
import { Panel, PanelContent, PanelHeader, PanelTitle, PanelDescription } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProvenanceChip, StatusBadge } from "@/components/status/status-badge";
import { SignalBadge } from "@/components/status/signal-badge";
import { ProvenancePanel } from "@/components/status/provenance-panel";
import { EmptyState } from "@/components/status/empty-state";
import { Sparkline } from "@/components/visualization/sparkline";
import { CandleChart } from "@/components/visualization/candle-chart";
import { getDesk } from "@/lib/data/desks";
import { candlesFor, deskScoreHistory, deskSparkline } from "@/lib/data/series";
import { deskSignals } from "@/lib/data/signals";
import { SECURITY_BY_DESK } from "@/lib/data/security";
import { MARKET_DRIVERS, NEWS_EVENTS } from "@/lib/data/intelligence";
import { notFound } from "next/navigation";
import { navHref } from "@/lib/nav";
import { formatDateTime, formatDaysRelativeToDataset, formatDayShort } from "@/lib/formatters/dates";
import { formatNumber, formatScore, localizeDigits } from "@/lib/formatters/numbers";
import { cn } from "@/lib/utils";

type DeskDetailProps = { deskId: string };

export function DeskDetail({ deskId }: DeskDetailProps) {
  const { dict, locale } = useLocale();
  const desk = getDesk(deskId);
  if (!desk) notFound();

  const candles = useMemo(() => candlesFor(desk.id), [desk.id]);
  const spark = useMemo(() => deskSparkline(desk.id), [desk.id]);
  const scoreHist = useMemo(() => deskScoreHistory(desk.id), [desk.id]);
  const signals = useMemo(() => deskSignals(desk.id), [desk.id]);
  const security = SECURITY_BY_DESK[desk.id];
  const drivers = MARKET_DRIVERS.filter((d) => d.deskId === desk.id);
  const news = NEWS_EVENTS.filter((e) => e.desks.includes(desk.id));
  const isRtl = locale === "fa";

  return (
    <div className="flex flex-col gap-4">
      {/* header */}
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="outline" size="sm" asChild>
          <Link href={navHref(locale, "/desks")}>
            {isRtl ? <ArrowRight aria-hidden /> : <ArrowLeft aria-hidden />}
            {dict.deskDetail.back}
          </Link>
        </Button>
        <span aria-hidden className="text-border-strong">/</span>
        <h2 className="text-lg font-extrabold">{desk.name[locale]}</h2>
        <Badge variant={desk.priority === "PRIORITY" ? "default" : "muted"}>
          {desk.priority === "PRIORITY" ? dict.desks.priorityHigh : dict.desks.standard}
        </Badge>
        <span className="font-mono text-[10px] text-subtle" dir="ltr">
          {desk.instruments.join(" · ")}
        </span>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        {/* main column */}
        <div className="flex min-w-0 flex-col gap-4">
          {/* market chart */}
          <Panel>
            <PanelHeader>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <PanelTitle>{dict.deskDetail.marketChart}</PanelTitle>
                  <PanelDescription>
                    {candles.value ? `${candles.value.symbol} — ${localizeDigits("90", locale)} ${dict.health.days}` : dict.deskDetail.candleUnsupported}
                  </PanelDescription>
                </div>
                <ProvenanceChip envelope={candles.value ? candles : spark} />
              </div>
            </PanelHeader>
            <PanelContent>
              {candles.value ? (
                <Tabs defaultValue="candles">
                  <TabsList>
                    <TabsTrigger value="candles">
                      <CandlestickChart aria-hidden />
                      {dict.deskDetail.candles}
                    </TabsTrigger>
                    <TabsTrigger value="line">
                      <LineChartIcon aria-hidden />
                      {dict.deskDetail.line}
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="candles">
                    <div className="relative">
                      <span aria-hidden className="pointer-events-none absolute end-2 top-1 z-10 -rotate-6 select-none text-lg font-extrabold tracking-[0.3em] text-foreground/[0.06]" dir="ltr">
                        SAMPLE
                      </span>
                      <CandleChart bars={candles.value.bars} />
                    </div>
                  </TabsContent>
                  <TabsContent value="line">
                    <div className="h-72" dir="ltr">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={candles.value.bars.map((b) => ({ t: b.time, close: b.close }))}>
                          <defs>
                            <linearGradient id="desk-line-fill" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="rgb(var(--chart-1))" stopOpacity={0.25} />
                              <stop offset="100%" stopColor="rgb(var(--chart-1))" stopOpacity={0.02} />
                            </linearGradient>
                          </defs>
                          <XAxis dataKey="t" tickFormatter={(t: string) => formatDayShort(t, locale)} tick={{ fontSize: 10 }} stroke="rgb(var(--muted-foreground))" tickLine={false} minTickGap={48} />
                          <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10 }} stroke="rgb(var(--muted-foreground))" tickLine={false} width={56} tickFormatter={(v: number) => formatNumber(v, "en", 0)} />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (!active || !payload?.[0]) return null;
                              const row = payload[0].payload as { t: string; close: number };
                              return (
                                <div className="rounded-lg border border-border-strong bg-navy-900 px-2.5 py-1.5 text-[11px] light:bg-white">
                                  <p className="font-bold" dir="ltr">{formatNumber(row.close, "en", 2)}</p>
                                  <p className="text-muted-foreground">{row.t}</p>
                                </div>
                              );
                            }}
                          />
                          <Area type="monotone" dataKey="close" stroke="rgb(var(--chart-1))" strokeWidth={1.8} fill="url(#desk-line-fill)" isAnimationActive={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </TabsContent>
                </Tabs>
              ) : spark.value ? (
                <div className="h-56">
                  <Sparkline values={spark.value} className="h-full" fill />
                </div>
              ) : (
                <EmptyState
                  icon={CircleSlash}
                  title={dict.status.NOT_MEASURED}
                  body={dict.reason.no_measurement}
                />
              )}
            </PanelContent>
          </Panel>

          {/* signal timeline */}
          <Panel>
            <PanelHeader>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <PanelTitle>{dict.deskDetail.signalTimeline}</PanelTitle>
                <ProvenanceChip envelope={signals} />
              </div>
            </PanelHeader>
            <PanelContent>
              {signals.value ? (
                <ol className="relative flex flex-col gap-0 border-s border-border/70 ps-5">
                  {signals.value.map((sig) => (
                    <li key={sig.id} className="relative pb-4 last:pb-0">
                      <span aria-hidden className="absolute -start-[26px] top-1.5 size-2.5 rounded-full border-2 border-background bg-primary/70" />
                      <div className="flex flex-wrap items-center gap-2">
                        <SignalBadge state={sig.state} size="sm" />
                        <time className="tnum text-[11px] text-muted-foreground" dateTime={sig.at ?? undefined}>
                          {sig.at ? formatDateTime(sig.at, locale) : dict.intelligence.noTime}
                        </time>
                        <span className="tnum text-[11px] text-muted-foreground">
                          {dict.desks.score}: <span className="font-bold text-foreground" dir="ltr">{formatScore(sig.score.value?.value ?? 0, locale)}</span>
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{sig.basis[locale]}</p>
                    </li>
                  ))}
                </ol>
              ) : (
                <EmptyState icon={CircleSlash} title={dict.status.NOT_MEASURED} body={dict.reason.no_measurement} />
              )}
            </PanelContent>
          </Panel>

          {/* drivers */}
          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.deskDetail.driversSection}</PanelTitle>
              <PanelDescription>{dict.intelligence.driversNote}</PanelDescription>
            </PanelHeader>
            <PanelContent className="grid gap-3 sm:grid-cols-2">
              {drivers.map((driver) => (
                <div key={driver.id} className="rounded-xl border border-border/70 bg-muted/20 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-bold leading-relaxed">{driver.name[locale]}</p>
                    <DriverDirection dir={driver.direction} />
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-muted" dir="ltr">
                      {driver.weight.value !== null ? (
                        <span
                          className={cn(
                            "absolute inset-y-0 rounded-full",
                            driver.weight.value >= 0 ? "bg-success/70 left-1/2" : "bg-danger/70 right-1/2",
                          )}
                          style={{ width: `${Math.abs(driver.weight.value) * 50}%` }}
                        />
                      ) : null}
                      <span aria-hidden className="absolute inset-y-0 left-1/2 w-px bg-border-strong" />
                    </div>
                    {driver.weight.value !== null ? (
                      <span className="tnum text-[10px] font-bold" dir="ltr">
                        {formatNumber(driver.weight.value, "en", 2)}
                      </span>
                    ) : (
                      <StatusBadge status={driver.weight.provenance.status} size="sm" />
                    )}
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-2 text-[11px]">
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
                  <p className="mt-2 border-t border-border/50 pt-2 text-[10px] leading-relaxed text-subtle">
                    {driver.explanation[locale]}
                  </p>
                </div>
              ))}
            </PanelContent>
          </Panel>

          {/* news */}
          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.deskDetail.newsSection}</PanelTitle>
            </PanelHeader>
            <PanelContent className="flex flex-col gap-2.5">
              {news.length === 0 ? (
                <EmptyState icon={CircleSlash} title={dict.deskDetail.noNews} />
              ) : (
                news.slice(0, 4).map((ev) => (
                  <div key={ev.id} className="rounded-xl border border-border/70 bg-muted/20 p-3">
                    <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground">
                      <Badge variant="muted">{dict.intelligence.categories[ev.category]}</Badge>
                      <time className="tnum">{ev.at ? formatDateTime(ev.at, locale) : dict.intelligence.noTime}</time>
                      <StatusBadge status={ev.provenance.status} size="sm" />
                    </div>
                    <p className="mt-1.5 text-xs font-bold leading-relaxed">{ev.title[locale]}</p>
                  </div>
                ))
              )}
            </PanelContent>
          </Panel>
        </div>

        {/* rail */}
        <div className="flex min-w-0 flex-col gap-4">
          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.deskDetail.overview}</PanelTitle>
            </PanelHeader>
            <PanelContent className="flex flex-col gap-3 text-xs">
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">{dict.desks.signal}</span>
                <span className="flex items-center gap-1.5">
                  <SignalBadge state={desk.signal.value ?? "UNKNOWN"} size="sm" />
                  <ProvenanceChip envelope={desk.signal} />
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">{dict.desks.score}</span>
                <span className="flex items-center gap-1.5">
                  {desk.score.value ? (
                    <span className="tnum font-extrabold" dir="ltr">{formatScore(desk.score.value.value, locale)}</span>
                  ) : (
                    <StatusBadge status={desk.score.provenance.status} size="sm" />
                  )}
                  <ProvenanceChip envelope={desk.score} />
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">{dict.desks.lastObservation}</span>
                {desk.lastObservation.value ? (
                  <time className="tnum" dateTime={desk.lastObservation.value}>
                    {formatDaysRelativeToDataset(desk.lastObservation.value, locale)}
                  </time>
                ) : (
                  <StatusBadge status={desk.lastObservation.provenance.status} size="sm" />
                )}
              </div>
              <p className="rounded-lg border border-warning/30 bg-warning/5 p-2.5 text-[10px] leading-relaxed text-warning">
                {dict.deskDetail.scoreNote}
              </p>
            </PanelContent>
          </Panel>

          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.deskDetail.evidencePanel}</PanelTitle>
            </PanelHeader>
            <PanelContent className="flex flex-col gap-2.5">
              <ProvenancePanel provenance={desk.signal.provenance} title={dict.desks.signal} />
              <ProvenancePanel provenance={(candles.value ? candles : spark).provenance} title={dict.deskDetail.marketChart} />
            </PanelContent>
          </Panel>

          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.deskDetail.securitySection}</PanelTitle>
              <ProvenanceChip envelope={{ value: null, provenance: security.provenance }} />
            </PanelHeader>
            <PanelContent className="flex flex-col gap-2">
              <ul className="flex flex-col gap-1.5">
                {security.checks.map((check) => (
                  <li key={check.id} className="flex items-center justify-between gap-2 rounded-lg border border-border/60 bg-muted/20 px-2.5 py-1.5 text-[11px]">
                    <span className="inline-flex items-center gap-1.5">
                      <ShieldQuestion className="size-3.5 text-muted-foreground" aria-hidden />
                      {check.name[locale]}
                    </span>
                    <StatusBadge status={check.status} size="sm" />
                  </li>
                ))}
              </ul>
              <p className="text-[10px] leading-relaxed text-muted-foreground">{dict.deskDetail.securityNotMeasured}</p>
            </PanelContent>
          </Panel>

          <Panel>
            <PanelHeader>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <PanelTitle>{dict.deskDetail.scoreHistory}</PanelTitle>
                <ProvenanceChip envelope={scoreHist} />
              </div>
            </PanelHeader>
            <PanelContent>
              <div className="h-40" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={scoreHist.value ?? []}>
                    <XAxis dataKey="t" tickFormatter={() => ""} tick={false} stroke="rgb(var(--border))" />
                    <YAxis domain={[0, 1]} ticks={[0, 0.5, 1]} tick={{ fontSize: 9 }} stroke="rgb(var(--muted-foreground))" tickLine={false} width={28} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload?.[0]) return null;
                        const row = payload[0].payload as { t: string; score: number };
                        return (
                          <div className="rounded-lg border border-border-strong bg-navy-900 px-2.5 py-1.5 text-[11px] light:bg-white">
                            <p className="tnum font-bold" dir="ltr">{formatScore(row.score, "en")}</p>
                            <p className="text-muted-foreground">{row.t.slice(0, 10)} · {row.t.slice(11, 16)}</p>
                          </div>
                        );
                      }}
                    />
                    <Line type="monotone" dataKey="score" stroke="rgb(var(--chart-3))" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-2 text-[10px] leading-relaxed text-subtle">{dict.deskDetail.scoreNote}</p>
            </PanelContent>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function DriverDirection({ dir }: { dir: "UP" | "DOWN" | "FLAT" | "UNKNOWN" }) {
  const { dict } = useLocale();
  const map = {
    UP: { label: dict.intelligence.dirUp, cls: "text-success" },
    DOWN: { label: dict.intelligence.dirDown, cls: "text-danger" },
    FLAT: { label: dict.intelligence.dirFlat, cls: "text-muted-foreground" },
    UNKNOWN: { label: dict.intelligence.dirUnknown, cls: "text-muted-foreground" },
  } as const;
  const entry = map[dir];
  return (
    <span className={cn("shrink-0 text-[10px] font-extrabold", entry.cls)} dir="auto">
      {entry.label}
    </span>
  );
}
