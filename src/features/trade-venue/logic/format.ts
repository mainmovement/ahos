/**
 * AHOS · Trade Venue — formatting helpers (pure, SSR-safe)
 * ============================================================================
 * Conventions (documented in README_MERGE.md so the main app can match them):
 *  - Numerals are **Latin** everywhere ("2,436.10"), including inside Persian
 *    sentences, so tables stay column-aligned and copy-pasteable.
 *  - Missing values are «—» (`MISSING_GLYPH`) with «ناموجود» available as a
 *    longer label. A missing value is never rendered as `0`.
 *  - Relative times are computed against an explicit reference instant, never
 *    against the ambient clock, so server and client markup always agree.
 *  - The Tehran clock is the only wall-clock on the page; it is client-only and
 *    degrades to minute resolution under `prefers-reduced-motion`.
 */

import { MISSING_GLYPH, UNKNOWN_LABEL_FA, formatValue, valueText } from "./truth";

export const TEHRAN_TZ = "Asia/Tehran";
export const TEHRAN_ZONE_LABEL = "IRST · Tehran";

export { valueText, formatValue, MISSING_GLYPH };

/** `2,436.10` / `—`. */
export function num(value: number | null | undefined, fractionDigits = 2): string {
  return valueText(value, { fractionDigits });
}

/** Signed variant for neutral delta columns: `+0.98%` / `—`. */
export function signedPct(value: number | null | undefined, fractionDigits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return MISSING_GLYPH;
  return `${value >= 0 ? "+" : "-"}${Math.abs(value).toFixed(fractionDigits)}%`;
}

/** Integer with grouping: `1,204` / `—`. */
export function int(value: number | null | undefined): string {
  return valueText(value, { fractionDigits: 0 });
}

/** «ناموجود» for a value the backend cannot provide at all. */
export function unavailableLabel(): string {
  return UNKNOWN_LABEL_FA;
}

/* --------------------------------------------------------------- time math -- */

export interface TehranParts {
  dateISO: string;
  time: string;
  date: string;
  weekday: string;
}

/** Deterministic Tehran wall-clock pieces for an instant (Intl, no network). */
export function tehranParts(at: Date | string | number): TehranParts {
  const date = at instanceof Date ? at : new Date(at);
  if (Number.isNaN(date.getTime())) {
    return {
      dateISO: MISSING_GLYPH,
      time: MISSING_GLYPH,
      date: MISSING_GLYPH,
      weekday: MISSING_GLYPH,
    };
  }
  const fmt = new Intl.DateTimeFormat("en-GB", {
    timeZone: TEHRAN_TZ,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
  const dateFmt = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    timeZone: TEHRAN_TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const weekdayFmt = new Intl.DateTimeFormat("fa-IR", {
    timeZone: TEHRAN_TZ,
    weekday: "long",
  });
  return {
    dateISO: new Intl.DateTimeFormat("en-CA", {
      timeZone: TEHRAN_TZ,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(date),
    time: fmt.format(date),
    date: dateFmt.format(date),
    weekday: weekdayFmt.format(date),
  };
}

/** `14:32:07` in Tehran. Minute resolution when `withSeconds` is false. */
export function tehranClock(at: Date | string | number, withSeconds = true): string {
  const parts = tehranParts(at);
  if (parts.time === MISSING_GLYPH) return MISSING_GLYPH;
  return withSeconds ? parts.time : parts.time.slice(0, 5);
}

/** `41m ago` → «41 دقیقه پیش». Reference instant is always explicit. */
export function relativeFa(fromISO: string | null, toISO: string | null): string {
  if (!fromISO || !toISO) return UNKNOWN_LABEL_FA;
  const from = new Date(fromISO).getTime();
  const to = new Date(toISO).getTime();
  if (!Number.isFinite(from) || !Number.isFinite(to)) return UNKNOWN_LABEL_FA;

  const seconds = Math.max(0, Math.round((to - from) / 1000));
  if (seconds < 45) return "همین حالا";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} دقیقه پیش`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} ساعت پیش`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days} روز پیش`;
  const months = Math.round(days / 30);
  if (months < 12) return `${months} ماه پیش`;
  return `${Math.round(months / 12)} سال پیش`;
}

/** Age of a row in a compact, unambiguous form: `41m` / `3h` / `2d` / `—`. */
export function ageShort(updatedAtISO: string | null, referenceISO: string | null): string {
  if (!updatedAtISO || !referenceISO) return MISSING_GLYPH;
  const seconds = Math.max(
    0,
    Math.round((new Date(referenceISO).getTime() - new Date(updatedAtISO).getTime()) / 1000),
  );
  if (!Number.isFinite(seconds)) return MISSING_GLYPH;
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h`;
  return `${Math.round(seconds / 86400)}d`;
}

/** «۳ دقیقه پیش» plus the row's own timestamp, for STALE cells. */
export function staleDetail(updatedAtISO: string | null, referenceISO: string | null): string {
  if (!updatedAtISO) return UNKNOWN_LABEL_FA;
  return `${relativeFa(updatedAtISO, referenceISO)} · ${ageShort(updatedAtISO, referenceISO)}`;
}

/* ------------------------------------------------------------------ numbers -- */

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/** Share of rows that are DEMO — used for the honesty footnote, never a KPI. */
export function ratio(numerator: number, denominator: number): number | null {
  if (!denominator) return null;
  return numerator / denominator;
}
