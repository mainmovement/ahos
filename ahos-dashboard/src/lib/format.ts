"use client";

import { useMemo } from "react";
import { useSettings } from "@/lib/settings/provider";
import type { DigitMode, Locale } from "@/lib/settings/types";
import type { ValueFormat } from "@/lib/api/types";

export const DASH = "—";

export function numberLocale(locale: Locale, digits: DigitMode): string {
  if (locale === "fa") return digits === "persian" ? "fa-IR" : "fa-IR-u-nu-latn";
  return digits === "persian" ? "en-US-u-nu-arabext" : "en-US";
}

export function dateLocale(locale: Locale, digits: DigitMode): string {
  if (locale === "fa") return digits === "persian" ? "fa-IR-u-ca-persian" : "fa-IR-u-ca-persian-nu-latn";
  return digits === "persian" ? "en-GB-u-nu-arabext" : "en-GB";
}

export interface Formatter {
  locale: Locale;
  numLocale: string;
  num: (v: number | null | undefined, decimals?: number, minDecimals?: number) => string;
  compact: (v: number | null | undefined, decimals?: number) => string;
  /** v is already a percentage (2.31 → "+2.31%"). */
  pct: (v: number | null | undefined, decimals?: number, signed?: boolean) => string;
  usd: (v: number | null | undefined, decimals?: number) => string;
  usdCompact: (v: number | null | undefined) => string;
  value: (v: number | null | undefined, format: ValueFormat, decimals?: number) => string;
  time: (d: string | number | Date | null | undefined, opts?: { seconds?: boolean; timeZone?: string }) => string;
  date: (d: string | number | Date | null | undefined, opts?: { timeZone?: string; withYear?: boolean }) => string;
  dateTime: (d: string | number | Date | null | undefined, timeZone?: string) => string;
  ago: (d: string | number | Date | null | undefined, now: number | null) => string;
  duration: (seconds: number | null | undefined) => string;
  digits: (s: string) => string;
}

const PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹";

export function toPersianDigits(input: string): string {
  return input.replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)]!);
}

const cache = new Map<string, Intl.NumberFormat>();
function nf(locale: string, opts: Intl.NumberFormatOptions): Intl.NumberFormat {
  const key = locale + JSON.stringify(opts);
  let f = cache.get(key);
  if (!f) {
    f = new Intl.NumberFormat(locale, opts);
    cache.set(key, f);
  }
  return f;
}

const dcache = new Map<string, Intl.DateTimeFormat>();
function df(locale: string, opts: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
  const key = locale + JSON.stringify(opts);
  let f = dcache.get(key);
  if (!f) {
    f = new Intl.DateTimeFormat(locale, opts);
    dcache.set(key, f);
  }
  return f;
}

function toDate(d: string | number | Date): Date {
  return d instanceof Date ? d : new Date(d);
}

