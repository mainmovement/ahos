/**
 * MOCK — cross-asset instrument universe. Prices are plausible DEMO levels,
 * NOT market data. Shared by markets / crypto / equities / commodities mocks
 * so the same symbol shows the same price everywhere.
 */
import type { AssetClass, Candle, DataStatus, Instrument, Localized } from "@/lib/api/types";
import { DAY, HOUR, L, candles, gauss, rng, round } from "./_seed";

interface Spec {
  id: string;
  symbol: string;
  name: Localized;
  cls: AssetClass;
  price: number | null;
  chg: number | null;
  quote: string;
  decimals: number;
  vol: number;
  volume?: number | null;
  status?: DataStatus;
  /** seconds since retrieval */
  age?: number;
  source?: string;
}

const SPECS: Spec[] = [
  // Crypto
  { id: "btc", symbol: "BTC", name: L("بیت‌کوین", "Bitcoin"), cls: "crypto", price: 112840, chg: 2.31, quote: "USD", decimals: 0, vol: 0.006, volume: 41.2e9 },
  { id: "eth", symbol: "ETH", name: L("اتریوم", "Ethereum"), cls: "crypto", price: 4382.6, chg: 3.84, quote: "USD", decimals: 1, vol: 0.008, volume: 22.8e9 },
  { id: "sol", symbol: "SOL", name: L("سولانا", "Solana"), cls: "crypto", price: 212.4, chg: 6.12, quote: "USD", decimals: 2, vol: 0.011, volume: 6.1e9 },
  { id: "bnb", symbol: "BNB", name: L("بی‌ان‌بی", "BNB"), cls: "crypto", price: 1048.3, chg: 1.07, quote: "USD", decimals: 1, vol: 0.007, volume: 2.4e9 },
  { id: "xrp", symbol: "XRP", name: L("ریپل", "XRP"), cls: "crypto", price: 2.842, chg: -1.36, quote: "USD", decimals: 3, vol: 0.01, volume: 4.9e9 },
  { id: "ton", symbol: "TON", name: L("تون‌کوین", "Toncoin"), cls: "crypto", price: 3.124, chg: -2.48, quote: "USD", decimals: 3, vol: 0.012, volume: 0.42e9 },
  { id: "doge", symbol: "DOGE", name: L("دوج‌کوین", "Dogecoin"), cls: "crypto", price: 0.2413, chg: 4.92, quote: "USD", decimals: 4, vol: 0.014, volume: 2.2e9 },
  { id: "link", symbol: "LINK", name: L("چین‌لینک", "Chainlink"), cls: "crypto", price: 22.86, chg: 2.04, quote: "USD", decimals: 2, vol: 0.011, volume: 0.9e9 },
  { id: "arb", symbol: "ARB", name: L("آربیتروم", "Arbitrum"), cls: "crypto", price: 0.684, chg: -0.62, quote: "USD", decimals: 3, vol: 0.013, volume: 0.38e9 },
  // FX
  { id: "eurusd", symbol: "EUR/USD", name: L("یورو / دلار", "Euro / US Dollar"), cls: "fx", price: 1.1642, chg: 0.18, quote: "USD", decimals: 4, vol: 0.0012 },
  { id: "usdjpy", symbol: "USD/JPY", name: L("دلار / ین", "US Dollar / Yen"), cls: "fx", price: 149.35, chg: -0.27, quote: "JPY", decimals: 2, vol: 0.0016 },
  { id: "gbpusd", symbol: "GBP/USD", name: L("پوند / دلار", "Pound / US Dollar"), cls: "fx", price: 1.3378, chg: 0.09, quote: "USD", decimals: 4, vol: 0.0013 },
  { id: "dxy", symbol: "DXY", name: L("شاخص دلار", "US Dollar Index"), cls: "fx", price: 98.62, chg: -0.21, quote: "pts", decimals: 2, vol: 0.0011 },
  // Commodities
  { id: "brent", symbol: "BRENT", name: L("نفت برنت", "Brent Crude"), cls: "commodity", price: 68.42, chg: 1.26, quote: "USD/bbl", decimals: 2, vol: 0.006, volume: 312e3 },
  { id: "wti", symbol: "WTI", name: L("نفت وست تگزاس", "WTI Crude"), cls: "commodity", price: 64.95, chg: 1.41, quote: "USD/bbl", decimals: 2, vol: 0.0065, volume: 284e3 },
  { id: "xau", symbol: "XAU/USD", name: L("طلای جهانی (انس)", "Gold spot (oz)"), cls: "commodity", price: 4186.4, chg: 0.74, quote: "USD/oz", decimals: 1, vol: 0.004 },
  { id: "xag", symbol: "XAG/USD", name: L("نقره جهانی (انس)", "Silver spot (oz)"), cls: "commodity", price: 48.75, chg: 1.92, quote: "USD/oz", decimals: 2, vol: 0.008 },
  { id: "ng", symbol: "NG", name: L("گاز طبیعی هنری‌هاب", "Henry Hub Nat Gas"), cls: "commodity", price: 3.42, chg: -2.1, quote: "USD/MMBtu", decimals: 3, vol: 0.014 },
  { id: "hg", symbol: "HG", name: L("مس", "Copper"), cls: "commodity", price: 4.98, chg: 0.35, quote: "USD/lb", decimals: 3, vol: 0.006 },
  // Indices
  { id: "spx", symbol: "SPX", name: L("اس‌اند‌پی ۵۰۰", "S&P 500"), cls: "index", price: 6912.4, chg: 0.42, quote: "pts", decimals: 1, vol: 0.0035 },
  { id: "ndx", symbol: "NDX", name: L("نزدک ۱۰۰", "Nasdaq 100"), cls: "index", price: 25120.6, chg: 0.81, quote: "pts", decimals: 1, vol: 0.0048 },
  { id: "dji", symbol: "DJI", name: L("داوجونز", "Dow Jones"), cls: "index", price: 46982.1, chg: 0.12, quote: "pts", decimals: 1, vol: 0.003 },
  { id: "rut", symbol: "RUT", name: L("راسل ۲۰۰۰", "Russell 2000"), cls: "index", price: null, chg: null, quote: "pts", decimals: 1, vol: 0.005, status: "UNAVAILABLE", age: 0, source: "mock/provider-down" },
  { id: "sx5e", symbol: "STOXX600", name: L("استاکس ۶۰۰", "STOXX Europe 600"), cls: "index", price: 572.3, chg: -0.18, quote: "pts", decimals: 1, vol: 0.003 },
  { id: "dax", symbol: "DAX", name: L("دکس آلمان", "DAX 40"), cls: "index", price: 24410.5, chg: 0.33, quote: "pts", decimals: 1, vol: 0.0038 },
  { id: "cac", symbol: "CAC40", name: L("کک ۴۰ فرانسه", "CAC 40"), cls: "index", price: 8105.2, chg: -0.41, quote: "pts", decimals: 1, vol: 0.0037 },
  { id: "ukx", symbol: "FTSE100", name: L("فوتسی ۱۰۰", "FTSE 100"), cls: "index", price: 9512.8, chg: 0.07, quote: "pts", decimals: 1, vol: 0.003 },
  { id: "nky", symbol: "N225", name: L("نیکی ۲۲۵", "Nikkei 225"), cls: "index", price: 49320.4, chg: 1.18, quote: "pts", decimals: 1, vol: 0.0052, status: "STALE", age: 6 * 3600 },
  { id: "hsi", symbol: "HSI", name: L("هنگ‌سنگ", "Hang Seng"), cls: "index", price: 25880.3, chg: -0.92, quote: "pts", decimals: 1, vol: 0.006, status: "STALE", age: 5 * 3600 },
  { id: "shcomp", symbol: "SSEC", name: L("شانگهای", "Shanghai Composite"), cls: "index", price: 3912.6, chg: 0.21, quote: "pts", decimals: 1, vol: 0.004, status: "STALE", age: 5 * 3600 },
  { id: "kospi", symbol: "KOSPI", name: L("کوسپی کره", "KOSPI"), cls: "index", price: 3640.2, chg: 0.65, quote: "pts", decimals: 1, vol: 0.005, status: "STALE", age: 6 * 3600 },
  { id: "nifty", symbol: "NIFTY50", name: L("نیفتی ۵۰ هند", "Nifty 50"), cls: "index", price: 25640.5, chg: 0.28, quote: "pts", decimals: 1, vol: 0.0035, status: "STALE", age: 4 * 3600 },
  { id: "tedpix", symbol: "TEDPIX", name: L("شاخص کل بورس تهران", "Tehran TEDPIX"), cls: "iran", price: 3084500, chg: -0.64, quote: "pts", decimals: 0, vol: 0.006, status: "STALE", age: 2 * 86400 },
  // Iran market (toman)
  { id: "usdirt", symbol: "USD/IRT", name: L("دلار بازار آزاد", "USD free market"), cls: "iran", price: 112850, chg: 0.36, quote: "IRT", decimals: 0, vol: 0.004, status: "STALE", age: 3 * 3600 },
  { id: "emami", symbol: "EMAMI", name: L("سکه امامی", "Emami gold coin"), cls: "iran", price: 118400000, chg: 0.52, quote: "IRT", decimals: 0, vol: 0.005, status: "STALE", age: 3 * 3600 },
  { id: "gold18", symbol: "GOLD18", name: L("طلای ۱۸ عیار (گرم)", "18k gold (gram)"), cls: "iran", price: 11240000, chg: 0.61, quote: "IRT", decimals: 0, vol: 0.004, status: "STALE", age: 3 * 3600 },
  // Rates
  { id: "us10y", symbol: "US10Y", name: L("بازده اوراق ۱۰ ساله آمریکا", "US 10Y yield"), cls: "rate", price: 4.062, chg: -0.74, quote: "%", decimals: 3, vol: 0.004 },
  { id: "de10y", symbol: "DE10Y", name: L("بازده بوند ۱۰ ساله آلمان", "Bund 10Y yield"), cls: "rate", price: 2.618, chg: 0.31, quote: "%", decimals: 3, vol: 0.004 },
  { id: "iranheavy", symbol: "IRAN-HVY", name: L("نفت سنگین ایران (برآورد)", "Iran Heavy (est.)"), cls: "commodity", price: null, chg: null, quote: "USD/bbl", decimals: 2, vol: 0.006, status: "UNKNOWN", age: 0, source: "mock/no-public-source" },
];

