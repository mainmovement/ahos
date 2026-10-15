"use client";

import { ChartPie, Globe2, LineChart, ShieldAlert, Wallet } from "lucide-react";
import type { DataEnvelope, PortfolioOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { StatTile } from "@/components/cards/blocks";
import { DonutChart, LinesChart } from "@/components/charts/charts";
import { Delta, Meter, Num } from "@/components/ui/primitives";
import { Chip } from "@/components/ui/chip";

export function PortfolioView({ portfolio }: { portfolio: DataEnvelope<PortfolioOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const p = portfolio.data;
  return (
    <PageBody>
      <PageHeader title={t.nav.items.portfolio} subtitle={tx("سبد کاغذی: تخصیص، اکسپوژر، عملکرد در برابر معیارها و ریسک", "Paper portfolio: allocation, exposure, performance vs benchmarks and risk")} icon={ChartPie} />
      <section className="grid grid-cols-2 gap-3 @2xl:grid-cols-3 @5xl:grid-cols-6">
        <StatTile label={tx("ارزش کل (کاغذی)", "Total value (paper)")} value={f.usd(p.totalValue, 0)} delta={p.changePct} tone="gold" />
        <StatTile label={tx("ارزش در معرض ریسک ۹۵٪", "VaR 95%")} value={f.pct(p.risk.var95Pct, 1)} tone="down" />
        <StatTile label={tx("نوسان سالانه", "Volatility (ann.)")} value={f.pct(p.risk.volatilityPct, 1, false)} />
        <StatTile label={tx("شارپ", "Sharpe")} value={f.num(p.risk.sharpe, 2)} />
        <StatTile label={tx("بتا نسبت به BTC", "Beta vs BTC")} value={f.num(p.risk.beta, 2)} />
        <StatTile label={tx("افت حداکثر", "Max drawdown")} value={f.pct(p.risk.maxDrawdownPct, 1)} tone="down" />
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-4" title={tx("تخصیص دارایی", "Allocation")} icon={ChartPie} meta={portfolio.meta}>
          <DonutChart items={p.allocation.map((a) => ({ name: l(a.label), value: a.value }))} height={220} label={tx("تخصیص دارایی", "Allocation")} centerLabel={f.usdCompact(p.totalValue)} />
          <ul className="mt-2 space-y-1">
            {p.allocation.map((a) => (
              <li key={a.id} className="flex items-center justify-between text-2xs">
                <span className="text-fg-2">{l(a.label)}</span>
                <Num className="text-fg-1">{f.pct((a.value / p.totalValue) * 100, 1, false)}</Num>
              </li>
            ))}
          </ul>
        </DataCard>
        <DataCard className="@4xl:col-span-8" title={tx("عملکرد در برابر معیارها", "Performance vs benchmarks")} subtitle={tx("بازده تجمعی ۹۰ روزه", "Cumulative 90-day return")} icon={LineChart} meta={portfolio.meta}>
          <LinesChart series={p.performance} height={300} label={tx("عملکرد", "Performance")} normalize percentAxis />
        </DataCard>
      </div>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("دارایی‌ها", "Holdings")} icon={Wallet} meta={portfolio.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{t.common.symbol}</th>
                <th scope="col">{tx("طبقه", "Class")}</th>
                <th scope="col" className="num-cell">{tx("ارزش", "Value")}</th>
                <th scope="col" className="w-36">{tx("وزن", "Weight")}</th>
                <th scope="col" className="num-cell">{t.common.change24h}</th>
                <th scope="col" className="num-cell pe-3.5">{tx("سود/زیان", "PnL")}</th>
              </tr>
            </thead>
            <tbody>
              {p.holdings.map((h) => (
                <tr key={h.symbol}>
                  <td className="ps-3.5">
                    <bdi className="block text-xs font-semibold text-fg-1">{h.symbol}</bdi>
                    <span className="text-3xs text-fg-4">{l(h.name)}</span>
                  </td>
                  <td><Chip tone="muted">{h.assetClass}</Chip></td>
                  <td className="num-cell"><Num className="text-2xs text-fg-1">{f.usd(h.value, 0)}</Num></td>
                  <td>
                    <div className="flex items-center gap-1.5">
                      <Meter value={h.weight} max={0.25} label={tx("وزن", "Weight")} />
                      <Num className="w-10 text-3xs text-fg-3">{f.pct(h.weight * 100, 1, false)}</Num>
                    </div>
                  </td>
                  <td className="num-cell"><Delta value={h.changePct} size="xs" /></td>
                  <td className="num-cell pe-3.5"><Num className={h.pnl === null ? "text-2xs text-fg-4" : h.pnl >= 0 ? "text-2xs text-up" : "text-2xs text-down"}>{f.usd(h.pnl, 0)}</Num></td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard className="@4xl:col-span-4" title={tx("اکسپوژر", "Exposure")} icon={Globe2} meta={portfolio.meta}>
          <ul className="space-y-2.5">
            {p.exposure.map((e) => (
              <li key={e.label.en}>
                <div className="mb-1 flex justify-between text-2xs">
                  <span className="text-fg-2">{l(e.label)}</span>
                  <Num className="text-fg-1">{f.pct(e.pct, 1, false)}</Num>
                </div>
                <Meter value={e.pct} max={100} tone="data" label={l(e.label)} height={5} />
              </li>
            ))}
          </ul>
          <p className="mt-3 flex items-start gap-1.5 text-3xs leading-relaxed text-fg-4">
            <ShieldAlert aria-hidden className="mt-0.5 size-3 shrink-0" />
            {tx("معیارهای ریسک روی داده نمایشی محاسبه شده‌اند و پیش‌بینی آینده نیستند.", "Risk metrics are computed on demo data and are not forecasts.")}
          </p>
        </DataCard>
      </div>
    </PageBody>
  );
}
