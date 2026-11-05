"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useLocale } from "@/components/providers/locale-provider";
import { useSettings } from "@/components/providers/settings-provider";
import { ChartFrame } from "@/components/visualization/chart-frame";
import { StatusBadge } from "@/components/status/status-badge";
import { EQUITY_SERIES, deskActivity, pnlHistogram } from "@/lib/data/series";
import { DESKS } from "@/lib/data/desks";
import { formatCompact, formatUsd, localizeDigits } from "@/lib/formatters/numbers";
import { formatDayShort, formatDate } from "@/lib/formatters/dates";
import { cn } from "@/lib/utils";

interface TooltipPayloadItem {
  payload: Record<string, unknown>;
}

function EquityTooltip({
  active,
  payload,
  locale,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  locale: "fa" | "en";
}) {
  if (!active || !payload?.[0]) return null;
  const row = payload[0].payload as { t: string; equity: number; drawdown: number };
  return (
    <div className="rounded-lg border border-border-strong bg-navy-900 px-3 py-2 text-[11px] shadow-panel light:bg-white">
      <p className="font-bold">{formatDate(row.t, locale)}</p>
      <p className="tnum mt-1 text-chart-1" dir="ltr">{formatUsd(row.equity, locale)}</p>
      <p className="tnum text-muted-foreground" dir="ltr">
        DD {row.drawdown >= 0 ? "0" : ""}{(row.drawdown * 100).toFixed(2)}%
      </p>
    </div>
  );
}

function PnlTooltip({
  active,
  payload,
  locale,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  locale: "fa" | "en";
}) {
  if (!active || !payload?.[0]) return null;
  const row = payload[0].payload as { from: number; to: number; count: number };
  return (
    <div className="rounded-lg border border-border-strong bg-navy-900 px-3 py-2 text-[11px] shadow-panel light:bg-white">
      <p className="tnum" dir="ltr">
        {formatUsd(row.from, locale)} → {formatUsd(row.to, locale)}
      </p>
      <p className="tnum mt-0.5 font-bold">
        {localizeDigits(String(row.count), locale)} {locale === "fa" ? "روز" : "days"}
      </p>
    </div>
  );
}

