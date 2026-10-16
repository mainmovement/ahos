"use client";

import { StatusChip } from "@/components/truth/StatusChip";
import { countNonDemo } from "../predicates";
import { exportCsv } from "../lib/export";
import type { Decision, PanelBodyState } from "../types";
import { CopyIdButton } from "./CopyIdButton";
import { DownloadIcon } from "./icons";
import { Panel } from "./Panel";
import { RelTime } from "./RelTime";

export interface DecisionQueueProps {
  decisions: Decision[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  state: PanelBodyState;
  demo: boolean;
}

/**
 * Decision review queue. Every decision shows the judge verdict — decisions
 * with no judge result render UNKNOWN (grey) and never CLEAN. Read-only:
 * the only verbs here are view, filter, export, copy-ID, open evidence.
 */
export function DecisionQueue({
  decisions,
  selectedId,
  onSelect,
  state,
  demo,
}: DecisionQueueProps) {
  const nonDemo = countNonDemo(decisions);

  return (
    <Panel
      title="صف بازبینی تصمیم‌ها"
      caption="Decision review queue"
      testId="decision-queue"
      demo={demo}
      state={state}
      badges={
        !demo ? (
          <span className="ah-chip ah-tone-grey" data-testid="decision-totals">
            <span>بدون دمو:</span>
            <span className="ah-num">{nonDemo}</span>
            <span className="opacity-60">از</span>
            <span className="ah-num">{decisions.length}</span>
          </span>
        ) : null
      }
      actions={
        state.kind === "content" && decisions.length > 0 ? (
          <button
            type="button"
            className="ah-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[11px] text-dim transition-colors hover:border-linestrong hover:text-gold"
            onClick={() =>
              exportCsv(
                "white-hats-decisions.csv",
                decisions.map((d) => ({
                  id: d.id,
                  market: d.market,
                  proposer: d.proposerAgent,
                  proposedAt: d.proposedAt ?? "",
                  verdict: d.verdict,
                  reasons: d.reasons.join(" | "),
                  evidence: d.evidenceId ?? "",
                  paperAllowed: d.paperAllowed ? "yes" : "no",
                  freshness: d.freshness,
                  demo: d.demo ? "DEMO" : "",
                })),
              )
            }
            aria-label="برون‌بری فقط‌خواندنی صف تصمیم‌ها (CSV)"
          >
            <DownloadIcon />
            برون‌بری CSV
          </button>
        ) : null
      }
      bodyClassName="px-0 pt-1 pb-0"
    >
      {decisions.length === 0 ? null : (
        <div className="max-h-[318px] overflow-auto">
          <table className="w-full min-w-[900px] border-collapse text-right">
            <thead className="sticky top-0 z-10 bg-surface">
              <tr className="text-[10px] text-mute">
                {["شناسه", "بازار", "عامل پیشنهاددهنده", "زمان", "شواهد", "دلایل داوری", "مجوز کاغذی", "تازگی", "حکم"].map(
                  (h) => (
                    <th
                      key={h}
                      className="border-b border-line px-3 py-2 font-medium first:ps-4 last:pe-4"
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {decisions.map((d) => (
                <tr
                  key={d.id}
                  tabIndex={0}
                  aria-selected={d.id === selectedId}
                  data-demo={d.demo ? "true" : "false"}
                  onClick={() => onSelect(d.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelect(d.id);
                    }
                  }}
                  className={`ah-focus cursor-pointer border-b border-[color:rgba(217,185,119,0.07)] align-middle transition-colors hover:bg-[color:rgba(217,185,119,0.035)] ${
                    d.demo ? "ah-demo-stripes" : ""
                  }`}
                >
                  <td className="px-3 py-[7px] ps-4">
                    <span className="flex items-center gap-1.5">
                      <span className="ah-id text-dim">{d.id}</span>
                      <CopyIdButton value={d.id} />
                    </span>
                  </td>
                  <td className="ah-num px-3 py-[7px] text-dim">{d.market}</td>
                  <td className="px-3 py-[7px] text-dim">{d.proposerAgent}</td>
                  <td className="px-3 py-[7px]">
                    <RelTime iso={d.proposedAt} className={d.proposedAt ? "text-mute" : "text-unknown"} />
                  </td>
                  <td className="px-3 py-[7px]">
                    {d.evidenceId ? (
                      <span className="ah-id text-cyan/90">{d.evidenceId}</span>
                    ) : (
                      <span className="ah-num text-mute">—</span>
                    )}
                  </td>
                  <td className="max-w-[240px] px-3 py-[7px]">
                    {d.reasons.length === 0 ? (
                      <span className="text-mute">—</span>
                    ) : (
                      <span className="block truncate text-[11.5px] text-mute" title={d.reasons.join(" · ")}>
                        {d.reasons[0]}
                        {d.reasons.length > 1 && (
                          <span className="ms-1 text-[10px] text-gold/80">+{d.reasons.length - 1}</span>
                        )}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-[7px]">
                    {d.paperAllowed ? (
                      <span className="ah-chip ah-tone-grey">
                        <span>مجاز کاغذی</span>
                      </span>
                    ) : (
                      <span
                        className="ah-chip ah-tone-sand"
                        title="این تصمیم اجازه‌ی حتی اجرای کاغذی هم ندارد."
                      >
                        غیرمجاز
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-[7px]">
                    <StatusChip status={d.freshness} />
                  </td>
                  <td className="px-3 py-[7px] pe-4">
                    <StatusChip
                      status={d.verdict}
                      title={
                        d.verdict === "UNKNOWN"
                          ? "بدون نتیجه داوری — UNKNOWN خاکستری است و هرگز CLEAN نمایش داده نمی‌شود."
                          : undefined
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
