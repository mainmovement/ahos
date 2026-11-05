"use client";

import { ArrowDownRight, ArrowUpRight, CircleDashed } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { Panel, PanelContent } from "@/components/ui/panel";
import { ProvenanceChip, StatusBadge } from "@/components/status/status-badge";
import { cn } from "@/lib/utils";
import { formatPercent, formatSignedUsd, formatUsd, localizeDigits } from "@/lib/formatters/numbers";
import {
  ACTIVE_DESKS,
  COMMAND_KPIS,
  LATEST_DAY_PNL,
  OPEN_POSITIONS,
  PAPER_EQUITY,
  SECURITY_STATUS,
  WIN_RATE,
} from "@/lib/data/kpi";
import { EQUITY_SERIES } from "@/lib/data/series";
import { closedWinRate } from "@/lib/data/positions";
import { GLOBAL_SAMPLE_SHARE } from "@/lib/data";
import { BACKEND_CONNECTION_STATUS } from "@/lib/adapters/ahos-adapter";
import type { ReactNode } from "react";

function Sparkline({ values, stroke }: { values: number[]; stroke: string }) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const points = values
    .map((v, i) => `${(i / (values.length - 1)) * 100},${28 - ((v - min) / range) * 24}`)
    .join(" ");
  return (
    <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="h-8 w-full" aria-hidden>
      <polyline points={points} fill="none" stroke={stroke} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function KpiCard({
  label,
  note,
  value,
  badge,
  extra,
  accent = false,
}: {
  label: string;
  note?: string;
  value: ReactNode;
  badge: ReactNode;
  extra?: ReactNode;
  accent?: boolean;
}) {
  return (
    <Panel className={cn("relative overflow-hidden", accent && "border-primary/30")}>
      {accent ? <span aria-hidden className="absolute inset-x-0 top-0 h-px bg-gradient-to-l from-transparent via-primary/60 to-transparent" /> : null}
      <PanelContent className="flex h-full flex-col gap-2">
        <div className="flex items-start justify-between gap-2">
          <p className="text-xs font-semibold text-muted-foreground">{label}</p>
          {badge}
        </div>
        <div className="mt-auto flex items-end justify-between gap-2">
          <div className="min-w-0">
            <p className="tnum truncate text-2xl font-extrabold leading-tight">{value}</p>
            {note ? <p className="mt-1 text-[10px] leading-relaxed text-subtle">{note}</p> : null}
          </div>
          {extra}
        </div>
      </PanelContent>
    </Panel>
  );
}

export function KpiGrid() {
  const { dict, locale } = useLocale();
  const win = closedWinRate();
  const lastEquity = EQUITY_SERIES[EQUITY_SERIES.length - 1]?.equity ?? 0;
  const prevEquity = EQUITY_SERIES[EQUITY_SERIES.length - 2]?.equity ?? lastEquity;
  const pnl = LATEST_DAY_PNL.value ?? 0;
  const pnlPositive = pnl >= 0;

  return (
    <section aria-label={dict.command.kpiTitle} className="mb-8">
      <div className="mb-3 flex items-center gap-3">
        <h3 className="text-sm font-bold">{dict.command.kpiTitle}</h3>
        <span className="text-[11px] text-muted-foreground">{dict.command.kpiNote}</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          accent
          label={dict.command.paperEquity}
          note={dict.command.paperEquityNote}
          value={formatUsd(PAPER_EQUITY.value ?? 0, locale)}
          badge={<ProvenanceChip envelope={PAPER_EQUITY} />}
          extra={
            <div className="w-20 shrink-0">
              <Sparkline values={EQUITY_SERIES.slice(-32).map((s) => s.equity)} stroke="rgb(var(--chart-1))" />
              <p className={cn("tnum text-end text-[10px] font-bold", pnlPositive ? "text-success" : "text-danger")} dir="ltr">
                {lastEquity >= prevEquity ? "▲" : "▼"} {formatPercent(Math.abs(((lastEquity - prevEquity) / prevEquity) * 100), locale, 2)}
              </p>
            </div>
          }
        />

        <KpiCard
          label={dict.command.dailyPnl}
          note={dict.command.dailyPnlNote}
          value={
            <span className={pnlPositive ? "text-success" : "text-danger"}>
              {formatSignedUsd(pnl, locale)}
            </span>
          }
          badge={<ProvenanceChip envelope={LATEST_DAY_PNL} />}
          extra={
            pnlPositive ? (
              <ArrowUpRight className="size-5 shrink-0 text-success" aria-hidden />
            ) : (
              <ArrowDownRight className="size-5 shrink-0 text-danger" aria-hidden />
            )
          }
        />

        <KpiCard
          label={dict.command.winRate}
          note={`${dict.command.winRateNote} — ${localizeDigits(String(win.wins), locale)}/${localizeDigits(String(win.computable), locale)}`}
          value={formatPercent((WIN_RATE.value ?? 0) * 100, locale, 1)}
          badge={<ProvenanceChip envelope={WIN_RATE} />}
        />

        <KpiCard
          label={dict.command.openPositions}
          note={dict.command.openPositionsNote}
          value={localizeDigits(String(OPEN_POSITIONS.value ?? 0), locale)}
          badge={<ProvenanceChip envelope={OPEN_POSITIONS} />}
        />

        {/* Brier score: NOT MEASURED — no calibration evidence exists, by law */}
        <KpiCard
          label={dict.command.brier}
          note={dict.command.brierNote}
          value={<span className="text-muted-foreground">{dict.common.valueMissing}</span>}
          badge={<StatusBadge status="NOT_MEASURED" />}
        />

        <KpiCard
          label={dict.command.activeDesks}
          note={dict.command.activeDesksNote}
          value={localizeDigits(String(ACTIVE_DESKS.value ?? 0), locale)}
          badge={<ProvenanceChip envelope={ACTIVE_DESKS} />}
        />

        <KpiCard
          label={dict.command.securityStatus}
          note={dict.command.securityStatusNote}
          value={<span className="inline-flex items-center gap-1.5 text-base font-bold text-muted-foreground"><CircleDashed className="size-4" aria-hidden />{dict.status.UNKNOWN}</span>}
          badge={<ProvenanceChip envelope={SECURITY_STATUS} />}
        />

        {/* provenance summary */}
        <Panel>
          <PanelContent className="flex h-full flex-col gap-2">
            <p className="text-xs font-semibold text-muted-foreground">{dict.command.provenanceTitle}</p>
            <ul className="mt-auto flex flex-col gap-1.5 text-[11px]">
              <li className="flex items-center justify-between gap-2">
                <StatusBadge status="SAMPLE" size="sm" />
                <span className="tnum font-bold">{localizeDigits(String(GLOBAL_SAMPLE_SHARE.sample), locale)}</span>
              </li>
              <li className="flex items-center justify-between gap-2">
                <StatusBadge status="NOT_MEASURED" size="sm" />
                <span className="tnum font-bold">{localizeDigits(String(GLOBAL_SAMPLE_SHARE.notMeasured), locale)}</span>
              </li>
              <li className="flex items-center justify-between gap-2">
                <StatusBadge status={BACKEND_CONNECTION_STATUS} size="sm" />
                <span className="tnum font-bold">{localizeDigits(String(GLOBAL_SAMPLE_SHARE.notConnected), locale)}</span>
              </li>
              <li className="flex items-center justify-between gap-2">
                <StatusBadge status="MEASURED" size="sm" />
                <span className="tnum font-bold">1</span>
              </li>
            </ul>
          </PanelContent>
        </Panel>
      </div>
      <p className="sr-only">{COMMAND_KPIS.length} indicator cards</p>
    </section>
  );
}
