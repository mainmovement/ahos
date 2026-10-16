/**
 * AHOS — formatting utilities (`lib/format.ts`)
 * ==============================================
 *
 * Built-in `Intl` only. No date library, no number library, no network, no I/O.
 *
 * Three promises this module makes:
 * 1. **Persian by default.** Digits, grouping, decimal separator, Jalali calendar
 *    and relative time all come from ICU (`fa-IR`, `fa-IR-u-ca-persian`). Latin
 *    digits stay available behind an explicit flag for tables where the operator
 *    compares against an exchange screen.
 * 2. **Never fabricate.** Every entry point accepts `null | undefined | NaN` and
 *    returns `PLACEHOLDER` instead of `0`, `Invalid Date` or a rounded guess.
 *    `formatObserved()` additionally refuses to print a number whose freshness is
 *    `UNKNOWN`, even if a value somehow leaked into the envelope.
 * 3. **Freshness travels with the text.** `formatObserved()` returns the chip kind
 *    and the `asOf` timestamp next to the string, so the UI can never render a
 *    bare number without knowing where it came from.
 *
 * Node ≥ 20 and every modern browser ship full ICU, so `fa-IR-u-ca-persian` and
 * `Intl.RelativeTimeFormat("fa")` are available without polyfills.
 */

import type { Freshness, IsoTimestamp, Observed } from "../types/contract.ts";
import { FRESHNESS } from "../types/contract.ts";

/* ------------------------------------------------------------------------- *
 * Locales & constants
 * ------------------------------------------------------------------------- */

export type LocaleTag = "fa" | "en";

/** AHOS is a Persian RTL product; `fa` is the default everywhere. */
export const DEFAULT_LOCALE: LocaleTag = "fa";

/** Rendered whenever a value is unknown, missing, NaN or unparsable. */
export const PLACEHOLDER = "—";

/** Word form of UNKNOWN, for cells that must not show a bare dash. */
export const UNKNOWN_TEXT: Record<LocaleTag, string> = {
  fa: "نامعلوم",
  en: "Unknown",
};

/** Spoken/written form of "just now" below the minute threshold. */
export const JUST_NOW_TEXT: Record<LocaleTag, string> = {
  fa: "همین حالا",
  en: "just now",
};

const UNIT_LABELS = {
  usd: { fa: "دلار", en: "USD" },
  usdt: { fa: "تتر", en: "USDT" },
  paperUsd: { fa: "دلار کاغذی", en: "paper USD" },
  paperUsdt: { fa: "تتر کاغذی", en: "paper USDT" },
  bps: { fa: "نقطهٔ پایه", en: "bps" },
} as const satisfies Record<string, Record<LocaleTag, string>>;

export type MoneyUnitTag = keyof typeof UNIT_LABELS;

/* ------------------------------------------------------------------------- *
 * BCP-47 helpers (the only place locale strings are assembled)
 * ------------------------------------------------------------------------- */

export interface LocaleExtensionOptions {
  /** `true` → Persian digits (۰۱۲۳…), `false` → Latin digits. Default: `true` for `fa`. */
  persianDigits?: boolean;
  /** `persian` → Jalali calendar, `gregory` → Gregorian. Default: `persian` for `fa`. */
  jalali?: boolean;
}

/**
 * Builds a BCP-47 tag with Unicode extensions, e.g.
 * `fa-IR-u-ca-persian`, `fa-IR-u-nu-latn`, `fa-IR-u-ca-persian-nu-latn`.
 *
 * Extension keys are emitted in alphabetical order (`ca` before `nu`), which is
 * what ICU and `Intl` canonicalisation expect.
 */
export function localeId(locale: LocaleTag, ext: LocaleExtensionOptions = {}): string {
  const base = locale === "fa" ? "fa-IR" : "en-US";
  const parts: string[] = [];
  if (locale === "fa" && ext.jalali !== false) parts.push("ca-persian");
  if (locale === "fa" && ext.persianDigits === false) parts.push("nu-latn");
  if (locale === "en" && ext.jalali === true) parts.push("ca-persian");
  return parts.length === 0 ? base : `${base}-u-${parts.join("-")}`;
}

/* ------------------------------------------------------------------------- *
 * Caches (Intl object construction is the expensive part)
 * ------------------------------------------------------------------------- */

const numberCache = new Map<string, Intl.NumberFormat>();
const dateCache = new Map<string, Intl.DateTimeFormat>();
const relativeCache = new Map<string, Intl.RelativeTimeFormat>();

