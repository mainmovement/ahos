"use client";

import { BookLock, Check, FileCheck2, Fingerprint, ScrollText, Scale, X } from "lucide-react";
import type { AcceptanceState, DataEnvelope, GovernanceOverview } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Chip, type ChipTone } from "@/components/ui/chip";
import { TimeAgo } from "@/components/ui/primitives";

const ACC_TONE: Record<AcceptanceState, ChipTone> = { PENDING: "gold", ACCEPTED: "up", REJECTED: "down", DEFERRED: "slate", EXPIRED: "muted" };

export function GovernanceView({ gov }: { gov: DataEnvelope<GovernanceOverview> }) {
  const { t, l, tx } = useI18n();
  const d = gov.data;
  const acc: Record<AcceptanceState, string> = { PENDING: tx("در انتظار", "Pending"), ACCEPTED: tx("پذیرفته", "Accepted"), REJECTED: tx("ردشده", "Rejected"), DEFERRED: tx("معوق", "Deferred"), EXPIRED: tx("منقضی", "Expired") };
  return (
    <PageBody>
      <PageHeader title={t.nav.items.governance} subtitle={tx("قانون اساسی، صف تأیید، دفتر ممیزی و مرزهای اختیار", "Constitution, approvals queue, audit ledger and authority boundaries")} icon={ScrollText} actions={<Chip tone="gold" icon={BookLock} size="sm"><bdi>{d.policyVersion}</bdi></Chip>} />
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-7" title={tx("اصول قانون اساسی", "Constitutional principles")} icon={BookLock} meta={gov.meta}>
          <ol className="space-y-2">
            {d.constitution.map((c) => (
              <li key={c.id} className="flex gap-3 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-3">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full border border-gold-400/40 bg-gold-400/10 text-2xs font-bold text-gold-200" dir="ltr">
                  {c.id}
                </span>
                <div>
                  <h3 className="text-xs font-semibold text-fg-1">{l(c.title)}</h3>
                  <p className="mt-0.5 text-2xs leading-relaxed text-fg-3">{l(c.summary)}</p>
                </div>
              </li>
            ))}
          </ol>
        </DataCard>
        <DataCard className="@4xl:col-span-5" title={tx("صف تأیید", "Approvals queue")} subtitle={tx("هیچ تغییر حساسی بدون پذیرش انسانی", "No sensitive change without human acceptance")} icon={FileCheck2} meta={gov.meta}>
          <ul className="space-y-2">
            {d.approvals.map((a) => (
              <li key={a.id} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5">
                <div className="flex items-center gap-1.5">
                  <bdi className="text-3xs font-semibold text-gold-300">{a.id}</bdi>
                  <Chip tone={ACC_TONE[a.state]}>{acc[a.state]}</Chip>
                  <Chip tone="muted"><bdi>{a.scope}</bdi></Chip>
                  <TimeAgo iso={a.at} className="ms-auto text-3xs text-fg-5" />
                </div>
                <p className="mt-1 text-2xs text-fg-1">{l(a.title)}</p>
                <p className="mt-0.5 text-3xs text-fg-4">
                  {tx("درخواست‌دهنده", "Requested by")}: <bdi className="mono">{a.requestedBy}</bdi>
                </p>
              </li>
            ))}
          </ul>
        </DataCard>
      </div>
      <DataCard title={tx("مرزهای اختیار", "Authority boundaries")} subtitle={tx("رابط TypeScript نمایش می‌دهد؛ پایتون تصمیم می‌گیرد", "TypeScript presents; Python decides")} icon={Scale} meta={gov.meta} bodyClassName="px-0 pb-0">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col" className="ps-3.5">{tx("سطح", "Surface")}</th>
              <th scope="col">{tx("مجاز", "May")}</th>
              <th scope="col" className="pe-3.5">{tx("ممنوع", "Must not")}</th>
            </tr>
          </thead>
          <tbody>
            {d.boundaries.map((b) => (
              <tr key={b.surface.en}>
                <td className="ps-3.5 text-xs font-medium text-fg-1">{l(b.surface)}</td>
                <td className="whitespace-normal text-2xs text-fg-2"><span className="inline-flex items-start gap-1"><Check aria-hidden className="mt-0.5 size-3 shrink-0 text-up" />{l(b.may)}</span></td>
                <td className="whitespace-normal pe-3.5 text-2xs text-fg-2"><span className="inline-flex items-start gap-1"><X aria-hidden className="mt-0.5 size-3 shrink-0 text-down" />{l(b.mustNot)}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </DataCard>
      <DataCard title={tx("دفتر ممیزی (فقط افزودنی)", "Audit ledger (append-only)")} icon={Fingerprint} meta={gov.meta} bodyClassName="px-0 pb-0">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col" className="ps-3.5">{t.common.time}</th>
              <th scope="col">{tx("کنشگر", "Actor")}</th>
              <th scope="col">{tx("اقدام", "Action")}</th>
              <th scope="col">{tx("هدف", "Target")}</th>
              <th scope="col" className="pe-3.5">{tx("هش", "Hash")}</th>
            </tr>
          </thead>
          <tbody>
            {d.audit.map((a) => (
              <tr key={a.id}>
                <td className="ps-3.5 text-3xs text-fg-4"><TimeAgo iso={a.at} /></td>
                <td><bdi className="mono text-3xs text-fg-2">{a.actor}</bdi></td>
                <td className="text-2xs text-fg-1">{l(a.action)}</td>
                <td><bdi className="mono text-3xs text-fg-3">{a.target}</bdi></td>
                <td className="pe-3.5"><bdi className="mono text-3xs text-gold-300">{a.hash}</bdi></td>
              </tr>
            ))}
          </tbody>
        </table>
      </DataCard>
    </PageBody>
  );
}
