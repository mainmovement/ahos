"use client";

import { Boxes, Bug, FlaskConical, Hammer, Wrench } from "lucide-react";
import type { DataEnvelope, WorkshopOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Chip } from "@/components/ui/chip";
import { Num, TimeAgo } from "@/components/ui/primitives";
import { SeverityChip } from "@/components/ui/status";

export function WorkshopView({ workshop }: { workshop: DataEnvelope<WorkshopOverview> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const d = workshop.data;
  return (
    <PageBody>
      <PageHeader title={t.nav.items.workshop} subtitle={tx("ساخت‌ها، مجموعه تست‌ها، پشته فناوری و مسائل باز", "Builds, test suites, tech stack and open issues")} icon={Wrench} />
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-2">
        <DataCard title={tx("ساخت‌ها", "Builds")} icon={Hammer} meta={workshop.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{tx("هدف", "Target")}</th>
                <th scope="col">{t.common.status}</th>
                <th scope="col" className="num-cell">{tx("مدت", "Duration")}</th>
                <th scope="col">{tx("کامیت", "Commit")}</th>
                <th scope="col" className="pe-3.5">{t.common.time}</th>
              </tr>
            </thead>
            <tbody>
              {d.builds.map((b) => (
                <tr key={b.id}>
                  <td className="ps-3.5"><bdi className="text-2xs text-fg-1">{b.target}</bdi></td>
                  <td><Chip tone={b.state === "PASS" ? "up" : b.state === "FAIL" ? "down" : b.state === "RUNNING" ? "gold" : "muted"}>{b.state}</Chip></td>
                  <td className="num-cell"><Num className="text-2xs text-fg-2">{b.durationSec === null ? "—" : `${f.num(b.durationSec, 0)}s`}</Num></td>
                  <td><bdi className="mono text-3xs text-gold-300">{b.commit}</bdi></td>
                  <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={b.at} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard title={tx("مجموعه تست‌ها", "Test suites")} subtitle={tx("نتایج نمایشی — شواهد واقعی در CI", "Demo results — real evidence lives in CI")} icon={FlaskConical} meta={workshop.meta}>
          <ul className="space-y-2.5">
            {d.tests.map((s) => {
              const total = s.passed + s.failed + s.skipped;
              return (
                <li key={s.suite}>
                  <div className="mb-1 flex items-center justify-between gap-2 text-2xs">
                    <bdi className="mono truncate text-fg-1">{s.suite}</bdi>
                    <span className="flex shrink-0 items-center gap-2 text-3xs">
                      <Num className="text-up">✓{f.num(s.passed, 0)}</Num>
                      <Num className={s.failed ? "text-down" : "text-fg-5"}>✗{f.num(s.failed, 0)}</Num>
                      <Num className="text-fg-4">↷{f.num(s.skipped, 0)}</Num>
                      <Num className="text-fg-5">{f.num(s.durationSec, 0)}s</Num>
                    </span>
                  </div>
                  <div className="flex h-1.5 overflow-hidden rounded-full bg-white/[0.05]" role="img" aria-label={`${s.passed}/${total}`}>
                    <div className="bg-up/80" style={{ width: `${(s.passed / total) * 100}%` }} />
                    <div className="bg-down/80" style={{ width: `${(s.failed / total) * 100}%` }} />
                    <div className="bg-fg-5" style={{ width: `${(s.skipped / total) * 100}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
        </DataCard>
      </div>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-2">
        <DataCard title={tx("پشته فناوری", "Tech stack")} icon={Boxes} meta={workshop.meta} bodyClassName="px-0 pb-0">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{t.common.name}</th>
                <th scope="col">{tx("نسخه", "Version")}</th>
                <th scope="col">{tx("مجوز", "License")}</th>
                <th scope="col" className="pe-3.5">{tx("نقش", "Role")}</th>
              </tr>
            </thead>
            <tbody>
              {d.stack.map((s) => (
                <tr key={s.name}>
                  <td className="ps-3.5"><bdi className="text-2xs font-medium text-fg-1">{s.name}</bdi></td>
                  <td><bdi className="mono text-3xs text-fg-2">{s.version}</bdi></td>
                  <td><Chip tone="muted"><bdi>{s.license}</bdi></Chip></td>
                  <td className="pe-3.5 text-3xs text-fg-3">{l(s.role)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>
        <DataCard title={tx("مسائل باز", "Open issues")} icon={Bug} meta={workshop.meta}>
          <ul className="space-y-2">
            {d.issues.map((i) => (
              <li key={i.id} className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-2.5 py-2">
                <bdi className="shrink-0 text-3xs font-semibold text-gold-300">{i.id}</bdi>
                <span className="min-w-0 flex-1 text-2xs text-fg-1">{l(i.title)}</span>
                <SeverityChip severity={i.severity} />
                <Chip tone={i.state === "DONE" ? "up" : i.state === "BLOCKED" ? "warn" : i.state === "IN_PROGRESS" ? "gold" : "muted"}>{i.state}</Chip>
              </li>
            ))}
          </ul>
        </DataCard>
      </div>
    </PageBody>
  );
}