function cached<T>(cache: Map<string, T>, key: string, make: () => T): T {
  const hit = cache.get(key);
  if (hit !== undefined) return hit;
  const made = make();
  cache.set(key, made);
  return made;
}

function numberFormat(locale: LocaleTag, persianDigits: boolean, opts: Intl.NumberFormatOptions): Intl.NumberFormat {
  const id = localeId(locale, { persianDigits, jalali: false });
  const key = `${id}|${JSON.stringify(opts)}`;
  return cached(numberCache, key, () => new Intl.NumberFormat(id, opts));
}

function dateFormat(id: string, opts: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
  const key = `${id}|${JSON.stringify(opts)}`;
  return cached(dateCache, key, () => new Intl.DateTimeFormat(id, opts));
}

function relativeFormat(locale: LocaleTag): Intl.RelativeTimeFormat {
  const id = locale === "fa" ? "fa" : "en";
  return cached(relativeCache, id, () => new Intl.RelativeTimeFormat(id, { numeric: "auto", style: "long" }));
}

/* ------------------------------------------------------------------------- *
 * Value normalisation — the "never fabricate" gate
 * ------------------------------------------------------------------------- */

export type MaybeNumber = number | null | undefined;

/** True for a finite, non-NaN number. Everything else is treated as UNKNOWN. */
export function isFiniteNumber(x: MaybeNumber): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

/** Parses a date without ever throwing. Invalid input → `null`, never `Invalid Date`. */
export function toDate(input: Date | IsoTimestamp | number | null | undefined): Date | null {
  if (input === null || input === undefined) return null;
  const d = input instanceof Date ? input : new Date(input);
  const t = d.getTime();
  return Number.isFinite(t) ? d : null;
}

/* ------------------------------------------------------------------------- *
 * Digits
 * ------------------------------------------------------------------------- */

const FA_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
const AR_DIGITS = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"];
const FA_DECIMAL = "٫"; // ARABIC DECIMAL SEPARATOR
const FA_GROUP = "٬"; // ARABIC THOUSAND SEPARATOR

/** Converts ASCII digits in an already-formatted string to Persian digits. */
export function toPersianDigits(text: string): string {
  let out = "";
  for (const ch of text) {
    const ascii = ch.charCodeAt(0) - 48;
    out += ascii >= 0 && ascii <= 9 ? FA_DIGITS[ascii] ?? ch : ch;
  }
  return out.replace(/,/g, FA_GROUP).replace(/\./g, FA_DECIMAL);
}

/** Converts Persian/Arabic-Indic digits and separators back to ASCII. */
export function toLatinDigits(text: string): string {
  let out = "";
  for (const ch of text) {
    const fa = FA_DIGITS.indexOf(ch);
    const ar = AR_DIGITS.indexOf(ch);
    if (fa >= 0) out += String(fa);
    else if (ar >= 0) out += String(ar);
    else if (ch === FA_DECIMAL) out += ".";
    else if (ch === FA_GROUP) out += ",";
    else out += ch;
  }
  return out;
}

/* ------------------------------------------------------------------------- *
 * Numbers
 * ------------------------------------------------------------------------- */

export interface NumberOptions extends LocaleExtensionOptions {
  locale?: LocaleTag;
  /** Exact fraction digits. Defaults to `0` for integers, `2` for money. */
  digits?: number;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  /** Thousands separators. Default `true`. */
  grouping?: boolean;
  /** Rendered when the value is unknown. Default `PLACEHOLDER`. */
  placeholder?: string;
}

/**
 * Locale-aware number formatting.
 *
 * ```ts
 * formatNumber(1234567.891);                          // "۱٬۲۳۴٬۵۶۷٫۸۹۱"
 * formatNumber(1234567.891, { digits: 0 });           // "۱٬۲۳۴٬۵۶۸"
 * formatNumber(1234567.891, { persianDigits: false }); // "1,234,567.891"
 * formatNumber(null);                                 // "—"
 * ```
 */
export function formatNumber(value: MaybeNumber, opts: NumberOptions = {}): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  if (!isFiniteNumber(value)) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const persianDigits = opts.persianDigits ?? locale === "fa";
  const nfOpts: Intl.NumberFormatOptions = { useGrouping: opts.grouping ?? true };
  if (opts.digits !== undefined) {
    nfOpts.minimumFractionDigits = opts.digits;
    nfOpts.maximumFractionDigits = opts.digits;
  } else {
    if (opts.minimumFractionDigits !== undefined) nfOpts.minimumFractionDigits = opts.minimumFractionDigits;
    if (opts.maximumFractionDigits !== undefined) nfOpts.maximumFractionDigits = opts.maximumFractionDigits;
  }
  return numberFormat(locale, persianDigits, nfOpts).format(value);
}

