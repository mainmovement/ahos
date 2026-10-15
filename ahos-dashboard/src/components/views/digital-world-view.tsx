"use client";

import { Activity, Blocks, Network } from "lucide-react";
import type { DataEnvelope, DigitalWorldOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { StatTile } from "@/components/cards/blocks";
import { LinesChart, NetworkGraph } from "@/components/charts/charts";
import { Delta, Num, UnknownValue } from "@/components/ui/primitives";
import { StatusChip } from "@/components/ui/status";

export function DigitalWorldView({ dw }: { dw: DataEnvelope<DigitalWorldOverview> }) {
  const { t, tx } = useI18n();
  const f = useFormat();
  const d = dw.data;
  const cats = ["chain", "stablecoin", "protocol", "oracle", "bridge"] as const;
  const catLabels = [tx("زنجیره", "Chain"), tx("استیبل‌کوین", "Stablecoin"), tx("پروتکل", "Protocol"), tx("اوراکل", "Oracle"), tx("پل", "Bridge")];
  return (
    <PageBody>
      <PageHeader title={t.nav.items.digitalWorld} subtitle={tx("نقشه شبکه اکوسیستم‌های دیجیتال: زنجیره‌ها، پروتکل‌ها، استیبل‌کوین‌ها، پل‌ها و اوراکل‌ها", "Network map of digital ecosystems: chains, protocols, stablecoins, bridges and oracles")} icon={Network} />
      <section className="grid grid-cols-2 gap-3 @4xl:grid-cols-4">
        <StatTile label={tx("ارزش قفل‌شده کل (TVL)", "Total value locked")} value={f.usdCompact(d.totals.tvl)} tone="gold" />
        <StatTile label={tx("عرضه استیبل‌کوین", "Stablecoin supply")} value={f.usdCompact(d.totals.stablecoinSupply)} tone="data" />
        <StatTile label={tx("حجم ۲۴ساعته DEX", "24h DEX volume")} value={f.usdCompact(d.totals.dexVolume24h)} />
        <StatTile label={tx("آدرس‌های فعال", "Active addresses")} value={f.compact(d.totals.activeAddresses)} />
      </section>
      <DataCard title={tx("گراف اکوسیستم", "Ecosystem graph")} subtitle={tx("کشیدن برای جابه‌جایی · چرخ برای بزرگ‌نمایی · گره را نگه دارید", "Drag to pan · wheel to zoom · drag nodes")} icon={Network} meta={dw.meta}>
        <NetworkGraph
          nodes={d.graph.nodes.map((n) => ({ ...n, category: cats.indexOf(n.category) }))}
          links={d.graph.links}
          categories={catLabels}
          height={460}
          label={tx("گراف اکوسیستم دیجیتال", "Digital ecosystem graph")}
        />
      </DataCard>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-7" title={tx("زنجیره‌ها", "Chains")} icon={Blocks} meta={dw.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("زنجیره", "Chain")}</th>
                <th scope="col" className="num-cell">TVL</th>
                <th scope="col" className="num-cell">{tx("تغییر ۷ روزه", "7d change")}</th>
                <th scope="col" className="num-cell">TPS</th>
                <th scope="col" className="num-cell">{tx("کارمزد ۲۴س", "Fees 24h")}</th>
                <th scope="col" className="pe-3.5">{t.common.status}</th>
              </tr>
            </thead>
            <tbody>
              {d.chains.map((c) => (
                <tr key={c.id}>
                  <td className="ps-3.5"><bdi className="text-xs font-semibold text-fg-1">{c.name}</bdi></td>
                  <td className="num-cell">{c.tvl === null ? <UnknownValue /> : <Num className="text-2xs text-fg-1">{f.usdCompact(c.tvl)}</Num>}</td>
                  <td className="num-cell"><Delta value={c.change7d} size="xs" /></td>
                  <td className="num-cell">{c.tps === null ? <UnknownValue /> : <Num className="text-2xs text-fg-2">{f.num(c.tps, 0)}</Num>}</td>
                  <td className="num-cell">{c.fees24h === null ? <UnknownValue /> : <Num className="text-2xs text-fg-2">{f.usdCompact(c.fees24h)}</Num>}</td>
                  <td className="pe-3.5"><StatusChip status={c.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard className="@4xl:col-span-5" title={tx("فعالیت", "Activity")} subtitle={tx("۶۰ روز", "60 days")} icon={Activity} meta={dw.meta}>
          <LinesChart series={d.activity.slice(0, 1)} height={130} label="DEX volume" area valueFormat={(v) => f.num(v, 1)} />
          <LinesChart series={d.activity.slice(1, 2)} height={130} label="Stablecoin supply" area valueFormat={(v) => f.num(v, 0)} />
        </DataCard>
      </div>
    </PageBody>
  );
}
