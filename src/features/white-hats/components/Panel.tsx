"use client";
import { tr } from "@/src/lib/i18n";

import type { ReactNode } from "react";
import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
import { DemoBadge } from "@/src/features/white-hats/truth/DemoBadge";
import type { PanelBodyState } from "../types";

export type { PanelBodyState };

export interface PanelProps {
  title: string;
  caption?: string;
  testId: string;
  demo?: boolean;
  badges?: ReactNode;
  actions?: ReactNode;
  state?: PanelBodyState;
  bodyClassName?: string;
  children?: ReactNode;
}

const STATE_CHIP = {
  loading: "LOADING",
  empty: "EMPTY",
  unknown: "UNKNOWN",
  unavailable: "UNAVAILABLE",
  error: "ERROR",
} as const;

/**
 * The glass-panel shell every section uses: hairline gold frame, overline
 * caption, truth chips, and the mandated component states.
 */
export function Panel({
  title,
  caption,
  testId,
  demo = false,
  badges,
  actions,
  state = { kind: "content" },
  bodyClassName = "",
  children,
}: PanelProps) {
  return (
    <section className="wh-panel wh-enter flex min-w-0 flex-col" data-testid={testId}>
      {(demo || state.kind !== "content") && (
        <div aria-hidden="true" className="wh-demo-edge h-[3px] rounded-t-[17px] opacity-70" />
      )}
      <header className="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-4 pb-2 pt-3">
        <div className="flex min-w-0 flex-col">
          <h2 className="text-[13.5px] font-semibold leading-6 text-ink">{title}</h2>
          {caption && (
            <span className="wh-latin text-[12px] uppercase leading-4 tracking-[0.18em] text-mute">
              {caption}
            </span>
          )}
        </div>
        <div className="ms-auto flex flex-wrap items-center gap-1.5">
          {badges}
          {demo && <DemoBadge />}
          {state.kind !== "content" && <StatusChip status={STATE_CHIP[state.kind]} />}
          {actions}
        </div>
      </header>
      <div className="wh-hairline mx-4" aria-hidden="true" />
      <div className={`min-w-0 flex-1 px-4 py-3 ${bodyClassName}`}>
        {state.kind === "content" ? (
          children
        ) : state.kind === "loading" ? (
          <PanelSkeleton />
        ) : (
          <PanelStateMessage kind={state.kind} message={state.message} />
        )}
      </div>
    </section>
  );
}

function PanelSkeleton() {
  return (
    <div className="flex flex-col gap-2.5 py-1" aria-hidden="true">
      {[74, 92, 60, 84].map((w, i) => (
        <div key={i} className="wh-skeleton h-[18px]" style={{ width: `${w}%` }} />
      ))}
      <span className="sr-only">{tr("fa", "whiteHats.ui.Panel_1")}</span>
    </div>
  );
}

const STATE_ICON: Record<"empty" | "unknown" | "unavailable" | "error", string> = {
  empty: "◌",
  unknown: "?",
  unavailable: "⌁",
  error: "!",
};

function PanelStateMessage({
  kind,
  message,
}: {
  kind: "empty" | "unknown" | "unavailable" | "error";
  message: string;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-1.5 py-7 text-center"
      data-testid={`panel-state-${kind}`}
    >
      <span
        className="wh-chip wh-chip-lg"
        aria-hidden="true"
        style={{ fontSize: 13, letterSpacing: 0 }}
      >
        <span className="wh-latin">{STATE_ICON[kind]}</span>
      </span>
      <StatusChip status={STATE_CHIP[kind]} size="lg" />
      <p className="max-w-[46ch] text-[12px] leading-6 text-mute">{message}</p>
    </div>
  );
}
