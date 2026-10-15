"use client";

/**
 * Reusable data blocks shared by market / intelligence pages.
 */
import type { ReactNode } from "react";
import { ArrowDownRight, ArrowLeftRight, ArrowUpRight, Compass, Gauge as GaugeIcon, Network } from "lucide-react";
import type { DataMeta, DriverNote, Instrument, Mover, ProviderHealth, SectorPerf } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/ui/chip";
import { Delta, Num, TimeAgo } from "@/components/ui/primitives";
import { ConfidenceChip, ProviderChip, StatusChip } from "@/components/ui/status";
import { Sparkline } from "@/components/charts/sparkline";
import { SectorTreemap } from "@/components/charts/charts";
import { DataCard } from "./data-card";

/* ------------------------------------------------------- stat tile */

export function StatTile({ label, value, delta, hint, icon, className, tone }: { label: string; value: ReactNode; delta?: number | null; hint?: ReactNode; icon?: ReactNode; className?: string; tone?: "gold" | "data" | "down" | "up" }) {
  return (
    <div className={cn("rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.025] px-3 py-2.5", className)}>
      <div className="flex items-center gap-1.5 text-3xs text-fg-4">
        {icon}
        <span className="truncate">{label}</span>
      </div>
      <div className="mt-1 flex items-baseline justify-between gap-2">
        <span className={cn("num text-lg font-semibold leading-none", tone === "gold" ? "text-gold-100" : tone === "data" ? "text-data-300" : tone === "down" ? "text-down" : tone === "up" ? "text-up" : "text-fg-1")} dir="ltr">
          {value}
        </span>
        {delta !== undefined && <Delta value={delta} size="xs" />}
      </div>
      {hint && <div className="mt-1 text-3xs text-fg-5">{hint}</div>}
    </div>
  );
}

/* --------------------------------------------------- instrument tile */

