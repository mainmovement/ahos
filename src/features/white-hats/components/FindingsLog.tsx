"use client";
import { tr } from "@/src/lib/i18n";

import { useMemo, useState } from "react";
import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
import { countNonDemo } from "../predicates";
import { exportCsv, exportJson } from "../lib/export";
import type { Finding, FindingSeverity, FindingStatus, Inspector } from "../types";
import type { PanelBodyState } from "../types";
import { CopyIdButton } from "./CopyIdButton";
import { DownloadIcon, EyeIcon, FilterIcon } from "./icons";
import { Panel } from "./Panel";
import { RelTime } from "./RelTime";

export interface FindingsLogProps {
  findings: Finding[];
  inspectors: Inspector[];
  state: PanelBodyState;
  demo: boolean;
  onOpenFinding: (id: string) => void;
}

type SeverityFilter = "ALL" | FindingSeverity;
type StatusFilter = "ALL" | FindingStatus;

const SEVERITIES: { value: SeverityFilter; label: string }[] = [
  { value: "ALL", label: tr("fa", "whiteHats.ui.FindingsLog_1") },
  { value: "CRITICAL", label: tr("fa", "whiteHats.ui.FindingsLog_2") },
  { value: "MAJOR", label: tr("fa", "whiteHats.ui.FindingsLog_3") },
  { value: "MINOR", label: tr("fa", "whiteHats.ui.FindingsLog_4") },
  { value: "INFO", label: tr("fa", "whiteHats.ui.FindingsLog_5") },
];

/**
 * Filterable findings log (verbs: view / filter / export read-only).
 * DEMO rows stay visible but striped and excluded from the totals line.
 */
