"use client";

import { useMemo, useState } from "react";
import { StatusChip } from "@/components/truth/StatusChip";
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
  { value: "ALL", label: "همه شدت‌ها" },
  { value: "CRITICAL", label: "بحرانی" },
  { value: "MAJOR", label: "مهم" },
  { value: "MINOR", label: "جزئی" },
  { value: "INFO", label: "اطلاع" },
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
      title="دفتر یافته‌ها"
      caption="Findings log"
      testId="findings-log"
      demo={demo}
      state={state}
      badges={
        !demo && findings.length > 0 ? (
          <span className="ah-chip ah-tone-grey" data-testid="findings-totals">
            <span>بدون دمو:</span>
            <span className="ah-num">{nonDemoTotal}</span>
            <span className="opacity-60">از</span>
            <span className="ah-num">{findings.length}</span>
          </span>
        ) : null
      }
      actions={
        state.kind === "content" && findings.length > 0 ? (
          <span className="flex items-center gap-1.5">
            <button
              type="button"
              className="ah-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[11px] text-dim transition-colors hover:border-linestrong hover:text-gold"
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
              aria-label="برون‌بری فقط‌خواندنی یافته‌ها (CSV)"
            >
              <DownloadIcon />
              CSV
            </button>
            <button
              type="button"
              className="ah-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[11px] text-dim transition-colors hover:border-linestrong hover:text-gold"
              onClick={() => exportJson("white-hats-findings.json", filtered)}
              aria-label="برون‌بری فقط‌خواندنی یافته‌ها (JSON)"
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
          <span className="flex items-center gap-1.5 text-[10px] text-mute">
            <FilterIcon />
            فیلتر:
          </span>

          <select
            className="ah-focus rounded-sm border border-line bg-surface px-1.5 py-[3px] text-[11px] text-dim hover:border-linestrong"
            value={severity}
            onChange={(e) => setSeverity(e.target.value as SeverityFilter)}
            aria-label="فیلتر شدت"
          >
            {SEVERITIES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>

          <select
            className="ah-focus rounded-sm border border-line bg-surface px-1.5 py-[3px] text-[11px] text-dim hover:border-linestrong"
            value={inspector}
            onChange={(e) => setInspector(e.target.value)}
            aria-label="فیلتر بازرس"
          >
            <option value="ALL">همه بازرس‌ها</option>
            {inspectors.map((i) => (
              <option key={i.id} value={i.id}>
                {i.title}
              </option>
            ))}
          </select>

          <span
            className="flex overflow-hidden rounded-sm border border-line"
            role="group"
            aria-label="فیلتر وضعیت"
          >
            {(
              [
                { value: "ALL", label: "همه" },
                { value: "OPEN", label: "باز" },
                { value: "RESOLVED", label: "برطرف" },
              ] as { value: StatusFilter; label: string }[]
            ).map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setStatus(opt.value)}
                aria-pressed={status === opt.value}
                className={`ah-focus px-2 py-[3px] text-[11px] transition-colors ${
                  status === opt.value
                    ? "bg-[color:rgba(217,185,119,0.12)] text-gold"
                    : "text-mute hover:text-dim"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </span>

          <span className="ms-auto text-[10px] text-mute">
            نمایش: <span className="ah-num text-dim">{filtered.length}</span>
            <span className="opacity-60"> (</span>بدون دمو: <span className="ah-num text-dim">{nonDemoShown}</span>
            <span className="opacity-60">)</span>
          </span>
        </div>
      )}

      {filtered.length > 0 && (
        <div className="max-h-[252px] overflow-auto rounded-md border border-[color:rgba(217,185,119,0.08)]">
          <table className="w-full min-w-[640px] border-collapse text-right">
            <thead className="sticky top-0 z-10 bg-surface">
              <tr className="text-[10px] text-mute">
                {["شناسه", "شدت", "بازرس", "بازار", "وضعیت", "زمان", ""].map((h, i) => (
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
                    f.demo ? "ah-demo-stripes" : ""
                  }`}
                >
                  <td className="px-2.5 py-[6px] ps-3">
                    <span className="flex items-center gap-1.5">
                      <span className="ah-id text-dim">{f.id}</span>
                      <CopyIdButton value={f.id} />
                    </span>
                  </td>
                  <td className="px-2.5 py-[6px]">
                    <StatusChip status={f.severity} />
                  </td>
                  <td className="px-2.5 py-[6px] text-[11.5px] text-dim">
                    {inspectorTitle(f.inspectorId)}
                  </td>
                  <td className="ah-num px-2.5 py-[6px] text-dim">{f.market ?? "—"}</td>
                  <td className="px-2.5 py-[6px]">
                    <StatusChip status={f.status} />
                  </td>
                  <td className="px-2.5 py-[6px]">
                    <RelTime iso={f.openedAt} className={f.openedAt ? "text-mute" : "text-unknown"} />
                  </td>
                  <td className="px-2.5 py-[6px] pe-3">
                    <button
                      type="button"
                      className="ah-focus inline-flex items-center gap-1 rounded-sm border border-line px-1.5 py-[1px] text-[10px] text-cyan/90 transition-colors hover:border-linestrong hover:text-gold"
                      onClick={() => onOpenFinding(f.id)}
                      aria-label={`مشاهده جزئیات یافته ${f.id}`}
                    >
                      <EyeIcon />
                      جزئیات
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {findings.length > 0 && (
        <p className="text-[9.5px] leading-5 text-mute">
          ردیف‌های راه‌راه «نمایشی» فقط برای رندرند و در هیچ مجموع و شمارشی لحاظ نمی‌شوند.
        </p>
      )}
    </Panel>
  );
}
