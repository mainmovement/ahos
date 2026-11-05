/**
 * Pure, dependency-free derivations for the live layer — unit-testable.
 * No DOM, no network, no three.js.
 */
import type { AssetQuote } from "./market-bus";

/* ------------------------- demo portfolio (holdings are DEMO; prices are live) ------------------------- */

export interface DemoHolding {
  asset: string;
  qty: number;
}

/** DEMO holdings configuration — the UI must always label these as demo. */
export const DEMO_HOLDINGS: DemoHolding[] = [
  { asset: "BTC", qty: 12.5 },
  { asset: "ETH", qty: 180 },
  { asset: "SOL", qty: 3200 },
  { asset: "DOGE", qty: 9_000_000 },
  { asset: "XAU", qty: 850 },
  { asset: "WTI", qty: 60_000 },
  { asset: "GSPC", qty: 400 },
];

export interface PortfolioTotals {
  totalUsd: number | null;
  pnlTodayUsd: number | null;
  liveAssets: number;
  totalAssets: number;
}

export function computePortfolio(quotes: Partial<Record<string, Pick<AssetQuote, "price" | "change24h">>>): PortfolioTotals {
  let total = 0;
  let pnl = 0;
  let live = 0;
  let withChange = 0;
  for (const holding of DEMO_HOLDINGS) {
    const quote = quotes[holding.asset];
    if (!quote || quote.price == null) continue;
    total += holding.qty * quote.price;
    live += 1;
    if (quote.change24h != null) {
      pnl += holding.qty * quote.price * (quote.change24h / 100);
      withChange += 1;
    }
  }
  return {
    totalUsd: live > 0 ? total : null,
    pnlTodayUsd: withChange > 0 ? pnl : null,
    liveAssets: live,
    totalAssets: DEMO_HOLDINGS.length,
  };
}

/* ------------------------- weather-code classification (WMO) ------------------------- */

export type WeatherKind = "clear" | "partly" | "cloudy" | "fog" | "rain" | "snow";

const RAIN_CODES = new Set([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]);
const SNOW_CODES = new Set([71, 73, 75, 77, 85, 86]);

export function classifyWmo(code: number | null): WeatherKind {
  if (code == null) return "cloudy";
  if (code === 0) return "clear";
  if (code === 1 || code === 2) return "partly";
  if (code === 45 || code === 48) return "fog";
  if (RAIN_CODES.has(code)) return "rain";
  if (SNOW_CODES.has(code)) return "snow";
  return "cloudy";
}

/* ------------------------- sky phase from local hour ------------------------- */

export type SkyPhase = "night" | "dawn" | "day" | "dusk";

export function skyPhaseFromHour(hour: number): SkyPhase {
  if (hour >= 5 && hour < 7) return "dawn";
  if (hour >= 7 && hour < 17) return "day";
  if (hour >= 17 && hour < 19) return "dusk";
  return "night";
}

/** Live Tehran hour-of-day (0..23, fractional) — real clock, no simulation. */
export function tehranHour(at: Date = new Date()): number {
  const fmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Tehran", hour12: false, hour: "2-digit", minute: "2-digit" });
  const [h, m] = fmt.format(at).split(":");
  return (Number(h) % 24) + Number(m) / 60;
}

/* ------------------------- wall clock (4 zones) ------------------------- */

export const WALL_CLOCK_ZONES = [
  { id: "tehran", tz: "Asia/Tehran" },
  { id: "newYork", tz: "America/New_York" },
  { id: "beijing", tz: "Asia/Shanghai" },
  { id: "berlin", tz: "Europe/Berlin" },
] as const;

export type WallClockId = (typeof WALL_CLOCK_ZONES)[number]["id"];

export function tzClockParts(tz: string, at: Date = new Date()): { h: string; m: string; s: string } {
  const fmt = new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const parts = fmt.format(at).split(":");
  return { h: parts[0], m: parts[1], s: parts[2] ?? "00" };
}

/* ------------------------- number formatting ------------------------- */

/** Financial USD formatting for canvas text (latin digits). */
export function fmtUsd(v: number): string {
  const abs = Math.abs(v);
  const digits = abs >= 1000 ? 0 : abs >= 10 ? 2 : 4;
  return v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function fmtPct(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

export function fmtQty(v: number): string {
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(1)}K`;
  return v.toFixed(v < 10 ? 3 : 0);
}