export function FindingsLog({
  findings,
  inspectors,
  state,
  demo,
  onOpenFinding,
}: FindingsLogProps) {
  const [severity, setSeverity] = useState<SeverityFilter>("ALL");
  const [status, setStatus] = useState<StatusFilter>("ALL");
  const [inspector, setInspector] = useState<string>("ALL");

  const filtered = useMemo(
    () =>
      findings.filter(
        (f) =>
          (severity === "ALL" || f.severity === severity) &&
          (status === "ALL" || f.status === status) &&
          (inspector === "ALL" || f.inspectorId === inspector),
      ),
    [findings, severity, status, inspector],
  );

  const nonDemoTotal = countNonDemo(findings);
  const nonDemoShown = countNonDemo(filtered);
  const inspectorTitle = (id: string) =>
    inspectors.find((i) => i.id === id)?.title ?? id;

  return (
    <Panel
      title={tr("fa", "whiteHats.ui.FindingsLog_6")}
      caption="Findings log"
      testId="findings-log"
      demo={demo}
      state={state}
      badges={
        !demo && findings.length > 0 ? (
          <span className="wh-chip wh-tone-grey" data-testid="findings-totals">
            <span>{tr("fa", "whiteHats.ui.DecisionQueue_2")}</span>
            <span className="wh-num">{nonDemoTotal}</span>
            <span className="opacity-60">{tr("fa", "whiteHats.ui.DecisionQueue_3")}</span>
            <span className="wh-num">{findings.length}</span>
          </span>
        ) : null
      }
      actions={
        state.kind === "content" && findings.length > 0 ? (
          <span className="flex items-center gap-1.5">
            <button
              type="button"
              className="wh-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[12px] text-dim transition-colors hover:border-linestrong hover:text-gold"
              onClick={() =>
                exportCsv(
                  "white-hats-findings.csv",
                  filtered.map((f) => ({
                    id: f.id,
                    severity: f.severity,
                    inspector: inspectorTitle(f.inspectorId),
                    market: f.market ?? "",
                    status: f.status,
                    openedAt: f.openedAt ?? "",
                    rule: f.ruleText,
                    evidence: f.evidenceId ?? "",
                    verdictImpact: f.verdictImpact,
                    demo: f.demo ? "DEMO" : "",
                  })),
                )
              }
              aria-label={tr("fa", "whiteHats.ui.FindingsLog_7")}
            >
              <DownloadIcon />
              CSV
            </button>
            <button
              type="button"
              className="wh-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[12px] text-dim transition-colors hover:border-linestrong hover:text-gold"
              onClick={() => exportJson("white-hats-findings.json", filtered)}
              aria-label={tr("fa", "whiteHats.ui.FindingsLog_8")}
            >
              <DownloadIcon />
              JSON
            </button>
          </span>
        ) : null
      }
      bodyClassName="flex flex-col gap-2.5"
    >
      {findings.length > 0 && (
        <div className="flex flex-wrap items-center gap-2" data-testid="findings-filters">
          <span className="flex items-center gap-1.5 text-[12px] text-mute">
            <FilterIcon />
            {tr("fa", "whiteHats.ui.FindingsLog_9")}
          </span>

          <select
            className="wh-focus rounded-sm border border-line bg-surface px-1.5 py-[3px] text-[12px] text-dim hover:border-linestrong"
            value={severity}
            onChange={(e) => setSeverity(e.target.value as SeverityFilter)}
            aria-label={tr("fa", "whiteHats.ui.FindingsLog_10")}
          >
            {SEVERITIES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>

          <select
            className="wh-focus rounded-sm border border-line bg-surface px-1.5 py-[3px] text-[12px] text-dim hover:border-linestrong"
            value={inspector}
            onChange={(e) => setInspector(e.target.value)}
            aria-label={tr("fa", "whiteHats.ui.FindingsLog_11")}
          >
            <option value="ALL">{tr("fa", "whiteHats.ui.FindingsLog_12")}</option>
            {inspectors.map((i) => (
              <option key={i.id} value={i.id}>
                {i.title}
              </option>
            ))}
          </select>

          <span
            className="flex overflow-hidden rounded-sm border border-line"
            role="group"
            aria-label={tr("fa", "whiteHats.ui.FindingsLog_13")}
          >
            {(
              [
                { value: "ALL", label: tr("fa", "whiteHats.ui.FindingsLog_14") },
                { value: "OPEN", label: tr("fa", "whiteHats.ui.FindingsLog_15") },
                { value: "RESOLVED", label: tr("fa", "whiteHats.ui.FindingsLog_16") },
              ] as { value: StatusFilter; label: string }[]
            ).map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setStatus(opt.value)}
                aria-pressed={status === opt.value}
                className={`wh-focus px-2 py-[3px] text-[12px] transition-colors ${
                  status === opt.value
                    ? "bg-[color:rgba(217,185,119,0.12)] text-gold"
                    : "text-mute hover:text-dim"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </span>

          <span className="ms-auto text-[12px] text-mute">
            نمایش: <span className="wh-num text-dim">{filtered.length}</span>
            <span className="opacity-60"> (</span>{tr("fa", "whiteHats.ui.DecisionQueue_2")}<span className="wh-num text-dim">{nonDemoShown}</span>
            <span className="opacity-60">)</span>
          </span>
        </div>
      )}

      {filtered.length > 0 && (
        <div className="max-h-[252px] overflow-auto rounded-md border border-[color:rgba(217,185,119,0.08)]">
          <table className="w-full min-w-[640px] border-collapse text-right">
            <thead className="sticky top-0 z-10 bg-surface">
              <tr className="text-[12px] text-mute">
                {["شناسه", tr("fa", "whiteHats.ui.FindingsLog_17"), tr("fa", "whiteHats.ui.FindingsLog_18"), tr("fa", "whiteHats.ui.DecisionQueue_6"), tr("fa", "whiteHats.ui.FindingsLog_19"), tr("fa", "whiteHats.ui.DecisionQueue_8"), ""].map((h, i) => (
                  <th
                    key={`${h}-${i}`}
                    className="border-b border-line px-2.5 py-2 font-medium first:ps-3 last:pe-3"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => (
                <tr
                  key={f.id}
                  data-demo={f.demo ? "true" : "false"}
                  className={`border-b border-[color:rgba(217,185,119,0.06)] transition-colors hover:bg-[color:rgba(217,185,119,0.035)] ${
                    f.demo ? "wh-demo-stripes" : ""
                  }`}
                >
                  <td className="px-2.5 py-[6px] ps-3">
                    <span className="flex items-center gap-1.5">
                      <span className="wh-id text-dim">{f.id}</span>
                      <CopyIdButton value={f.id} />
                    </span>
                  </td>
                  <td className="px-2.5 py-[6px]">
                    <StatusChip status={f.severity} />
                  </td>
                  <td className="px-2.5 py-[6px] text-[12px] text-dim">
                    {inspectorTitle(f.inspectorId)}
                  </td>
                  <td className="wh-num px-2.5 py-[6px] text-dim">{f.market ?? "—"}</td>
                  <td className="px-2.5 py-[6px]">
                    <StatusChip status={f.status} />
                  </td>
                  <td className="px-2.5 py-[6px]">
                    <RelTime iso={f.openedAt} className={f.openedAt ? "text-mute" : "text-unknown"} />
                  </td>
                  <td className="px-2.5 py-[6px] pe-3">
                    <button
                      type="button"
                      className="wh-focus inline-flex items-center gap-1 rounded-sm border border-line px-1.5 py-[1px] text-[12px] text-cyan/90 transition-colors hover:border-linestrong hover:text-gold"
                      onClick={() => onOpenFinding(f.id)}
                      aria-label={`مشاهده جزئیات یافته ${f.id}`}
                    >
                      <EyeIcon />
                      {tr("fa", "whiteHats.ui.FindingsLog_20")}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {findings.length > 0 && (
        <p className="text-[12px] leading-5 text-mute">
          {tr("fa", "whiteHats.ui.FindingsLog_21")}
        </p>
      )}
    </Panel>
  );
}
