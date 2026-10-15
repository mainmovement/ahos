"use client";

import { Archive, Brain, CircleSlash, Hourglass, LineChart, Sparkles } from "lucide-react";
import type { DataEnvelope, MemoryOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Notice, StatTile } from "@/components/cards/blocks";
import { LinesChart } from "@/components/charts/charts";
import { Chip } from "@/components/ui/chip";
import { TimeAgo } from "@/components/ui/primitives";
import { ConfidenceChip } from "@/components/ui/status";

export function MemoryView({ memory }: { memory: DataEnvelope<MemoryOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const d = memory.data;
  const kind = { lesson: tx("درس", "Lesson"), pattern: tx("الگو", "Pattern"), "source-trust": tx("اعتماد منبع", "Source trust"), calibration: tx("کالیبراسیون", "Calibration") } as const;
  const state = { CANDIDATE: { label: tx("نامزد", "Candidate"), tone: "info", icon: Hourglass }, PROMOTED: { label: tx("ارتقایافته", "Promoted"), tone: "gold", icon: Sparkles }, REVOKED: { label: tx("لغوشده", "Revoked"), tone: "down", icon: CircleSlash }, EXPIRED: { label: tx("منقضی", "Expired"), tone: "muted", icon: Archive } } as const;
  return (
    <PageBody>
      <PageHeader title={t.nav.items.memory} subtitle={tx("حافظه سازمانی، درس‌ها و منحنی‌های یادگیری", "Organizational memory, lessons and learning curves")} icon={Brain} />
      <Notice icon={<Brain />} tone="violet">
        <b>PROMOTED ≠ TRUTH.</b> {tx("حافظه ارتقایافته فقط یعنی برای استفاده مجاز شده؛ همچنان قابل لغو است و تاریخ انقضا دارد.", "A promoted memory is only approved for use; it remains revocable and expires.")}
      </Notice>
      <section className="grid grid-cols-2 gap-3 @4xl:grid-cols-4">
        <StatTile label={state.CANDIDATE.label} value={f.num(d.counts.candidates, 0)} />
        <StatTile label={state.PROMOTED.label} value={f.num(d.counts.promoted, 0)} tone="gold" />
        <StatTile label={state.REVOKED.label} value={f.num(d.counts.revoked, 0)} tone="down" />
        <StatTile label={state.EXPIRED.label} value={f.num(d.counts.expired, 0)} />
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-7" title={tx("اقلام حافظه", "Memory items")} icon={Archive} meta={memory.meta}>
          <ul className="space-y-2">
            {d.items.map((m) => {
              const s = state[m.state];
              return (
                <li key={m.id} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <Chip tone={s.tone} icon={s.icon}>{s.label}</Chip>
                    <Chip tone="muted">{kind[m.kind]}</Chip>
                    <ConfidenceChip confidence={m.confidence} />
                    <TimeAgo iso={m.at} className="ms-auto text-3xs text-fg-5" />
                  </div>
                  <p className="mt-1.5 text-2xs text-fg-1">{l(m.title)}</p>
                  <p className="mt-0.5 text-3xs text-fg-4">
                    {t.common.source}: <bdi>{m.source}</bdi>
                  </p>
                </li>
              );
            })}
          </ul>
        </DataCard>
        <DataCard className="@4xl:col-span-5" title={tx("منحنی‌های یادگیری", "Learning curves")} subtitle={tx("۳۰ روز — دقت فیلتر و خطای کالیبراسیون", "30 days — filter precision and calibration error")} icon={LineChart} meta={memory.meta}>
          <LinesChart series={d.learning} height={300} label={tx("منحنی یادگیری", "Learning curves")} valueFormat={(v) => f.num(v, 3)} />
        </DataCard>
      </div>
    </PageBody>
  );
}
