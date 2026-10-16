"use client";

import { tr } from "@/src/lib/i18n";

import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
import type { ChipStatus } from "@/src/features/white-hats/truth/status";
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
      className="flex min-h-9 shrink-0 flex-wrap items-center gap-x-4 gap-y-0 overflow-x-auto border-t border-line bg-[color:var(--ah-bg)]/92 px-4 text-[12px] text-mute backdrop-blur-md"
      data-testid="telemetry-strip"
    >
      <span className="wh-id flex items-center gap-1.5">
        <span className="size-1.5 rounded-full bg-[color:var(--ah-gold-dim)]" aria-hidden="true" />
        {snapshot?.demo ? tr("fa", "whiteHats.sourceDemo") : tr("fa", "whiteHats.sourceUnknown")}
      </span>
      <StatusChip status={freshness} />
      {snapshot?.demo && <StatusChip status="DEMO" />}

      <span className="flex items-center gap-1">
        {tr("fa", "whiteHats.ui.TelemetryStrip_1")}
        <RelTime iso={snapshot?.fetchedAt ?? null} />
      </span>

      {rows && (
        <span className="flex items-center gap-1">
          {tr("fa", "whiteHats.ui.TelemetryStrip_2")}
          <span className="wh-num text-dim">{rows.total}</span>
          <span className="opacity-60">(</span>بدون دمو:
          <span className="wh-num text-dim">{rows.nonDemo}</span>
          <span className="opacity-60">)</span>
        </span>
      )}

      <span className="ms-auto flex items-center gap-2 whitespace-nowrap">
        <span className="hidden opacity-70 md:inline">{tr("fa", "whiteHats.ui.TelemetryStrip_3")}</span>
        <span className="wh-latin text-[12px] uppercase tracking-[0.18em] opacity-60">
          read-only · no execution
        </span>
      </span>
    </footer>
  );
}
