"use client";
import { tr } from "@/src/lib/i18n";

import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
import type { Inspector, PanelBodyState } from "../types";
import { Panel } from "./Panel";
import { RelTime } from "./RelTime";

export interface InspectorsPanelProps {
  inspectors: Inspector[];
  state: PanelBodyState;
  demo: boolean;
}

/**
 * Inspectors: data-sanity, leak canary/lookahead, cost-model, two-source
 * price, risk-limit, paper-only invariant. Status chip + last-run + pass/fail
 * counts as neutral numbers (failures highlighted in sand, never green/red).
 */
export function InspectorsPanel({ inspectors, state, demo }: InspectorsPanelProps) {
  return (
    <Panel
      title={tr("fa", "whiteHats.ui.InspectorsPanel_1")}
      caption="Independent inspectors"
      testId="inspectors-panel"
      demo={demo}
      state={state}
      bodyClassName="flex flex-col gap-1"
    >
      {inspectors.map((ins) => (
        <div
          key={ins.id}
          data-demo={ins.demo ? "true" : "false"}
          className={`flex items-center gap-2 rounded-md border border-[color:rgba(217,185,119,0.08)] bg-[color:rgba(236,236,231,0.015)] px-2.5 py-[7px] ${
            ins.demo ? "wh-demo-stripes" : ""
          }`}
        >
          <div className="flex min-w-0 flex-1 flex-col leading-tight">
            <span className="break-words text-[13px] text-ink">{ins.title}</span>
            <span className="wh-latin break-all text-[12px] uppercase tracking-[0.14em] text-mute">
              {ins.kind}
            </span>
          </div>
          <div className="flex flex-col items-end leading-tight">
            <StatusChip status={ins.status} />
            <span className="mt-[3px] text-[12px] text-mute">
              آخرین اجرا: <RelTime iso={ins.lastRunAt} />
            </span>
          </div>
          <div className="flex w-[64px] flex-col items-end leading-tight" title={tr("fa", "whiteHats.ui.InspectorsPanel_2")}>
            <span className="wh-num text-[12px] text-dim">
              {ins.passes}
              <span className="mx-0.5 text-mute">/</span>
              <span className={ins.failures > 0 ? "text-sand" : "text-mute"}>
                {ins.failures}
              </span>
            </span>
            <span className="text-[12px] text-mute">{tr("fa", "whiteHats.ui.InspectorsPanel_3")}</span>
          </div>
        </div>
      ))}
      {inspectors.some((i) => i.note) && (
        <p className="px-1 pt-1 text-[12px] leading-5 text-mute">
          {tr("fa", "whiteHats.ui.InspectorsPanel_4")}
        </p>
      )}
    </Panel>
  );
}
