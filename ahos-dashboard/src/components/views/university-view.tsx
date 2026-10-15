"use client";

import { useMemo } from "react";
import { BookOpenCheck, ClipboardCheck, GraduationCap, LineChart, RefreshCw, Users } from "lucide-react";
import type { DataEnvelope, UniversityOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Notice, StatTile } from "@/components/cards/blocks";
import { EChart, useChartContext } from "@/components/charts/echart";
import { Sparkline } from "@/components/charts/sparkline";
import { Chip } from "@/components/ui/chip";
import { Meter, Num, TimeAgo } from "@/components/ui/primitives";
import { SeverityChip, VerificationChip } from "@/components/ui/status";
import { alpha } from "@/lib/tokens";

export function UniversityView({ uni }: { uni: DataEnvelope<UniversityOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const d = uni.data;
  const c = useChartContext();
  const stateLabel = { enrolled: tx("ثبت‌نام", "Enrolled"), examining: tx("در حال آزمون", "Examining"), passed: tx("قبول", "Passed"), failed: tx("مردود", "Failed"), retraining: tx("بازآموزی", "Retraining") } as const;
  const stateTone = { enrolled: "info", examining: "gold", passed: "up", failed: "down", retraining: "warn" } as const;
  const calibrationOption = useMemo(() => {
    const { p } = c;
    return {
      backgroundColor: "transparent",
      grid: { left: 36, right: 16, top: 16, bottom: 30 },
      tooltip: { ...c.tooltip, trigger: "axis" },
      xAxis: { type: "value", min: 0, max: 1, name: tx("اطمینان پیش‌بینی‌شده", "Predicted"), nameLocation: "middle", nameGap: 20, nameTextStyle: { color: p.fg4, fontSize: 10 }, axisLabel: { ...c.axisLabel, formatter: (v: number) => f.pct(v * 100, 0, false) }, splitLine: c.splitLine, axisLine: c.axisLine },
      yAxis: { type: "value", min: 0, max: 1, axisLabel: { ...c.axisLabel, formatter: (v: number) => f.pct(v * 100, 0, false) }, splitLine: c.splitLine },
      series: [
        { name: tx("کالیبراسیون کامل", "Perfect calibration"), type: "line", data: [[0, 0], [1, 1]], showSymbol: false, lineStyle: { color: alpha(p.fg3, 0.5), type: "dashed", width: 1 } },
        {
          name: tx("مشاهده‌شده", "Observed"),
          type: "line",
          data: d.calibration.filter((b) => b.observed !== null).map((b) => [b.predicted, b.observed]),
          symbol: "circle",
          symbolSize: 7,
          lineStyle: { color: p.gold, width: 1.8 },
          itemStyle: { color: p.gold, borderColor: p.bg, borderWidth: 1.5 },
        },
      ],
    };
  }, [c, f, d.calibration, tx]);

  const passRate = d.passRateTrend[d.passRateTrend.length - 1] ?? null;

  return (
    <PageBody>
      <PageHeader title={t.nav.items.university} subtitle={tx("آموزش عامل‌ها، آزمون‌ها، نتایج قبول/مردود و صف بازآموزی", "Agent training, exams, pass/fail results and the retraining queue")} icon={GraduationCap} />
      <Notice icon={<ClipboardCheck />} tone="info">
        {tx("آزمون «خودارزیابی» با آزمون «مستقل» هم‌ارز نیست؛ هر نتیجه نوع راستی‌آزمایی خود را نشان می‌دهد.", "A SELF_CHECK exam is not equivalent to an INDEPENDENT one; every result shows its verification kind.")}
      </Notice>
      <section className="grid grid-cols-2 gap-3 @4xl:grid-cols-4">
        <StatTile label={tx("دانشجو (عامل)", "Students (agents)")} value={f.num(d.students.length, 0)} icon={<Users className="size-3" />} />
        <StatTile label={tx("نرخ قبولی", "Pass rate")} value={passRate === null ? "—" : f.pct(passRate * 100, 0, false)} tone="gold" hint={<Sparkline data={d.passRateTrend} height={20} area={false} label="pass rate trend" />} />
        <StatTile label={tx("آزمون‌ها", "Exams")} value={f.num(d.exams.length, 0)} icon={<BookOpenCheck className="size-3" />} />
        <StatTile label={tx("صف بازآموزی", "Retraining queue")} value={f.num(d.retraining.length, 0)} tone="down" icon={<RefreshCw className="size-3" />} />
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-7" title={tx("عامل‌ها در دوره آموزشی", "Agents in training")} icon={Users} meta={uni.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("عامل", "Agent")}</th>
                <th scope="col">{tx("دوره", "Program")}</th>
                <th scope="col" className="num-cell">{tx("سطح", "Level")}</th>
                <th scope="col" className="w-36">{tx("پیشرفت", "Progress")}</th>
                <th scope="col" className="pe-3.5">{t.common.status}</th>
              </tr>
            </thead>
            <tbody>
              {d.students.map((s) => (
                <tr key={s.agentId}>
                  <td className="ps-3.5 text-xs font-medium text-fg-1">{l(s.name)}</td>
                  <td className="text-2xs text-fg-3">{l(s.program)}</td>
                  <td className="num-cell"><Num className="text-xs text-fg-2">L{f.num(s.level, 0)}</Num></td>
                  <td>
                    <div className="flex items-center gap-1.5">
                      <Meter value={s.progress} max={1} label={tx("پیشرفت", "Progress")} />
                      <Num className="w-9 text-3xs text-fg-3">{f.pct(s.progress * 100, 0, false)}</Num>
                    </div>
                  </td>
                  <td className="pe-3.5"><Chip tone={stateTone[s.state]}>{stateLabel[s.state]}</Chip></td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard className="@4xl:col-span-5" title={tx("منحنی کالیبراسیون اطمینان", "Confidence calibration curve")} subtitle={tx("زیر خط = بیش‌اطمینانی", "Below the line = overconfidence")} icon={LineChart} meta={uni.meta}>
          <EChart option={calibrationOption} height={250} label={tx("منحنی کالیبراسیون", "Calibration curve")} />
        </DataCard>
      </div>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("آزمون‌ها", "Exams")} icon={ClipboardCheck} meta={uni.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("آزمون", "Exam")}</th>
                <th scope="col">{tx("عامل", "Agent")}</th>
                <th scope="col" className="num-cell">{tx("نمره / حد قبولی", "Score / pass mark")}</th>
                <th scope="col">{tx("نتیجه", "Result")}</th>
                <th scope="col" className="pe-3.5">{t.common.time}</th>
              </tr>
            </thead>
            <tbody>
              {d.exams.map((e) => (
                <tr key={e.id}>
                  <td className="ps-3.5 text-2xs text-fg-1">{l(e.title)}</td>
                  <td className="text-2xs text-fg-3">{l(e.agentName)}</td>
                  <td className="num-cell">
                    <Num className={cn("text-xs font-semibold", e.score === null ? "text-fg-4" : e.score >= e.passMark ? "text-up" : "text-down")}>{e.score === null ? "—" : f.num(e.score, 0)}</Num>
                    <Num className="text-3xs text-fg-5"> / {f.num(e.passMark, 0)}</Num>
                  </td>
                  <td>
                    {e.result === "PENDING" ? <Chip tone="info">{tx("در انتظار", "Pending")}</Chip> : <VerificationChip status={e.result} kind={e.kind} />}
                  </td>
                  <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={e.at} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard className="@4xl:col-span-4" title={tx("صف بازآموزی", "Retraining queue")} icon={RefreshCw} meta={uni.meta}>
          <ul className="space-y-2">
            {d.retraining.map((r) => (
              <li key={r.agentId} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-fg-1">{l(r.agentName)}</span>
                  <SeverityChip severity={r.priority} />
                </div>
                <p className="mt-1 text-2xs text-fg-3">{l(r.reason)}</p>
                <TimeAgo iso={r.queuedAt} className="text-3xs text-fg-5" />
              </li>
            ))}
          </ul>
          <div className="mt-3 space-y-1.5">
            <div className="text-3xs font-semibold text-fg-4">{tx("دوره‌ها", "Programs")}</div>
            {d.programs.map((p) => (
              <div key={p.id} className="flex items-center gap-2 text-2xs">
                <span className="min-w-0 flex-1 truncate text-fg-2">{l(p.name)}</span>
                <Num className="text-3xs text-fg-4">{f.num(p.enrolled, 0)}</Num>
                <Num className="w-10 text-end text-3xs text-fg-2">{p.passRate === null ? "—" : f.pct(p.passRate * 100, 0, false)}</Num>
              </div>
            ))}
          </div>
        </DataCard>
      </div>
    </PageBody>
  );
}
