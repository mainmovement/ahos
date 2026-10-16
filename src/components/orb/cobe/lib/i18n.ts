/**
 * i18n + Persian number/time helpers.
 *
 * Persian (`fa`) is the default language and drives RTL. Nothing here invents data: relative
 * times are derived strictly from a real `asOf` timestamp, and a missing timestamp renders as
 * a dash, never as "just now".
 */

import type { Freshness, Lang } from "../types/globe";

const FA_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"] as const;

/** Converts ASCII digits in a string to Persian digits (leaves everything else untouched). */
export function toPersianDigits(value: string): string {
  let out = "";
  for (const char of value) {
    const code = char.charCodeAt(0) - 48;
    out += code >= 0 && code <= 9 ? FA_DIGITS[code] : char;
  }
  return out;
}

/** Digits in the requested language; decimals use the Persian decimal separator in `fa`. */
export function localizeNumber(value: string | number, lang: Lang): string {
  const raw = typeof value === "number" ? String(value) : value;
  if (lang === "en") return raw;
  return toPersianDigits(raw).replace(".", "٫");
}

/** Signed percentage, localized, or `null` when the value is not a usable number. */
export function formatPercent(value: number | null | undefined, lang: Lang, digits = 2): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  const sign = value > 0 ? "+" : value < 0 ? "−" : "±";
  const magnitude = Math.abs(value).toFixed(digits);
  return `${lang === "fa" ? "" : ""}${sign}${localizeNumber(magnitude, lang)}٪`;
}

