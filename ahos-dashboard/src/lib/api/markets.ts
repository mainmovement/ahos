import type { Candle, DataEnvelope, Instrument, MarketBoard } from "./types";
import { fromMock, label } from "./_envelope";
import { mockCandles, mockInstrument, mockInstruments, type Timeframe } from "@/mock/markets";

export type { Timeframe };

const CANDLE_IDS = ["btc", "eth", "sol", "xau", "brent", "spx", "eurusd", "dax", "nky", "usdirt"];

/** Cross-asset price board. Real source: Binance public, CoinGecko, exchange feeds. */
export async function getMarketBoard(): Promise<DataEnvelope<MarketBoard>> {
  const now = Date.now();
  const instruments = mockInstruments(now);
  const candles: Record<string, Candle[]> = {};
  for (const id of CANDLE_IDS) candles[id] = mockCandles(id, "1D", 140, now);
  return fromMock({ instruments, candles }, "markets", label("قیمت‌های نمایشی چنددارایی", "Multi-asset demo prices"), 18, 60);
}

/** OHLCV history for one instrument (client-callable). */
export async function getCandles(id: string, timeframe: Timeframe = "1D"): Promise<DataEnvelope<Candle[]>> {
  return fromMock(mockCandles(id, timeframe, 140), "candles", label("تاریخچه قیمت نمایشی", "Demo price history"), 18, 60);
}

export async function getInstrument(id: string): Promise<DataEnvelope<Instrument | null>> {
  return fromMock(mockInstrument(id) ?? null, "markets", label("قیمت نمایشی", "Demo price"), 18, 60);
}
