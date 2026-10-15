"use client";

import { ArrowLeft, ArrowRight, LifeBuoy, Timer, TrendingDown, UserRound } from "lucide-react";
import type { DataEnvelope, ErrorStage, ErrorsOverview } from "@/lib/api/types";
import { ERROR_STAGES } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { StatTile } from "@/components/cards/blocks";
import { AreaSeriesChart } from "@/components/charts/charts";
import { Chip } from "@/components/ui/chip";
import { Num, TimeAgo } from "@/components/ui/primitives";
import { SeverityChip } from "@/components/ui/status";

const FLOW: ErrorStage[] = ["DETECTED", "TRIAGED", "DIAGNOSING", "RECOVERING", "VERIFYING", "RESOLVED"];

function StageTrack({ stage }: { stage: ErrorStage }) {
  const idx = FLOW.indexOf(stage);
  const escalated = stage === "ESCALATED";
  return (
    <div className="flex items-center gap-0.5" aria-hidden>
      {FLOW.map((s, i) => (
        <span key={s} className={cn("h-1.5 w-4 rounded-full", escalated ? (i <= 1 ? "bg-down/70" : "bg-white/[0.06]") : i < idx ? "bg-gold-500/70" : i === idx ? (stage === "RESOLVED" ? "bg-up" : "bg-gold-300 shadow-[0_0_6px_var(--color-gold-300)]") : "bg-white/[0.06]")} />
      ))}
    </div>
  );
}

export function ErrorsView({ errors }: { errors: DataEnvelope<ErrorsOverview> }) {
  const { t, tx, dir, l } = useI18n();
  const f = useFormat();
  const d = errors.data;
  const counts = Object.fromEntries(ERROR_STAGES.map((s) => [s, d.incidents.filter((i) => i.stage === s).length])) as Record<ErrorStage, number>;
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const open = d.incidents.filter((i) => i.stage !== "RESOLVED").length;
  return (
    <PageBody>
      <PageHeader title={t.nav.items.errors} subtitle={tx("چرخه حیات بازیابی: شناسایی ← تریاژ ← عیب‌یابی ← بازیابی ← راستی‌آزمایی ← حل", "Recovery lifecycle: detect → triage → diagnose → recover → verify → resolve")} icon={LifeBuoy} />
      <DataCard title={tx("مراحل چرخه حیات", "Lifecycle stages")} subtitle={tx("هر خطا تا راستی‌آزمایی بازیابی «حل‌شده» نیست", "No error is resolved until recovery is verified")} icon={LifeBuoy} meta={errors.meta}>
        <ol className="flex flex-wrap items-stretch gap-1.5">
          {FLOW.map((s, i) => (
            <li key={s} className="flex items-center gap-1.5">
              <div className={cn("min-w-[110px] rounded-[var(--radius-md)] border px-3 py-2", counts[s] ? "border-gold-400/35 bg-gold-400/[0.06]" : "border-[var(--line-subtle)] bg-white/[0.02]")}>
                <div className="text-3xs text-fg-4">
                  <Num>{f.num(i + 1, 0)}</Num> · {t.errorStage[s]}
                </div>
                <Num className="text-lg font-semibold text-fg-1">{f.num(counts[s], 0)}</Num>
              </div>
              {i < FLOW.length - 1 && <Arrow aria-hidden className="size-3.5 text-gold-500/60" />}
            </li>
          ))}
          <li className="flex items-center gap-1.5">
            <span aria-hidden className="mx-1 h-8 w-px bg-white/10" />
            <div className="min-w-[110px] rounded-[var(--radius-md)] border border-down/40 bg-down/[0.06] px-3 py-2">
              <div className="flex items-center gap-1 text-3xs text-down">
                <UserRound aria-hidden className="size-3" />
                {t.errorStage.ESCALATED}
              </div>
              <Num className="text-lg font-semibold text-fg-1">{f.num(counts.ESCALATED, 0)}</Num>
            </div>
          </li>
        </ol>
      </DataCard>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <div className="grid grid-cols-2 gap-3 @4xl:col-span-4 @4xl:grid-cols-1">
          <StatTile label={tx("خطاهای باز", "Open errors")} value={f.num(open, 0)} tone="down" icon={<LifeBuoy className="size-3" />} />
          <StatTile label={tx("میانگین زمان بازیابی (MTTR)", "Mean time to recover (MTTR)")} value={d.mttrMinutes === null ? "—" : `${f.num(d.mttrMinutes, 0)} ${tx("دقیقه", "min")}`} icon={<Timer className="size-3" />} tone="gold" />
        </div>
        <DataCard className="@4xl:col-span-8" title={tx("روند خطا — ۲۴ ساعت", "Error trend — 24h")} icon={TrendingDown} meta={errors.meta}>
          <AreaSeriesChart points={d.trend} height={170} label={tx("روند خطا", "Error trend")} color="down" />
        </DataCard>
      </div>
      <DataCard title={tx("رخدادهای خطا", "Error incidents")} icon={LifeBuoy} meta={errors.meta} bodyClassName="px-0 pb-0">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("شناسه", "ID")}</th>
                <th scope="col">{tx("عنوان", "Title")}</th>
                <th scope="col">{tx("شدت", "Severity")}</th>
                <th scope="col">{tx("مرحله", "Stage")}</th>
                <th scope="col">{tx("جزء / نوع", "Component / type")}</th>
                <th scope="col" className="num-cell">{tx("تلاش مجدد", "Retries")}</th>
                <th scope="col">{tx("اقدام بازیابی", "Recovery action")}</th>
                <th scope="col">{tx("مسئول", "Owner")}</th>
                <th scope="col" className="pe-3.5">{t.common.updated}</th>
              </tr>
            </thead>
            <tbody>
              {d.incidents.map((i) => (
                <tr key={i.id}>
                  <td className="ps-3.5"><bdi className="mono text-3xs text-fg-4">{i.id}</bdi></td>
                  <td className="max-w-[220px] truncate text-2xs text-fg-1">{l(i.title)}</td>
                  <td><SeverityChip severity={i.severity} /></td>
                  <td>
                    <div className="flex flex-col gap-1">
                      <Chip tone={i.stage === "RESOLVED" ? "up" : i.stage === "ESCALATED" ? "down" : "gold"}>{t.errorStage[i.stage]}</Chip>
                      <StageTrack stage={i.stage} />
                    </div>
                  </td>
                  <td className="text-3xs text-fg-3">
                    <bdi className="mono">{i.component}</bdi>
                    <div className="text-fg-5"><bdi>{i.errorType}</bdi></div>
                  </td>
                  <td className="num-cell"><Num className="text-2xs text-fg-2">{f.num(i.retries, 0)}</Num></td>
                  <td className="max-w-[220px] whitespace-normal text-3xs text-fg-3">{l(i.recovery)}</td>
                  <td className="text-3xs text-fg-4">{i.owner === "human" ? <Chip tone="warn" icon={UserRound}>{tx("انسان", "Human")}</Chip> : <bdi className="mono">{i.owner.replace("agent.", "")}</bdi>}</td>
                  <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={i.updatedAt} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataCard>
    </PageBody>
  );
}