/** Absolute timestamp for the detail rows: `1405/07/24 09:31` (fa) or `2026-10-16 09:31` (en). */
export function formatAbsolute(iso: string | null, lang: Lang): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  if (lang === "en") {
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} ${pad(
      date.getUTCHours(),
    )}:${pad(date.getUTCMinutes())}Z`;
  }
  const parts = new Intl.DateTimeFormat("fa-IR-u-nu-latn", {
    timeZone: "UTC",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const pick = (type: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === type)?.value ?? "";
  const stamp = `${pick("year")}/${pick("month")}/${pick("day")} ${pick("hour")}:${pick("minute")}`;
  return localizeNumber(stamp, "fa");
}

const FA_RELATIVE = {
  now: "همین حالا",
  seconds: (n: number) => `${localizeNumber(n, "fa")} ثانیه پیش`,
  minutes: (n: number) => `${localizeNumber(n, "fa")} دقیقه پیش`,
  hours: (n: number) => `${localizeNumber(n, "fa")} ساعت پیش`,
  days: (n: number) => `${localizeNumber(n, "fa")} روز پیش`,
} as const;

const EN_RELATIVE = {
  now: "just now",
  seconds: (n: number) => `${n}s ago`,
  minutes: (n: number) => `${n}m ago`,
  hours: (n: number) => `${n}h ago`,
  days: (n: number) => `${n}d ago`,
} as const;

/**
 * Relative time from an ISO timestamp. Returns `null` when there is no usable timestamp —
 * callers must render an explicit UNKNOWN/"—" rather than a fake "just now".
 */
export function relativeTime(iso: string | null, nowMs: number, lang: Lang = "fa"): string | null {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  const deltaSec = Math.max(0, Math.round((nowMs - then) / 1000));
  const words = lang === "fa" ? FA_RELATIVE : EN_RELATIVE;
  if (deltaSec < 20) return words.now;
  if (deltaSec < 60) return words.seconds(deltaSec);
  const minutes = Math.round(deltaSec / 60);
  if (minutes < 60) return words.minutes(minutes);
  const hours = Math.round(minutes / 60);
  if (hours < 24) return words.hours(hours);
  const days = Math.round(hours / 24);
  if (days < 30) return words.days(days);
  return formatAbsolute(iso, lang);
}

/**
 * How a datum's timestamp should read right now.
 *
 * Before the client clock exists (`nowMs === null`, i.e. server render / hydration) the absolute
 * timestamp is shown, which is deterministic and never misrepresents freshness. Once a clock is
 * available the Persian relative form ("۳ دقیقه پیش") leads, with the absolute value as tooltip text.
 */
export function asOfText(
  iso: string | null,
  nowMs: number | null,
  lang: Lang,
): { relative: string | null; absolute: string | null; display: string | null } {
  const absolute = formatAbsolute(iso, lang);
  if (nowMs === null) return { relative: null, absolute, display: absolute };
  const relative = relativeTime(iso, nowMs, lang);
  return { relative, absolute, display: relative ?? absolute };
}

/* ------------------------------------------------------------------ strings */

export type Dictionary = {
  readonly globeAria: string;
  readonly ringAria: string;
  readonly gateAria: string;
  readonly tableCaption: string;
  readonly columnName: string;
  readonly columnFreshness: string;
  readonly columnAsOf: string;
  readonly columnChange: string;
  readonly columnAttention: string;
  readonly attentionYes: string;
  readonly attentionNo: string;
  readonly unknownValue: string;
  readonly moreMarkers: (n: number) => string;
  readonly markerAria: (name: string, freshness: Freshness, relative: string | null) => string;
  readonly signalAria: (from: string, to: string, outcome: string, reason: string | null) => string;
  readonly outcomeAbsorbed: string;
  readonly outcomeDissipated: string;
  readonly outcomePending: string;
  readonly gateAbsorbed: string;
  readonly gateDissipated: string;
  readonly heartbeatStale: string;
  readonly heartbeatLive: (bpm: string, jitter: string) => string;
  readonly fallbackNotice: string;
  readonly freshness: Record<Freshness, string>;
};

const FA: Dictionary = {
  globeAria: "کره‌ی زنده‌ی بازارهای جهانی — نقاط بازار، کمان‌های سیگنال، حلقه‌ی دروازه",
  ringAria: "حلقه‌ی دوازده دپارتمان",
  gateAria: "دروازه‌ی جذب سیگنال",
  tableCaption: "جدول متنی همه‌ی گره‌های بازار (برای صفحه‌خوان و دستگاه‌های کم‌توان)",
  columnName: "بازار",
  columnFreshness: "تازگی",
  columnAsOf: "زمان داده",
  columnChange: "تغییر",
  columnAttention: "نیاز به توجه",
  attentionYes: "بله",
  attentionNo: "خیر",
  unknownValue: "نامشخص",
  moreMarkers: (n) => `${localizeNumber(n, "fa")} بازار دیگر در حالت آرام پنهان است`,
  markerAria: (name, freshness, relative) =>
    `بازار ${name}، وضعیت ${FA.freshness[freshness]}${relative ? `، آخرین داده ${relative}` : ""}`,
  signalAria: (from, to, outcome, reason) =>
    `سیگنال از ${from} به ${to}، نتیجه ${outcome}${reason ? `، دلیل ${reason}` : ""}`,
  outcomeAbsorbed: "جذب شد",
  outcomeDissipated: "تحلیل رفت",
  outcomePending: "در انتظار",
  gateAbsorbed: "جذب‌شده",
  gateDissipated: "تحلیل‌رفته",
  heartbeatStale: "ضربان متوقف — داده کهنه",
  heartbeatLive: (bpm, jitter) => `ضربان ${bpm} در دقیقه، لرزش ${jitter}`,
  fallbackNotice: "نمایش تخت (بدون WebGL) — همان داده، بدون چرخش",
  freshness: { LIVE: "زنده", STALE: "کهنه", UNKNOWN: "نامشخص", DEMO: "نمونه‌ی نمایشی" },
};

const EN: Dictionary = {
  globeAria: "Live world-market globe — market markers, signal arcs, absorption gate ring",
  ringAria: "Twelve-department outer ring",
  gateAria: "Signal absorption gate",
  tableCaption: "Text table of every market node (screen readers and low-power devices)",
  columnName: "Market",
  columnFreshness: "Freshness",
  columnAsOf: "Data time",
  columnChange: "Change",
  columnAttention: "Attention",
  attentionYes: "yes",
  attentionNo: "no",
  unknownValue: "unknown",
  moreMarkers: (n) => `${n} more market(s) hidden in calm mode`,
  markerAria: (name, freshness, relative) =>
    `Market ${name}, freshness ${EN.freshness[freshness]}${relative ? `, last data ${relative}` : ""}`,
  signalAria: (from, to, outcome, reason) =>
    `Signal from ${from} to ${to}, outcome ${outcome}${reason ? `, reason ${reason}` : ""}`,
  outcomeAbsorbed: "absorbed",
  outcomeDissipated: "dissipated",
  outcomePending: "pending",
  gateAbsorbed: "Absorbed",
  gateDissipated: "Dissipated",
  heartbeatStale: "Heartbeat stopped — stale feed",
  heartbeatLive: (bpm, jitter) => `Heartbeat ${bpm} bpm, jitter ${jitter}`,
  fallbackNotice: "Flat render (no WebGL) — same data, no rotation",
  freshness: { LIVE: "LIVE", STALE: "STALE", UNKNOWN: "UNKNOWN", DEMO: "DEMO" },
};

export function dictionary(lang: Lang): Dictionary {
  return lang === "en" ? EN : FA;
}

/** Text direction for the given language. */
export function direction(lang: Lang): "rtl" | "ltr" {
  return lang === "en" ? "ltr" : "rtl";
}
