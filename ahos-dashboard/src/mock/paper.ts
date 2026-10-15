/** MOCK — paper-trading account. PAPER ONLY: no real funds, no wallets. */
import type { PaperAccount, PortfolioOverview } from "@/lib/api/types";
import { DAY, HOUR, L, minutesAgo, round, series } from "./_seed";

export function mockPaperAccount(now = Date.now()): PaperAccount {
  const start = 100_000;
  const curve = series("paper:equity", 90, 112_384.6, DAY, 0.006, 0.0012, now, 2);
  return {
    mode: "PAPER_ONLY",
    equity: 112_384.6,
    startingEquity: start,
    cash: 61_920.4,
    pnlDay: 2_644.1,
    pnlDayPct: 2.41,
    pnlTotal: 12_384.6,
    pnlTotalPct: 12.38,
    winRate: 0.62,
    tradeCount: 126,
    maxDrawdownPct: -6.8,
    sharpe: 1.42,
    equityCurve: curve,
    positions: [
      { id: "pp1", symbol: "SOL", side: "LONG", qty: 85, entry: 198.6, mark: 212.4, pnl: round(85 * (212.4 - 198.6), 2), pnlPct: round((212.4 / 198.6 - 1) * 100, 2), stop: 186, target: 236, openedAt: minutesAgo(60 * 30, now), strategy: L("روند + شواهد چندمنبعی", "Trend + multi-source evidence"), status: "DEMO" },
      { id: "pp2", symbol: "ETH", side: "LONG", qty: 4.2, entry: 4210.5, mark: 4382.6, pnl: round(4.2 * (4382.6 - 4210.5), 2), pnlPct: round((4382.6 / 4210.5 - 1) * 100, 2), stop: 4020, target: 4700, openedAt: minutesAgo(60 * 52, now), strategy: L("بازگشت به میانگین", "Mean reversion"), status: "DEMO" },
      { id: "pp3", symbol: "AEROX", side: "LONG", qty: 6200, entry: 1.094, mark: 1.062, pnl: round(6200 * (1.062 - 1.094), 2), pnlPct: round((1.062 / 1.094 - 1) * 100, 2), stop: 0.98, target: 1.28, openedAt: minutesAgo(60 * 6, now), strategy: L("نامزد کاغذی (مرجع کانونی)", "Paper candidate (canonical)"), status: "DEMO" },
      { id: "pp4", symbol: "XAU", side: "LONG", qty: 2, entry: 4122.0, mark: 4186.4, pnl: round(2 * (4186.4 - 4122), 2), pnlPct: round((4186.4 / 4122 - 1) * 100, 2), stop: 4040, target: 4320, openedAt: minutesAgo(60 * 80, now), strategy: L("پوشش ریسک کلان", "Macro hedge"), status: "DEMO" },
      { id: "pp5", symbol: "BRENT", side: "SHORT", qty: 120, entry: 69.4, mark: null, pnl: null, pnlPct: null, stop: 71.2, target: 64.5, openedAt: minutesAgo(60 * 3, now), strategy: L("اسپرد انرژی", "Energy spread"), status: "STALE" },
    ],
    fills: [
      { id: "f1", symbol: "SOL", side: "LONG", kind: "CLOSE", qty: 40, price: 206.2, pnl: 248.0, at: minutesAgo(42, now), reason: L("رسیدن به هدف جزئی", "Partial target reached") },
      { id: "f2", symbol: "AEROX", side: "LONG", kind: "OPEN", qty: 6200, price: 1.094, pnl: null, at: minutesAgo(360, now), reason: L("مجوز paper_allowed از مرجع کانونی", "paper_allowed from canonical authority") },
      { id: "f3", symbol: "BRENT", side: "SHORT", kind: "OPEN", qty: 120, price: 69.4, pnl: null, at: minutesAgo(180, now), reason: L("اسپرد برنت-دبی", "Brent–Dubai spread") },
      { id: "f4", symbol: "LINK", side: "LONG", kind: "CLOSE", qty: 300, price: 21.9, pnl: -96.0, at: minutesAgo(60 * 9, now), reason: L("فعال شدن حد ضرر", "Stop triggered") },
      { id: "f5", symbol: "BTC", side: "LONG", kind: "CLOSE", qty: 0.4, price: 111_900, pnl: 1_120.0, at: minutesAgo(60 * 20, now), reason: L("خروج زمانی", "Time-based exit") },
    ],
    limits: [
      { id: "l1", label: L("حداکثر اندازه هر موقعیت", "Max position size"), used: 15.9, limit: 20, unit: "pct", state: "ok" },
      { id: "l2", label: L("سقف زیان روزانه", "Daily loss limit"), used: 0, limit: 3, unit: "pct", state: "ok" },
      { id: "l3", label: L("مجموع اکسپوژر", "Gross exposure"), used: 44.9, limit: 60, unit: "pct", state: "ok" },
      { id: "l4", label: L("موقعیت‌های هم‌زمان", "Concurrent positions"), used: 5, limit: 6, unit: "count", state: "warn" },
      { id: "l5", label: L("تمرکز در یک زنجیره", "Single-chain concentration"), used: 38.2, limit: 40, unit: "pct", state: "warn" },
    ],
  };
}