/** Integer formatting (counts, queue depth, cycles). */
export function formatInteger(value: MaybeNumber, opts: NumberOptions = {}): string {
  return formatNumber(value, { ...opts, digits: 0 });
}

/** Compact notation: «۱٫۲ میلیون» / "1.2M". */
export function formatCompact(value: MaybeNumber, opts: NumberOptions = {}): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  if (!isFiniteNumber(value)) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const persianDigits = opts.persianDigits ?? locale === "fa";
  return numberFormat(locale, persianDigits, {
    notation: "compact",
    compactDisplay: "short",
    maximumFractionDigits: opts.digits ?? 1,
  }).format(value);
}

export interface PercentOptions extends NumberOptions {
  /** Prepend «+» for positive values (PnL, 24h change). Default `false`. */
  signed?: boolean;
  /** Fraction digits. Default `1`. */
  digits?: number;
}

/**
 * Percent formatting. The input is already in percent units (3.2 → «۳٫۲٪»).
 *
 * ```ts
 * formatPercent(3.24);                       // "۳٫۲٪"
 * formatPercent(-3.24, { signed: true });    // "−۳٫۲٪"
 * formatPercent(0.4, { signed: true });      // "٪+۰٫۴"  → see note
 * ```
 *
 * Note: ICU places the percent sign per locale, so the `+` is prepended to the
 * formatted string. For `fa` that yields «+۳٫۲٪», which reads correctly in RTL.
 */
export function formatPercent(value: MaybeNumber, opts: PercentOptions = {}): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  if (!isFiniteNumber(value)) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const persianDigits = opts.persianDigits ?? locale === "fa";
  const digits = opts.digits ?? 1;
  const body = numberFormat(locale, persianDigits, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Math.abs(value));
  const sign = value < 0 ? "−" : opts.signed === true && value > 0 ? "+" : "";
  const pct = locale === "fa" ? "٪" : "%";
  return `${sign}${body}${pct}`;
}

export interface MoneyOptions extends NumberOptions {
  /** Which unit label to append. Default `paperUsdt`. */
  unit?: MoneyUnitTag;
  /** Append the unit label at all. Default `true`. */
  withUnit?: boolean;
  /** Fraction digits. Default `2`; large money often reads better at `0`. */
  digits?: number;
  signed?: boolean;
}

/**
 * Money formatting for the paper book. The default unit is *paper* USDT so a
 * stray screenshot can never be mistaken for a real balance.
 *
 * ```ts
 * formatMoney(1234567.5);                  // "۱٬۲۳۴٬۵۶۷٫۵۰ تتر کاغذی"
 * formatMoney(-120.25, { signed: true });  // "−۱۲۰٫۲۵ تتر کاغذی"
 * formatMoney(1234567.5, { digits: 0, unit: "usd", locale: "en" }); // "1,234,568 USD"
 * ```
 */
export function formatMoney(value: MaybeNumber, opts: MoneyOptions = {}): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  if (!isFiniteNumber(value)) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const unit = opts.unit ?? "paperUsdt";
  const digits = opts.digits ?? 2;
  const body = formatNumber(Math.abs(value), {
    ...opts,
    digits,
    locale,
    placeholder,
  });
  const sign = value < 0 ? "−" : opts.signed === true && value > 0 ? "+" : "";
  if (opts.withUnit === false) return `${sign}${body}`;
  return `${sign}${body} ${UNIT_LABELS[unit][locale]}`;
}

/** Basis points, spelled out in Persian («نقطهٔ پایه»). */
export function formatBps(value: MaybeNumber, opts: NumberOptions = {}): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  if (!isFiniteNumber(value)) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const body = formatNumber(Math.abs(value), { ...opts, digits: opts.digits ?? 1, locale, placeholder });
  const sign = value < 0 ? "−" : "";
  return locale === "fa" ? `${sign}${body} ${UNIT_LABELS.bps.fa}` : `${sign}${body} ${UNIT_LABELS.bps.en}`;
}

