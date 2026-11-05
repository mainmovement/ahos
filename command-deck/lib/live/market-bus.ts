/**
 * AHOS live market bus — client-side polling of PUBLIC, KEY-LESS, CORS-open
 * market/weather/news sources directly from the browser.
 *
 * Honesty contract:
 *  - When a source answers, the value is REAL and tagged with its source.
 *  - When no source answers, status is "offline" and the UI must show
 *    NO numbers at all (never fabricated values).
 *  - Holdings configuration for the portfolio board is a DEMO constant;
 *    only the prices multiplied into it are live. UI must say so.
 *
 * All network failures are silent (stored internally, never thrown, never
 * logged) so the scene console stays clean in offline sandboxes.
 */

export type FeedStatus = "live" | "stale" | "offline";

export type AssetId =
  | "XAU" | "PAXG" | "BTC" | "ETH" | "SOL" | "DOGE" | "SHIB" | "PEPE"
  | "WTI" | "BRENT" | "DAX" | "FTSE" | "N225" | "SSE" | "IXIC" | "GSPC";

export interface TradeTick {
  price: number;
  qty: number;
  time: number;
  /** true → the aggressive side was a seller (red tick) */
  buyerMaker: boolean;
}

export interface AssetQuote {
  id: AssetId;
  label: string;
  price: number | null;
  change24h: number | null;
  high24h: number | null;
  low24h: number | null;
  spark: number[];
  tape: TradeTick[];
  source: string | null;
  status: FeedStatus;
  updatedAt: number | null;
}

export interface WeatherNow {
  temperature: number | null;
  humidity: number | null;
  wind: number | null;
  code: number | null;
  isDay: boolean | null;
  sunrise: string | null;
  sunset: string | null;
  source: string | null;
  status: FeedStatus;
  updatedAt: number | null;
}

export interface NewsItem {
  title: string;
}

export interface NewsFeed {
  items: NewsItem[];
  source: string | null;
  status: FeedStatus;
  updatedAt: number | null;
}

export interface MarketSnapshot {
  assets: Record<AssetId, AssetQuote>;
  weather: WeatherNow;
  news: NewsFeed;
}

export const ASSET_LABELS: Record<AssetId, string> = {
  XAU: "XAU", PAXG: "PAXG", BTC: "BTC", ETH: "ETH", SOL: "SOL",
  DOGE: "DOGE", SHIB: "SHIB", PEPE: "PEPE", WTI: "WTI", BRENT: "BRENT",
  DAX: "DAX", FTSE: "FTSE", N225: "N225", SSE: "SSE", IXIC: "IXIC", GSPC: "S&P 500",
};

const ASSET_IDS = Object.keys(ASSET_LABELS) as AssetId[];

function emptyQuote(id: AssetId): AssetQuote {
  return { id, label: ASSET_LABELS[id], price: null, change24h: null, high24h: null, low24h: null, spark: [], tape: [], source: null, status: "offline", updatedAt: null };
}

function initialSnapshot(): MarketSnapshot {
  const assets = {} as Record<AssetId, AssetQuote>;
  for (const id of ASSET_IDS) assets[id] = emptyQuote(id);
  return {
    assets,
    weather: { temperature: null, humidity: null, wind: null, code: null, isDay: null, sunrise: null, sunset: null, source: null, status: "offline", updatedAt: null },
    news: { items: [], source: null, status: "offline", updatedAt: null },
  };
}

/* --------------------------- source endpoints --------------------------- */

const BINANCE_BASE = "https://api.binance.com/api/v3";
const OKX_BASE = "https://www.okx.com/api/v5";
const PROXY = "https://api.allorigins.win/raw?url=";
const REFRESH = { crypto: 45_000, gold: 60_000, indices: 150_000, weather: 600_000, news: 420_000 };

const BINANCE_SYMBOLS: Array<{ id: AssetId; symbol: string }> = [
  { id: "BTC", symbol: "BTCUSDT" },
  { id: "ETH", symbol: "ETHUSDT" },
  { id: "SOL", symbol: "SOLUSDT" },
  { id: "DOGE", symbol: "DOGEUSDT" },
  { id: "SHIB", symbol: "SHIBUSDT" },
  { id: "PEPE", symbol: "PEPEUSDT" },
  { id: "PAXG", symbol: "PAXGUSDT" },
];

const OKX_SYMBOLS: Array<{ id: AssetId; instId: string }> = [
  { id: "BTC", instId: "BTC-USDT" },
  { id: "ETH", instId: "ETH-USDT" },
  { id: "SOL", instId: "SOL-USDT" },
  { id: "DOGE", instId: "DOGE-USDT" },
  { id: "PAXG", instId: "PAXG-USDT" },
];