/** Brownian bridge from `start` to `end` with n points. */
export function bridge(key: string, n: number, start: number, end: number, vol: number): number[] {
  const r = rng(key);
  const noise: number[] = [0];
  for (let i = 1; i < n; i++) noise.push(noise[i - 1]! + gauss(r) * vol);
  const nLast = noise[n - 1]!;
  return noise.map((z, i) => {
    const t = i / (n - 1);
    const base = start + (end - start) * t;
    return base * (1 + (z - nLast * t));
  });
}

function build(spec: Spec, now: number): Instrument {
  const n = 36;
  const status: DataStatus = spec.status ?? "DEMO";
  if (spec.price === null) {
    return {
      id: spec.id,
      symbol: spec.symbol,
      name: spec.name,
      assetClass: spec.cls,
      price: null,
      change24h: null,
      high24h: null,
      low24h: null,
      volume24h: null,
      quote: spec.quote,
      decimals: spec.decimals,
      status,
      retrievedAt: status === "UNKNOWN" ? null : new Date(now - (spec.age ?? 60) * 1000).toISOString(),
      source: spec.source ?? "mock/markets",
      spark: [],
    };
  }
  const chg = spec.chg ?? 0;
  const start = spec.price / (1 + chg / 100);
  const pts = bridge(`spark:${spec.id}`, n, start, spec.price, spec.vol).map((v) => round(v, Math.max(spec.decimals, 2) + 2));
  pts[n - 1] = spec.price;
  const hi = Math.max(...pts) * (1 + spec.vol * 0.15);
  const lo = Math.min(...pts) * (1 - spec.vol * 0.15);
  return {
    id: spec.id,
    symbol: spec.symbol,
    name: spec.name,
    assetClass: spec.cls,
    price: spec.price,
    change24h: spec.chg,
    high24h: round(hi, spec.decimals + 1),
    low24h: round(lo, spec.decimals + 1),
    volume24h: spec.volume ?? null,
    quote: spec.quote,
    decimals: spec.decimals,
    status,
    retrievedAt: new Date(now - (spec.age ?? 20 + (spec.id.length * 7) % 50) * 1000).toISOString(),
    source: spec.source ?? "mock/markets",
    spark: pts,
  };
}

export function mockInstruments(now = Date.now()): Instrument[] {
  return SPECS.map((s) => build(s, now));
}

export function mockInstrument(id: string, now = Date.now()): Instrument | undefined {
  const spec = SPECS.find((s) => s.id === id);
  return spec ? build(spec, now) : undefined;
}

export type Timeframe = "1H" | "4H" | "1D";

const TF_INTERVAL: Record<Timeframe, number> = { "1H": HOUR, "4H": 4 * HOUR, "1D": DAY };

export function mockCandles(id: string, timeframe: Timeframe = "1D", n = 140, now = Date.now()): Candle[] {
  const spec = SPECS.find((s) => s.id === id);
  if (!spec || spec.price === null) return [];
  const volMul = timeframe === "1D" ? 2.2 : timeframe === "4H" ? 1.1 : 0.55;
  return candles(`candles:${id}:${timeframe}`, n, spec.price, TF_INTERVAL[timeframe], spec.vol * volMul, now);
}