/** Quantities (coin amounts) with generous precision and no unit label. */
export function formatQty(value: MaybeNumber, opts: NumberOptions = {}): string {
  if (!isFiniteNumber(value)) return opts.placeholder ?? PLACEHOLDER;
  const abs = Math.abs(value);
  const digits = opts.digits ?? (abs >= 1000 ? 2 : abs >= 1 ? 4 : 8);
  return formatNumber(value, { ...opts, digits });
}

/* ------------------------------------------------------------------------- *
 * Jalali dates — `Intl` only, `fa-IR-u-ca-persian`
 * ------------------------------------------------------------------------- */

export type DateStyle = "date" | "long" | "datetime" | "time" | "monthDay" | "yearMonth" | "weekday";

const DATE_STYLE_OPTIONS: Record<DateStyle, Intl.DateTimeFormatOptions> = {
  date: { year: "numeric", month: "2-digit", day: "2-digit" },
  long: { weekday: "long", year: "numeric", month: "long", day: "numeric" },
  datetime: { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" },
  time: { hour: "2-digit", minute: "2-digit" },
  monthDay: { month: "long", day: "numeric" },
  yearMonth: { year: "numeric", month: "long" },
  weekday: { weekday: "long" },
};

export interface DateOptions extends LocaleExtensionOptions {
  locale?: LocaleTag;
  style?: DateStyle;
  timeZone?: string;
  placeholder?: string;
}

/**
 * Jalali (Persian calendar) date formatting using nothing but `Intl`.
 *
 * ```ts
 * formatJalali("2026-10-15T12:00:00.000Z", { timeZone: "UTC" });
 * // style "date"    → "۱۴۰۵/۰۷/۲۳"
 * // style "long"    → "پنجشنبه ۲۳ مهر ۱۴۰۵"
 * // style "datetime"→ "۱۴۰۵/۰۷/۲۳، ۱۲:۰۰"
 * ```
 *
 * `locale: "en"` keeps the Gregorian calendar unless `jalali: true` is passed,
 * in which case the Jalali date is rendered with Latin digits (`1405-07-23`).
 */
export function formatJalali(input: Date | IsoTimestamp | number | null | undefined, opts: DateOptions = {}): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  const d = toDate(input);
  if (d === null) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const style = opts.style ?? "date";
  const persianDigits = opts.persianDigits ?? locale === "fa";
  const dtOpts: Intl.DateTimeFormatOptions = { ...DATE_STYLE_OPTIONS[style] };
  if (opts.timeZone !== undefined) dtOpts.timeZone = opts.timeZone;
  const id = localeId(locale, { persianDigits, jalali: opts.jalali });
  try {
    return dateFormat(id, dtOpts).format(d);
  } catch {
    // An unsupported timeZone must degrade to a placeholder, never to a crash
    // and never to a silently wrong date.
    return placeholder;
  }
}

/** Gregorian rendering, for the English UI and for audit exports. */
export function formatGregorian(input: Date | IsoTimestamp | number | null | undefined, opts: DateOptions = {}): string {
  return formatJalali(input, { ...opts, locale: opts.locale ?? "en", jalali: false });
}

/** Jalali date with the weekday spelled out — used for equity-curve day headers. */
export function formatJalaliLong(input: Date | IsoTimestamp | number | null | undefined, opts: DateOptions = {}): string {
  return formatJalali(input, { ...opts, style: "long" });
}

/** Time-of-day only, e.g. «۱۴:۰۵». */
export function formatClock(input: Date | IsoTimestamp | number | null | undefined, opts: DateOptions = {}): string {
  return formatJalali(input, { ...opts, style: "time" });
}

/**
 * Jalali date in a stable, machine-friendly form: `1405-07-23`.
 * Built from `formatToParts` so it never depends on locale punctuation.
 * Returns `null` when the input is not a valid date — never a fake year.
 */
export function jalaliIsoDate(
  input: Date | IsoTimestamp | number | null | undefined,
  opts: { timeZone?: string; persianDigits?: boolean } = {},
): string | null {
  const d = toDate(input);
  if (d === null) return null;
  const dtOpts: Intl.DateTimeFormatOptions = { year: "numeric", month: "2-digit", day: "2-digit" };
  if (opts.timeZone !== undefined) dtOpts.timeZone = opts.timeZone;
  let parts: Intl.DateTimeFormatPart[];
  try {
    parts = dateFormat(localeId("fa", { persianDigits: false, jalali: true }), dtOpts).formatToParts(d);
  } catch {
    return null;
  }
  const get = (type: string): string => parts.find((p) => p.type === type)?.value ?? "";
  const y = get("year");
  const m = get("month");
  const day = get("day");
  if (y === "" || m === "" || day === "") return null;
  return `${y}-${m}-${day}`;
}

