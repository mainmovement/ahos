/** MOCK — crypto market board. */
import type { CryptoBoard } from "@/lib/api/types";
import { DAY, L, series } from "./_seed";
import { mockCandles, mockInstruments } from "./markets";

export function mockCrypto(now = Date.now()): CryptoBoard {
  const assets = mockInstruments(now).filter((i) => i.assetClass === "crypto");
  return {
    totalMarketCap: 3.94e12,
    totalMarketCapChange: 2.86,
    btcDominance: 57.4,
    volume24h: 142.6e9,
    fearGreed: { value: 64, label: L("طمع", "Greed") },
    assets,
    sectors: [
      { id: "l1", name: L("لایه ۱", "Layer 1"), change: 3.4, weight: 0.42 },
      { id: "defi", name: L("دیفای", "DeFi"), change: 4.8, weight: 0.12 },
      { id: "l2", name: L("لایه ۲", "Layer 2"), change: -0.9, weight: 0.06 },
      { id: "ai", name: L("هوش مصنوعی", "AI tokens"), change: 7.2, weight: 0.05 },
      { id: "meme", name: L("میم", "Memes"), change: 9.6, weight: 0.07 },
      { id: "rwa", name: L("دارایی واقعی (RWA)", "RWA"), change: 1.3, weight: 0.04 },
      { id: "game", name: L("گیمینگ", "Gaming"), change: -2.7, weight: 0.03 },
      { id: "stable", name: L("استیبل‌کوین", "Stablecoins"), change: 0.01, weight: 0.21 },
    ],
    funding: [
      { symbol: "BTC", rate: 0.0081, openInterest: 38.4e9 },
      { symbol: "ETH", rate: 0.0112, openInterest: 21.7e9 },
      { symbol: "SOL", rate: 0.0215, openInterest: 6.2e9 },
      { symbol: "DOGE", rate: 0.0304, openInterest: 2.1e9 },
      { symbol: "XRP", rate: -0.0042, openInterest: 3.9e9 },
      { symbol: "TON", rate: null, openInterest: null },
    ],
    stablecoins: [
      { symbol: "USDT", supply: 182.4e9, change7d: 0.62 },
      { symbol: "USDC", supply: 76.1e9, change7d: 1.14 },
      { symbol: "USDe", supply: 13.2e9, change7d: -2.4 },
      { symbol: "DAI", supply: 5.3e9, change7d: -0.3 },
    ],
    candles: mockCandles("btc", "1D", 140, now),
    dominance: [
      { id: "btc", label: L("بیت‌کوین", "BTC"), points: series("dom:btc", 90, 57.4, DAY, 0.004, 0, now, 2) },
      { id: "eth", label: L("اتریوم", "ETH"), points: series("dom:eth", 90, 13.4, DAY, 0.01, 0, now, 2) },
    ],
  };
}
