"use client";

import { Activity, BookText, Building, ClipboardList, Cpu, Gauge, ListChecks, ShieldBan } from "lucide-react";
import type { Agent, AgentsOverview } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { Dialog, DialogDescription, DialogTitle, SheetContent } from "@/components/ui/dialog";
import { Chip } from "@/components/ui/chip";
import { Num, TimeAgo } from "@/components/ui/primitives";
import { ImplementationChip, RuntimeChip, VerificationChip } from "@/components/ui/status";
import { ActivityFeed } from "./activity-feed";
import { AgentGlyph, MaturityDots } from "./agent-glyph";

/** Side drawer with the full agent record. Opens from the inline-end edge. */
export function AgentInspector({ agent, departments, onClose }: { agent: Agent | null; departments: AgentsOverview["departments"]; onClose: () => void }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const dept = agent ? departments.find((d) => d.id === agent.department) : undefined;
  return (
    <Dialog open={!!agent} onOpenChange={(o) => !o && onClose()}>
      {agent && (
        <SheetContent closeLabel={t.common.close} aria-describedby="agent-inspector-desc">
          <header className="flex items-start gap-3 border-b border-[var(--line-hairline)] p-4 pe-12">
            <AgentGlyph code={agent.code} size={48} />
            <div className="min-w-0">
              <DialogTitle className="text-base font-bold text-fg-1">{l(agent.name)}</DialogTitle>
              <DialogDescription id="agent-inspector-desc" className="mt-0.5 text-2xs text-fg-3">
                {l(agent.role)}
              </DialogDescription>
              <div className="mt-2 flex flex-wrap gap-1.5">
                <RuntimeChip state={agent.runtime} size="sm" />
                <ImplementationChip status={agent.implementation} size="sm" />
              </div>
            </div>
          </header>
          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4 text-2xs">
            <p className="rounded-[var(--radius-md)] border border-dashed border-info/40 bg-info/[0.05] px-2.5 py-2 text-3xs leading-relaxed text-fg-2">
              {tx("ثبت‌شده ≠ عملیاتی · برنامه‌ریزی‌شده ≠ زنده · نامعلوم ≠ تأییدشده. وضعیت اجرا، پیاده‌سازی و راستی‌آزمایی سه محور مستقل‌اند.", "REGISTERED ≠ OPERATIONAL · PLANNED ≠ LIVE · UNKNOWN ≠ VERIFIED. Runtime, implementation and verification are independent axes.")}
            </p>
            <dl className="grid grid-cols-2 gap-2">
              <Field icon={<Building className="size-3" />} label={tx("دپارتمان", "Department")} value={dept ? l(dept.name) : agent.department} />
              <Field icon={<Cpu className="size-3" />} label={tx("شناسه", "ID")} value={<bdi className="mono text-3xs">{agent.id}</bdi>} />
              <Field icon={<Gauge className="size-3" />} label={tx("سطح بلوغ", "Maturity")} value={<MaturityDots level={agent.maturity} />} />
              <Field icon={<ListChecks className="size-3" />} label={tx("راستی‌آزمایی", "Verification")} value={<VerificationChip status={agent.verification.status} kind={agent.verification.kind} />} />
            </dl>
            <section>
              <h3 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-fg-1">
                <ClipboardList aria-hidden className="size-3.5 text-gold-300" />
                {tx("کار جاری", "Current task")}
              </h3>
              <div className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5">
                {agent.currentTask ? <p className="text-fg-1">{l(agent.currentTask)}</p> : <p className="text-fg-4">{tx("بدون کار جاری", "No current task")}</p>}
                <div className="mt-1 text-3xs text-fg-5">
                  {tx("آخرین فعالیت", "Last activity")}: {agent.lastActivityAt ? <TimeAgo iso={agent.lastActivityAt} /> : t.common.never}
                </div>
              </div>
            </section>
            <section className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-[var(--radius-md)] bg-white/[0.03] p-2">
                <div className="text-3xs text-fg-4">{tx("کار ۲۴س", "Tasks 24h")}</div>
                <Num className="text-sm font-semibold text-fg-1">{agent.metrics.tasks24h === null ? "—" : f.num(agent.metrics.tasks24h, 0)}</Num>
              </div>
              <div className="rounded-[var(--radius-md)] bg-white/[0.03] p-2">
                <div className="text-3xs text-fg-4">{tx("موفقیت", "Success")}</div>
                <Num className="text-sm font-semibold text-fg-1">{agent.metrics.successRate === null ? "—" : f.pct(agent.metrics.successRate * 100, 0, false)}</Num>
              </div>
              <div className="rounded-[var(--radius-md)] bg-white/[0.03] p-2">
                <div className="text-3xs text-fg-4">{tx("تأخیر", "Latency")}</div>
                <Num className="text-sm font-semibold text-fg-1">{agent.metrics.avgLatencyMs === null ? "—" : `${f.num(agent.metrics.avgLatencyMs / 1000, 1)}s`}</Num>
              </div>
            </section>
            <section className="grid grid-cols-1 gap-2 @lg:grid-cols-2">
              <div>
                <h3 className="mb-1 text-3xs font-semibold text-up">{tx("قابلیت‌ها", "Capabilities")}</h3>
                {agent.capabilities.length ? (
                  <ul className="space-y-0.5 text-fg-2">
                    {agent.capabilities.map((c) => (
                      <li key={c.en}>• {l(c)}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-3xs text-fg-5">{tx("هیچ قابلیتی اعطا نشده", "No capability granted")}</p>
                )}
              </div>
              <div>
                <h3 className="mb-1 flex items-center gap-1 text-3xs font-semibold text-warn">
                  <ShieldBan aria-hidden className="size-3" />
                  {tx("محدودیت‌ها", "Limitations")}
                </h3>
                <ul className="space-y-0.5 text-fg-2">
                  {agent.limitations.map((c) => (
                    <li key={c.en}>• {l(c)}</li>
                  ))}
                </ul>
              </div>
            </section>
            {agent.sourceDoc && (
              <section className="flex items-center gap-1.5 text-3xs text-fg-4">
                <BookText aria-hidden className="size-3" />
                {tx("سند مرجع", "Reference")}: <bdi className="mono text-fg-3">{agent.sourceDoc}</bdi>
              </section>
            )}
            <section>
              <h3 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-fg-1">
                <Activity aria-hidden className="size-3.5 text-gold-300" />
                {tx("رویدادهای اخیر", "Recent events")}
              </h3>
              {agent.events.length ? (
                <ActivityFeed events={agent.events} index={{ [agent.id]: { name: agent.name, runtime: agent.runtime, code: agent.code } }} />
              ) : (
                <Chip tone="muted">{t.common.noData}</Chip>
              )}
            </section>
          </div>
        </SheetContent>
      )}
    </Dialog>
  );
}

function Field({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2">
      <dt className="mb-1 flex items-center gap-1 text-3xs text-fg-4">
        {icon}
        {label}
      </dt>
      <dd className="text-fg-1">{value}</dd>
    </div>
  );
}