/* ------------------------------------------------------------------------- *
 * Relative time — «۳ دقیقه پیش»
 * ------------------------------------------------------------------------- */

export interface RelativeOptions {
  locale?: LocaleTag;
  persianDigits?: boolean;
  /** Reference instant. Injectable so tests and storybooks are deterministic. */
  now?: Date | IsoTimestamp | number;
  /** Below this many seconds, collapse to «همین حالا». Default `45`. */
  justNowBelowSeconds?: number;
  placeholder?: string;
}

const RELATIVE_UNITS = ["year", "month", "week", "day", "hour", "minute", "second"] as const;
type RelativeUnit = (typeof RELATIVE_UNITS)[number];

const UNIT_SECONDS: Record<RelativeUnit, number> = {
  year: 31_536_000,
  month: 2_592_000,
  week: 604_800,
  day: 86_400,
  hour: 3_600,
  minute: 60,
  second: 1,
};

/**
 * Chooses the coarsest unit whose magnitude is ≥ 1, i.e. the unit a human would
 * say out loud. 90 seconds → minutes, 25 hours → days.
 */
export function pickRelativeUnit(deltaSeconds: number): RelativeUnit {
  const abs = Math.abs(deltaSeconds);
  for (const unit of RELATIVE_UNITS) {
    if (abs >= UNIT_SECONDS[unit]) return unit;
  }
  return "second";
}

/**
 * Persian relative time, produced by `Intl.RelativeTimeFormat("fa")`.
 *
 * ```ts
 * formatRelative(Date.now() - 3 * 60_000);       // "۳ دقیقه پیش"
 * formatRelative(Date.now() + 2 * 3_600_000);    // "۲ ساعت دیگر"
 * formatRelative(Date.now() - 10_000);           // "همین حالا"
 * formatRelative("nonsense");                    // "—"
 * ```
 *
 * `numeric: "auto"` is what turns `-1 day` into «دیروز» instead of «۱ روز پیش».
 */
export function formatRelative(input: Date | IsoTimestamp | number | null | undefined, opts: RelativeOptions = {}): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  const d = toDate(input);
  if (d === null) return placeholder;
  const nowDate = toDate(opts.now ?? Date.now());
  if (nowDate === null) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const deltaSeconds = Math.round((d.getTime() - nowDate.getTime()) / 1000);
  const justNowBelow = opts.justNowBelowSeconds ?? 45;
  if (Math.abs(deltaSeconds) < justNowBelow) return JUST_NOW_TEXT[locale];
  const unit = pickRelativeUnit(deltaSeconds);
  const amount = Math.trunc(deltaSeconds / UNIT_SECONDS[unit]);
  if (amount === 0) return JUST_NOW_TEXT[locale];
  const rtf = relativeFormat(locale);
  const text = rtf.format(amount, unit);
  if (locale === "fa" && opts.persianDigits === false) return toLatinDigits(text);
  return text;
}

/** Short relative time for dense tables: «۳ دقیقه»، «۲ روز». No «پیش». */
export function formatRelativeShort(
  input: Date | IsoTimestamp | number | null | undefined,
  opts: RelativeOptions = {},
): string {
  const placeholder = opts.placeholder ?? PLACEHOLDER;
  const d = toDate(input);
  if (d === null) return placeholder;
  const nowDate = toDate(opts.now ?? Date.now());
  if (nowDate === null) return placeholder;
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const deltaSeconds = Math.abs(Math.round((d.getTime() - nowDate.getTime()) / 1000));
  const unit = pickRelativeUnit(deltaSeconds);
  const amount = Math.max(1, Math.trunc(deltaSeconds / UNIT_SECONDS[unit]));
  const body = formatNumber(amount, { locale, persianDigits: opts.persianDigits, digits: 0, placeholder });
  const words: Record<LocaleTag, Record<RelativeUnit, string>> = {
    fa: { year: "سال", month: "ماه", week: "هفته", day: "روز", hour: "ساعت", minute: "دقیقه", second: "ثانیه" },
    en: { year: "y", month: "mo", week: "w", day: "d", hour: "h", minute: "m", second: "s" },
  };
  return locale === "fa" ? `${body} ${words.fa[unit]}` : `${body}${words.en[unit]}`;
}