const COINGECKO_IDS: Array<{ id: AssetId; cg: string }> = [
  { id: "BTC", cg: "bitcoin" },
  { id: "ETH", cg: "ethereum" },
  { id: "SOL", cg: "solana" },
  { id: "DOGE", cg: "dogecoin" },
  { id: "SHIB", cg: "shiba-inu" },
  { id: "PEPE", cg: "pepe" },
  { id: "PAXG", cg: "pax-gold" },
];

const YAHOO_SYMBOLS: Array<{ id: AssetId; sym: string }> = [
  { id: "WTI", sym: "CL=F" },
  { id: "BRENT", sym: "BZ=F" },
  { id: "DAX", sym: "^GDAXI" },
  { id: "FTSE", sym: "^FTSE" },
  { id: "N225", sym: "^N225" },
  { id: "SSE", sym: "000001.SS" },
  { id: "IXIC", sym: "^IXIC" },
  { id: "GSPC", sym: "^GSPC" },
];

async function fetchJson<T>(url: string, timeoutMs = 9000): Promise<T | null> {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { signal: ctrl.signal, headers: { accept: "application/json" } });
      if (!res.ok) return null;
      return (await res.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  } catch {
    return null;
  }
}

async function fetchText(url: string, timeoutMs = 9000): Promise<string | null> {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { signal: ctrl.signal });
      if (!res.ok) return null;
      return await res.text();
    } finally {
      clearTimeout(timer);
    }
  } catch {
    return null;
  }
}

interface TickerResp { lastPrice?: string; priceChangePercent?: string; highPrice?: string; lowPrice?: string }
type KlinesResp = Array<[number, string, string, string, string, ...unknown[]]>;
interface TradeResp { price?: string; qty?: string; time?: number; isBuyerMaker?: boolean }
interface GoldResp { price?: number }
interface CandlesResp { data?: Array<{ last?: string; open24h?: string; high24h?: string; low24h?: string; ts?: string }> }
interface OkxTradesResp { data?: Array<{ px?: string; sz?: string; ts?: string; side?: string }> }
interface YahooChart {
  chart?: { result?: Array<{ meta?: { regularMarketPrice?: number; chartPreviousClose?: number }; indicators?: { quote?: Array<{ close?: Array<number | null> }> } }> }
}
interface OpenMeteo {
  current?: { temperature_2m?: number; relative_humidity_2m?: number; weather_code?: number; wind_speed_10m?: number; is_day?: number };
  daily?: { sunrise?: string[]; sunset?: string[] };
}

/* ------------------------------ the bus ------------------------------ */

export class MarketBus {
  private snapshot: MarketSnapshot = initialSnapshot();
  private listeners = new Set<() => void>();
  private started = false;
  /** internal tally of silent failures (for debugging, never rendered) */
  public failures = 0;

  getSnapshot(): MarketSnapshot {
    return this.snapshot;
  }

  subscribe(fn: () => void): () => void {
    this.listeners.add(fn);
    this.start();
    return () => {
      this.listeners.delete(fn);
    };
  }

  private emit() {
    this.snapshot = { assets: { ...this.snapshot.assets }, weather: { ...this.snapshot.weather }, news: { ...this.snapshot.news } };
    for (const fn of this.listeners) {
      try {
        fn();
      } catch {
        /* listener errors must never break the bus */
      }
    }
  }

  private patchAsset(id: AssetId, patch: Partial<AssetQuote>) {
    this.snapshot.assets[id] = { ...this.snapshot.assets[id], ...patch };
  }

  private markStale(intervalMs: number, ids?: AssetId[]) {
    const now = Date.now();
    const targets = ids ?? ASSET_IDS;
    for (const id of targets) {
      const q = this.snapshot.assets[id];
      if (q.status === "live" && q.updatedAt !== null && now - q.updatedAt > intervalMs * 2.5) {
        this.patchAsset(id, { status: "stale" });
      }
    }
  }

  start() {
    if (this.started || typeof window === "undefined") return;
    this.started = true;
    const loop = (fn: () => Promise<void>, interval: number) => {
      const tick = async () => {
        await fn();
        window.setTimeout(tick, interval);
      };
      void tick();
    };
    loop(() => this.pollCrypto(), REFRESH.crypto);
    loop(() => this.pollGold(), REFRESH.gold);
    loop(() => this.pollIndices(), REFRESH.indices);
    loop(() => this.pollWeather(), REFRESH.weather);
    loop(() => this.pollNews(), REFRESH.news);
  }