export function InstrumentTile({ i, onSelect, selected }: { i: Instrument; onSelect?: () => void; selected?: boolean }) {
  const { l } = useI18n();
  const f = useFormat();
  const Comp = onSelect ? "button" : "div";
  return (
    <Comp
      type={onSelect ? "button" : undefined}
      onClick={onSelect}
      aria-pressed={onSelect ? selected : undefined}
      className={cn(
        "glass gold-border flex min-w-0 flex-col p-3 text-start transition-shadow",
        onSelect && "hover:shadow-[var(--shadow-glow-sm)]",
        selected && "shadow-[var(--shadow-glow-md)] ring-1 ring-gold-400/40",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <bdi className="block text-xs font-semibold text-fg-1">{i.symbol}</bdi>
          <span className="block truncate text-3xs text-fg-4">{l(i.name)}</span>
        </div>
        <StatusChip status={i.status} />
      </div>
      <div className="mt-2 flex items-baseline justify-between gap-2">
        <Num className={cn("text-base font-semibold", i.price === null ? "text-fg-4" : "text-fg-1")}>{f.num(i.price, i.decimals, i.decimals)}</Num>
        <Delta value={i.change24h} size="xs" />
      </div>
      <div className="mt-1">
        <Sparkline data={i.spark} height={26} color={(i.change24h ?? 0) >= 0 ? "var(--color-data-400)" : "var(--color-down)"} label={`${i.symbol}`} />
      </div>
      <div className="mt-1 flex items-center justify-between text-3xs text-fg-5">
        <span dir="ltr">{i.quote}</span>
        <TimeAgo iso={i.retrievedAt} />
      </div>
    </Comp>
  );
}

/* ------------------------------------------------------ drivers card */

export function DriversCard({ drivers, meta, title, className }: { drivers: DriverNote[]; meta: DataMeta; title?: string; className?: string }) {
  const { l, tx } = useI18n();
  const icon = { up: ArrowUpRight, down: ArrowDownRight, mixed: ArrowLeftRight } as const;
  const tone = { up: "text-up", down: "text-down", mixed: "text-warn" } as const;
  const dirLabel = { up: tx("صعودی", "Upward"), down: tx("نزولی", "Downward"), mixed: tx("دوسویه", "Mixed") } as const;
  return (
    <DataCard title={title ?? tx("محرک‌های قیمت", "Price drivers")} subtitle={tx("ادعا با سطح اطمینان — نه پیش‌بینی", "Claims with confidence — not forecasts")} icon={Compass} meta={meta} className={className}>
      <ul className="space-y-1.5">
        {drivers.map((d) => {
          const Icon = icon[d.direction];
          return (
            <li key={d.id} className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-2.5 py-2">
              <Icon aria-hidden className={cn("size-4 shrink-0", tone[d.direction])} />
              <span className="min-w-0 flex-1 text-2xs text-fg-1">{l(d.title)}</span>
              <span className="sr-only">{dirLabel[d.direction]}</span>
              <ConfidenceChip confidence={d.confidence} />
            </li>
          );
        })}
      </ul>
    </DataCard>
  );
}

/* --------------------------------------------------- sector heatmap */

export function SectorHeatmapCard({ sectors, meta, title, className, height = 250 }: { sectors: SectorPerf[]; meta: DataMeta; title?: string; className?: string; height?: number }) {
  const { l, tx } = useI18n();
  return (
    <DataCard title={title ?? tx("نقشه حرارتی بخش‌ها", "Sector heatmap")} subtitle={tx("اندازه = وزن · رنگ و برچسب = تغییر", "Size = weight · colour and label = change")} icon={Network} meta={meta} className={className}>
      <SectorTreemap items={sectors.map((s) => ({ name: l(s.name), weight: s.weight, change: s.change }))} height={height} label={title ?? tx("نقشه حرارتی بخش‌ها", "Sector heatmap")} />
    </DataCard>
  );
}

/* ------------------------------------------------------ movers table */

export function MoversCard({ gainers, losers, meta, className }: { gainers: Mover[]; losers: Mover[]; meta: DataMeta; className?: string }) {
  const { tx, l, t } = useI18n();
  const f = useFormat();
  const table = (rows: Mover[], caption: string) => (
    <table className="data-table">
      <caption className="px-1 pb-1 text-start text-3xs font-semibold text-fg-3">{caption}</caption>
      <thead>
        <tr>
          <th scope="col">{t.common.symbol}</th>
          <th scope="col" className="num-cell">{t.common.price}</th>
          <th scope="col" className="num-cell">{t.common.change}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((m) => (
          <tr key={m.symbol}>
            <td>
              <bdi className="block text-2xs font-semibold text-fg-1">{m.symbol}</bdi>
              <span className="block max-w-[120px] truncate text-3xs text-fg-4">
                <bdi>{m.name}</bdi> · {l(m.sector)}
              </span>
            </td>
            <td className="num-cell">
              <Num className="text-2xs text-fg-2">{f.num(m.price, 2)}</Num>
            </td>
            <td className="num-cell">
              <Delta value={m.change} size="xs" />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
  return (
    <DataCard title={tx("بیشترین تغییرات", "Top movers")} subtitle={tx("رشد و افت روزانه (نمایشی)", "Daily gainers and losers (demo)")} icon={GaugeIcon} meta={meta} className={className}>
      <div className="grid grid-cols-1 gap-3 @3xl:grid-cols-2">
        {table(gainers, tx("بیشترین رشد", "Top gainers"))}
        {table(losers, tx("بیشترین افت", "Top losers"))}
      </div>
    </DataCard>
  );
}

/* -------------------------------------------------- provider table */

export function ProviderHealthCard({ providers, meta, className, title }: { providers: ProviderHealth[]; meta: DataMeta; className?: string; title?: string }) {
  const { tx, l, t } = useI18n();
  const f = useFormat();
  return (
    <DataCard title={title ?? tx("سلامت منابع داده", "Data provider health")} subtitle={tx("وضعیت هر پروب — UNKNOWN یعنی بدون شواهد", "Per-probe status — UNKNOWN means no evidence")} icon={Network} meta={meta} className={className} bodyClassName="px-0 pb-0">
      <div className="max-h-[380px] overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col" className="ps-3.5">{t.common.source}</th>
              <th scope="col">{t.common.status}</th>
              <th scope="col" className="num-cell">{tx("تأخیر", "Latency")}</th>
              <th scope="col" className="num-cell">{tx("دسترس‌پذیری", "Availability")}</th>
              <th scope="col" className="pe-3.5">{tx("آخرین موفقیت", "Last success")}</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.name}>
                <td className="ps-3.5">
                  <bdi className="block text-2xs font-medium text-fg-1">{p.name}</bdi>
                  <span className="text-3xs text-fg-4">{l(p.category)}</span>
                </td>
                <td>
                  <ProviderChip status={p.status} />
                </td>
                <td className="num-cell">
                  <Num className="text-2xs text-fg-2">{p.latencyMs === null ? "—" : `${f.num(p.latencyMs, 0)} ms`}</Num>
                </td>
                <td className="num-cell">
                  <Num className="text-2xs text-fg-2">{p.availability === null ? "—" : f.pct(p.availability * 100, 1, false)}</Num>
                </td>
                <td className="pe-3.5 text-3xs text-fg-4">{p.lastSuccess ? <TimeAgo iso={p.lastSuccess} /> : <Chip tone="muted">{t.common.never}</Chip>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DataCard>
  );
}

/* ---------------------------------------------------- notice banner */

export function Notice({ icon, children, tone = "gold", className }: { icon?: ReactNode; children: ReactNode; tone?: "gold" | "warn" | "info" | "violet"; className?: string }) {
  const tones = {
    gold: "border-gold-400/25 bg-gold-400/[0.05] text-gold-100",
    warn: "border-warn/30 bg-warn/[0.06] text-fg-1",
    info: "border-info/30 bg-info/[0.06] text-fg-1",
    violet: "border-violet/30 bg-violet/[0.06] text-fg-1",
  } as const;
  return (
    <div role="note" className={cn("flex items-start gap-2.5 rounded-[var(--radius-lg)] border px-3.5 py-2.5 text-2xs leading-relaxed", tones[tone], className)}>
      {icon && <span className="mt-0.5 shrink-0 [&_svg]:size-4">{icon}</span>}
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
