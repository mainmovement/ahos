"use client";
import { tr } from "@/src/lib/i18n";

import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
import type { CanaryRun, PanelBodyState } from "../types";
import { Panel } from "./Panel";
import { RelTime } from "./RelTime";

export interface CanaryTileProps {
  canary: CanaryRun | null;
  state: PanelBodyState;
  demo: boolean;
}

/**
 * Leak-canary tile. A deliberate cheat attempt MUST FAIL. So:
 * - result FAIL (expected) → informational cyan «سالم»
 * - result PASS (canary went blind) → danger alarm
 * - no run / no timestamp → UNKNOWN, never a fabricated result.
 */
export function CanaryTile({ canary, state, demo }: CanaryTileProps) {
  const noRun = !canary || canary.result === "UNKNOWN" || !canary.ranAt;

  return (
    <Panel
      title={tr("fa", "whiteHats.ui.CanaryTile_1")}
      caption="Leak canary — lookahead check"
      testId="canary-tile"
      demo={demo}
      state={
        noRun && state.kind === "content"
          ? { kind: "unknown", message: tr("fa", "whiteHats.ui.CanaryTile_2") }
          : state
      }
      badges={canary && !noRun ? <StatusChip status={canary.result} /> : null}
    >
      {canary && !noRun ? (
        <div className="flex flex-col gap-2 text-[12px] leading-6">
          <div className="rounded-md border border-[color:rgba(217,185,119,0.12)] bg-[color:rgba(236,236,231,0.015)] p-2.5">
            <span className="text-[12px] text-mute">{tr("fa", "whiteHats.ui.CanaryTile_3")}</span>
            <p className="text-dim">{canary.cheatAttempt}</p>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-mute">{tr("fa", "whiteHats.ui.CanaryTile_4")}</span>
            <StatusChip status="FAIL" title={tr("fa", "whiteHats.ui.CanaryTile_5")} />
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="text-mute">{tr("fa", "whiteHats.ui.CanaryTile_6")}</span>
            <StatusChip
              status={canary.result}
              title={
                canary.result === "FAIL"
                  ? tr("fa", "whiteHats.ui.CanaryTile_7")
                  : tr("fa", "whiteHats.ui.CanaryTile_8")
              }
            />
          </div>
          {canary.caught && (
            <p className="rounded-md border border-[color:rgba(120,203,209,0.14)] bg-[color:rgba(120,203,209,0.05)] px-2.5 py-1.5 text-[12px] text-cyan/90">
              {canary.caught}
            </p>
          )}
          <p className="text-[12px] text-mute">
            {canary.note} · آخرین اجرا: <RelTime iso={canary.ranAt} />
          </p>
        </div>
      ) : null}
    </Panel>
  );
}
