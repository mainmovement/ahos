"use client";
import { tr } from "@/src/lib/i18n";

import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
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
      title={tr("fa", "whiteHats.ui.DecisionQueue_1")}
      caption="Decision review queue"
      testId="decision-queue"
      demo={demo}
      state={state}
      badges={
        !demo ? (
          <span className="wh-chip wh-tone-grey" data-testid="decision-totals">
            <span>{tr("fa", "whiteHats.ui.DecisionQueue_2")}</span>
            <span className="wh-num">{nonDemo}</span>
            <span className="opacity-60">{tr("fa", "whiteHats.ui.DecisionQueue_3")}</span>
            <span className="wh-num">{decisions.length}</span>
          </span>
        ) : null
      }
      actions={
        state.kind === "content" && decisions.length > 0 ? (
          <button
            type="button"
            className="wh-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[12px] text-dim transition-colors hover:border-linestrong hover:text-gold"
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
            aria-label={tr("fa", "whiteHats.ui.DecisionQueue_4")}
          >
            <DownloadIcon />
            {tr("fa", "whiteHats.ui.DecisionQueue_5")}
          </button>
        ) : null
      }
      bodyClassName="px-0 pt-1 pb-0"
    >
      {decisions.length === 0 ? null : (
        <div className="max-h-[318px] overflow-auto">
          <table className="w-full min-w-[900px] border-collapse text-right">
            <thead className="sticky top-0 z-10 bg-surface">
              <tr className="text-[12px] text-mute">
                {["شناسه", tr("fa", "whiteHats.ui.DecisionQueue_6"), tr("fa", "whiteHats.ui.DecisionQueue_7"), tr("fa", "whiteHats.ui.DecisionQueue_8"), tr("fa", "whiteHats.ui.DecisionQueue_9"), tr("fa", "whiteHats.ui.DecisionQueue_10"), tr("fa", "whiteHats.ui.DecisionQueue_11"), tr("fa", "whiteHats.ui.DecisionQueue_12"), tr("fa", "whiteHats.ui.ChallengeTimeline_5")].map(
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
                  className={`wh-focus cursor-pointer border-b border-[color:rgba(217,185,119,0.07)] align-middle transition-colors hover:bg-[color:rgba(217,185,119,0.035)] ${
                    d.demo ? "wh-demo-stripes" : ""
                  }`}
                >
                  <td className="px-3 py-[7px] ps-4">
                    <span className="flex items-center gap-1.5">
                      <span className="wh-id text-dim">{d.id}</span>
                      <CopyIdButton value={d.id} />
                    </span>
                  </td>
                  <td className="wh-num px-3 py-[7px] text-dim">{d.market}</td>
                  <td className="px-3 py-[7px] text-dim">{d.proposerAgent}</td>
                  <td className="px-3 py-[7px]">
                    <RelTime iso={d.proposedAt} className={d.proposedAt ? "text-mute" : "text-unknown"} />
                  </td>
                  <td className="px-3 py-[7px]">
                    {d.evidenceId ? (
                      <span className="wh-id text-cyan/90">{d.evidenceId}</span>
                    ) : (
                      <span className="wh-num text-mute">—</span>
                    )}
                  </td>
                  <td className="min-w-[260px] max-w-[460px] px-3 py-[7px]">
                    {d.reasons.length === 0 ? (
                      <span className="text-mute">—</span>
                    ) : (
                      <span className="block whitespace-normal text-[12px] text-mute" title={d.reasons.join(" · ")}>
                        {d.reasons[0]}
                        {d.reasons.length > 1 && (
                          <span className="ms-1 text-[12px] text-gold/80">+{d.reasons.length - 1}</span>
                        )}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-[7px]">
                    {d.paperAllowed ? (
                      <span className="wh-chip wh-tone-grey">
                        <span>{tr("fa", "whiteHats.ui.DecisionQueue_13")}</span>
                      </span>
                    ) : (
                      <span
                        className="wh-chip wh-tone-sand"
                        title={tr("fa", "whiteHats.ui.DecisionQueue_14")}
                      >
                        {tr("fa", "whiteHats.ui.DecisionQueue_15")}
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
                          ? tr("fa", "whiteHats.ui.DecisionQueue_16")
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
