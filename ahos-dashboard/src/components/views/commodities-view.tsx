"use client";

import { Coins, Droplets, Factory, Flame, Gem, Landmark, Scale } from "lucide-react";
import type { DataEnvelope, GoldBoard, OilBoard } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard, SectionTitle } from "@/components/cards/data-card";
import { DriversCard, InstrumentTile, Notice } from "@/components/cards/blocks";
import { CandlesChart, BarsChart, LinesChart } from "@/components/charts/charts";
import { Meter, Num } from "@/components/ui/primitives";
import { UnknownValue } from "@/components/ui/primitives";

export function OilView({ oil }: { oil: DataEnvelope<OilBoard> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const d = oil.data;
  const brent = d.benchmarks.find((b) => b.id === "brent");
  return (
    <PageBody>
      <PageHeader title={t.nav.items.oil} subtitle={tx("شاخص‌های جهانی، اسپرد، ذخایر و تولید اوپک+", "Global benchmarks, spreads, inventories and OPEC+ output")} icon={Flame} />
      <section aria-label={tx("شاخص‌های نفت", "Oil benchmarks")} className="grid grid-cols-2 gap-3 @2xl:grid-cols-3 @5xl:grid-cols-6">
        {d.benchmarks.map((b) => (
          <InstrumentTile key={b.id} i={b} />
        ))}
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("برنت — کندل روزانه", "Brent — daily candles")} subtitle={tx("نمایشی · MA20/MA50", "Demo · MA20/MA50")} icon={Flame} meta={oil.meta}>
          <CandlesChart candles={d.candles} height={330} label="Brent" decimals={brent?.decimals ?? 2} />
        </DataCard>
        <DriversCard className="@4xl:col-span-4" drivers={d.drivers} meta={oil.meta} />
      </div>
      <div className="grid grid-cols-1 gap-3 @3xl:grid-cols-2 @6xl:grid-cols-3">
        <DataCard title={tx("اسپرد برنت − WTI", "Brent − WTI spread")} subtitle={tx("دلار بر بشکه", "USD per barrel")} icon={Scale} meta={oil.meta}>
          <LinesChart series={[{ id: "spread", label: { fa: "اسپرد", en: "Spread" }, points: d.spread }]} height={220} label="Brent-WTI spread" area valueFormat={(v) => f.num(v, 2)} />
        </DataCard>
        <DataCard title={tx("تغییر ذخایر تجاری آمریکا (EIA)", "US commercial inventory change (EIA)")} subtitle={tx("میلیون بشکه — هفتگی (نمایشی)", "Million barrels — weekly (demo)")} icon={Droplets} meta={oil.meta}>
          <BarsChart categories={d.inventories.map((x) => x.week)} values={d.inventories.map((x) => x.change)} signed height={220} label="EIA inventories" unit="M" decimals={1} />
        </DataCard>
        <DataCard className="@3xl:col-span-2 @6xl:col-span-1" title={tx("تولید اوپک+", "OPEC+ production")} subtitle={tx("هزار بشکه در روز — سهمیه در برابر تولید", "kb/d — quota vs actual")} icon={Factory} meta={oil.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("کشور", "Country")}</th>
                <th scope="col" className="num-cell">{tx("سهمیه", "Quota")}</th>
                <th scope="col" className="num-cell">{tx("تولید", "Actual")}</th>
                <th scope="col" className="pe-3.5">{tx("پایبندی", "Compliance")}</th>
              </tr>
            </thead>
            <tbody>
              {d.opec.map((r) => {
                const ratio = r.quota && r.actual ? r.actual / r.quota : null;
                return (
                  <tr key={r.country.en}>
                    <td className="ps-3.5 text-2xs text-fg-1">{l(r.country)}</td>
                    <td className="num-cell">{r.quota === null ? <UnknownValue /> : <Num className="text-2xs text-fg-2">{f.num(r.quota, 0)}</Num>}</td>
                    <td className="num-cell"><Num className="text-2xs text-fg-1">{f.num(r.actual, 0)}</Num></td>
                    <td className="w-28 pe-3.5">
                      {ratio === null ? (
                        <span className="text-3xs text-fg-4">{tx("معاف / نامعلوم", "Exempt / unknown")}</span>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <Meter value={Math.min(ratio, 1.2)} max={1.2} tone={ratio > 1.02 ? "warn" : "gold"} label={l(r.country)} />
                          <Num className="text-3xs text-fg-3">{f.pct(ratio * 100, 0, false)}</Num>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </DataCard>
      </div>
    </PageBody>
  );
}

export function GoldView({ gold }: { gold: DataEnvelope<GoldBoard> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const d = gold.data;
  return (
    <PageBody>
      <PageHeader title={t.nav.items.gold} subtitle={tx("طلای جهانی، بازار داخلی ایران (سکه و طلای ۱۸ عیار) و جریان بانک‌های مرکزی", "Global gold, Iran's domestic market (coins, 18k gold) and central-bank flows")} icon={Gem} />
      <SectionTitle hint={tx("دلار بر انس", "USD per ounce")}>{tx("بازار جهانی", "Global market")}</SectionTitle>
      <section className="grid grid-cols-2 gap-3 @3xl:grid-cols-4">
        {d.spot.map((i) => (
          <InstrumentTile key={i.id} i={i} />
        ))}
      </section>
      <SectionTitle hint={tx("تومان — داده‌های داخلی کهنه علامت‌گذاری شده‌اند", "Toman — domestic quotes are marked stale")}>{tx("بازار داخلی ایران", "Iran domestic market")}</SectionTitle>
      <Notice icon={<Coins />} tone="warn">
        {tx(
          "نرخ‌های داخلی از منابع عمومی با تأخیر می‌آیند؛ این نسخه آن‌ها را عمداً «کهنه» نشان می‌دهد تا هیچ‌گاه به‌عنوان قیمت لحظه‌ای برداشت نشوند.",
          "Domestic quotes arrive from public sources with delay; this build deliberately marks them STALE so they are never mistaken for real-time prices.",
        )}
      </Notice>
      <section className="grid grid-cols-2 gap-3 @2xl:grid-cols-3 @5xl:grid-cols-6">
        {d.iran.map((i) => (
          <InstrumentTile key={i.id} i={i} />
        ))}
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("طلای جهانی — کندل روزانه", "Gold spot — daily candles")} icon={Gem} meta={gold.meta}>
          <CandlesChart candles={d.candles} height={320} label="XAU/USD" decimals={1} />
        </DataCard>
        <DriversCard className="@4xl:col-span-4" drivers={d.drivers} meta={gold.meta} />
      </div>
      <div className="grid grid-cols-1 gap-3 @3xl:grid-cols-3">
        <DataCard title={tx("حباب سکه امامی", "Emami coin premium")} subtitle={tx("درصد اختلاف با ارزش ذاتی", "% over intrinsic value")} icon={Coins} meta={gold.meta}>
          <LinesChart series={[{ id: "premium", label: { fa: "حباب", en: "Premium" }, points: d.coinPremium }]} height={220} label="coin premium" area percentAxis valueFormat={(v) => f.pct(v, 1, false)} />
        </DataCard>
        <DataCard title={tx("خرید بانک‌های مرکزی", "Central-bank purchases")} subtitle={tx("تن — سه‌ماهه اخیر (نمایشی)", "Tonnes — last quarter (demo)")} icon={Landmark} meta={gold.meta}>
          <BarsChart categories={d.centralBanks.map((c) => l(c.country))} values={d.centralBanks.map((c) => c.tonnes)} horizontal height={220} label="central banks" unit="t" decimals={1} />
        </DataCard>
        <DataCard title={tx("جریان صندوق‌های طلا (ETF)", "Gold ETF flows")} subtitle={tx("تن — هفتگی (نمایشی)", "Tonnes — weekly (demo)")} icon={Scale} meta={gold.meta}>
          <BarsChart categories={d.etfFlows.map((x) => x.week)} values={d.etfFlows.map((x) => x.tonnes)} signed height={220} label="ETF flows" unit="t" decimals={1} />
        </DataCard>
      </div>
    </PageBody>
  );
}
