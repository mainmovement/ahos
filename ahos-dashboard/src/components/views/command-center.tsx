"use client";

import { Activity, Clock, HeartPulse, LayoutDashboard, Timer } from "lucide-react";
import type { DataEnvelope, EarthOverview, Kpi, MarketBoard, Newsroom, PaperAccount, SeriesPoint, SystemOverview, UniversityOverview } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { useFormat } from "@/lib/format";
import { useNowMinute } from "@/lib/time/now";
import { zonedClock } from "@/lib/time/sessions";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { KpiCard } from "@/components/cards/kpi-card";
import { MarketChartCard } from "@/components/cards/market-chart-card";
import { MarketWatchCard } from "@/components/cards/market-watch";
import { NewsFeedCard, PaperSummaryCard, SystemHealthCard, UniversityStatusCard } from "@/components/cards/summary-cards";
import { GlobeHero } from "@/components/globe/globe-hero";
import { Tip } from "@/components/ui/tooltip";
import { StatusChip } from "@/components/ui/status";

interface Props {
  kpis: DataEnvelope<Kpi[]>;
  earth: DataEnvelope<EarthOverview>;
  market: DataEnvelope<MarketBoard>;
  paper: DataEnvelope<PaperAccount>;
  intraday: DataEnvelope<SeriesPoint[]>;
  news: DataEnvelope<Newsroom>;
  university: DataEnvelope<UniversityOverview>;
  system: DataEnvelope<SystemOverview>;
}

function useGreeting() {
  const { tx, t } = useI18n();
  const minute = useNowMinute();
  if (minute === null) return tx(`درود، ${t.app.operatorName}`, `Hello, ${t.app.operatorName}`);
  const h = Math.floor(zonedClock(new Date(minute), "Asia/Tehran").minutes / 60);
  const fa = h >= 5 && h < 12 ? "صبح بخیر" : h >= 12 && h < 15 ? "ظهر بخیر" : h >= 15 && h < 19 ? "عصر بخیر" : "شب بخیر";
  const en = h >= 5 && h < 12 ? "Good morning" : h >= 12 && h < 18 ? "Good afternoon" : "Good evening";
  return tx(`${fa}، ${t.app.operatorName}`, `${en}, ${t.app.operatorName}`);
}

export function CommandCenterView({ kpis, earth, market, paper, intraday, news, university, system }: Props) {
  const { tx } = useI18n();
  const f = useFormat();
  const greeting = useGreeting();
  const watchIds = ["btc", "eth", "sol", "xau", "brent", "eurusd", "spx", "usdirt", "tedpix", "rut"];
  const watch = watchIds.map((id) => market.data.instruments.find((i) => i.id === id)).filter((x): x is NonNullable<typeof x> => Boolean(x));

  return (
    <PageBody>
      <PageHeader
        title={greeting}
        subtitle={tx("مرکز فرماندهی AHOS — «آینده از آنِ کسانی است که اطلاعات را به هوش تبدیل می‌کنند.»", "AHOS command center — “The future belongs to those who turn information into intelligence.”")}
        icon={LayoutDashboard}
        actions={
          <div className="hidden items-center gap-2 @3xl:flex">
            <Tip content={tx("سلامت سامانه (نمایشی)", "System health (demo)")}>
              <span tabIndex={0} className="flex h-7 items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-2.5 text-3xs text-fg-3">
                <HeartPulse aria-hidden className="size-3 text-up" />
                {tx("سلامت", "Health")} <b className="num font-semibold text-fg-1">{f.pct(99.8, 1, false)}</b>
                <StatusChip status="DEMO" showLabel={false} />
              </span>
            </Tip>
            <Tip content={tx("تازگی شواهد (نمایشی)", "Evidence freshness (demo)")}>
              <span tabIndex={0} className="flex h-7 items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-2.5 text-3xs text-fg-3">
                <Clock aria-hidden className="size-3 text-gold-300" />
                {tx("تازگی شواهد", "Evidence")} <b className="num font-semibold text-fg-1">{f.duration(system.data.evidenceFreshnessSec)}</b>
              </span>
            </Tip>
            <Tip content={tx("زمان اجرا (نمایشی)", "Runtime (demo)")}>
              <span tabIndex={0} className="flex h-7 items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-2.5 text-3xs text-fg-3">
                <Timer aria-hidden className="size-3 text-data-300" />
                {tx("اجرا", "Runtime")} <b className="font-semibold text-fg-1">{f.duration(system.data.uptimeSec)}</b>
              </span>
            </Tip>
          </div>
        }
      />

      <section aria-label={tx("شاخص‌های کلیدی", "Key indicators")} className="grid grid-cols-2 gap-3 @2xl:grid-cols-3 @5xl:grid-cols-6">
        {kpis.data.map((k) => (
          <KpiCard key={k.id} kpi={k} meta={kpis.meta} />
        ))}
      </section>

      <GlobeHero earth={earth.data} meta={earth.meta} />

      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <MarketChartCard className="@4xl:col-span-7" instruments={market.data.instruments} candles={market.data.candles} meta={market.meta} ids={["btc", "xau", "brent", "spx", "eth"]} height={290} />
        <MarketWatchCard className="@4xl:col-span-5" instruments={watch} meta={market.meta} />
      </div>

      <section aria-label={tx("خلاصه عملیات", "Operations summary")} className="grid grid-cols-1 gap-3 @2xl:grid-cols-2 @6xl:grid-cols-4">
        <PaperSummaryCard account={paper.data} intraday={intraday.data} meta={paper.meta} />
        <NewsFeedCard news={news.data} meta={news.meta} />
        <UniversityStatusCard uni={university.data} meta={university.meta} />
        <SystemHealthCard system={system.data} meta={system.meta} />
      </section>

      <p className="flex items-center justify-center gap-1.5 pb-2 text-3xs text-fg-5">
        <Activity aria-hidden className="size-3" />
        {tx("همه اعداد این صفحه نمایشی‌اند؛ مرز روز/شب و ساعت‌ها از زمان واقعی دستگاه محاسبه می‌شوند.", "All figures on this page are demo data; the day/night terminator and clocks are computed from the device's real time.")}
      </p>
    </PageBody>
  );
}
