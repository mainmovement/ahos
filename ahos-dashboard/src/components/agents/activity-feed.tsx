"use client";

import { Activity, CircleCheck, CircleDashed, CircleX, Info, OctagonAlert, Play } from "lucide-react";
import type { AgentEvent, AgentRuntimeState, Localized } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { RuntimeChip } from "@/components/ui/status";
import { TimeAgo } from "@/components/ui/primitives";

const KIND_ICON = {
  task_started: { icon: Play, cls: "text-up" },
  task_completed: { icon: CircleCheck, cls: "text-data-300" },
  blocked: { icon: OctagonAlert, cls: "text-warn" },
  failed: { icon: CircleX, cls: "text-down" },
  heartbeat: { icon: Activity, cls: "text-fg-4" },
  registered: { icon: CircleDashed, cls: "text-info" },
  note: { icon: Info, cls: "text-fg-3" },
} as const;

export interface AgentIndexEntry {
  name: Localized;
  runtime: AgentRuntimeState;
  code: string;
}

/** Timeline of agent events. Each row shows the agent's explicit runtime chip. */
export function ActivityFeed({ events, index, limit, dense }: { events: AgentEvent[]; index: Record<string, AgentIndexEntry>; limit?: number; dense?: boolean }) {
  const { l } = useI18n();
  const items = limit ? events.slice(0, limit) : events;
  return (
    <ol className="relative space-y-0.5">
      {items.map((e, i) => {
        const k = KIND_ICON[e.kind];
        const Icon = k.icon;
        const agent = index[e.agentId];
        return (
          <li key={e.id} className={cn("relative flex gap-2.5 rounded-[var(--radius-md)] px-1.5 transition-colors hover:bg-[var(--surface-hover)]", dense ? "py-1.5" : "py-2")}>
            {i < items.length - 1 && <span aria-hidden className="absolute bottom-[-6px] start-[15px] top-6 w-px bg-gradient-to-b from-gold-400/25 to-transparent" />}
            <span className="relative mt-0.5 flex size-[18px] shrink-0 items-center justify-center rounded-full border border-white/10 bg-ink-900">
              <Icon aria-hidden className={cn("size-2.5", k.cls)} strokeWidth={2.6} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-2xs font-medium text-fg-1">{agent ? l(agent.name) : e.agentId}</span>
                {agent && <RuntimeChip state={agent.runtime} />}
              </div>
              <p className="mt-0.5 line-clamp-2 text-2xs leading-snug text-fg-3">{l(e.text)}</p>
              <TimeAgo iso={e.at} className="text-3xs text-fg-5" />
            </div>
          </li>
        );
      })}
    </ol>
  );
}
