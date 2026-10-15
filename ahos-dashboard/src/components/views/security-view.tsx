"use client";

import { useMemo } from "react";
import { BarChart3, CircleHelp, Globe2, ShieldAlert, ShieldCheck, ShieldX, Siren, Clock } from "lucide-react";
import type { DataEnvelope, SecurityGateState, SecurityOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Notice, ProviderHealthCard } from "@/components/cards/blocks";
import { BarsChart } from "@/components/charts/charts";
import { EChart, useChartContext } from "@/components/charts/echart";
import { Chip } from "@/components/ui/chip";
import { Num, TimeAgo } from "@/components/ui/primitives";
import { GateChip, SeverityChip } from "@/components/ui/status";
import { alpha } from "@/lib/tokens";

const GATE_ICON: Record<SecurityGateState, typeof ShieldCheck> = { PASS: ShieldCheck, REJECT: ShieldX, INCOMPLETE: ShieldAlert, STALE: Clock };

export function SecurityView({ security }: { security: DataEnvelope<SecurityOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const s = security.data;
  const c = useChartContext();
  const trendOption = useMemo(() => {
    const { p } = c;
    return {
      backgroundColor: "transparent",
      grid: { left: 8, right: 40, top: 28, bottom: 22 },
      legend: { top: 0, [c.rtl ? "right" : "left"]: 0, textStyle: { color: p.fg3, fontFamily: p.fontFamily, fontSize: 10 }, itemWidth: 10, itemHeight: 6 },
      tooltip: { ...c.tooltip, trigger: "axis" },
      xAxis: { type: "category", data: s.trend.map((x) => f.time(x.t)), axisLine: c.axisLine, axisTick: { show: false }, axisLabel: { ...c.axisLabel, interval: 3 } },
      yAxis: { type: "value", position: "right", axisLabel: c.axisLabel, splitLine: c.splitLine },
      series: [
        { name: t.gate.PASS, type: "bar", stack: "g", data: s.trend.map((x) => x.pass), itemStyle: { color: alpha(p.up, 0.75) }, barMaxWidth: 14 },
        { name: t.gate.INCOMPLETE, type: "bar", stack: "g", data: s.trend.map((x) => x.incomplete), itemStyle: { color: alpha(p.warn, 0.75) } },
        { name: t.gate.REJECT, type: "bar", stack: "g", data: s.trend.map((x) => x.reject), itemStyle: { color: alpha(p.down, 0.75), borderRadius: [3, 3, 0, 0] } },
      ],
    };
  }, [c, f, s.trend, t]);

  return (
    <PageBody>
      <PageHeader title={t.nav.items.security} subtitle={tx("دروازه امنیت توکن، اسکن‌ها، فیشینگ و رخدادها", "Token security gate, scans, phishing and incidents")} icon={ShieldCheck} />
      <Notice icon={<CircleHelp />} tone="violet">
        <b>UNKNOWN ≠ SAFE.</b>{" "}
        {tx("نبود پرچم خطر به معنی امن بودن نیست؛ بررسی ناقص یا کهنه همیشه با وضعیت خودش نمایش داده می‌شود و به PASS تبدیل نمی‌شود.", "Absence of a red flag does not mean safe; incomplete or stale checks keep their own state and are never shown as PASS.")}
      </Notice>
      <section className="grid grid-cols-2 gap-3 @4xl:grid-cols-4">
        {(Object.keys(s.gateCounts) as SecurityGateState[]).map((g) => {
          const Icon = GATE_ICON[g];
          return (
            <div key={g} className={cn("glass gold-border flex items-center gap-3 p-3")}>
              <span className={cn("flex size-10 items-center justify-center rounded-[var(--radius-md)] border", g === "PASS" ? "border-up/30 bg-up/10 text-up" : g === "REJECT" ? "border-down/30 bg-down/10 text-down" : "border-warn/30 bg-warn/10 text-warn")}>
                <Icon aria-hidden className="size-5" />
              </span>
              <div>
                <GateChip state={g} />
                <Num className="mt-1 block text-xl font-semibold text-fg-1">{f.num(s.gateCounts[g], 0)}</Num>
              </div>
            </div>
          );
        })}
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("روند دروازه امنیت — ۲۴ ساعت", "Security gate trend — 24h")} icon={BarChart3} meta={security.meta}>
          <EChart option={trendOption} height={240} label={tx("روند دروازه امنیت", "Security gate trend")} />
        </DataCard>
        <DataCard className="@4xl:col-span-4" title={tx("پرچم‌های پرتکرار", "Most frequent flags")} icon={ShieldAlert} meta={security.meta}>
          <BarsChart categories={s.flagCounts.map((x) => l(x.flag))} values={s.flagCounts.map((x) => x.count)} horizontal height={240} label="flags" decimals={0} />
        </DataCard>
      </div>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-2">
        <DataCard title={tx("اسکن‌های اخیر", "Recent scans")} icon={ShieldCheck} meta={security.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("هدف", "Target")}</th>
                <th scope="col">{tx("دروازه", "Gate")}</th>
                <th scope="col">{tx("پرچم‌ها", "Flags")}</th>
                <th scope="col">{t.common.source}</th>
                <th scope="col" className="pe-3.5">{t.common.time}</th>
              </tr>
            </thead>
            <tbody>
              {s.scans.map((x) => (
                <tr key={x.id}>
                  <td className="ps-3.5">
                    <bdi className="block text-xs font-semibold text-fg-1">{x.target}</bdi>
                    <span className="text-3xs text-fg-4">{x.chain}</span>
                  </td>
                  <td><GateChip state={x.gate} /></td>
                  <td className="max-w-[220px] whitespace-normal text-3xs text-fg-3">{x.flags.length ? x.flags.map((fl) => l(fl)).join(" · ") : <span className="text-fg-5">—</span>}</td>
                  <td className="text-3xs text-fg-3"><bdi>{x.provider}</bdi></td>
                  <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={x.at} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard title={tx("رخدادها", "Incidents")} icon={Siren} meta={security.meta}>
          <ol className="relative space-y-2 border-s border-[var(--line-hairline)] ps-4">
            {s.incidents.map((i) => (
              <li key={i.id} className="relative">
                <span aria-hidden className={cn("absolute -start-[21px] top-1 size-2.5 rounded-full border-2 border-ink-900", i.severity === "HIGH" || i.severity === "CRITICAL" ? "bg-warn" : i.severity === "MEDIUM" ? "bg-gold-400" : "bg-info")} />
                <div className="flex flex-wrap items-center gap-1.5">
                  <SeverityChip severity={i.severity} />
                  <Chip tone={i.state === "CLOSED" ? "muted" : i.state === "MITIGATED" ? "up" : i.state === "OPEN" ? "warn" : "info"}>{i.state}</Chip>
                  <TimeAgo iso={i.at} className="ms-auto text-3xs text-fg-4" />
                </div>
                <p className="mt-1 text-2xs text-fg-1">{l(i.title)}</p>
              </li>
            ))}
          </ol>
        </DataCard>
      </div>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-2">
        <DataCard title={tx("دامنه‌های فیشینگ", "Phishing domains")} subtitle={tx("دامنه‌های نمایشی با پسوند ‎.example", "Demo domains use the .example TLD")} icon={Globe2} meta={security.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("دامنه", "Domain")}</th>
                <th scope="col">{tx("جعل", "Imitates")}</th>
                <th scope="col">{t.common.status}</th>
                <th scope="col" className="pe-3.5">{t.common.time}</th>
              </tr>
            </thead>
            <tbody>
              {s.phishing.map((p) => (
                <tr key={p.domain}>
                  <td className="ps-3.5"><bdi className="mono text-2xs text-down">{p.domain}</bdi></td>
                  <td><bdi className="mono text-2xs text-fg-2">{p.imitates}</bdi></td>
                  <td><Chip tone={p.state === "BLOCKED" ? "down" : "warn"}>{p.state === "BLOCKED" ? tx("مسدود", "Blocked") : tx("پایش", "Monitoring")}</Chip></td>
                  <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={p.detectedAt} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <ProviderHealthCard providers={s.providers} meta={security.meta} title={tx("منابع امنیتی", "Security providers")} />
      </div>
    </PageBody>
  );
}
