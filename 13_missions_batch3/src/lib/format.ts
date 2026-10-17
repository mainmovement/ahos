// FILE: 13_missions_batch3/src/lib/format.ts
/**
 * Display helpers. Rule: missing values render «—», never a fabricated zero.
 */

/** «—» for any null/undefined/empty value. */
export function dash(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" && value.trim() === "") return "—";
  return String(value);
}

/** Persian digits with fa-IR grouping. */
export function faNum(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "—";
  return new Intl.NumberFormat("fa-IR").format(n);
}

/** Count label that refuses to fake zero: null ⇒ «—». */
export function countLabel(n: number | null | undefined): string {
  return faNum(n);
}

const tehranDateFmt = new Intl.DateTimeFormat("fa-IR", {
  timeZone: "Asia/Tehran",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

const tehranTimeFmt = new Intl.DateTimeFormat("fa-IR", {
  timeZone: "Asia/Tehran",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

/** Tehran date part of an ISO timestamp. null ⇒ «—». */
export function tehranDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return tehranDateFmt.format(d);
}

/** Tehran time part of an ISO timestamp. null ⇒ «—». */
export function tehranTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return tehranTimeFmt.format(d);
}

/** Tehran date + time. null ⇒ «—». */
export function tehranDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return `${tehranDate(iso)} — ${tehranTime(iso)}`;
}

/** Short age label between two ISO timestamps. Unknown ⇒ «—». */
export function ageLabel(fromIso: string | null | undefined, toIso: string | null | undefined): string {
  if (!fromIso || !toIso) return "—";
  const a = new Date(fromIso).getTime();
  const b = new Date(toIso).getTime();
  if (Number.isNaN(a) || Number.isNaN(b) || b < a) return "—";
  const mins = Math.floor((b - a) / 60000);
  if (mins < 60) return `${faNum(mins)} دقیقه`;
  const hours = Math.floor(mins / 60);
  if (hours < 48) return `${faNum(hours)} ساعت`;
  return `${faNum(Math.floor(hours / 24))} روز`;
}

/** Median of numbers. Empty set ⇒ null (renders —). */
export function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

/** Clamp a string to n chars (no ellipsis tricks that hide content). */
export function clamp(text: string, n: number): string {
  return text.length <= n ? text : text.slice(0, n);
}
