"use client";

import { StatusChip } from "@/components/truth/StatusChip";
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
      title="بازرس‌ها"
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
            ins.demo ? "ah-demo-stripes" : ""
          }`}
        >
          <div className="flex min-w-0 flex-1 flex-col leading-tight">
            <span className="truncate text-[12px] text-ink">{ins.title}</span>
            <span className="ah-latin truncate text-[8px] uppercase tracking-[0.14em] text-mute">
              {ins.kind}
            </span>
          </div>
          <div className="flex flex-col items-end leading-tight">
            <StatusChip status={ins.status} />
            <span className="mt-[3px] text-[9.5px] text-mute">
              آخرین اجرا: <RelTime iso={ins.lastRunAt} />
            </span>
          </div>
          <div className="flex w-[64px] flex-col items-end leading-tight" title="شمار پاس / شکست">
            <span className="ah-num text-[11px] text-dim">
              {ins.passes}
              <span className="mx-0.5 text-mute">/</span>
              <span className={ins.failures > 0 ? "text-sand" : "text-mute"}>
                {ins.failures}
              </span>
            </span>
            <span className="text-[8.5px] text-mute">پاس / شکست</span>
          </div>
        </div>
      ))}
      {inspectors.some((i) => i.note) && (
        <p className="px-1 pt-1 text-[10px] leading-5 text-mute">
          نبودِ مهر زمانی یعنی «نامشخص» — صفرِ ساختگی ثبت نمی‌شود.
        </p>
      )}
    </Panel>
  );
}
