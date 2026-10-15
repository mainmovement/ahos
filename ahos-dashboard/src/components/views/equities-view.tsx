"use client";

import { Building2, Coins, Landmark, Scale, TrendingUp } from "lucide-react";
import type { DataEnvelope, EquitiesBoard, EquityRegion } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { useNowMinute } from "@/lib/time/now";
import { EXCHANGES, formatCountdown, sessionState } from "@/lib/time/sessions";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { InstrumentTile, MoversCard, SectorHeatmapCard } from "@/components/cards/blocks";
import { LinesChart } from "@/components/charts/charts";
import { Chip } from "@/components/ui/chip";
import { Num } from "@/components/ui/primitives";
import { Tip } from "@/components/ui/tooltip";

const META: Record<EquityRegion, { icon: typeof Landmark; key: "equitiesUs" | "equitiesEu" | "equitiesAsia"; sub: { fa: string; en: string } }> = {
  us: { icon: Landmark, key: "equitiesUs", sub: { fa: "شاخص‌های اصلی وال‌استریت، بخش‌ها و بیشترین تغییرات", en: "Wall Street benchmarks, sectors and top movers" } },
  eu: { icon: Building2, key: "equitiesEu", sub: { fa: "استاکس، دکس، کک و فوتسی — بخش‌ها و بیشترین تغییرات", en: "STOXX, DAX, CAC and FTSE — sectors and top movers" } },
  asia: { icon: Coins, key: "equitiesAsia", sub: { fa: "نیکی، هنگ‌سنگ، شانگهای، کوسپی، نیفتی و بورس تهران", en: "Nikkei, Hang Seng, Shanghai, KOSPI, Nifty and Tehran" } },
};

/** Shared template for the three regional equities pages. */
export function EquitiesView({ board }: { board: DataEnvelope<EquitiesBoard> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const minute = useNowMinute();
  const d = board.data;
  const m = META[d.region];
  const sessions = minute === null ? [] : d.exchanges.map((id) => EXCHANGES.find((e) => e.id === id)).filter((e): e is NonNullable<typeof e> => !!e).map((e) => sessionState(e, new Date(minute)));
  const total = d.breadth ? d.breadth.advancers + d.breadth.decliners + d.breadth.unchanged : 0;

  return (
    <PageBody>
      <PageHeader
        title={t.nav.items[m.key]}
        subtitle={l(m.sub)}
        icon={m.icon}
        actions={
          <div className="flex flex-wrap items-center gap-1.5">
            {sessions.map((s) => (
              <Tip key={s.exchange.id} content={`${t.topbar.estimated}`}>
                <span tabIndex={0}>
                  <Chip tone={s.open ? "up" : "slate"} size="sm">
                    {l(s.exchange.name)} · {s.open ? t.topbar.open : t.topbar.closed} · {f.digits(formatCountdown(s.minutesToChange))}
                  </Chip>
                </span>
              </Tip>
            ))}
          </div>
        }
      />
      <section aria-label={tx("شاخص‌ها", "Indices")} className="grid grid-cols-2 gap-3 @2xl:grid-cols-3 @4xl:grid-cols-4 @6xl:grid-cols-6">
        {d.indices.map((i) => (
          <InstrumentTile key={i.id} i={i} />
        ))}
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("عملکرد نسبی شاخص‌ها", "Relative index performance")} subtitle={tx("تغییر درصدی از ابتدای بازه — ۱۲۰ روز", "% change from period start — 120 days")} icon={TrendingUp} meta={board.meta}>
          <LinesChart series={d.performance} height={300} label="index performance" normalize percentAxis />
        </DataCard>
        <DataCard className="@4xl:col-span-4" title={tx("پهنای بازار", "Market breadth")} subtitle={tx("تعداد نمادهای مثبت، منفی و بدون تغییر", "Advancers, decliners, unchanged")} icon={Scale} meta={board.meta}>
          {d.breadth ? (
            <div className="space-y-3">
              <div className="flex h-3 overflow-hidden rounded-full" role="img" aria-label={tx("نسبت پهنای بازار", "Breadth ratio")}>
                <div className="bg-up/80" style={{ width: `${(d.breadth.advancers / total) * 100}%` }} />
                <div className="bg-fg-5" style={{ width: `${(d.breadth.unchanged / total) * 100}%` }} />
                <div className="bg-down/80" style={{ width: `${(d.breadth.decliners / total) * 100}%` }} />
              </div>
              <dl className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-[var(--radius-sm)] bg-up/[0.08] py-2">
                  <dt className="text-3xs text-up">▲ {tx("مثبت", "Up")}</dt>
                  <dd><Num className="text-base font-semibold text-fg-1">{f.num(d.breadth.advancers, 0)}</Num></dd>
                </div>
                <div className="rounded-[var(--radius-sm)] bg-white/[0.04] py-2">
                  <dt className="text-3xs text-fg-3">■ {tx("بدون تغییر", "Flat")}</dt>
                  <dd><Num className="text-base font-semibold text-fg-1">{f.num(d.breadth.unchanged, 0)}</Num></dd>
                </div>
                <div className="rounded-[var(--radius-sm)] bg-down/[0.08] py-2">
                  <dt className="text-3xs text-down">▼ {tx("منفی", "Down")}</dt>
                  <dd><Num className="text-base font-semibold text-fg-1">{f.num(d.breadth.decliners, 0)}</Num></dd>
                </div>
              </dl>
              <p className="text-3xs leading-relaxed text-fg-4">
                {tx("نسبت مثبت به منفی", "Advance/decline ratio")}: <Num className="text-fg-2">{f.num(d.breadth.advancers / Math.max(1, d.breadth.decliners), 2)}</Num>
              </p>
            </div>
          ) : (
            <p className="text-2xs text-fg-4">{t.common.noData}</p>
          )}
        </DataCard>
      </div>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-2">
        <SectorHeatmapCard sectors={d.sectors} meta={board.meta} height={280} />
        <MoversCard gainers={d.gainers} losers={d.losers} meta={board.meta} />
      </div>
    </PageBody>
  );
}
