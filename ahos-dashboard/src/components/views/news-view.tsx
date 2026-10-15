"use client";

import { useMemo, useState } from "react";
import { CircleAlert, CircleCheck, OctagonAlert, Newspaper, Radio, Split, Workflow } from "lucide-react";
import type { DataEnvelope, NewsItem, Newsroom, VerificationState } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Chip } from "@/components/ui/chip";
import { Num, TimeAgo } from "@/components/ui/primitives";
import { Segmented } from "@/components/ui/segmented";
import { NewsStateChip, ProviderChip, StatusChip } from "@/components/ui/status";
import { Meter } from "@/components/ui/primitives";

type VFilter = "all" | VerificationState;

export function NewsView({ news }: { news: DataEnvelope<Newsroom> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const [filter, setFilter] = useState<VFilter>("all");
  const items = useMemo(() => news.data.items.filter((n) => filter === "all" || n.verification === filter), [news.data.items, filter]);
  const counts = { VERIFIED: 0, UNVERIFIED: 0, CONFLICTING: 0 } as Record<VerificationState, number>;
  news.data.items.forEach((n) => counts[n.verification]++);

  return (
    <PageBody>
      <PageHeader title={t.nav.items.news} subtitle={tx("خط لوله: دریافت ← حذف تکرار ← بازنویسی فارسی ← دسته‌بندی ← تأیید چندمنبعی ← انتشار", "Pipeline: ingest → dedupe → Persian rewrite → classify → cross-source verify → publish")} icon={Newspaper} />

      <DataCard title={tx("مراحل خط لوله", "Pipeline stages")} subtitle={tx("حجم ۲۴ ساعته، توان عملیاتی و صف هر مرحله", "24h volume, throughput and backlog per stage")} icon={Workflow} meta={news.meta}>
        <ol className="grid grid-cols-2 gap-2 @2xl:grid-cols-3 @5xl:grid-cols-6">
          {news.data.pipeline.map((s, i) => {
            const Icon = s.health === "ok" ? CircleCheck : s.health === "degraded" ? CircleAlert : OctagonAlert;
            return (
              <li key={s.id} className="relative">
                <div className={cn("glass-strong h-full rounded-[var(--radius-md)] border p-2.5", s.health === "ok" ? "border-[var(--line-subtle)]" : s.health === "degraded" ? "border-warn/40" : "border-down/40")}>
                  <div className="flex items-center gap-1.5">
                    <Num className="flex size-5 items-center justify-center rounded-full bg-gold-400/15 text-3xs font-bold text-gold-200">{f.num(i + 1, 0)}</Num>
                    <span className="flex-1 truncate text-2xs font-semibold text-fg-1">{l(s.label)}</span>
                    <Icon aria-label={s.health} className={cn("size-3.5", s.health === "ok" ? "text-up" : s.health === "degraded" ? "text-warn" : "text-down")} />
                  </div>
                  <Num className="mt-1.5 block text-lg font-semibold text-fg-1">{f.num(s.count, 0)}</Num>
                  <div className="flex justify-between text-3xs text-fg-4">
                    <span>{s.perHour === null ? "—" : `${f.num(s.perHour, 0)}/${tx("س", "h")}`}</span>
                    <span>
                      {tx("صف", "backlog")} <Num className={s.backlog > 20 ? "text-warn" : "text-fg-2"}>{f.num(s.backlog, 0)}</Num>
                    </span>
                  </div>
                  {s.note && <p className="mt-1 text-3xs text-warn">{l(s.note)}</p>}
                  <div className="relative mt-2 h-1 overflow-hidden rounded-full bg-white/[0.05]" aria-hidden>
                    <div className="absolute inset-y-0 w-1/3 rounded-full bg-gradient-to-r from-transparent via-data-400 to-transparent animate-shimmer motion-off:hidden" style={{ backgroundSize: "200% 100%" }} />
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </DataCard>

      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard
          className="@4xl:col-span-8"
          title={tx("خبرها", "Stories")}
          subtitle={tx("خبر متناقض تا رفع تناقض به‌عنوان واقعیت گزارش نمی‌شود", "Conflicting stories are not reported as fact until resolved")}
          icon={Radio}
          meta={news.meta}
          actions={
            <Segmented
              label={tx("وضعیت تأیید", "Verification state")}
              size="xs"
              value={filter}
              onChange={setFilter}
              options={[
                { value: "all", label: `${t.common.all} ${f.num(news.data.items.length, 0)}` },
                { value: "VERIFIED", label: `${t.newsState.VERIFIED} ${f.num(counts.VERIFIED, 0)}` },
                { value: "UNVERIFIED", label: `${t.newsState.UNVERIFIED} ${f.num(counts.UNVERIFIED, 0)}` },
                { value: "CONFLICTING", label: `${t.newsState.CONFLICTING} ${f.num(counts.CONFLICTING, 0)}` },
              ]}
            />
          }
        >
          <ul className="space-y-2">
            {items.map((n) => (
              <NewsRow key={n.id} n={n} />
            ))}
          </ul>
        </DataCard>

        <DataCard className="@4xl:col-span-4" title={tx("اعتبار منابع", "Source reliability")} subtitle={tx("امتیاز اعتبار بر اساس سابقه تأیید", "Reliability from verification history")} icon={Radio} meta={news.meta}>
          <ul className="space-y-2">
            {news.data.sources.map((s) => (
              <li key={s.source} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-2.5 py-2">
                <div className="flex items-center justify-between gap-2">
                  <bdi className="truncate text-2xs font-medium text-fg-1">{s.source}</bdi>
                  <ProviderChip status={s.status} />
                </div>
                <div className="mt-1.5 flex items-center gap-2">
                  <Meter value={s.reliability} max={1} tone={s.reliability !== null && s.reliability < 0.5 ? "warn" : "gold"} label={tx("اعتبار", "Reliability")} />
                  <Num className="w-10 text-end text-3xs text-fg-3">{s.reliability === null ? "—" : f.pct(s.reliability * 100, 0, false)}</Num>
                </div>
                <div className="mt-1 flex justify-between text-3xs text-fg-5">
                  <span>{s.language.toUpperCase()}</span>
                  <span>
                    {tx("۲۴س", "24h")}: <Num>{f.num(s.items24h, 0)}</Num>
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </DataCard>
      </div>
    </PageBody>
  );
}

function NewsRow({ n }: { n: NewsItem }) {
  const { l, tx } = useI18n();
  const stageLabel: Record<NewsItem["stage"], string> = {
    ingest: tx("دریافت", "Ingest"),
    dedupe: tx("حذف تکرار", "Dedupe"),
    translate: tx("ترجمه", "Translate"),
    classify: tx("دسته‌بندی", "Classify"),
    verify: tx("تأیید", "Verify"),
    publish: tx("منتشرشده", "Published"),
  };
  const importance = { HIGH: tx("اهمیت بالا", "High importance"), MED: tx("اهمیت متوسط", "Medium importance"), LOW: tx("اهمیت کم", "Low importance"), UNKNOWN: tx("اهمیت نامعلوم", "Importance unknown") };
  const sentiment = { POS: tx("مثبت", "Positive"), NEG: tx("منفی", "Negative"), NEU: tx("خنثی", "Neutral"), UNKNOWN: tx("نامعلوم", "Unknown") };
  return (
    <li className={cn("rounded-[var(--radius-lg)] border bg-white/[0.02] p-3 transition-colors hover:bg-white/[0.035]", n.verification === "CONFLICTING" ? "border-warn/35" : "border-[var(--line-subtle)]")}>
      <div className="flex flex-wrap items-center gap-1.5">
        <NewsStateChip state={n.verification} size="sm" />
        <Chip tone="muted">{l(n.category)}</Chip>
        <Chip tone={n.importance === "HIGH" ? "gold" : "muted"}>{importance[n.importance]}</Chip>
        <Chip tone={n.sentiment === "POS" ? "up" : n.sentiment === "NEG" ? "down" : n.sentiment === "UNKNOWN" ? "violet" : "slate"}>{sentiment[n.sentiment]}</Chip>
        <Chip tone="info" icon={Workflow}>{stageLabel[n.stage]}</Chip>
        <span className="ms-auto"><StatusChip status={n.status} /></span>
      </div>
      <h3 className="mt-2 text-sm font-semibold leading-snug text-fg-1">{l(n.title)}</h3>
      <p className="mt-1 text-2xs leading-relaxed text-fg-3">{l(n.summary)}</p>
      {n.verification === "CONFLICTING" && n.conflictNote && (
        <div className="mt-2 flex items-center gap-2 rounded-[var(--radius-md)] border border-dashed border-warn/40 bg-warn/[0.05] px-2.5 py-1.5 text-2xs text-warn">
          <Split aria-hidden className="size-3.5" />
          {l(n.conflictNote)}
        </div>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-3xs text-fg-4">
        <span>
          {tx("منبع", "Source")}: <bdi className="text-fg-2">{n.source}</bdi>
        </span>
        <span>
          {tx("تأییدکننده‌ها", "Corroborating")}: {n.corroboratingSources.length ? n.corroboratingSources.map((s) => <bdi key={s} className="me-1 text-fg-2">{s}</bdi>) : <span className="text-fg-5">{tx("هیچ", "none")}</span>}
        </span>
        {n.relatedAssets.length > 0 && (
          <span>
            {tx("دارایی‌ها", "Assets")}: {n.relatedAssets.map((a) => <bdi key={a} className="me-1 text-gold-200">{a}</bdi>)}
          </span>
        )}
        <TimeAgo iso={n.publishedAt} className="ms-auto" />
      </div>
    </li>
  );
}
