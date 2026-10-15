"use client";

import type { AlertItem } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { AlertTierChip, StatusChip, alertTierIcon } from "@/components/ui/status";
import { TimeAgo } from "@/components/ui/primitives";

const TIER_TONE = {
  SECURITY: "border-s-down/70",
  HIGH_ATTENTION: "border-s-warn/70",
  WATCH: "border-s-gold-400/70",
  INFO: "border-s-slate/50",
} as const;

export function AlertsList({ alerts, dense }: { alerts: AlertItem[]; dense?: boolean }) {
  const { l } = useI18n();
  return (
    <ul className="space-y-1.5">
      {alerts.map((a) => {
        const Icon = alertTierIcon(a.tier);
        return (
          <li key={a.id} className={cn("rounded-[var(--radius-md)] border border-[var(--line-subtle)] border-s-2 bg-white/[0.02] px-2.5", TIER_TONE[a.tier], dense ? "py-1.5" : "py-2")}>
            <div className="flex items-center gap-1.5">
              <Icon aria-hidden className="size-3.5 shrink-0 text-fg-3" />
              <span className="min-w-0 flex-1 truncate text-2xs font-medium text-fg-1">{l(a.title)}</span>
              <AlertTierChip tier={a.tier} />
            </div>
            <p className="mt-0.5 line-clamp-1 text-3xs text-fg-3">{l(a.detail)}</p>
            <div className="mt-1 flex items-center justify-between">
              <TimeAgo iso={a.at} className="text-3xs text-fg-5" />
              <StatusChip status={a.status} />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
