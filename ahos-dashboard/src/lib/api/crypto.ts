import type { CryptoBoard, DataEnvelope } from "./types";
import { fromMock, label } from "./_envelope";
import { mockCrypto } from "@/mock/crypto";

/** Crypto market board. Real source: CoinGecko global, Binance public futures, DefiLlama stablecoins, Alternative.me. */
export async function getCrypto(): Promise<DataEnvelope<CryptoBoard>> {
  return fromMock(mockCrypto(), "crypto", label("بازار رمزارز نمایشی", "Demo crypto market"), 20, 120);
}
