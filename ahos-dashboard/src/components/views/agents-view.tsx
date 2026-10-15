"use client";

import { useMemo, useState } from "react";
import { Bot, Info } from "lucide-react";
import type { AgentRuntimeState, AgentsOverview, DataEnvelope, DepartmentId } from "@/lib/api/types";
import { AGENT_RUNTIME_STATES } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { useSound } from "@/lib/audio/use-sound";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { CardFooter } from "@/components/cards/data-card";
import { Notice } from "@/components/cards/blocks";
import { AgentInspector } from "@/components/agents/agent-inspector";
import { AgentGlyph, MaturityDots } from "@/components/agents/agent-glyph";
import { TimeAgo } from "@/components/ui/primitives";
import { ImplementationChip, RuntimeChip } from "@/components/ui/status";

export function AgentsView({ agents, initialAgent }: { agents: DataEnvelope<AgentsOverview>; initialAgent?: string }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const play = useSound();
  const all = agents.data.agents;
  const [runtime, setRuntime] = useState<AgentRuntimeState | "all">("all");
  const [dept, setDept] = useState<DepartmentId | "all">("all");
  const [openId, setOpenId] = useState<string | null>(initialAgent && all.some((a) => a.id === initialAgent) ? initialAgent : null);
  const counts = useMemo(() => {
    const c = Object.fromEntries(AGENT_RUNTIME_STATES.map((s) => [s, 0])) as Record<AgentRuntimeState, number>;
    all.forEach((a) => c[a.runtime]++);
    return c;
  }, [all]);
  const list = all.filter((a) => (runtime === "all" || a.runtime === runtime) && (dept === "all" || a.department === dept));
  const open = all.find((a) => a.id === openId) ?? null;

  return (
    <PageBody>
      <PageHeader title={t.nav.items.agents} subtitle={tx("هر عامل با وضعیت صریح: پیاده‌سازی، اجرا، بلوغ و راستی‌آزمایی", "Every agent with explicit status: implementation, runtime, maturity and verification")} icon={Bot} />
      <Notice icon={<Info />} tone="info">
        {tx(
          "۱۹ نقش سازمانی از نقشه «PLANNED_19_AGENT_MAP» هنوز عملیاتی نیستند (بلوغ ۰). وضعیت‌های اجرای اجزای موجود در این نسخه نمایشی‌اند. نماد شش‌ضلعی فقط شناسه است و به معنی در حال کار بودن نیست.",
          "The 19 organizational roles from PLANNED_19_AGENT_MAP are not operational (maturity 0). Runtime states of the existing components are demo values. The hexagon glyph is only an identifier and never implies activity.",
        )}
      </Notice>

      <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label={tx("فیلتر وضعیت اجرا", "Runtime filter")}>
        <button type="button" onClick={() => setRuntime("all")} aria-pressed={runtime === "all"} className={cn("rounded-full border px-2.5 py-1 text-3xs transition-colors", runtime === "all" ? "border-gold-400/50 bg-gold-400/10 text-gold-100" : "border-white/10 text-fg-3 hover:text-fg-1")}>
          {t.common.all} · {f.num(all.length, 0)}
        </button>
        {AGENT_RUNTIME_STATES.filter((s) => counts[s] > 0).map((s) => (
          <button key={s} type="button" onClick={() => setRuntime(s)} aria-pressed={runtime === s} className={cn("flex items-center gap-1 rounded-full border px-1.5 py-0.5 transition-colors", runtime === s ? "border-gold-400/50 bg-gold-400/10" : "border-transparent hover:border-white/10")}>
            <RuntimeChip state={s} />
            <span className="num text-3xs text-fg-3">{f.num(counts[s], 0)}</span>
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-white/10" aria-hidden />
        <label className="flex items-center gap-1.5 text-3xs text-fg-4">
          {tx("دپارتمان", "Department")}
          <select value={dept} onChange={(e) => setDept(e.target.value as DepartmentId | "all")} className="h-7 rounded-[var(--radius-sm)] border border-[var(--line-subtle)] bg-[var(--surface-input)] px-2 text-2xs text-fg-1 focus:border-gold-400/50 focus:outline-none">
            <option value="all">{t.common.all}</option>
            {agents.data.departments.map((d) => (
              <option key={d.id} value={d.id}>
                {l(d.name)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <section aria-label={t.nav.items.agents} className="grid grid-cols-1 gap-3 @2xl:grid-cols-2 @4xl:grid-cols-3 @6xl:grid-cols-4">
        {list.map((a) => (
          <article key={a.id} className="glass gold-border card-sheen flex flex-col">
            <button
              type="button"
              onClick={() => {
                setOpenId(a.id);
                play("open");
              }}
              className="flex flex-1 flex-col gap-2 p-3 text-start transition-colors hover:bg-white/[0.02]"
              aria-label={`${l(a.name)} — ${tx("بازرس عامل", "Agent inspector")}`}
            >
              <div className="flex items-start gap-2.5">
                <AgentGlyph code={a.code} />
                <div className="min-w-0 flex-1">
                  <h3 className="truncate text-xs font-semibold text-fg-1">{l(a.name)}</h3>
                  <p className="line-clamp-2 text-3xs leading-snug text-fg-4">{l(a.role)}</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1">
                <RuntimeChip state={a.runtime} />
                <ImplementationChip status={a.implementation} />
              </div>
              <div className="rounded-[var(--radius-sm)] bg-white/[0.025] px-2 py-1.5 text-3xs">
                <span className="text-fg-4">{tx("کار جاری", "Current task")}: </span>
                {a.currentTask ? <span className="text-fg-2">{l(a.currentTask)}</span> : <span className="text-fg-5">{tx("ندارد", "none")}</span>}
              </div>
              <div className="mt-auto flex items-center justify-between text-3xs text-fg-5">
                <MaturityDots level={a.maturity} />
                <span>{a.lastActivityAt ? <TimeAgo iso={a.lastActivityAt} /> : tx("بدون فعالیت", "no activity")}</span>
              </div>
            </button>
          </article>
        ))}
      </section>
      <div className="glass gold-border">
        <CardFooter meta={agents.meta} />
      </div>
      <AgentInspector agent={open} departments={agents.data.departments} onClose={() => setOpenId(null)} />
    </PageBody>
  );
}