/** Elapsed duration in `mm:ss` / `h:mm:ss` form — used by kill-switch cooldowns. */
export function formatDuration(ms: MaybeNumber, opts: { locale?: LocaleTag; persianDigits?: boolean } = {}): string {
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const placeholder = PLACEHOLDER;
  if (!isFiniteNumber(ms) || ms < 0) return placeholder;
  const total = Math.floor(ms / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n: number): string => String(n).padStart(2, "0");
  const body = h > 0 ? `${pad(h)}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
  return opts.persianDigits === false || locale === "en" ? body : toPersianDigits(body);
}

/* ------------------------------------------------------------------------- *
 * Freshness: classification and rollup
 * ------------------------------------------------------------------------- */

/** Milliseconds after which an observation of this kind is no longer LIVE. */
export const STALENESS_BUDGET_MS = {
  quote: 15_000,
  signal: 300_000,
  position: 60_000,
  risk: 60_000,
  health: 30_000,
  log: Number.POSITIVE_INFINITY,
} as const;

export type StalenessKind = keyof typeof STALENESS_BUDGET_MS;

/** How far in the past (or future) an observation is, in milliseconds. */
export function stalenessMs(
  asOf: IsoTimestamp | null | undefined,
  now: Date | IsoTimestamp | number = Date.now(),
): number | null {
  const d = toDate(asOf);
  const n = toDate(now);
  if (d === null || n === null) return null;
  return n.getTime() - d.getTime();
}

/**
 * Derives LIVE / STALE / UNKNOWN from a timestamp and a budget.
 *
 * A future timestamp is treated as UNKNOWN, not as LIVE: a clock that claims to
 * have observed the future is a clock we cannot trust.
 */
export function deriveFreshness(
  asOf: IsoTimestamp | null | undefined,
  kind: StalenessKind = "quote",
  now: Date | IsoTimestamp | number = Date.now(),
): Freshness {
  const age = stalenessMs(asOf, now);
  if (age === null || Number.isNaN(age)) return "UNKNOWN";
  if (age < 0) return "UNKNOWN";
  return age <= STALENESS_BUDGET_MS[kind] ? "LIVE" : "STALE";
}

/**
 * Rollup precedence — checked in order, first match wins.
 *
 * `DEMO` is first on purpose: provenance is a claim about the whole record, and
 * a synthetic record must never be allowed to un-mark itself just because one of
 * its fields is empty. After that the least trustworthy observation wins
 * (`UNKNOWN < STALE < LIVE`), because a row with one missing number must not be
 * advertised as fully observed.
 *
 * This single ordering is used by `worstFreshness()`, by `recordFreshness()`, by
 * `chipForRecord()` in `lib/status.ts`, by `scripts/generate-mocks.mjs` and by
 * `scripts/validate.mjs`, which recomputes it and fails on disagreement.
 */
export const FRESHNESS_ROLLUP_ORDER: readonly Freshness[] = ["DEMO", "UNKNOWN", "STALE", "LIVE"];

/**
 * Worst-of rollup over a list of freshness values.
 * An empty list is `UNKNOWN` — "no rows" is never "everything is fine".
 */
export function worstFreshness(values: readonly Freshness[]): Freshness {
  for (const candidate of FRESHNESS_ROLLUP_ORDER) {
    if (values.includes(candidate)) return candidate;
  }
  return "UNKNOWN";
}

/** True for anything shaped like an `Observed<T>` envelope. */
function isObservedEnvelope(node: object): boolean {
  return "value" in node && "freshness" in node && "asOf" in node;
}

/**
 * Collects every `Observed<T>.freshness` in a record (recursively, including
 * nested entities and arrays) and rolls them up with `worstFreshness()`.
 *
 * Used to fill the record-level `EntityBase.freshness`. Structural identity
 * fields (`id`, `symbol`, …) carry no envelope of their own, so they cannot
 * influence the result: the record-level `freshness` + `asOf` covers them.
 */
export function recordFreshness(record: unknown): Freshness {
  const found: Freshness[] = [];
  const walk = (node: unknown): void => {
    if (Array.isArray(node)) {
      for (const item of node) walk(item);
      return;
    }
    if (node !== null && typeof node === "object") {
      if (isObservedEnvelope(node)) {
        const freshness = (node as { freshness: unknown }).freshness;
        if (typeof freshness === "string" && (FRESHNESS as readonly string[]).includes(freshness)) {
          found.push(freshness as Freshness);
        }
      }
      for (const value of Object.values(node)) walk(value);
    }
  };
  walk(record);
  return worstFreshness(found);
}

/** Every freshness value that means "do not trust this as current truth". */
export function isUntrusted(freshness: Freshness): boolean {
  return freshness === "UNKNOWN" || freshness === "STALE" || freshness === "DEMO";
}

/* ------------------------------------------------------------------------- *
 * formatObserved — the only function tables should call
 * ------------------------------------------------------------------------- */

export type ObservedFormatter<T> = (value: T, locale: LocaleTag, persianDigits: boolean) => string;

export interface FormatObservedOptions extends NumberOptions {
  /** Rendered for UNKNOWN. Default `PLACEHOLDER`. */
  placeholder?: string;
  /** Append the DEMO marker to the text itself, for copy/paste-safe exports. Default `false`. */
  markDemo?: boolean;
  /** Reference instant for the "as of …" relative text. Injectable for tests. */
  now?: Date | IsoTimestamp | number;
}

export interface FormattedValue {
  /** Ready-to-render text. Never a fabricated number. */
  text: string;
  /** The freshness that belongs next to this text as a chip. */
  freshness: Freshness;
  /** i18n key of the chip label, e.g. `status.DEMO.label`. */
  chipKey: string;
  /** i18n key of the one-line explanation used as the tooltip. */
  hintKey: string;
  asOf: IsoTimestamp;
  /** Relative form of `asOf`, e.g. «۳ دقیقه پیش». */
  asOfRelative: string;
  /** Jalali form of `asOf`, e.g. «۱۴۰۵/۰۷/۲۳ ۱۲:۰۰». */
  asOfJalali: string;
  /** `false` whenever the value must not be rendered as data. */
  isKnown: boolean;
  /** `true` for synthetic sample data — the DEMO chip is mandatory. */
  isDemo: boolean;
}

function chipKeys(freshness: Freshness): { chipKey: string; hintKey: string } {
  return { chipKey: `status.${freshness}.label`, hintKey: `status.${freshness}.hint` };
}

/**
 * Formats an `Observed<T>` field into render-ready text plus its provenance.
 *
 * The rule that matters: **an UNKNOWN observation renders as the placeholder even
 * if a value is present.** A number without provenance is not a number.
 *
 * ```ts
 * const price: Observed<number> = demoOf(61250.5, "2026-10-15T11:59:00.000Z");
 * formatObserved(price, (v) => formatMoney(v, { digits: 2 }));
 * // → { text: "۶۱٬۲۵۰٫۵۰ تتر کاغذی", freshness: "DEMO", isDemo: true, … }
 *
 * formatObserved(unknownOf<number>(asOf), (v) => formatMoney(v));
 * // → { text: "—", isKnown: false, freshness: "UNKNOWN" }
 * ```
 */
export function formatObserved<T>(
  obs: Observed<T> | null | undefined,
  format: ObservedFormatter<T>,
  opts: FormatObservedOptions = {},
): FormattedValue {
  const locale = opts.locale ?? DEFAULT_LOCALE;
  const persianDigits = opts.persianDigits ?? locale === "fa";
  const placeholder = opts.placeholder ?? PLACEHOLDER;

  if (obs === null || obs === undefined || !isFiniteDate(obs.asOf)) {
    const unknownAsOf = obs?.asOf ?? "";
    return {
      text: placeholder,
      freshness: "UNKNOWN",
      ...chipKeys("UNKNOWN"),
      asOf: unknownAsOf,
      asOfRelative: placeholder,
      asOfJalali: placeholder,
      isKnown: false,
      isDemo: false,
    };
  }

  const { chipKey, hintKey } = chipKeys(obs.freshness);
  const asOfRelative = formatRelative(obs.asOf, { locale, persianDigits, now: opts.now ?? Date.now() });
  const asOfJalali = formatJalali(obs.asOf, { locale, persianDigits, style: "datetime", timeZone: "UTC" });

  if (obs.freshness === "UNKNOWN" || obs.value === null || obs.value === undefined) {
    return {
      text: placeholder,
      freshness: obs.freshness === "UNKNOWN" ? "UNKNOWN" : obs.freshness,
      chipKey,
      hintKey,
      asOf: obs.asOf,
      asOfRelative,
      asOfJalali,
      isKnown: false,
      isDemo: obs.freshness === "DEMO",
    };
  }

  let text = format(obs.value, locale, persianDigits);
  if (opts.markDemo === true && obs.freshness === "DEMO") {
    text = locale === "fa" ? `${text} (نمایشی)` : `${text} (demo)`;
  }
  return {
    text,
    freshness: obs.freshness,
    chipKey,
    hintKey,
    asOf: obs.asOf,
    asOfRelative,
    asOfJalali,
    isKnown: true,
    isDemo: obs.freshness === "DEMO",
  };
}

function isFiniteDate(asOf: string): boolean {
  return typeof asOf === "string" && Number.isFinite(Date.parse(asOf));
}

/* ------------------------------------------------------------------------- *
 * Ready-made formatters for the common columns
 * ------------------------------------------------------------------------- */

/** Column formatter registry: pass a key to `formatObserved` instead of a lambda. */
export const COLUMN_FORMATTERS = {
  price: (v: number, locale: LocaleTag, persianDigits: boolean): string =>
    formatNumber(v, { locale, persianDigits, digits: v >= 1000 ? 2 : v >= 1 ? 4 : 8 }),
  money: (v: number, locale: LocaleTag, persianDigits: boolean): string =>
    formatMoney(v, { locale, persianDigits, digits: 2 }),
  moneyCompact: (v: number, locale: LocaleTag, persianDigits: boolean): string =>
    formatMoney(v, { locale, persianDigits, digits: 0 }),
  percent: (v: number, locale: LocaleTag, persianDigits: boolean): string =>
    formatPercent(v, { locale, persianDigits, digits: 2, signed: true }),
  percentSigned1: (v: number, locale: LocaleTag, persianDigits: boolean): string =>
    formatPercent(v, { locale, persianDigits, digits: 1, signed: true }),
  qty: (v: number, locale: LocaleTag, persianDigits: boolean): string => formatQty(v, { locale, persianDigits }),
  integer: (v: number, locale: LocaleTag, persianDigits: boolean): string =>
    formatInteger(v, { locale, persianDigits }),
  bps: (v: number, locale: LocaleTag, persianDigits: boolean): string => formatBps(v, { locale, persianDigits }),
  text: (v: string, locale: LocaleTag, persianDigits: boolean): string =>
    persianDigits || locale === "en" ? v : toLatinDigits(v),
  localized: (v: { fa: string; en: string }, locale: LocaleTag, _persianDigits: boolean): string =>
    locale === "fa" ? v.fa : v.en,
  timestamp: (v: IsoTimestamp, locale: LocaleTag, persianDigits: boolean): string =>
    formatJalali(v, { locale, persianDigits, style: "datetime", timeZone: "UTC" }),
} as const;

export type ColumnFormatterKey = keyof typeof COLUMN_FORMATTERS;

/**
 * Convenience wrapper: `formatColumn(record.quote.last, "price")`.
 * Type-checked against the registry, so a money column cannot silently be
 * rendered with an integer formatter without the compiler noticing.
 */
export function formatColumn<K extends ColumnFormatterKey>(
  obs: Observed<Parameters<(typeof COLUMN_FORMATTERS)[K]>[0]> | null | undefined,
  key: K,
  opts: FormatObservedOptions = {},
): FormattedValue {
  const formatter = COLUMN_FORMATTERS[key] as ObservedFormatter<Parameters<(typeof COLUMN_FORMATTERS)[K]>[0]>;
  return formatObserved(obs, formatter, opts);
}

/* ------------------------------------------------------------------------- *
 * Misc UI helpers
 * ------------------------------------------------------------------------- */

/** «BTC/USDT» stays LTR inside an RTL table — wrap it in a bidi isolate. */
export function bidiIsolate(text: string): string {
  return `\u2068${text}\u2069`;
}

/** Keeps symbol strings left-to-right without injecting markup. */
export function formatSymbol(symbol: string | null | undefined): string {
  if (symbol === null || symbol === undefined || symbol === "") return PLACEHOLDER;
  return bidiIsolate(symbol);
}

/** Truncates long ids/addresses: `0x1234…abcd`. */
export function shortenMiddle(text: string | null | undefined, head = 6, tail = 4): string {
  if (text === null || text === undefined || text === "") return PLACEHOLDER;
  if (text.length <= head + tail + 1) return text;
  return `${text.slice(0, head)}…${text.slice(-tail)}`;
}

/** Exports the freshness union for exhaustive switches in UI components. */
export const FRESHNESS_VALUES: readonly Freshness[] = FRESHNESS;
