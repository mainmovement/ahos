"use client";

import { BookMarked, FlaskConical, Lightbulb, Microscope, Telescope } from "lucide-react";
import type { DataEnvelope, EpistemicPosture, MissionState, ResearchOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { StatTile } from "@/components/cards/blocks";
import { Chip, type ChipTone } from "@/components/ui/chip";
import { Meter, Num, TimeAgo } from "@/components/ui/primitives";
import { VerificationChip } from "@/components/ui/status";

const MISSION_TONE: Record<MissionState, ChipTone> = {
  DRAFT: "muted", PLANNING: "info", PROPOSED: "info", AUTHORIZED: "gold", ACTIVE: "up", WAITING: "slate", BLOCKED: "warn", VERIFICATION: "violet", ACCEPTANCE: "gold", COMPLETE: "up", FAILED: "down", CANCELLED: "muted", REJECTED: "down",
};
const POSTURE_TONE: Record<EpistemicPosture, ChipTone> = { KNOWN: "up", UNCERTAIN: "gold", UNKNOWN: "violet", CONTRADICTORY: "warn", NOVEL: "data" };

export function ResearchView({ research }: { research: DataEnvelope<ResearchOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const d = research.data;
  const posture: Record<EpistemicPosture, string> = { KNOWN: tx("شناخته‌شده", "Known"), UNCERTAIN: tx("نامطمئن", "Uncertain"), UNKNOWN: tx("نامعلوم", "Unknown"), CONTRADICTORY: tx("متناقض", "Contradictory"), NOVEL: tx("نوظهور", "Novel") };
  const evidenceLabel = { NONE: tx("بدون شواهد", "None"), PARTIAL: tx("جزئی", "Partial"), SUFFICIENT: tx("کافی", "Sufficient"), STALE: tx("کهنه", "Stale"), CONTRADICTED: tx("نقض‌شده", "Contradicted") } as const;
  const verifMap = { NOT_REQUESTED: "UNVERIFIED", PENDING: "UNVERIFIED", PASS: "PASS", FAIL: "FAIL", INCONCLUSIVE: "INCONCLUSIVE" } as const;
  const active = d.missions.filter((m) => m.state === "ACTIVE" || m.state === "VERIFICATION").length;

  return (
    <PageBody>
      <PageHeader title={t.nav.items.research} subtitle={tx("مأموریت‌ها، فرضیه‌ها، آزمایش‌ها و مقالات — با وضعیت معرفتی صریح", "Missions, hypotheses, experiments and papers — with explicit epistemic posture")} icon={FlaskConical} />
      <section className="grid grid-cols-2 gap-3 @4xl:grid-cols-4">
        <StatTile label={tx("مأموریت‌ها", "Missions")} value={f.num(d.missions.length, 0)} icon={<Telescope className="size-3" />} />
        <StatTile label={tx("فعال / راستی‌آزمایی", "Active / verifying")} value={f.num(active, 0)} tone="gold" />
        <StatTile label={tx("فرضیه‌ها", "Hypotheses")} value={f.num(d.hypotheses.length, 0)} icon={<Lightbulb className="size-3" />} />
        <StatTile label={tx("مقالات در صف", "Papers queued")} value={f.num(d.papers.filter((p) => p.state === "QUEUED").length, 0)} tone="data" />
      </section>

      <DataCard title={tx("مأموریت‌های پژوهشی", "Research missions")} subtitle={tx("چرخه حیات · شواهد · راستی‌آزمایی · پذیرش — ابعاد مستقل", "Lifecycle · evidence · verification · acceptance — independent axes")} icon={Telescope} meta={research.meta} bodyClassName="px-0 pb-0">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("مأموریت", "Mission")}</th>
                <th scope="col">{tx("چرخه حیات", "Lifecycle")}</th>
                <th scope="col">{tx("شواهد", "Evidence")}</th>
                <th scope="col">{tx("راستی‌آزمایی", "Verification")}</th>
                <th scope="col">{tx("پذیرش", "Acceptance")}</th>
                <th scope="col">{tx("برچسب‌ها", "Tags")}</th>
                <th scope="col" className="pe-3.5">{t.common.updated}</th>
              </tr>
            </thead>
            <tbody>
              {d.missions.map((m) => (
                <tr key={m.id}>
                  <td className="ps-3.5">
                    <bdi className="me-1.5 text-3xs text-fg-5">{m.id}</bdi>
                    <span className="text-xs text-fg-1">{l(m.title)}</span>
                  </td>
                  <td><Chip tone={MISSION_TONE[m.state]}>{m.state}</Chip></td>
                  <td><Chip tone={m.evidence === "SUFFICIENT" ? "up" : m.evidence === "CONTRADICTED" ? "down" : m.evidence === "STALE" ? "warn" : m.evidence === "NONE" ? "muted" : "info"}>{evidenceLabel[m.evidence]}</Chip></td>
                  <td>{m.verification === "PENDING" ? <Chip tone="info">{tx("در انتظار", "Pending")}</Chip> : m.verification === "NOT_REQUESTED" ? <Chip tone="muted">{tx("درخواست نشده", "Not requested")}</Chip> : <VerificationChip status={verifMap[m.verification]} kind={m.verificationKind} />}</td>
                  <td><Chip tone={m.acceptance === "ACCEPTED" ? "up" : m.acceptance === "REJECTED" ? "down" : m.acceptance === "PENDING" ? "gold" : "muted"}>{m.acceptance}</Chip></td>
                  <td className="text-3xs text-fg-4">{m.tags.map((tg) => <bdi key={tg} className="me-1 rounded bg-white/[0.04] px-1">{tg}</bdi>)}</td>
                  <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={m.updatedAt} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataCard>

      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-7" title={tx("فرضیه‌ها", "Hypotheses")} subtitle={tx("شواهد موافق در برابر مخالف — بدون میانگین‌گیری کور", "Supporting vs. opposing evidence — no blind averaging")} icon={Lightbulb} meta={research.meta}>
          <ul className="space-y-2">
            {d.hypotheses.map((h) => {
              const total = h.support + h.against;
              return (
                <li key={h.id} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5">
                  <div className="flex items-start gap-2">
                    <bdi className="mt-0.5 shrink-0 text-3xs font-semibold text-gold-300">{h.id}</bdi>
                    <p className="min-w-0 flex-1 text-2xs leading-relaxed text-fg-1">{l(h.statement)}</p>
                    <Chip tone={POSTURE_TONE[h.posture]}>{posture[h.posture]}</Chip>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <Num className="w-8 text-3xs text-up">+{f.num(h.support, 0)}</Num>
                    <div className="flex h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.05]" role="img" aria-label={`${h.support} / ${h.against}`}>
                      {total > 0 ? (
                        <>
                          <div className="bg-up/80" style={{ width: `${(h.support / total) * 100}%` }} />
                          <div className="bg-down/80" style={{ width: `${(h.against / total) * 100}%` }} />
                        </>
                      ) : (
                        <div className="w-full bg-[repeating-linear-gradient(135deg,rgb(167_139_250/0.3)_0_4px,transparent_4px_8px)]" />
                      )}
                    </div>
                    <Num className="w-8 text-end text-3xs text-down">−{f.num(h.against, 0)}</Num>
                  </div>
                </li>
              );
            })}
          </ul>
        </DataCard>
        <div className="flex flex-col gap-3 @4xl:col-span-5">
          <DataCard title={tx("آزمایش‌ها", "Experiments")} icon={Microscope} meta={research.meta}>
            <ul className="space-y-1.5">
              {d.experiments.map((x) => (
                <li key={x.id} className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--line-subtle)] px-2.5 py-2">
                  <span className="min-w-0 flex-1 truncate text-2xs text-fg-1">{l(x.title)}</span>
                  <bdi className="text-3xs text-fg-4">{x.metric}</bdi>
                  <Num className="w-10 text-end text-2xs text-fg-2">{x.value === null ? "—" : f.num(x.value, 2)}</Num>
                  <Chip tone={x.state === "DONE" ? "up" : x.state === "RUNNING" ? "gold" : x.state === "FAILED" ? "down" : "muted"}>{x.state}</Chip>
                </li>
              ))}
            </ul>
          </DataCard>
          <DataCard title={tx("مقالات", "Papers")} icon={BookMarked} meta={research.meta}>
            <ul className="space-y-1.5">
              {d.papers.map((p) => (
                <li key={p.id} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] px-2.5 py-2">
                  <bdi className="block text-2xs text-fg-1" dir="ltr">{p.title}</bdi>
                  <div className="mt-1 flex items-center gap-2 text-3xs text-fg-4">
                    <bdi>{p.venue}</bdi>
                    <Num>{p.year}</Num>
                    <div className="ms-auto flex w-28 items-center gap-1.5">
                      <Meter value={p.relevance} max={1} tone="data" label={tx("ارتباط", "Relevance")} />
                    </div>
                    <Chip tone={p.state === "SUMMARIZED" ? "up" : p.state === "READ" ? "info" : "muted"} className={cn()}>{p.state}</Chip>
                  </div>
                </li>
              ))}
            </ul>
          </DataCard>
        </div>
      </div>
    </PageBody>
  );
}