  /* ------------------------- crypto (Binance → OKX → CoinGecko) ------------------------- */

  private async pollCrypto() {
    const ok = await this.pollBinance();
    if (!ok) {
      const ok2 = await this.pollOkx();
      if (!ok2) await this.pollCoinGecko();
    }
    this.markStale(REFRESH.crypto, BINANCE_SYMBOLS.map((s) => s.id));
    this.emit();
  }

  private async pollBinance(): Promise<boolean> {
    let any = false;
    for (const { id, symbol } of BINANCE_SYMBOLS) {
      const ticker = await fetchJson<TickerResp>(`${BINANCE_BASE}/ticker/24hr?symbol=${symbol}`);
      if (!ticker?.lastPrice) continue;
      const price = Number(ticker.lastPrice);
      if (!Number.isFinite(price)) continue;
      const patch: Partial<AssetQuote> = {
        price,
        change24h: ticker.priceChangePercent != null ? Number(ticker.priceChangePercent) : null,
        high24h: ticker.highPrice != null ? Number(ticker.highPrice) : null,
        low24h: ticker.lowPrice != null ? Number(ticker.lowPrice) : null,
        source: "Binance",
        status: "live",
        updatedAt: Date.now(),
      };
      const [klines, trades] = await Promise.all([
        fetchJson<KlinesResp>(`${BINANCE_BASE}/klines?symbol=${symbol}&interval=15m&limit=48`),
        fetchJson<TradeResp[]>(`${BINANCE_BASE}/trades?symbol=${symbol}&limit=10`),
      ]);
      if (klines) patch.spark = klines.map((k) => Number(k[4])).filter((v) => Number.isFinite(v));
      if (trades) {
        patch.tape = trades
          .filter((t) => t.price != null && t.qty != null)
          .map((t) => ({ price: Number(t.price), qty: Number(t.qty), time: t.time ?? Date.now(), buyerMaker: t.isBuyerMaker === true }));
      }
      this.patchAsset(id, patch);
      any = true;
    }
    if (!any) this.failures += 1;
    return any;
  }

  private async pollOkx(): Promise<boolean> {
    let any = false;
    for (const { id, instId } of OKX_SYMBOLS) {
      const q = this.snapshot.assets[id];
      if (q.status === "live" && q.source === "Binance") continue;
      const tick = await fetchJson<CandlesResp>(`${OKX_BASE}/market/ticker?instId=${instId}`);
      const last = tick?.data?.[0]?.last;
      if (!last) continue;
      const price = Number(last);
      const open = Number(tick?.data?.[0]?.open24h ?? "0");
      const patch: Partial<AssetQuote> = {
        price,
        change24h: open > 0 ? ((price - open) / open) * 100 : null,
        high24h: Number(tick?.data?.[0]?.high24h ?? "") || null,
        low24h: Number(tick?.data?.[0]?.low24h ?? "") || null,
        source: "OKX",
        status: "live",
        updatedAt: Date.now(),
      };
      const [candles, trades] = await Promise.all([
        fetchJson<{ data?: string[][] }>(`${OKX_BASE}/market/candles?instId=${instId}&bar=15m&limit=48`),
        fetchJson<OkxTradesResp>(`${OKX_BASE}/market/trades?instId=${instId}&limit=10`),
      ]);
      if (candles?.data) patch.spark = candles.data.map((row) => Number(row[4])).filter((v) => Number.isFinite(v)).reverse();
      if (trades?.data) {
        patch.tape = trades.data
          .filter((t) => t.px != null && t.sz != null)
          .map((t) => ({ price: Number(t.px), qty: Number(t.sz), time: Number(t.ts ?? Date.now()), buyerMaker: t.side === "sell" }));
      }
      this.patchAsset(id, patch);
      any = true;
    }
    return any;
  }

  private async pollCoinGecko(): Promise<boolean> {
    const ids = COINGECKO_IDS.map((s) => s.cg).join(",");
    const j = await fetchJson<Record<string, { usd?: number; usd_24h_change?: number }>>(
      `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true`,
    );
    if (!j) {
      this.failures += 1;
      return false;
    }
    for (const { id, cg } of COINGECKO_IDS) {
      const entry = j[cg];
      if (entry?.usd != null) {
        this.patchAsset(id, { price: entry.usd, change24h: entry.usd_24h_change ?? null, source: "CoinGecko", status: "live", updatedAt: Date.now() });
      }
    }
    return true;
  }

  /* ------------------------- gold spot (gold-api.com, keyless) ------------------------- */

