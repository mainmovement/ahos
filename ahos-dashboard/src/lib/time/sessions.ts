/**
 * Market-session estimator (pure, no React — unit tested in tests/).
 *
 * Computes OPEN/CLOSED from official regular-session hours in each exchange's
 * own time zone using Intl (DST-correct). Holidays, half-days and auctions are
 * NOT modelled — the UI labels every result as an estimate.
 */
export interface Exchange {
  id: string;
  short: string;
  name: { fa: string; en: string };
  timeZone: string;
  /** 0 = Sunday … 6 = Saturday (in exchange local time) */
  days: number[];
  /** Regular sessions as [startMinutes, endMinutes] local wall-clock. */
  sessions: [number, number][];
  alwaysOpen?: boolean;
}

const hm = (h: number, m = 0) => h * 60 + m;

export const EXCHANGES: Exchange[] = [
  { id: "tse-ir", short: "TSE", name: { fa: "بورس تهران", en: "Tehran SE" }, timeZone: "Asia/Tehran", days: [6, 0, 1, 2, 3], sessions: [[hm(9), hm(12, 30)]] },
  { id: "tse-jp", short: "TYO", name: { fa: "بورس توکیو", en: "Tokyo SE" }, timeZone: "Asia/Tokyo", days: [1, 2, 3, 4, 5], sessions: [[hm(9), hm(11, 30)], [hm(12, 30), hm(15, 30)]] },
  { id: "hkex", short: "HKEX", name: { fa: "بورس هنگ‌کنگ", en: "HKEX" }, timeZone: "Asia/Hong_Kong", days: [1, 2, 3, 4, 5], sessions: [[hm(9, 30), hm(12)], [hm(13), hm(16)]] },
  { id: "xetra", short: "XETRA", name: { fa: "زترا فرانکفورت", en: "Xetra" }, timeZone: "Europe/Berlin", days: [1, 2, 3, 4, 5], sessions: [[hm(9), hm(17, 30)]] },
  { id: "lse", short: "LSE", name: { fa: "بورس لندن", en: "London SE" }, timeZone: "Europe/London", days: [1, 2, 3, 4, 5], sessions: [[hm(8), hm(16, 30)]] },
  { id: "nyse", short: "NYSE", name: { fa: "بورس نیویورک", en: "NYSE" }, timeZone: "America/New_York", days: [1, 2, 3, 4, 5], sessions: [[hm(9, 30), hm(16)]] },
  { id: "crypto", short: "CRYPTO", name: { fa: "رمزارز", en: "Crypto" }, timeZone: "UTC", days: [0, 1, 2, 3, 4, 5, 6], sessions: [[0, 1440]], alwaysOpen: true },
];

const WEEKDAYS: Record<string, number> = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
const partsCache = new Map<string, Intl.DateTimeFormat>();

/** Wall-clock weekday + minutes-since-midnight in a time zone. */
export function zonedClock(date: Date, timeZone: string): { weekday: number; minutes: number } {
  let fmt = partsCache.get(timeZone);
  if (!fmt) {
    fmt = new Intl.DateTimeFormat("en-US", { timeZone, weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
    partsCache.set(timeZone, fmt);
  }
  const parts = fmt.formatToParts(date);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  const hour = Number(get("hour")) % 24;
  return { weekday: WEEKDAYS[get("weekday")] ?? 0, minutes: hour * 60 + Number(get("minute")) };
}

export interface SessionState {
  exchange: Exchange;
  open: boolean;
  /** Minutes until the next open/close transition (null for 24/7). */
  minutesToChange: number | null;
}

export function sessionState(exchange: Exchange, date: Date): SessionState {
  if (exchange.alwaysOpen) return { exchange, open: true, minutesToChange: null };
  const { weekday, minutes } = zonedClock(date, exchange.timeZone);
  const today = exchange.days.includes(weekday);
  if (today) {
    for (const [start, end] of exchange.sessions) {
      if (minutes >= start && minutes < end) return { exchange, open: true, minutesToChange: end - minutes };
    }
    const next = exchange.sessions.find(([start]) => start > minutes);
    if (next) return { exchange, open: false, minutesToChange: next[0] - minutes };
  }
  // Find the next trading day (up to 7 days ahead).
  for (let d = 1; d <= 7; d++) {
    const wd = (weekday + d) % 7;
    if (exchange.days.includes(wd)) {
      const first = exchange.sessions[0]![0];
      return { exchange, open: false, minutesToChange: d * 1440 - minutes + first };
    }
  }
  return { exchange, open: false, minutesToChange: null };
}

export function allSessions(date: Date, ids?: string[]): SessionState[] {
  return EXCHANGES.filter((e) => !ids || ids.includes(e.id)).map((e) => sessionState(e, date));
}

/** "2h 05m" style countdown (locale-neutral digits; UI localises). */
export function formatCountdown(minutes: number | null): string {
  if (minutes === null) return "";
  const d = Math.floor(minutes / 1440);
  const h = Math.floor((minutes % 1440) / 60);
  const m = Math.floor(minutes % 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
  return `${m}m`;
}
