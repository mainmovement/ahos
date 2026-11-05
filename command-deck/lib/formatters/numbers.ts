/**
 * Deterministic, locale-aware number formatting.
 * Deliberately avoids `Intl` so server-rendered HTML and client hydration
 * always produce identical strings (no ICU version drift), and so the app
 * stays fully offline-capable and reproducible.
 */

const FA_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"] as const;

export function localizeDigits(input: string, locale: "fa" | "en"): string {
  if (locale !== "fa") return input;
  return input.replace(/[0-9]/g, (d) => FA_DIGITS[Number(d)] ?? d);
}

const GROUP: Record<"fa" | "en", string> = { fa: "٬", en: "," };
const DECIMAL: Record<"fa" | "en", string> = { fa: "٫", en: "." };

export function formatNumber(
  value: number,
  locale: "fa" | "en",
  fractionDigits = 2,
  opts: { sign?: boolean } = {},
): string {
  if (!Number.isFinite(value)) return value === null || Number.isNaN(value) ? "—" : "∞";
  const negative = value < 0 || Object.is(value, -0);
  const abs = Math.abs(value);
  const fixed = abs.toFixed(fractionDigits);
  const [intPart, fracPart] = fixed.split(".");
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, GROUP[locale]);
  const body = fracPart ? `${grouped}${DECIMAL[locale]}${fracPart}` : grouped;
  const sign = negative ? "−" : opts.sign ? "+" : "";
  return `${sign}${body}`;
}

export function formatPercent(value: number, locale: "fa" | "en", fractionDigits = 1, opts: { sign?: boolean } = {}): string {
  const body = formatNumber(value, locale, fractionDigits, opts);
  return locale === "fa" ? `${body}٪` : `${body}%`;
}

export function formatUsd(value: number, locale: "fa" | "en", fractionDigits = 0): string {
  return `$${formatNumber(value, locale, fractionDigits)}`;
}

/** Compact axis-tick formatting: 12.4K / 1.2M — digits localized. */
export function formatCompact(value: number, locale: "fa" | "en"): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${formatNumber(value / 1_000_000, locale, 1)}M`;
  if (abs >= 1_000) return `${formatNumber(value / 1_000, locale, 1)}K`;
  return formatNumber(value, locale, abs < 10 ? 1 : 0);
}

export function formatScore(value: number, locale: "fa" | "en"): string {
  return formatNumber(value, locale, 3);
}

export function formatLeverage(leverage: number | null, locale: "fa" | "en"): string {
  if (leverage === null) return "—";
  return `${localizeDigits(String(leverage), locale)}×`;
}

export function formatSignedUsd(value: number | null, locale: "fa" | "en", fractionDigits = 0): string {
  if (value === null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}$${formatNumber(Math.abs(value), locale, fractionDigits)}`;
}
