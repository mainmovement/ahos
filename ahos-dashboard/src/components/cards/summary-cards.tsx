"use client";

import Link from "next/link";
import { Activity, CircleCheck, CircleX, GraduationCap, Lock, Newspaper, RefreshCw, Server, ShieldCheck, Wallet } from "lucide-react";
import type { DataMeta, Newsroom, PaperAccount, SeriesPoint, SystemOverview, UniversityOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/ui/chip";
import { Delta, Meter, Num, TimeAgo } from "@/components/ui/primitives";
import { NewsStateChip } from "@/components/ui/status";
import { Sparkline } from "@/components/charts/sparkline";
import { RingGauge } from "@/components/charts/ring-gauge";
import { DataCard } from "./data-card";

/* ---------------------------------------------------------- paper */

export function PaperSummaryCard({ account, intraday, meta, className }: { account: PaperAccount; intraday: SeriesPoint[]; meta: DataMeta; className?: string }) {
  const { tx, t, l } = useI18n();
  const f = useFormat();
  const gross = account.limits.find((x) => x.id === "l3");
  return (
    <DataCard
      title={tx("خلاصه معاملات کاغذی", "Paper trading summary")}
      subtitle={tx("حساب شبیه‌سازی — بدون وجه واقعی", "Simulated account — no real funds")}
      icon={Wallet}
      meta={meta}
      className={className}
      actions={
        <Chip tone="gold" icon={Lock}>
          PAPER
        </Chip>
      }
    >
      <div className="flex items-end justify-between gap-2">
        <div>
          <div className="text-3xs text-fg-4">{tx("ارزش حساب", "Equity")}</div>
          <Num className="text-xl font-semibold text-fg-1">{f.usd(account.equity, 0)}</Num>
        </div>
        <div className="text-end">
          <Delta value={account.pnlDayPct} size="md" />
          <div className="text-3xs text-fg-5">{tx("امروز", "today")}</div>
        </div>
      </div>
      <Sparkline data={intraday.map((p) => p.v)} height={38} label={tx("ارزش درون‌روزی", "Intraday equity")} />
      <dl className="mt-2 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-[var(--radius-sm)] bg-white/[0.03] py-1.5">
          <dt className="text-3xs text-fg-4">{tx("موقعیت باز", "Open")}</dt>
          <dd><Num className="text-sm font-semibold text-fg-1">{f.num(account.positions.length, 0)}</Num></dd>
        </div>
        <div className="rounded-[var(--radius-sm)] bg-white/[0.03] py-1.5">
          <dt className="text-3xs text-fg-4">{tx("نرخ برد", "Win rate")}</dt>
          <dd><Num className="text-sm font-semibold text-fg-1">{account.winRate === null ? "—" : f.pct(account.winRate * 100, 0, false)}</Num></dd>
        </div>
        <div className="rounded-[var(--radius-sm)] bg-white/[0.03] py-1.5">
          <dt className="text-3xs text-fg-4">{tx("افت حداکثر", "Max DD")}</dt>
          <dd><Num className="text-sm font-semibold text-down">{f.pct(account.maxDrawdownPct, 1)}</Num></dd>
        </div>
      </dl>
      {gross && (
        <div className="mt-2.5">
          <div className="mb-1 flex justify-between text-3xs">
            <span className="text-fg-3">{l(gross.label)}</span>
            <Num className="text-fg-2">
              {f.num(gross.used, 1)}% / {f.num(gross.limit, 0)}%
            </Num>
          </div>
          <Meter value={gross.used} max={gross.limit} label={l(gross.label)} />
        </div>
      )}
      <Link href="/paper-trading" className="mt-2.5 block text-3xs text-gold-300 hover:text-gold-100">
        {t.common.viewAll} →
      </Link>
    </DataCard>
  );
}

/* ----------------------------------------------------------- news */

export function NewsFeedCard({ news, meta, className, limit = 4 }: { news: Newsroom; meta: DataMeta; className?: string; limit?: number }) {
  const { tx, l, t } = useI18n();
  return (
    <DataCard
      title={tx("خوراک خبر", "News feed")}
      subtitle={tx("تأییدشده / تأییدنشده / متناقض", "Verified / unverified / conflicting")}
      icon={Newspaper}
      meta={meta}
      className={className}
      actions={
        <Link href="/news" className="text-3xs text-gold-300 hover:text-gold-100">
          {t.common.viewAll}
        </Link>
      }
    >
      <ul className="space-y-2">
        {news.items.slice(0, limit).map((n) => (
          <li key={n.id} className="group">
            <div className="flex items-start gap-2">
              <span aria-hidden className={cn("mt-1.5 size-1.5 shrink-0 rounded-full", n.verification === "VERIFIED" ? "bg-up" : n.verification === "CONFLICTING" ? "bg-warn" : "bg-slate")} />
              <div className="min-w-0 flex-1">
                <p className="line-clamp-2 text-2xs leading-snug text-fg-1 group-hover:text-gold-100">{l(n.title)}</p>
                <div className="mt-1 flex flex-wrap items-center gap-1.5 text-3xs text-fg-4">
                  <NewsStateChip state={n.verification} />
                  <bdi>{n.source}</bdi>
                  <span aria-hidden>·</span>
                  <TimeAgo iso={n.publishedAt} />
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </DataCard>
  );
}

/* ----------------------------------------------------- university */

export function UniversityStatusCard({ uni, meta, className }: { uni: UniversityOverview; meta: DataMeta; className?: string }) {
  const { tx, l, t } = useI18n();
  const f = useFormat();
  const passed = uni.exams.filter((e) => e.result === "PASS").length;
  const failed = uni.exams.filter((e) => e.result === "FAIL").length;
  const pending = uni.exams.filter((e) => e.result === "PENDING").length;
  const rate = uni.passRateTrend[uni.passRateTrend.length - 1] ?? null;
  return (
    <DataCard
      title={tx("وضعیت دانشگاه", "University status")}
      subtitle={tx("آزمون عامل‌ها و صف بازآموزی", "Agent exams and retraining queue")}
      icon={GraduationCap}
      meta={meta}
      className={className}
      actions={
        <Link href="/university" className="text-3xs text-gold-300 hover:text-gold-100">
          {t.common.viewAll}
        </Link>
      }
    >
      <div className="flex items-center gap-3">
        <RingGauge value={rate === null ? null : rate * 100} size={78} label={tx("نرخ قبولی", "Pass rate")} caption={tx("قبولی", "pass")} display={rate === null ? "—" : f.pct(rate * 100, 0, false)} />
        <dl className="grid flex-1 grid-cols-3 gap-1.5 text-center">
          <div className="rounded-[var(--radius-sm)] bg-up/[0.07] py-1.5">
            <dt className="flex items-center justify-center gap-0.5 text-3xs text-up"><CircleCheck aria-hidden className="size-3" />{t.verification.PASS}</dt>
            <dd><Num className="text-sm font-semibold text-fg-1">{f.num(passed, 0)}</Num></dd>
          </div>
          <div className="rounded-[var(--radius-sm)] bg-down/[0.07] py-1.5">
            <dt className="flex items-center justify-center gap-0.5 text-3xs text-down"><CircleX aria-hidden className="size-3" />{t.verification.FAIL}</dt>
            <dd><Num className="text-sm font-semibold text-fg-1">{f.num(failed, 0)}</Num></dd>
          </div>
          <div className="rounded-[var(--radius-sm)] bg-white/[0.04] py-1.5">
            <dt className="text-3xs text-fg-3">{tx("در انتظار", "Pending")}</dt>
            <dd><Num className="text-sm font-semibold text-fg-1">{f.num(pending, 0)}</Num></dd>
          </div>
        </dl>
      </div>
      <div className="mt-2.5">
        <div className="mb-1 flex items-center gap-1 text-3xs text-fg-3">
          <RefreshCw aria-hidden className="size-3" />
          {tx("صف بازآموزی", "Retraining queue")} · <Num>{f.num(uni.retraining.length, 0)}</Num>
        </div>
        <ul className="space-y-1">
          {uni.retraining.map((r) => (
            <li key={r.agentId} className="flex items-center justify-between gap-2 rounded-[var(--radius-sm)] bg-white/[0.03] px-2 py-1 text-3xs">
              <span className="truncate text-fg-2">{l(r.agentName)}</span>
              <span className="shrink-0 text-fg-4">{t.severity[r.priority]}</span>
            </li>
          ))}
        </ul>
      </div>
    </DataCard>
  );
}

/* --------------------------------------------------------- system */

export function SystemHealthCard({ system, meta, className }: { system: SystemOverview; meta: DataMeta; className?: string }) {
  const { tx, l, t } = useI18n();
  const f = useFormat();
  const live = system.providers.filter((p) => p.status === "LIVE").length;
  const stateTone = (s: string) => (s === "UP" ? "up" : s === "DEGRADED" ? "warn" : s === "DOWN" ? "down" : "slate");
  return (
    <DataCard
      title={tx("سلامت سامانه", "System health")}
      subtitle={tx("سرویس‌ها، منابع و یکپارچگی Lane A", "Services, providers and Lane A integrity")}
      icon={Server}
      meta={meta}
      className={className}
      actions={
        <Link href="/system" className="text-3xs text-gold-300 hover:text-gold-100">
          {t.common.viewAll}
        </Link>
      }
    >
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-[var(--radius-sm)] bg-white/[0.03] p-2">
          <div className="text-3xs text-fg-4">{tx("منابع فعال", "Live providers")}</div>
          <Num className="text-base font-semibold text-fg-1">
            {f.num(live, 0)}/{f.num(system.providers.length, 0)}
          </Num>
        </div>
        <div className="rounded-[var(--radius-sm)] bg-white/[0.03] p-2">
          <div className="flex items-center gap-1 text-3xs text-fg-4">
            <ShieldCheck aria-hidden className="size-3" /> Lane A
          </div>
          <Chip tone={system.laneA.state === "PASS" ? "up" : system.laneA.state === "FAIL" ? "down" : "violet"} icon={system.laneA.state === "PASS" ? CircleCheck : CircleX} className="mt-1">
            {system.laneA.state}
          </Chip>
        </div>
      </div>
      <div className="mt-2">
        <div className="mb-0.5 flex items-center justify-between text-3xs text-fg-4">
          <span className="flex items-center gap-1"><Activity aria-hidden className="size-3" />CPU</span>
          <Num className="text-fg-2">{f.num(system.cpu[system.cpu.length - 1]?.v ?? null, 0)}%</Num>
        </div>
        <Sparkline data={system.cpu.map((p) => p.v)} height={26} label="CPU" />
      </div>
      <ul className="mt-1.5 space-y-1">
        {system.services.slice(0, 5).map((s) => (
          <li key={s.id} className="flex items-center justify-between gap-2 text-3xs">
            <span className="truncate text-fg-2">{l(s.name)}</span>
            <Chip tone={stateTone(s.state)}>{s.state}</Chip>
          </li>
        ))}
      </ul>
      <div className="mt-1.5 flex items-center justify-between text-3xs text-fg-4">
        <span>{tx("زمان کارکرد", "Uptime")}</span>
        <span className="text-fg-2">{f.duration(system.uptimeSec)}</span>
      </div>
    </DataCard>
  );
}
