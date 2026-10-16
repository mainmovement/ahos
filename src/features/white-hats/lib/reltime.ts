/* Time formatting helpers — Persian labels, tabular Latin digits.
   A missing timestamp is rendered as "—" and the related status becomes
   UNKNOWN; this module never invents a fallback time. */

const MIN = 60_000;
const HOUR = 60 * MIN;
const DAY = 24 * HOUR;

export function formatRelTime(iso: string | null, now: number = Date.now()): string {
  if (!iso) return "—";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "—";
  const delta = now - t;
  if (delta < 0) return "لحظه‌ای پیش";
  if (delta < 45_000) return "لحظه‌ای پیش";
  if (delta < HOUR) {
    const m = Math.max(1, Math.round(delta / MIN));
    return `${m} دقیقه پیش`;
  }
  if (delta < DAY) {
    const h = Math.round(delta / HOUR);
    return `${h} ساعت پیش`;
  }
  const d = Math.round(delta / DAY);
  return `${d} روز پیش`;
}

export function formatClock(iso: string | null): string {
  if (!iso) return "—";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "—";
  const d = new Date(t);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "—";
  const d = new Date(t);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function formatNum(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return String(n);
}
