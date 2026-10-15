"use client";

import { Cpu, GitCommitHorizontal, HardDrive, Lock, Server, ShieldCheck, Timer } from "lucide-react";
import type { DataEnvelope, ServiceStatus, SystemOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { ProviderHealthCard, StatTile } from "@/components/cards/blocks";
import { AreaSeriesChart } from "@/components/charts/charts";
import { Chip, type ChipTone } from "@/components/ui/chip";
import { Num, TimeAgo } from "@/components/ui/primitives";

const STATE_TONE: Record<ServiceStatus["state"], ChipTone> = { UP: "up", DEGRADED: "warn", DOWN: "down", NOT_CONFIGURED: "slate", UNKNOWN: "violet" };

export function SystemView({ system }: { system: DataEnvelope<SystemOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const s = system.data;
  const stateLabel: Record<ServiceStatus["state"], string> = { UP: tx("فعال", "Up"), DEGRADED: tx("افت کیفیت", "Degraded"), DOWN: tx("از کار افتاده", "Down"), NOT_CONFIGURED: tx("پیکربندی‌نشده", "Not configured"), UNKNOWN: tx("نامعلوم", "Unknown") };
  return (
    <PageBody>
      <PageHeader title={t.nav.items.system} subtitle={tx("فرایندها، پایگاه داده، لبه‌ها، منابع داده و یکپارچگی Lane A", "Processes, database, edges, data providers and Lane A integrity")} icon={Server} />
      <section className="grid grid-cols-2 gap-3 @2xl:grid-cols-3 @5xl:grid-cols-6">
        <StatTile label={tx("حالت", "Mode")} value={<span className="text-sm">PAPER_ONLY</span>} tone="gold" icon={<Lock className="size-3" />} />
        <StatTile label={tx("طبقه‌بندی پروژه", "Project classification")} value={<span className="text-sm">{s.classification}</span>} hint={tx("OPERATOR_READY هنوز تأیید نشده", "OPERATOR_READY not yet verified")} />
        <StatTile label={tx("زمان کارکرد", "Uptime")} value={<span className="text-sm">{f.duration(s.uptimeSec)}</span>} icon={<Timer className="size-3" />} />
        <StatTile label={tx("تازگی شواهد", "Evidence freshness")} value={<span className="text-sm">{f.duration(s.evidenceFreshnessSec)}</span>} />
        <StatTile label="Lane A" value={<span className="text-sm">{s.laneA.state}</span>} tone={s.laneA.state === "PASS" ? "up" : "down"} icon={<ShieldCheck className="size-3" />} hint={s.laneA.checkedAt ? <TimeAgo iso={s.laneA.checkedAt} /> : undefined} />
        <StatTile label={tx("نسخه / کامیت", "Build / commit")} value={<span className="text-sm">{s.build.version}</span>} icon={<GitCommitHorizontal className="size-3" />} hint={<bdi className="mono">{s.build.commit}</bdi>} />
      </section>
      <DataCard title={tx("سرویس‌ها", "Services")} subtitle={tx("«پیکربندی‌نشده» و «نامعلوم» هرگز سالم شمرده نمی‌شوند", "NOT_CONFIGURED and UNKNOWN are never counted as healthy")} icon={Server} meta={system.meta} bodyClassName="px-0 pb-0">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col" className="ps-3.5">{tx("سرویس", "Service")}</th>
              <th scope="col">{tx("نوع", "Kind")}</th>
              <th scope="col">{t.common.status}</th>
              <th scope="col" className="num-cell">{tx("زمان کارکرد", "Uptime")}</th>
              <th scope="col">{tx("نسخه", "Version")}</th>
              <th scope="col">{tx("آخرین ضربان", "Last heartbeat")}</th>
              <th scope="col" className="pe-3.5">{tx("یادداشت", "Note")}</th>
            </tr>
          </thead>
          <tbody>
            {s.services.map((x) => (
              <tr key={x.id}>
                <td className="ps-3.5 text-xs text-fg-1">{l(x.name)}</td>
                <td><Chip tone="muted">{x.kind}</Chip></td>
                <td><Chip tone={STATE_TONE[x.state]}>{stateLabel[x.state]}</Chip></td>
                <td className="num-cell text-2xs text-fg-2">{f.duration(x.uptimeSec)}</td>
                <td><bdi className="mono text-3xs text-fg-3">{x.version ?? "—"}</bdi></td>
                <td className="text-3xs text-fg-4">{x.lastHeartbeat ? <TimeAgo iso={x.lastHeartbeat} /> : t.common.never}</td>
                <td className="pe-3.5 text-3xs text-fg-3">{x.note ? l(x.note) : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </DataCard>
      <div className="grid grid-cols-1 gap-3 @3xl:grid-cols-3">
        <DataCard title="CPU" subtitle={tx("درصد — ۶۰ دقیقه", "% — 60 minutes")} icon={Cpu} meta={system.meta}>
          <AreaSeriesChart points={s.cpu} height={150} label="CPU" />
          <div className="mt-1 text-end text-3xs text-fg-4">{tx("فعلی", "Now")}: <Num className="text-fg-1">{f.num(s.cpu[s.cpu.length - 1]?.v ?? null, 0)}%</Num></div>
        </DataCard>
        <DataCard title={tx("حافظه", "Memory")} subtitle={tx("درصد — ۶۰ دقیقه", "% — 60 minutes")} icon={HardDrive} meta={system.meta}>
          <AreaSeriesChart points={s.memory} height={150} label="Memory" color="gold" />
          <div className="mt-1 text-end text-3xs text-fg-4">{tx("فعلی", "Now")}: <Num className="text-fg-1">{f.num(s.memory[s.memory.length - 1]?.v ?? null, 0)}%</Num></div>
        </DataCard>
        <DataCard title={tx("تأخیر چرخه", "Cycle latency")} subtitle={tx("میلی‌ثانیه — ۶۰ دقیقه", "ms — 60 minutes")} icon={Timer} meta={system.meta}>
          <AreaSeriesChart points={s.latency} height={150} label="Latency" />
          <div className="mt-1 text-end text-3xs text-fg-4">{tx("فعلی", "Now")}: <Num className="text-fg-1">{f.num(s.latency[s.latency.length - 1]?.v ?? null, 0)} ms</Num></div>
        </DataCard>
      </div>
      <ProviderHealthCard providers={s.providers} meta={system.meta} />
    </PageBody>
  );
}
