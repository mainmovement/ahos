/**
 * Display-independent tone mapping for provenance statuses.
 * Labels live in the i18n dictionaries; icons live in components.
 * Keeping this pure lets unit tests pin the non-color semantics.
 */
import type { DataStatus } from "@/lib/types";

export type StatusTone =
  | "measured" // cyan — genuine observation
  | "sample" // violet — demo data
  | "absent" // slate — nothing measured
  | "disconnected" // slate + dashed — real endpoint, intentionally off
  | "stale" // amber — too old
  | "warning" // amber-ish — unverified
  | "danger" // red — quarantined / fail
  | "excluded" // red hatch — removed from evidence
  | "unknown"; // slate question — genuinely unknown

export function statusTone(status: DataStatus): StatusTone {
  switch (status) {
    case "MEASURED":
      return "measured";
    case "SAMPLE":
      return "sample";
    case "NOT_MEASURED":
      return "absent";
    case "NOT_CONNECTED":
      return "disconnected";
    case "STALE":
      return "stale";
    case "UNVERIFIED":
      return "warning";
    case "QUARANTINED":
      return "danger";
    case "EXCLUDED":
      return "excluded";
    case "UNAVAILABLE":
      return "absent";
    case "UNKNOWN":
      return "unknown";
  }
}

/**
 * Every status also carries a distinct glyph name (screen-reader + shape
 * channel) so information is never encoded by color alone.
 */
export function statusGlyph(status: DataStatus): string {
  switch (status) {
    case "MEASURED":
      return "check";
    case "SAMPLE":
      return "flask";
    case "NOT_MEASURED":
      return "slash";
    case "NOT_CONNECTED":
      return "plug-off";
    case "STALE":
      return "clock";
    case "UNVERIFIED":
      return "help";
    case "QUARANTINED":
      return "shield-x";
    case "EXCLUDED":
      return "ban";
    case "UNAVAILABLE":
      return "minus";
    case "UNKNOWN":
      return "question";
  }
}
