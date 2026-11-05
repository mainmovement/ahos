"use client";

import { ArrowDownRight, ArrowUpRight, CircleDashed, Pause } from "lucide-react";
import type { SignalState } from "@/lib/types";
import { useLocale } from "@/components/providers/locale-provider";
import { cn } from "@/lib/utils";

/** LONG / SHORT / HOLD / UNKNOWN — never conflated with provenance status. */
export function SignalBadge({ state, size = "md" }: { state: SignalState; size?: "sm" | "md" }) {
  const { dict } = useLocale();
  const map: Record<SignalState, { icon: typeof ArrowUpRight; cls: string; label: string }> = {
    LONG: { icon: ArrowUpRight, cls: "border-success/40 bg-success/10 text-success", label: dict.positions.long },
    SHORT: { icon: ArrowDownRight, cls: "border-danger/40 bg-danger/10 text-danger", label: dict.positions.short },
    HOLD: { icon: Pause, cls: "border-border-strong bg-muted/50 text-muted-foreground", label: "HOLD" },
    UNKNOWN: { icon: CircleDashed, cls: "border-border bg-muted/40 text-muted-foreground", label: dict.desks.signalUnknown },
  };
  const entry = map[state];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-extrabold",
        size === "sm" ? "px-1.5 py-px text-[10px]" : "px-2 py-0.5 text-[11px]",
        entry.cls,
      )}
    >
      <entry.icon className="size-3" aria-hidden />
      <span dir="ltr">{entry.label}</span>
    </span>
  );
}
