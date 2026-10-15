"use client";

import type { DataMeta, Kpi } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { ICONS } from "@/components/ui/icon";
import { Delta, Num } from "@/components/ui/primitives";
import { StatusChip } from "@/components/ui/status";
import { Tip } from "@/components/ui/tooltip";
import { Sparkline } from "@/components/charts/sparkline";
import { CardFooter } from "./data-card";

/** KPI card: label, value, delta, sparkline and provenance footer. */
export function KpiCard({ kpi, meta, className }: { kpi: Kpi; meta: DataMeta; className?: string }) {
  const { l } = useI18n();
  const f = useFormat();
  const Icon = ICONS[kpi.icon];
  const value = f.value(kpi.value, kpi.format, kpi.decimals);
  const sparkColor = kpi.polarity === "up-good" && (kpi.delta ?? 0) < 0 ? "var(--color-down)" : "var(--color-data-400)";
  return (
    <article className={cn("glass gold-border card-sheen group flex min-w-0 flex-col transition-shadow duration-[var(--dur-base)] hover:shadow-[var(--shadow-glow-sm)]", className)} aria-label={l(kpi.label)}>
      <div className="flex items-start gap-2 px-3 pt-2.5">
        <Icon aria-hidden className="mt-0.5 size-3.5 shrink-0 text-gold-300" />
        <Tip content={kpi.hint ? l(kpi.hint) : null}>
          <h3 tabIndex={kpi.hint ? 0 : undefined} className="line-clamp-2 min-h-[2rem] min-w-0 flex-1 text-2xs font-medium leading-4 text-fg-3">
            {l(kpi.label)}
          </h3>
        </Tip>
        {meta.isMock && <StatusChip status="DEMO" showLabel={false} />}
      </div>
      <div className="flex items-end justify-between gap-2 px-3 pt-1">
        <Num className={cn("text-[1.45rem] font-semibold leading-none tracking-tight text-fg-1", kpi.value === null && "text-fg-4")}>{value}</Num>
        <div className="flex flex-col items-end gap-0.5 pb-0.5">
          <Delta value={kpi.delta} polarity={kpi.polarity} size="xs" />
          <span className="text-3xs text-fg-5">{l(kpi.deltaWindow)}</span>
        </div>
      </div>
      <div className="px-1 pb-1 pt-1.5">
        <Sparkline data={kpi.spark} color={sparkColor} height={30} label={`${l(kpi.label)} — ${value}`} />
      </div>
      <CardFooter meta={{ ...meta, status: kpi.status }} compact />
    </article>
  );
}