  private async pollGold() {
    const j = await fetchJson<GoldResp>("https://api.gold-api.com/price/XAU");
    const price = j?.price;
    if (Number.isFinite(price) && price != null) {
      const paxg = this.snapshot.assets.PAXG;
      this.patchAsset("XAU", {
        price,
        change24h: paxg.status === "live" ? paxg.change24h : null,
        source: "gold-api.com",
        status: "live",
        updatedAt: Date.now(),
      });
    } else if (this.snapshot.assets.PAXG.status === "live") {
      // honest fallback: PAXG is a gold-backed token trading ≈ spot gold
      this.patchAsset("XAU", { price: this.snapshot.assets.PAXG.price, change24h: this.snapshot.assets.PAXG.change24h, source: "PAXG proxy", status: "live", updatedAt: Date.now() });
    } else {
      this.failures += 1;
    }
    this.markStale(REFRESH.gold, ["XAU"]);
    this.emit();
  }

  /* ------------------------- indices + oil (Yahoo via CORS mirror) ------------------------- */

  private async pollIndices() {
    for (const { id, sym } of YAHOO_SYMBOLS) {
      const target = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?interval=15m&range=1d`;
      const j = await fetchJson<YahooChart>(PROXY + encodeURIComponent(target), 12000);
      const res = j?.chart?.result?.[0];
      const price = res?.meta?.regularMarketPrice;
      if (Number.isFinite(price) && price != null) {
        const prev = res?.meta?.chartPreviousClose ?? null;
        const closes = (res?.indicators?.quote?.[0]?.close ?? []).filter((v): v is number => v != null && Number.isFinite(v));
        this.patchAsset(id, {
          price,
          change24h: prev && prev > 0 ? ((price - prev) / prev) * 100 : null,
          spark: closes.slice(-48),
          source: "Yahoo Finance",
          status: "live",
          updatedAt: Date.now(),
        });
      } else {
        this.failures += 1;
      }
      this.emit();
      await new Promise((r) => setTimeout(r, 2200)); // stay far below the mirror's rate limit
    }
    this.markStale(REFRESH.indices, YAHOO_SYMBOLS.map((s) => s.id));
    this.emit();
  }

  /* ------------------------- weather (Open-Meteo, Dezful) ------------------------- */

  private async pollWeather() {
    const url =
      "https://api.open-meteo.com/v1/forecast?latitude=32.3815&longitude=48.4095" +
      "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day" +
      "&daily=sunrise,sunset&timezone=Asia%2FTehran&forecast_days=1";
    const j = await fetchJson<OpenMeteo>(url);
    const cur = j?.current;
    if (cur?.temperature_2m != null) {
      this.snapshot.weather = {
        temperature: cur.temperature_2m,
        humidity: cur.relative_humidity_2m ?? null,
        wind: cur.wind_speed_10m ?? null,
        code: cur.weather_code ?? null,
        isDay: cur.is_day == null ? null : cur.is_day === 1,
        sunrise: j?.daily?.sunrise?.[0] ?? null,
        sunset: j?.daily?.sunset?.[0] ?? null,
        source: "Open-Meteo",
        status: "live",
        updatedAt: Date.now(),
      };
    } else {
      this.failures += 1;
      if (this.snapshot.weather.status === "live" && this.snapshot.weather.updatedAt !== null && Date.now() - this.snapshot.weather.updatedAt > REFRESH.weather * 2.5) {
        this.snapshot.weather = { ...this.snapshot.weather, status: "stale" };
      }
    }
    this.emit();
  }

  /* ------------------------- news headlines (BBC Persian RSS via mirror) ------------------------- */

  private async pollNews() {
    const target = "https://feeds.bbci.co.uk/persian/rss.xml";
    const xml = await fetchText(PROXY + encodeURIComponent(target), 12000);
    if (!xml) {
      this.failures += 1;
      return;
    }
    try {
      const doc = new DOMParser().parseFromString(xml, "text/xml");
      const items = Array.from(doc.querySelectorAll("item > title"))
        .map((el) => (el.textContent ?? "").trim())
        .filter((t) => t.length > 0)
        .slice(0, 8)
        .map((title) => ({ title }));
      if (items.length > 0) {
        this.snapshot.news = { items, source: "BBC Persian", status: "live", updatedAt: Date.now() };
      }
    } catch {
      this.failures += 1;
    }
    this.emit();
  }
}

let singleton: MarketBus | null = null;

export function getMarketBus(): MarketBus {
  if (!singleton) singleton = new MarketBus();
  return singleton;
}
