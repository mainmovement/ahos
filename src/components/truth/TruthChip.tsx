import type { ReactNode } from "react";
import { tr } from "@/src/lib/i18n";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { STATUS_FA, STATUS_TONE } from "@/src/features/trade-venue/logic/truth";

/**
 * The single chip primitive of the AHOS truth system.
 *
 * Every status that appears anywhere on the venue page goes through this
 * component, which guarantees three things in one place:
 *   1. the Persian label always ships beside the Latin enum code;
 *   2. `data-tone` is derived from `STATUS_TONE` — UNKNOWN/UNAVAILABLE/PLANNED
 *      can therefore never render with the green `live` tone;
 *   3. `data-status` is a stable test hook for the truth-rule unit tests.
 */
export interface TruthChipProps {
  status: ChipStatus;
  /** Override the Persian label (e.g. «غیرمجاز» instead of «ردشده»). */
  labelFa?: string;
  /** Hide the Latin enum code (for dense tables). */
  hideCode?: boolean;
  /** Compact variant. */
  size?: "sm" | "md";
  /** Trailing hint, e.g. an evidence id or a source note. */
  trailing?: ReactNode;
  title?: string;
}

export function TruthChip({
  status,
  labelFa,
  hideCode = false,
  size = "md",
  trailing,
  title,
}: TruthChipProps) {
  const tone = STATUS_TONE[status];
  const SHARED = ["LIVE", "STALE", "UNKNOWN", "DEMO"];
  // Arena contract: the four shared chips take their label from the i18n pack via tr(); venue-only states stay local.
  const label = labelFa ?? (SHARED.includes(status) ? tr("fa", `status.${status}.label`) : STATUS_FA[status]);
  return (
    <span
      className={size === "sm" ? "tv-chip tv-chip--sm" : "tv-chip"}
      data-chip=""
      data-status={status}
      data-tone={tone}
      data-live={tone === "live" ? "true" : "false"}
      title={title ?? `${label} · ${status}`}
    >
      <i className="tv-chip__dot" aria-hidden="true" />
      <span className="tv-chip__fa">{label}</span>
      {hideCode ? null : (
        <span className="tv-chip__code tv-chip__en" dir="ltr">
          {status}
        </span>
      )}
      {trailing}
    </span>
  );
}

/** Source provenance chip: the id of the feed/ledger a row came from. */
export function SourceChip({ sourceId, demo }: { sourceId: string; demo?: boolean }) {
  return (
    <span
      className="tv-chip tv-chip--sm"
      data-chip=""
      data-source={sourceId}
      data-source-demo={demo ? "true" : "false"}
      data-tone="unknown"
      title={demo ? `${sourceId} — منبع نمایشی` : sourceId}
    >
      <span className="tv-chip__code" dir="ltr">
        {sourceId}
      </span>
    </span>
  );
}
