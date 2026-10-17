// FILE: 13_missions_batch3/src/lib/stats.ts
/**
 * Pure display-rule helpers shared by every page. Nothing here mutates data.
 * Truth rules encoded here:
 *   - DEMO rows are excluded from every total/count/aggregate.
 *   - A missing value is «—», never a fake 0.
 *   - No timestamp ⇒ UNKNOWN. UNKNOWN is never green.
 *   - REVIEWED/REJECTED without a reason renders as UNREVIEWED.
 */
import type {
  ChipStatus,
  Freshness,
  NewsItem,
  ReviewState,
  SkillMarketEntry,
  SnapshotMeta,
  TruthStatus,
} from "@/contract/types";

/** Rows that count toward totals (DEMO excluded). */
export function nonDemo<T extends { demo: boolean }>(rows: T[]): T[] {
  return rows.filter((r) => !r.demo);
}

/** Snapshot-level DEMO detection: explicit flag, or every row demo. */
export function isDemoSnapshot(meta: SnapshotMeta, rows: { demo: boolean }[]): boolean {
  if (meta.demo === true) return true;
  return rows.length > 0 && rows.every((r) => r.demo);
}

const STALE_AFTER_MS = 15 * 60 * 1000;

/**
 * Page truth chip status.
 * DEMO dominates (mock never presented as real). No timestamp ⇒ UNKNOWN.
 */
export function truthFromSnapshot(
  meta: SnapshotMeta,
  rows: { demo: boolean }[],
  nowMs: number = Date.now(),
): TruthStatus {
  if (isDemoSnapshot(meta, rows)) return "DEMO";
  if (!meta.generatedAt) return "UNKNOWN";
  const t = new Date(meta.generatedAt).getTime();
  if (Number.isNaN(t)) return "UNKNOWN";
  return nowMs - t > STALE_AFTER_MS ? "STALE" : "LIVE";
}

/** Freshness of a news item by its timestamp, relative to the snapshot clock.
 * Missing time or generatedAt ⇒ UNKNOWN. Item newer than snapshot ⇒ UNKNOWN. */
export function newsFreshness(
  item: Pick<NewsItem, "time">,
  generatedAt: string | null,
  staleAfterMinutes: number,
): Freshness {
  if (!item.time || !generatedAt) return "UNKNOWN";
  const itemMs = new Date(item.time).getTime();
  const genMs = new Date(generatedAt).getTime();
  if (Number.isNaN(itemMs) || Number.isNaN(genMs)) return "UNKNOWN";
  const ageMinutes = (genMs - itemMs) / 60000;
  if (ageMinutes < 0) return "UNKNOWN";
  return ageMinutes <= staleAfterMinutes ? "LIVE" : "STALE";
}

export interface EffectiveReview {
  state: ReviewState;
  /** Non-null when the declared state is being overridden. */
  note: string | null;
}

/**
 * REVIEWED/REJECTED without a reason is rendered as UNREVIEWED with a note.
 * Never imply a plugin is safe.
 */
export function effectiveReview(entry: Pick<SkillMarketEntry, "reviewState" | "reason">): EffectiveReview {
  const hasReason = typeof entry.reason === "string" && entry.reason.trim() !== "";
  if ((entry.reviewState === "REVIEWED" || entry.reviewState === "REJECTED") && !hasReason) {
    return { state: "UNREVIEWED", note: "دلیل ثبت نشده" };
  }
  return { state: entry.reviewState, note: null };
}

/** Whether a run/item set has enough non-DEMO samples to be descriptive. */
export function sampleAdequate(count: number, minSampleSize: number): boolean {
  return count >= minSampleSize;
}

/**
 * Resolve the display state of a page.
 * Contract failures are UNAVAILABLE (never thrown, never fake rows).
 * `forced` is the ?state= QA flag and wins over natural state.
 */
export function resolveViewState(
  phase: "LOADING" | "READY" | "ERROR",
  snapshot: { source: string | null; generatedAt: string | null } | null,
  rowCount: number,
  forced: "loading" | "empty" | "error" | "unavailable" | null,
): "OK" | "LOADING" | "ERROR" | "UNAVAILABLE" | "EMPTY" {
  if (forced === "loading") return "LOADING";
  if (forced === "error") return "ERROR";
  if (forced === "unavailable") return "UNAVAILABLE";
  if (forced === "empty") return "EMPTY";
  if (phase === "LOADING") return "LOADING";
  if (phase === "ERROR") return "ERROR";
  if (!snapshot) return "UNAVAILABLE";
  const isUnavailableShape =
    rowCount === 0 && snapshot.source === null && snapshot.generatedAt === null;
  if (isUnavailableShape) return "UNAVAILABLE";
  if (rowCount === 0) return "EMPTY";
  return "OK";
}

/** Chip status for a display-only install state (never "safe"). */
export function chipForInstallState(state: string): ChipStatus {
  switch (state) {
    case "INSTALLED":
      return "LIVE";
    case "BLOCKED":
      return "REJECTED";
    case "AVAILABLE":
      return "PARTIAL";
    default:
      return "UNKNOWN";
  }
}