export function mockPortfolio(now = Date.now()): PortfolioOverview {
  return {
    totalValue: 112_384.6,
    changePct: 2.41,
    allocation: [
      { id: "cash", label: L("نقد (کاغذی)", "Cash (paper)"), value: 61_920.4 },
      { id: "crypto", label: L("رمزارز", "Crypto"), value: 36_960.3 },
      { id: "metals", label: L("فلزات", "Metals"), value: 8_372.8 },
      { id: "energy", label: L("انرژی", "Energy"), value: 5_131.1 },
    ],
    holdings: [
      { symbol: "SOL", name: L("سولانا", "Solana"), assetClass: "crypto", value: 18_054, weight: 0.161, changePct: 6.12, pnl: 1_173 },
      { symbol: "ETH", name: L("اتریوم", "Ethereum"), assetClass: "crypto", value: 18_406.9, weight: 0.164, changePct: 3.84, pnl: 722.8 },
      { symbol: "AEROX", name: L("ایروایکس (نمایشی)", "AeroX (demo)"), assetClass: "crypto", value: 6_584.4, weight: 0.059, changePct: 3.18, pnl: -198.4 },
      { symbol: "XAU", name: L("طلا", "Gold"), assetClass: "commodity", value: 8_372.8, weight: 0.075, changePct: 0.74, pnl: 128.8 },
      { symbol: "BRENT", name: L("برنت", "Brent"), assetClass: "commodity", value: 5_131.1, weight: 0.046, changePct: null, pnl: null },
    ],
    performance: [
      { id: "portfolio", label: L("سبد کاغذی", "Paper portfolio"), points: series("pf:perf", 90, 112.38, DAY, 0.006, 0.0012, now, 2) },
      { id: "btc", label: L("بیت‌کوین", "Bitcoin"), points: series("pf:btc", 90, 109.1, DAY, 0.012, 0.0009, now, 2) },
      { id: "spx", label: L("اس‌اند‌پی ۵۰۰", "S&P 500"), points: series("pf:spx", 90, 104.6, DAY, 0.005, 0.0005, now, 2) },
    ],
    exposure: [
      { label: L("سولانا", "Solana"), pct: 22 },
      { label: L("اتریوم و لایه ۲", "Ethereum & L2"), pct: 22.3 },
      { label: L("کالاها", "Commodities"), pct: 12.1 },
      { label: L("نقد", "Cash"), pct: 43.6 },
    ],
    risk: { var95Pct: -2.9, volatilityPct: 18.4, sharpe: 1.42, beta: 0.64, maxDrawdownPct: -6.8 },
  };
}

/** Intraday equity used by the Command Center sparkline. */
export function mockPaperIntraday(now = Date.now()) {
  return series("paper:intraday", 48, 112_384.6, HOUR / 2, 0.0018, 0.0004, now, 2);
}
