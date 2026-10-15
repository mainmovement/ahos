/**
 * Deterministic mock-data helpers.  MOCK ONLY — nothing in here may be
 * imported by components directly; go through `src/lib/api/*`.
 *
 * All generators are seeded so the same request renders identical numbers
 * on the server and the client (no hydration drift, stable screenshots).
 */
import type { Candle, DataMeta, Localized, SeriesPoint } from "@/lib/api/types";

export const MINUTE = 60_000;
export const HOUR = 60 * MINUTE;
export const DAY = 24 * HOUR;

/** Mulberry32 PRNG — tiny, fast, good enough for mock series. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** FNV-1a string hash → 32-bit seed. */
export function seedOf(key: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < key.length; i++) {
    h ^= key.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

export function rng(key: string): () => number {
  return mulberry32(seedOf(key));
}

/** Box–Muller normal sample. */
export function gauss(r: () => number): number {
  const u = Math.max(r(), 1e-9);
  const v = r();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export function round(value: number, decimals = 2): number {
  const f = 10 ** decimals;
  return Math.round(value * f) / f;
}

/**
 * Geometric random walk that ENDS at `end` (so headline prices match the
 * sparkline's last point). `vol` is per-step stdev as a fraction.
 */
export function walk(key: string, n: number, end: number, vol = 0.01, drift = 0): number[] {
  const r = rng(key);
  const out: number[] = new Array(n);
  let v = end;
  out[n - 1] = end;
  for (let i = n - 2; i >= 0; i--) {
    v = v / (1 + drift + vol * gauss(r));
    out[i] = v;
  }
  return out;
}

/** Same as `walk` but rounded. */
export function spark(key: string, end: number, n = 32, vol = 0.012, drift = 0, decimals = 4): number[] {
  return walk(key, n, end, vol, drift).map((v) => round(v, decimals));
}

/** Floor a timestamp to an interval boundary. */
export function floorTo(t: number, interval: number): number {
  return Math.floor(t / interval) * interval;
}

/** OHLCV candles ending at `end` price; last candle closes at `now` floored. */
export function candles(key: string, n: number, end: number, interval: number, vol = 0.012, now = Date.now()): Candle[] {
  const r = rng(`${key}:ohlc`);
  const closes = walk(key, n, end, vol, 0.0004);
  const last = floorTo(now, interval);
  const out: Candle[] = [];
  let prevClose = closes[0]! * (1 + vol * gauss(r) * 0.3);
  for (let i = 0; i < n; i++) {
    const c = closes[i]!;
    const o = prevClose;
    const span = Math.abs(c - o) + c * vol * (0.35 + r() * 0.9);
    const h = Math.max(o, c) + span * r() * 0.6;
    const l = Math.min(o, c) - span * r() * 0.6;
    const v = Math.round((0.6 + r() * 1.4) * 1000 * (1 + Math.abs(c - o) / (c * vol)));
    out.push({ t: last - (n - 1 - i) * interval, o: round(o, 4), h: round(h, 4), l: round(l, 4), c: round(c, 4), v });
    prevClose = c;
  }
  return out;
}

/** Time series of `n` points ending now. */
export function series(key: string, n: number, end: number, interval: number, vol = 0.01, drift = 0, now = Date.now(), decimals = 3): SeriesPoint[] {
  const vals = walk(key, n, end, vol, drift);
  const last = floorTo(now, interval);
  return vals.map((v, i) => ({ t: last - (n - 1 - i) * interval, v: round(v, decimals) }));
}

/** Bounded oscillating series (e.g. CPU %) between min and max. */
export function bounded(key: string, n: number, min: number, max: number, interval: number, now = Date.now()): SeriesPoint[] {
  const r = rng(key);
  const last = floorTo(now, interval);
  const out: SeriesPoint[] = [];
  let v = (min + max) / 2;
  for (let i = 0; i < n; i++) {
    v += (r() - 0.5) * (max - min) * 0.18 + ((min + max) / 2 - v) * 0.08;
    v = Math.min(max, Math.max(min, v));
    out.push({ t: last - (n - 1 - i) * interval, v: round(v, 1) });
  }
  return out;
}

export function isoAgo(ms: number, now = Date.now()): string {
  return new Date(now - ms).toISOString();
}

export function minutesAgo(min: number, now = Date.now()): string {
  return isoAgo(min * MINUTE, now);
}

export function pick<T>(r: () => number, items: readonly T[]): T {
  return items[Math.floor(r() * items.length)]!;
}

export const L = (fa: string, en: string): Localized => ({ fa, en });

/**
 * Standard envelope metadata for mock payloads. Status is ALWAYS `DEMO`:
 * mock data must never present itself as LIVE.
 */
export function mockMeta(source: string, label: Localized, retrievedSecondsAgo = 45, ttlSec = 300, note?: Localized): DataMeta {
  return {
    source: `mock/${source}`,
    sourceLabel: label,
    retrievedAt: new Date(Date.now() - retrievedSecondsAgo * 1000).toISOString(),
    status: "DEMO",
    isMock: true,
    ttlSec,
    note,
  };
}
