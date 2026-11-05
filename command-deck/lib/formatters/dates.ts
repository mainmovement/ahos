/**
 * Deterministic date/time formatting (Gregorian, locale-aware).
 * Relative times are computed against the FROZEN dataset as-of instant —
 * never against the wall clock — so nothing can masquerade as live.
 */
import { DATASET } from "@/lib/data/config";
import { localizeDigits } from "./numbers";

const FA_MONTHS = [
  "ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
  "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر",
] as const;
const FA_MONTHS_SHORT = [
  "ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
  "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر",
] as const;
const EN_MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
] as const;
const EN_MONTHS_SHORT = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
] as const;

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

interface UtcParts {
  y: number;
  m: number; // 1..12
  d: number;
  hh: number;
  mm: number;
}

function utcParts(iso: string): UtcParts | null {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return {
    y: date.getUTCFullYear(),
    m: date.getUTCMonth() + 1,
    d: date.getUTCDate(),
    hh: date.getUTCHours(),
    mm: date.getUTCMinutes(),
  };
}

/** "۳۱ اکتبر ۲۰۲۶" / "31 October 2026" */
export function formatDate(iso: string, locale: "fa" | "en"): string {
  const p = utcParts(iso);
  if (!p) return "—";
  const digits = localizeDigits(`${p.d} ${p.y}`, locale);
  return locale === "fa"
    ? `${digits.split(" ")[0]} ${FA_MONTHS[p.m - 1]} ${digits.split(" ")[1]}`
    : `${p.d} ${EN_MONTHS[p.m - 1]} ${p.y}`;
}

/** "۳۱ اکت" / "Oct 31" — short axis label. */
export function formatDayShort(iso: string, locale: "fa" | "en"): string {
  const p = utcParts(iso);
  if (!p) return "—";
  return locale === "fa"
    ? `${localizeDigits(String(p.d), locale)} ${FA_MONTHS_SHORT[p.m - 1]}`
    : `${EN_MONTHS_SHORT[p.m - 1]} ${p.d}`;
}

/** "۱۴:۳۰" / "14:30" (UTC, dataset time). */
export function formatTime(iso: string, locale: "fa" | "en"): string {
  const p = utcParts(iso);
  if (!p) return "—";
  return localizeDigits(`${pad2(p.hh)}:${pad2(p.mm)}`, locale);
}

export function formatDateTime(iso: string, locale: "fa" | "en"): string {
  const p = utcParts(iso);
  if (!p) return "—";
  return `${formatDate(iso, locale)} · ${formatTime(iso, locale)}`;
}

/** Whole days between the dataset as-of instant and `iso`, honest wording. */
export function formatDaysRelativeToDataset(iso: string, locale: "fa" | "en"): string {
  const then = new Date(iso).getTime();
  const asOf = new Date(DATASET.asOf).getTime();
  if (Number.isNaN(then)) return "—";
  const days = Math.round((asOf - then) / 86_400_000);
  if (days <= 0) return locale === "fa" ? "هم‌زمان با مجموعه داده" : "same day as dataset";
  const n = localizeDigits(String(days), locale);
  return locale === "fa" ? `${n} روز پیش از لنگر داده` : `${days} days before dataset anchor`;
}

export function isoDay(offsetDays: number, from: string = DATASET.windowStart): string {
  const base = new Date(from).getTime();
  const d = new Date(base + offsetDays * 86_400_000);
  return d.toISOString().slice(0, 10);
}

export function isoAt(dayIso: string, hour = 0, minute = 0): string {
  return `${dayIso}T${pad2(hour)}:${pad2(minute)}:00Z`;
}

/** Compact age vs the dataset anchor: "۳ روز" / "3d". */
export function formatDaysAgoShort(iso: string, locale: "fa" | "en"): string {
  const then = new Date(iso).getTime();
  const asOf = new Date(DATASET.asOf).getTime();
  if (Number.isNaN(then)) return "—";
  const days = Math.max(0, Math.round((asOf - then) / 86_400_000));
  return locale === "fa" ? `${localizeDigits(String(days), locale)} روز` : `${days}d`;
}
