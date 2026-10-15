import type { DataEnvelope, PaperAccount, PortfolioOverview, SeriesPoint } from "./types";
import { fromMock, label } from "./_envelope";
import { mockPaperAccount, mockPaperIntraday, mockPortfolio } from "@/mock/paper";

/** Paper account. Real source: `paper_trading/` ledger (Lane A, read-only). */
export async function getPaperAccount(): Promise<DataEnvelope<PaperAccount>> {
  return fromMock(mockPaperAccount(), "paper", label("حساب کاغذی نمایشی", "Demo paper account"), 20, 120);
}

export async function getPaperIntraday(): Promise<DataEnvelope<SeriesPoint[]>> {
  return fromMock(mockPaperIntraday(), "paper-intraday", label("ارزش درون‌روزی نمایشی", "Demo intraday equity"), 20, 120);
}

/** Portfolio. Real source: paper ledger + valuation service. */
export async function getPortfolio(): Promise<DataEnvelope<PortfolioOverview>> {
  return fromMock(mockPortfolio(), "portfolio", label("سبد نمایشی", "Demo portfolio"), 20, 120);
}
