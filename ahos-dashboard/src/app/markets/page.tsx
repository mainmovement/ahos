import type { Metadata } from "next";
import { getMarketBoard } from "@/lib/api/markets";
import { MarketsView } from "@/components/views/markets-view";

export const metadata: Metadata = { title: "قیمت‌های بازار · Market Prices" };

export default async function MarketsPage({ searchParams }: { searchParams: Promise<{ symbol?: string }> }) {
  const [{ symbol }, board] = await Promise.all([searchParams, getMarketBoard()]);
  // Only the initially selected instrument's candles are serialized; others load on demand via getCandles().
  const initial = symbol && board.data.instruments.some((i) => i.id === symbol && i.price !== null) ? symbol : "btc";
  const slim = { ...board, data: { ...board.data, candles: { [initial]: board.data.candles[initial] ?? [] } } };
  return <MarketsView board={slim} initialSymbol={initial} />;
}