export function ChartsSection() {
  const { dict, locale } = useLocale();
  const { prefs } = useSettings();
  const gridStroke = prefs.chartGrid ? "rgb(var(--border) / 0.6)" : "transparent";
  const histogram = pnlHistogram(13);
  const activity = deskActivity();
  const maxSignals = Math.max(...(activity.value ?? []).map((r) => r.signals ?? 0), 1);

  const equityTable = (
    <table className="w-full text-[11px]">
      <thead className="sticky top-0 bg-card">
        <tr className="text-muted-foreground">
          <th className="px-2 py-1.5 text-start font-semibold">t</th>
          <th className="px-2 py-1.5 text-end font-semibold">equity (USD)</th>
          <th className="px-2 py-1.5 text-end font-semibold">drawdown</th>
        </tr>
      </thead>
      <tbody className="tnum">
        {EQUITY_SERIES.filter((_, i) => i % 7 === 0).map((row) => (
          <tr key={row.t} className="border-t border-border/50">
            <td className="px-2 py-1 text-start">{row.t}</td>
            <td className="px-2 py-1 text-end">{row.equity.toFixed(2)}</td>
            <td className="px-2 py-1 text-end">{(row.drawdown * 100).toFixed(2)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  const pnlTable = (
    <table className="w-full text-[11px]">
      <thead className="sticky top-0 bg-card">
        <tr className="text-muted-foreground">
          <th className="px-2 py-1.5 text-start font-semibold">bin from</th>
          <th className="px-2 py-1.5 text-end font-semibold">bin to</th>
          <th className="px-2 py-1.5 text-end font-semibold">days</th>
        </tr>
      </thead>
      <tbody className="tnum">
        {histogram.map((row, i) => (
          <tr key={i} className="border-t border-border/50">
            <td className="px-2 py-1 text-start">{row.from.toFixed(0)}</td>
            <td className="px-2 py-1 text-end">{row.to.toFixed(0)}</td>
            <td className="px-2 py-1 text-end">{row.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <section aria-label={dict.command.chartsTitle} className="grid gap-4 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <h3 className="mb-3 text-sm font-bold">{dict.command.chartsTitle}</h3>
      </div>

      <ChartFrame
        title={dict.command.equityTitle}
        summary={dict.command.equitySummary}
        status="SAMPLE"
        className="lg:col-span-2"
        heightClass="h-72"
        table={equityTable}
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={EQUITY_SERIES} margin={{ top: 6, right: 8, bottom: 0, left: 8 }}>
            <defs>
              <linearGradient id="eq-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="rgb(var(--chart-1))" stopOpacity={0.28} />
                <stop offset="100%" stopColor="rgb(var(--chart-1))" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="t"
              tickFormatter={(t: string) => formatDayShort(t, locale)}
              stroke="rgb(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: gridStroke }}
              minTickGap={48}
            />
            <YAxis
              tickFormatter={(v: number) => formatCompact(v, locale)}
              stroke="rgb(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              width={54}
              domain={["dataMin - 1500", "dataMax + 1500"]}
            />
            <Tooltip content={<EquityTooltip locale={locale} />} cursor={{ stroke: "rgb(var(--border-strong))" }} />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="rgb(var(--chart-1))"
              strokeWidth={2}
              fill="url(#eq-fill)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartFrame>

      <ChartFrame
        title={dict.command.pnlTitle}
        summary={dict.command.pnlSummary}
        status="SAMPLE"
        heightClass="h-64"
        table={pnlTable}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={histogram} margin={{ top: 6, right: 8, bottom: 0, left: 8 }} barCategoryGap="22%">
            <XAxis
              tickFormatter={(_v: string, i: number) => {
                const row = histogram[i];
                return row ? formatCompact(Math.round((row.from + row.to) / 2), locale) : "";
              }}
              stroke="rgb(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: gridStroke }}
              minTickGap={16}
            />
            <YAxis
              allowDecimals={false}
              stroke="rgb(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              width={30}
            />
            <Tooltip content={<PnlTooltip locale={locale} />} cursor={{ fill: "rgb(var(--muted) / 0.35)" }} />
            <Bar dataKey="count" isAnimationActive={false} radius={[4, 4, 0, 0]}>
              {histogram.map((row, i) => (
                <Cell
                  key={i}
                  fill={(row.from + row.to) / 2 >= 0 ? "rgb(var(--chart-4))" : "rgb(var(--danger))"}
                  fillOpacity={0.75}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartFrame>

      {/* desk activity — custom honest bars (NOT MEASURED instead of fake zero) */}
      <ChartFrame
        title={dict.command.activityTitle}
        summary={dict.command.activitySummary}
        status={activity.provenance.status}
        heightClass="h-64"
        table={
          <table className="w-full text-[11px]">
            <thead className="sticky top-0 bg-card">
              <tr className="text-muted-foreground">
                <th className="px-2 py-1.5 text-start font-semibold">desk</th>
                <th className="px-2 py-1.5 text-end font-semibold">signals/30d</th>
              </tr>
            </thead>
            <tbody className="tnum">
              {(activity.value ?? []).map((row) => (
                <tr key={row.deskId} className="border-t border-border/50">
                  <td className="px-2 py-1 text-start">{DESKS.find((d) => d.id === row.deskId)?.name.en ?? row.deskId}</td>
                  <td className="px-2 py-1 text-end">{row.signals === null ? "NOT MEASURED" : row.signals}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      >
        <div dir={locale === "fa" ? "rtl" : "ltr"} className="flex h-full flex-col justify-center gap-2.5 px-1">
          {(activity.value ?? []).map((row) => {
            const desk = DESKS.find((d) => d.id === row.deskId);
            const pct = row.signals === null ? 0 : (row.signals / maxSignals) * 100;
            return (
              <div key={row.deskId} className="flex items-center gap-3 text-[11px]">
                <span className="w-24 shrink-0 truncate font-semibold sm:w-32">{desk?.name[locale] ?? row.deskId}</span>
                <div className="relative h-4 flex-1 overflow-hidden rounded-md bg-muted/50">
                  {row.signals === null ? (
                    <span className="absolute inset-0 flex items-center justify-start gap-1.5 ps-2">
                      <span className="h-px w-5 bg-border-strong" aria-hidden />
                    </span>
                  ) : (
                    <span
                      className={cn("absolute inset-y-0 start-0 rounded-md bg-chart-2/70")}
                      style={{ width: `${Math.max(pct, 3)}%` }}
                    />
                  )}
                </div>
                {row.signals === null ? (
                  <StatusBadge status="NOT_MEASURED" size="sm" />
                ) : (
                  <span className="tnum w-8 text-end font-bold">{localizeDigits(String(row.signals), locale)}</span>
                )}
              </div>
            );
          })}
        </div>
      </ChartFrame>
    </section>
  );
}
