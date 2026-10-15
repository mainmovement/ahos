"use client";

import { Fragment, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronDown, Filter, Radar, Scale } from "lucide-react";
import type { CanonicalOutcome, DataEnvelope, OpportunitiesOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn, shortenAddress } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Notice } from "@/components/cards/blocks";
import { Meter, Num, TimeAgo } from "@/components/ui/primitives";
import { Segmented } from "@/components/ui/segmented";
import { ConfidenceChip, GateChip, IdentityChip, OutcomeChip, StatusChip } from "@/components/ui/status";

type OutcomeFilter = "all" | CanonicalOutcome;

export function OpportunitiesView({ data }: { data: DataEnvelope<OpportunitiesOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const [filter, setFilter] = useState<OutcomeFilter>("all");
  const [open, setOpen] = useState<string | null>(null);
  const rows = useMemo(() => data.data.rows.filter((r) => filter === "all" || r.outcome === filter), [data.data.rows, filter]);
  const max = data.data.funnel[0]?.count ?? 1;

  return (
    <PageBody>
      <PageHeader title={t.nav.items.opportunities} subtitle={tx("تصمیم‌های مرجع کانونی — رابط فقط نمایش می‌دهد", "Canonical-authority decisions — the UI only presents")} icon={Radar} />
      <Notice icon={<Scale />} tone="gold">
        <b>{tx("مرز اختیار:", "Authority boundary:")}</b> {l(data.data.authorityNote)}{" "}
        {tx("هیچ برچسب «فرصت داغ» یا درصد سود هدف نمایش داده نمی‌شود.", "No “hot opportunity” labels or target-return percentages are shown.")}
      </Notice>

      <DataCard title={tx("قیف شواهد", "Evidence funnel")} subtitle={tx("از کشف تا نامزد کاغذی", "From discovery to paper candidate")} icon={Filter} meta={data.meta}>
        <ol className="space-y-1.5">
          {data.data.funnel.map((s, i) => (
            <li key={s.stage.en} className="grid grid-cols-[minmax(120px,180px)_1fr_auto] items-center gap-3">
              <span className="truncate text-2xs text-fg-2">
                <Num className="me-1 text-fg-5">{f.num(i + 1, 0)}.</Num>
                {l(s.stage)}
              </span>
              <div className="h-5 overflow-hidden rounded-[var(--radius-sm)] bg-white/[0.03]">
                <div
                  className="h-full rounded-[var(--radius-sm)] bg-gradient-to-l from-gold-400/70 to-gold-700/40 shadow-[var(--shadow-glow-sm)] rtl:bg-gradient-to-r"
                  style={{ width: `${Math.max(2, (s.count / max) * 100)}%` }}
                />
              </div>
              <Num className="w-14 text-end text-xs font-semibold text-fg-1">{f.num(s.count, 0)}</Num>
            </li>
          ))}
        </ol>
      </DataCard>

      <DataCard
        title={tx("تصمیم‌های کانونی", "Canonical decisions")}
        subtitle={tx("برای دیدن دلایل، ریسک‌ها و ناشناخته‌ها ردیف را باز کنید", "Expand a row to see reasons, risks and unknowns")}
        icon={Radar}
        meta={data.meta}
        bodyClassName="px-0 pb-0"
        actions={
          <Segmented
            label={tx("فیلتر نتیجه", "Outcome filter")}
            size="xs"
            value={filter}
            onChange={setFilter}
            options={[
              { value: "all", label: t.common.all },
              { value: "PAPER_CANDIDATE", label: t.outcome.PAPER_CANDIDATE },
              { value: "WATCH", label: t.outcome.WATCH },
              { value: "MONITOR_ONLY", label: t.outcome.MONITOR_ONLY },
              { value: "REJECT", label: t.outcome.REJECT },
            ]}
          />
        }
      >
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{t.common.symbol}</th>
                <th scope="col">{tx("نتیجه", "Outcome")}</th>
                <th scope="col">{tx("هویت", "Identity")}</th>
                <th scope="col">{tx("دروازه امنیت", "Security gate")}</th>
                <th scope="col">{tx("اطمینان", "Confidence")}</th>
                <th scope="col" className="num-cell">{t.common.score}</th>
                <th scope="col" className="w-32">{tx("پوشش شواهد", "Evidence coverage")}</th>
                <th scope="col">{tx("دلیل اصلی", "Primary reason")}</th>
                <th scope="col" className="pe-3.5">{t.common.updated}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const expanded = open === r.tokenKey;
                return (
                  <Fragment key={r.tokenKey}>
                    <tr data-selected={expanded}>
                      <td className="ps-3.5">
                        <button type="button" onClick={() => setOpen(expanded ? null : r.tokenKey)} aria-expanded={expanded} className="flex items-center gap-1.5 text-start">
                          <ChevronDown aria-hidden className={cn("size-3.5 text-fg-4 transition-transform", !expanded && "-rotate-90 rtl:rotate-90")} />
                          <span>
                            <bdi className="block text-xs font-semibold text-fg-1">{r.symbol}</bdi>
                            <span className="block text-3xs text-fg-4">
                              {r.chain}
                              {r.address && <bdi className="mono ms-1 text-fg-5">{shortenAddress(r.address)}</bdi>}
                            </span>
                          </span>
                        </button>
                      </td>
                      <td><OutcomeChip outcome={r.outcome} /></td>
                      <td><IdentityChip state={r.identityState} /></td>
                      <td><GateChip state={r.securityState} /></td>
                      <td><ConfidenceChip confidence={r.confidence} /></td>
                      <td className="num-cell"><Num className="text-xs font-semibold text-fg-1">{r.score === null ? "—" : f.num(r.score, 0)}</Num></td>
                      <td>
                        <div className="flex items-center gap-1.5">
                          <Meter value={r.evidenceCoverage} max={1} tone={r.evidenceCoverage < 0.5 ? "warn" : "data"} label={tx("پوشش شواهد", "Evidence coverage")} />
                          <Num className="w-9 text-3xs text-fg-3">{f.pct(r.evidenceCoverage * 100, 0, false)}</Num>
                        </div>
                      </td>
                      <td className="max-w-[260px] truncate text-2xs text-fg-2">{l(r.primaryReason)}</td>
                      <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={r.updatedAt} /></td>
                    </tr>
                    {expanded && (
                      <tr>
                        <td colSpan={9} className="bg-white/[0.015] px-3.5 py-3">
                          <div className="grid grid-cols-1 gap-3 @2xl:grid-cols-3">
                            {[
                              { title: tx("دلایل", "Reasons"), items: r.reasons, tone: "text-up" },
                              { title: tx("ریسک‌ها", "Risks"), items: r.risks, tone: "text-down" },
                              { title: tx("ناشناخته‌ها", "Unknowns"), items: r.unknowns, tone: "text-violet" },
                            ].map((blk) => (
                              <div key={blk.title} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] p-2.5">
                                <div className={cn("mb-1 text-3xs font-semibold", blk.tone)}>{blk.title}</div>
                                {blk.items.length ? (
                                  <ul className="space-y-1 text-2xs text-fg-2">
                                    {blk.items.map((it) => (
                                      <li key={it.en}>• {l(it)}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <p className="text-3xs text-fg-5">{tx("ثبت نشده", "None recorded")}</p>
                                )}
                              </div>
                            ))}
                          </div>
                          <div className="mt-2 flex flex-wrap items-center gap-2 text-3xs text-fg-4">
                            <StatusChip status={r.status} />
                            <span>paper_allowed: <b className={r.paperAllowed ? "text-up" : "text-fg-3"}>{String(r.paperAllowed)}</b></span>
                            <span>monitoring_only: <b className="text-fg-3">{String(r.monitoringOnly)}</b></span>
                            {r.address && (
                              <Link href={`/tokens?token=${encodeURIComponent(r.tokenKey)}`} className="text-gold-300 hover:text-gold-100">
                                {tx("پرونده توکن ←", "Token dossier →")}
                              </Link>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </DataCard>
    </PageBody>
  );
}
