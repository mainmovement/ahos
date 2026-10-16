"use client";

import { StatusChip } from "@/components/truth/StatusChip";
import type { ChipStatus } from "@/components/truth/status";
import { telemetryRowCount } from "../predicates";
import type { SnapshotPhase } from "../hooks/useWhiteHatsSnapshot";
import { RelTime } from "./RelTime";

/**
 * Bottom telemetry strip: source id, last read, row counts (DEMO rows are
 * reported but never counted into totals), plus the permanent paper note.
 */
export function TelemetryStrip({ phase }: { phase: SnapshotPhase }) {
  const snapshot = phase.phase === "ready" ? phase.snapshot : null;
  const unavailable = phase.phase === "unavailable";

  const freshness: ChipStatus = unavailable
    ? "UNAVAILABLE"
    : snapshot
      ? snapshot.freshness
      : "LOADING";

  const rows = snapshot ? telemetryRowCount(snapshot) : null;

  return (
    <footer
      className="sticky bottom-0 z-30 flex h-9 shrink-0 items-center gap-x-4 gap-y-0 overflow-x-auto border-t border-line bg-[color:var(--ah-bg)]/92 px-4 text-[10.5px] text-mute backdrop-blur-md"
      data-testid="telemetry-strip"
    >
      <span className="ah-id flex items-center gap-1.5">
        <span className="size-1.5 rounded-full bg-[color:var(--ah-gold-dim)]" aria-hidden="true" />
        {snapshot ? snapshot.sourceId : "mock://white-hats/snapshot@v1"}
      </span>
      <StatusChip status={freshness} />
      {snapshot?.demo && <StatusChip status="DEMO" />}

      <span className="flex items-center gap-1">
        آخرین خوانش:
        <RelTime iso={snapshot?.fetchedAt ?? null} />
      </span>

      {rows && (
        <span className="flex items-center gap-1">
          ردیف‌ها:
          <span className="ah-num text-dim">{rows.total}</span>
          <span className="opacity-60">(</span>بدون دمو:
          <span className="ah-num text-dim">{rows.nonDemo}</span>
          <span className="opacity-60">)</span>
        </span>
      )}

      <span className="ms-auto flex items-center gap-2 whitespace-nowrap">
        <span className="hidden opacity-70 md:inline">موقعیت کاغذی؛ پول واقعی در کار نیست</span>
        <span className="ah-latin text-[8.5px] uppercase tracking-[0.18em] opacity-60">
          read-only · no execution
        </span>
      </span>
    </footer>
  );
}
