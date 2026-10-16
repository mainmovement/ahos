/**
 * Formatting helpers — deterministic, timezone-pinned, ICU-free.
 *
 * Tehran is a fixed +03:30 offset (Iran abolished DST in 2022), so every
 * timestamp below is produced by shifting into Tehran wall-clock time and
 * formatting with UTC getters. No locale database is required, which keeps
 * server and client output byte-identical (no hydration mismatch).
 */

/** Tehran offset in minutes. */
export const TEHRAN_OFFSET_MINUTES = 210;

export const MISSING = '—';
export const MISSING_FA = 'ناموجود';

const PERSIAN_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'] as const;

/** Convert Latin digits to Persian digits. Non-digits pass through untouched. */
export function toPersianDigits(input: string | number): string {
  return String(input).replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)] ?? d);
}

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

/** Parse an ISO-8601 string. Returns `null` for anything unparseable. */
export function parseIso(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? null : date;
}

/** Shift a Date into Tehran wall-clock time (UTC getters then read as-is). */
function toTehran(date: Date): Date {
  return new Date(date.getTime() + TEHRAN_OFFSET_MINUTES * 60_000);
}

/** «۰۹:۳۵» in Tehran time. `null` ⇒ «—». */
export function formatTimeFa(iso: string | null | undefined): string {
  const date = parseIso(iso);
  if (!date) return MISSING;
  const t = toTehran(date);
  return toPersianDigits(`${pad2(t.getUTCHours())}:${pad2(t.getUTCMinutes())}`);
}

/** «۰۹:۳۵:۱۲» in Tehran time — used by the live Tehran clock. */
export function formatClockFa(date: Date): string {
  const t = toTehran(date);
  return toPersianDigits(
    `${pad2(t.getUTCHours())}:${pad2(t.getUTCMinutes())}:${pad2(t.getUTCSeconds())}`,
  );
}

/** «۲۰۲۶-۱۰-۱۶» (Gregorian date, Persian digits). */
export function formatDateFa(iso: string | null | undefined): string {
  const date = parseIso(iso);
  if (!date) return MISSING;
  const t = toTehran(date);
  return toPersianDigits(
    `${t.getUTCFullYear()}-${pad2(t.getUTCMonth() + 1)}-${pad2(t.getUTCDate())}`,
  );
}

/** «۰۹:۳۵ · ۲۰۲۶-۱۰-۱۶» */
export function formatStampFa(iso: string | null | undefined): string {
  const date = parseIso(iso);
  if (!date) return MISSING_FA;
  return `${formatTimeFa(iso)} · ${formatDateFa(iso)}`;
}

export type FreshnessBucket = 'FRESH' | 'RECENT' | 'AGING' | 'STALE' | 'UNKNOWN';

export const FRESHNESS_LABEL_FA: Record<FreshnessBucket, string> = {
  FRESH: 'تازه',
  RECENT: 'اخیر',
  AGING: 'در حال گذر',
  STALE: 'کهنه',
  UNKNOWN: 'نامعلوم',
};

export const FRESHNESS_LABEL_EN: Record<FreshnessBucket, string> = {
  FRESH: 'FRESH',
  RECENT: 'RECENT',
  AGING: 'AGING',
  STALE: 'STALE',
  UNKNOWN: 'UNKNOWN',
};

/**
 * Freshness is always measured against the snapshot's own `generatedAt`
 * (never `Date.now()`), so the screen is deterministic and testable.
 */
export function freshnessBucket(
  publishedAt: string | null | undefined,
  nowIso: string | null | undefined,
): FreshnessBucket {
  const published = parseIso(publishedAt);
  const now = parseIso(nowIso);
  if (!published || !now) return 'UNKNOWN';

  const minutes = (now.getTime() - published.getTime()) / 60_000;
  if (minutes < 0) return 'UNKNOWN';
  if (minutes <= 15) return 'FRESH';
  if (minutes <= 60) return 'RECENT';
  if (minutes <= 360) return 'AGING';
  return 'STALE';
}

/** «۱۲ دقیقه پیش» / «۳ ساعت پیش». Missing timestamps render «ناموجود». */
export function formatRelativeFa(
  iso: string | null | undefined,
  nowIso: string | null | undefined,
): string {
  const date = parseIso(iso);
  const now = parseIso(nowIso);
  if (!date || !now) return MISSING_FA;

  const minutes = Math.round((now.getTime() - date.getTime()) / 60_000);
  if (minutes < 0) return MISSING_FA;
  if (minutes < 1) return 'اکنون';
  if (minutes < 60) return `${toPersianDigits(minutes)} دقیقه پیش`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${toPersianDigits(hours)} ساعت پیش`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${toPersianDigits(days)} روز پیش`;

  const months = Math.floor(days / 30);
  return `${toPersianDigits(months)} ماه پیش`;
}

/** «۴/۳» for 4 passes out of 7 attempts. Unknown counters render «—». */
export function formatRatio(pass: number | null, attempts: number | null): string {
  if (pass === null || attempts === null) return MISSING;
  return `${toPersianDigits(pass)}/${toPersianDigits(attempts)}`;
}

/** Small helper: a value or the Persian «ناموجود» placeholder. */
export function orMissingFa(value: string | null | undefined): string {
  return value === null || value === undefined || value.trim() === '' ? MISSING_FA : value;
}

/** Small helper: a value or the «—» placeholder. */
export function orMissing(value: string | null | undefined): string {
  return value === null || value === undefined || value.trim() === '' ? MISSING : value;
}