export function createFormatter(locale: Locale, digits: DigitMode): Formatter {
  const numLocale = numberLocale(locale, digits);
  const dLocale = dateLocale(locale, digits);
  const ok = (v: number | null | undefined): v is number => typeof v === "number" && Number.isFinite(v);
  const fixDigits = (s: string) => (digits === "persian" ? toPersianDigits(s) : s);

  const num: Formatter["num"] = (v, decimals = 2, minDecimals) =>
    ok(v) ? nf(numLocale, { maximumFractionDigits: decimals, minimumFractionDigits: minDecimals ?? Math.min(decimals, Math.abs(v) < 1000 ? decimals : 0) }).format(v) : DASH;

  const compact: Formatter["compact"] = (v, decimals = 1) =>
    ok(v) ? nf(numLocale, { notation: "compact", maximumFractionDigits: decimals }).format(v) : DASH;

  const pct: Formatter["pct"] = (v, decimals = 2, signed = true) =>
    ok(v)
      ? nf(numLocale, { style: "percent", maximumFractionDigits: decimals, minimumFractionDigits: decimals, signDisplay: signed ? "exceptZero" : "auto" }).format(v / 100)
      : DASH;

  const usd: Formatter["usd"] = (v, decimals = 2) =>
    ok(v) ? nf(numLocale, { style: "currency", currency: "USD", currencyDisplay: "narrowSymbol", maximumFractionDigits: decimals, minimumFractionDigits: Math.min(decimals, 2) }).format(v) : DASH;

  // Persian: "18.4 میلیون $" (reads naturally RTL); English: "$18.4M".
  const usdCompact: Formatter["usdCompact"] = (v) =>
    ok(v)
      ? locale === "fa"
        ? `${nf(numLocale, { notation: "compact", maximumFractionDigits: 2 }).format(v)} $`
        : nf(numLocale, { style: "currency", currency: "USD", currencyDisplay: "narrowSymbol", notation: "compact", maximumFractionDigits: 2 }).format(v)
      : DASH;

  const value: Formatter["value"] = (v, format, decimals) => {
    switch (format) {
      case "count":
        return num(v, 0, 0);
      case "percent":
        return pct(v, decimals ?? 2, false);
      case "usd":
        return usd(v, decimals ?? 2);
      case "usdCompact":
        return usdCompact(v);
      case "score":
        return num(v, 0, 0);
      case "ratio":
        return num(v, decimals ?? 2, decimals ?? 2);
      default:
        return num(v, decimals ?? 2);
    }
  };

  const time: Formatter["time"] = (d, opts) => {
    if (d === null || d === undefined) return DASH;
    return df(dLocale, { hour: "2-digit", minute: "2-digit", second: opts?.seconds ? "2-digit" : undefined, hour12: false, timeZone: opts?.timeZone }).format(toDate(d));
  };

  const date: Formatter["date"] = (d, opts) => {
    if (d === null || d === undefined) return DASH;
    return df(dLocale, { day: "numeric", month: "short", year: opts?.withYear ? "numeric" : undefined, timeZone: opts?.timeZone }).format(toDate(d));
  };

  const dateTime: Formatter["dateTime"] = (d, timeZone) => {
    if (d === null || d === undefined) return DASH;
    return df(dLocale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false, timeZone }).format(toDate(d));
  };

  const rtf = new Intl.RelativeTimeFormat(locale === "fa" ? (digits === "persian" ? "fa" : "fa-u-nu-latn") : "en", { numeric: "auto", style: "short" });
  const ago: Formatter["ago"] = (d, now) => {
    if (d === null || d === undefined) return locale === "fa" ? "نامعلوم" : "unknown";
    if (now === null) return time(d);
    const diff = (toDate(d).getTime() - now) / 1000;
    const abs = Math.abs(diff);
    if (abs < 45) return fixDigits(rtf.format(Math.round(diff), "second"));
    if (abs < 3600) return fixDigits(rtf.format(Math.round(diff / 60), "minute"));
    if (abs < 86400) return fixDigits(rtf.format(Math.round(diff / 3600), "hour"));
    return fixDigits(rtf.format(Math.round(diff / 86400), "day"));
  };

  const duration: Formatter["duration"] = (seconds) => {
    if (!ok(seconds)) return DASH;
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const fa = locale === "fa";
    const D = fa ? `${d} روز` : `${d}d`;
    const Hh = fa ? `${h} ساعت` : `${h}h`;
    const M = fa ? `${m} دقیقه` : `${m}m`;
    const parts = d > 0 ? (h > 0 ? [D, Hh] : [D]) : h > 0 ? (m > 0 ? [Hh, M] : [Hh]) : [M];
    return fixDigits(parts.join(fa ? " و " : " "));
  };

  return { locale, numLocale, num, compact, pct, usd, usdCompact, value, time, date, dateTime, ago, duration, digits: fixDigits };
}

export function useFormat(): Formatter {
  const { settings } = useSettings();
  return useMemo(() => createFormatter(settings.locale, settings.digits), [settings.locale, settings.digits]);
}
