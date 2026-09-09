export type LocaleHint = "fa" | "en";

const nf = (locale: LocaleHint, opts: Intl.NumberFormatOptions) =>
  new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US", opts);

export function fmtInt(locale: LocaleHint, n: number): string {
  return nf(locale, { maximumFractionDigits: 0 }).format(n);
}

export function fmtCompact(locale: LocaleHint, n: number): string {
  return nf(locale, {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);
}

/** Money formatting — Persian spells out units, English uses compact $. */
export function fmtUsd(locale: LocaleHint, n: number): string {
  if (n >= 1000) {
    const compact = nf(locale, {
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(n);
    return locale === "fa" ? `${compact} دلار` : `$${compact}`;
  }
  const small = nf(locale, { maximumFractionDigits: n < 1 ? 4 : 2 }).format(n);
  return locale === "fa" ? `${small} دلار` : `$${small}`;
}

export function fmtPct(locale: LocaleHint, v: number, signed = true): string {
  const sign = signed && v > 0 ? (locale === "fa" ? "٪+" : "+") : "";
  const num = nf(locale, { maximumFractionDigits: 1 }).format(Math.abs(v));
  const neg = v < 0 ? (locale === "fa" ? "−" : "-") : "";
  return locale === "fa"
    ? `${sign}${neg}٪${num}`
    : `${sign}${neg}${num}%`;
}

export function fmtClock(locale: LocaleHint, d: Date): string {
  return new Intl.DateTimeFormat(locale === "fa" ? "fa-IR" : "en-US", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

/** Short relative time — «٣٨ دقیقه پیش» / "38m ago". */
export function timeAgo(locale: LocaleHint, date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const diffS = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
  const fa = locale === "fa";
  if (diffS < 60) return fa ? "همین حالا" : "just now";
  const m = Math.floor(diffS / 60);
  if (m < 60)
    return fa ? `${nf("fa", {}).format(m)} دقیقه پیش` : `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24)
    return fa ? `${nf("fa", {}).format(h)} ساعت پیش` : `${h}h ago`;
  const days = Math.floor(h / 24);
  return fa ? `${nf("fa", {}).format(days)} روز پیش` : `${days}d ago`;
}

export function fmtDate(locale: LocaleHint, date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat(locale === "fa" ? "fa-IR" : "en-US", {
    month: "short",
    day: "numeric",
  }).format(d);
}

export function shortAddress(addr: string): string {
  if (addr.length <= 14) return addr;
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}
