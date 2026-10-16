"use client";

/**
 * Glass caption pills that live in the dial's chrome band.
 *
 * Everything here is text (or a single 1 px line) — no decorative shape that could be misread as
 * data:
 *  - top centre: how many departments need attention, plus how many markets calm mode collapsed;
 *  - bottom centre: the gate readout in Persian digits, or UNKNOWN (never a fake 0%);
 *  - top left: the text-view toggle for low-power / screen-reader use;
 *  - top right: the DEMO badge, shown only while demo data is actually on screen.
 */

import { STAGE_PAD } from "./layout";
import type { Dictionary } from "../../lib/i18n";
import { localizeNumber } from "../../lib/i18n";
import { gateMath } from "../../lib/style";
import type { Gate, Lang } from "../../types/globe";

export type DialCaptionsProps = {
  size: number;
  lang: Lang;
  dict: Dictionary;
  gate: Gate;
  departmentsNeedingAttention: number;
  collapsedCount: number;
  hasDemoData: boolean;
  stale: boolean;
  textViewOpen: boolean;
  onToggleTextView: () => void;
};

export function DialCaptions({
  size,
  lang,
  dict,
  gate,
  departmentsNeedingAttention,
  collapsedCount,
  hasDemoData,
  stale,
  textViewOpen,
  onToggleTextView,
}: DialCaptionsProps) {
  const math = gateMath(gate);
  const percent =
    math.absorbedShare === null ? null : localizeNumber(`${(math.absorbedShare * 100).toFixed(0)}٪`, lang);
  const dissipatedPercent =
    math.dissipatedShare === null ? null : localizeNumber(`${(math.dissipatedShare * 100).toFixed(0)}٪`, lang);

  return (
    <div className="ahos-captions" style={{ left: STAGE_PAD, top: STAGE_PAD, width: size, height: size }}>
      <div className="ahos-caption-row ahos-caption-row-top" style={{ top: size * 0.012 }}>
        {departmentsNeedingAttention > 0 ? (
          <span className="ahos-caption-pill" data-tone="attention">
            <span className="ahos-dot" aria-hidden="true" />
            {lang === "fa"
              ? `${localizeNumber(departmentsNeedingAttention, lang)} دپارتمان نیازمند توجه`
              : `${departmentsNeedingAttention} department(s) need attention`}
          </span>
        ) : (
          <span className="ahos-caption-pill" data-tone="quiet">
            {lang === "fa" ? "همه‌ی دپارتمان‌ها آرام" : "all departments calm"}
          </span>
        )}
        {collapsedCount > 0 ? (
          <span
            className="ahos-more-chip"
            role="note"
            tabIndex={0}
            aria-label={dict.moreMarkers(collapsedCount)}
          >
            <span aria-hidden="true">{`+${localizeNumber(collapsedCount, lang)}`}</span>
            <span className="ahos-more-chip-tip" role="tooltip">
              {dict.moreMarkers(collapsedCount)}
            </span>
          </span>
        ) : null}
      </div>

      <div className="ahos-caption-row ahos-caption-row-bottom" style={{ top: size * 0.9 }}>
        <span className="ahos-caption-pill ahos-caption-pill-gate" data-known={math.known ? "true" : "false"}>
          {percent === null ? (
            <span className="ahos-caption-unknown">{`${dict.gateAria} · ${dict.unknownValue}`}</span>
          ) : (
            <>
              <span className="ahos-caption-value">{percent}</span>
              <span className="ahos-caption-label">{dict.gateAbsorbed}</span>
              <span className="ahos-caption-sep" aria-hidden="true">
                ·
              </span>
              <span className="ahos-caption-value" data-tone="dissipated">
                {dissipatedPercent}
              </span>
              <span className="ahos-caption-label">{dict.gateDissipated}</span>
              {math.strictnessFromData ? null : (
                <span className="ahos-caption-derived">
                  {lang === "fa" ? "محاسبه‌شده از شمارش" : "derived from counts"}
                </span>
              )}
            </>
          )}
        </span>
      </div>

      <button
        type="button"
        className="ahos-text-toggle"
        onClick={onToggleTextView}
        aria-expanded={textViewOpen}
        style={{ top: size * 0.012 }}
      >
        {lang === "fa" ? (textViewOpen ? "بستن فهرست" : "فهرست متنی") : textViewOpen ? "hide list" : "text list"}
      </button>

      {hasDemoData ? (
        <span className="ahos-caption-pill ahos-badge-demo" style={{ top: size * 0.012 }}>
          {lang === "fa" ? "داده‌ی نمایشی" : "DEMO DATA"}
        </span>
      ) : null}

      {stale ? (
        <span className="ahos-caption-pill ahos-caption-stale" style={{ top: size * 0.9 }}>
          {dict.heartbeatStale}
        </span>
      ) : null}
    </div>
  );
}
