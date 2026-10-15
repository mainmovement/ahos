"use client";

import { Banknote, Bitcoin, Gauge, Percent, PieChart } from "lucide-react";
import type { CryptoBoard, DataEnvelope } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { SectorHeatmapCard, StatTile } from "@/components/cards/blocks";
import { MarketWatchCard } from "@/components/cards/market-watch";
import { CandlesChart, LinesChart } from "@/components/charts/charts";
import { RingGauge } from "@/components/charts/ring-gauge";
import { Delta, Num, UnknownValue } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";

export function CryptoView({ crypto }: { crypto: DataEnvelope<CryptoBoard> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const d = crypto.data;
  return (
    <PageBody>
      <PageHeader title={t.nav.items.crypto} subtitle={tx("ارزش کل بازار، تسلط بیت‌کوین، احساسات، نرخ تأمین مالی و استیبل‌کوین‌ها", "Total market cap, BTC dominance, sentiment, funding and stablecoins")} icon={Bitcoin} />
      <section className="grid grid-cols-2 gap-3 @4xl:grid-cols-4">
        <StatTile label={tx("ارزش کل بازار", "Total market cap")} value={f.usdCompact(d.totalMarketCap)} delta={d.totalMarketCapChange} tone="gold" />
        <StatTile label={tx("تسلط بیت‌کوین", "BTC dominance")} value={f.pct(d.btcDominance, 1, false)} />
        <StatTile label={tx("حجم ۲۴ ساعته", "24h volume")} value={f.usdCompact(d.volume24h)} tone="data" />
        <div className="flex items-center gap-3 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.025] px-3 py-2">
          <RingGauge value={d.fearGreed.value} size={64} stroke={6} label={tx("شاخص ترس و طمع", "Fear & greed index")} />
          <div>
            <div className="text-3xs text-fg-4">{tx("ترس و طمع (Alternative.me — نمایشی)", "Fear & greed (Alternative.me — demo)")}</div>
            <div className="text-sm font-semibold text-gold-100">{l(d.fearGreed.label)}</div>
            <div className="text-3xs text-fg-5">{tx("احساسات ≠ سیگنال", "Sentiment ≠ signal")}</div>
          </div>
        </div>
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("بیت‌کوین — کندل روزانه", "Bitcoin — daily candles")} icon={Bitcoin} meta={crypto.meta}>
          <CandlesChart candles={d.candles} height={330} label="BTC" decimals={0} />
        </DataCard>
        <DataCard className="@4xl:col-span-4" title={tx("تسلط بازار", "Market dominance")} subtitle={tx("سهم از ارزش کل بازار — ۹۰ روز", "Share of total cap — 90 days")} icon={PieChart} meta={crypto.meta}>
          <LinesChart series={d.dominance} height={300} label="dominance" percentAxis valueFormat={(v) => f.pct(v, 1, false)} />
        </DataCard>
      </div>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-2">
        <MarketWatchCard instruments={d.assets} meta={crypto.meta} title={tx("دارایی‌های اصلی", "Major assets")} />
        <SectorHeatmapCard sectors={d.sectors} meta={crypto.meta} title={tx("روایت‌ها و بخش‌ها", "Narratives & sectors")} height={300} />
      </div>
      <div className="grid grid-cols-1 gap-3 @3xl:grid-cols-2">
        <DataCard title={tx("نرخ تأمین مالی و موقعیت‌های باز", "Funding & open interest")} subtitle={tx("قراردادهای دائمی — Binance public (نمایشی)", "Perpetuals — Binance public (demo)")} icon={Percent} meta={crypto.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{t.common.symbol}</th>
                <th scope="col" className="num-cell">{tx("نرخ تأمین (۸س)", "Funding (8h)")}</th>
                <th scope="col" className="num-cell pe-3.5">{tx("موقعیت باز", "Open interest")}</th>
              </tr>
            </thead>
            <tbody>
              {d.funding.map((r) => (
                <tr key={r.symbol}>
                  <td className="ps-3.5"><bdi className="text-xs font-semibold text-fg-1">{r.symbol}</bdi></td>
                  <td className="num-cell">
                    {r.rate === null ? <UnknownValue /> : <Num className={cn("text-xs", r.rate >= 0 ? "text-up" : "text-down")}>{f.pct(r.rate, 4)}</Num>}
                  </td>
                  <td className="num-cell pe-3.5">{r.openInterest === null ? <UnknownValue /> : <Num className="text-xs text-fg-2">{f.usdCompact(r.openInterest)}</Num>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard title={tx("استیبل‌کوین‌ها", "Stablecoins")} subtitle={tx("عرضه و تغییر ۷ روزه — DefiLlama (نمایشی)", "Supply and 7-day change — DefiLlama (demo)")} icon={Banknote} meta={crypto.meta}>
          <ul className="space-y-2">
            {d.stablecoins.map((s) => (
              <li key={s.symbol} className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-3 py-2">
                <bdi className="text-xs font-semibold text-fg-1">{s.symbol}</bdi>
                <Num className="text-xs text-fg-2">{f.usdCompact(s.supply)}</Num>
                <Delta value={s.change7d} size="xs" polarity="neutral" />
              </li>
            ))}
          </ul>
          <p className="mt-2 flex items-center gap-1 text-3xs text-fg-5">
            <Gauge aria-hidden className="size-3" />
            {tx("رشد عرضه استیبل‌کوین نقدینگی بالقوه است، نه سیگنال خرید.", "Stablecoin growth is potential liquidity, not a buy signal.")}
          </p>
        </DataCard>
      </div>
    </PageBody>
  );
}
