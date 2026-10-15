/** MOCK — oil and gold boards. */
import type { GoldBoard, Instrument, OilBoard } from "@/lib/api/types";
import { DAY, L, rng, round, series } from "./_seed";
import { bridge, mockCandles, mockInstrument } from "./markets";

function derived(
  id: string,
  symbol: string,
  name: { fa: string; en: string },
  price: number | null,
  chg: number | null,
  quote: string,
  decimals: number,
  status: Instrument["status"],
  ageSec: number,
  now: number,
): Instrument {
  const pts = price === null ? [] : bridge(`d:${id}`, 36, price / (1 + (chg ?? 0) / 100), price, 0.005).map((v) => round(v, decimals + 2));
  return {
    id,
    symbol,
    name,
    assetClass: "commodity",
    price,
    change24h: chg,
    high24h: pts.length ? round(Math.max(...pts), decimals) : null,
    low24h: pts.length ? round(Math.min(...pts), decimals) : null,
    volume24h: null,
    quote,
    decimals,
    status,
    retrievedAt: status === "UNKNOWN" ? null : new Date(now - ageSec * 1000).toISOString(),
    source: "mock/commodities",
    spark: pts,
  };
}

export function mockOil(now = Date.now()): OilBoard {
  const brent = mockInstrument("brent", now)!;
  const wti = mockInstrument("wti", now)!;
  const iranHeavy = mockInstrument("iranheavy", now)!;
  const r = rng("oil");
  const weeks = ["W-7", "W-6", "W-5", "W-4", "W-3", "W-2", "W-1", "W0"];
  return {
    benchmarks: [
      brent,
      wti,
      derived("dubai", "DUBAI", L("دبی / عمان", "Dubai / Oman"), 67.88, 1.02, "USD/bbl", 2, "DEMO", 120, now),
      derived("murban", "MURBAN", L("مربان", "Murban"), 69.31, 0.94, "USD/bbl", 2, "DEMO", 160, now),
      derived("orb", "OPEC-B", L("سبد اوپک", "OPEC basket"), 68.07, 0.88, "USD/bbl", 2, "STALE", 26 * 3600, now),
      iranHeavy,
    ],
    candles: mockCandles("brent", "1D", 140, now),
    spread: series("oil:spread", 120, 3.47, DAY, 0.035, 0, now, 2),
    inventories: weeks.map((week) => ({ week, change: round((r() - 0.55) * 7, 2) })),
    opec: [
      { country: L("عربستان سعودی", "Saudi Arabia"), quota: 9978, actual: 9865 },
      { country: L("عراق", "Iraq"), quota: 4273, actual: 4410 },
      { country: L("امارات", "UAE"), quota: 3375, actual: 3402 },
      { country: L("کویت", "Kuwait"), quota: 2580, actual: 2552 },
      { country: L("ایران (معاف)", "Iran (exempt)"), quota: null, actual: 3290 },
      { country: L("روسیه (اوپک+)", "Russia (OPEC+)"), quota: 9532, actual: 9410 },
      { country: L("قزاقستان (اوپک+)", "Kazakhstan (OPEC+)"), quota: 1557, actual: 1810 },
    ],
    drivers: [
      { id: "d1", title: L("تمدید سیاست عرضه اوپک+", "OPEC+ supply policy extension"), direction: "up", confidence: "MED" },
      { id: "d2", title: L("افزایش ذخایر تجاری آمریکا", "US commercial inventory build"), direction: "down", confidence: "LOW" },
      { id: "d3", title: L("ریسک ژئوپلیتیک تنگه هرمز", "Strait of Hormuz geopolitical risk"), direction: "mixed", confidence: "UNKNOWN" },
      { id: "d4", title: L("تقاضای پالایشگاه‌های آسیا", "Asian refinery demand"), direction: "up", confidence: "LOW" },
    ],
  };
}

export function mockGold(now = Date.now()): GoldBoard {
  const xau = mockInstrument("xau", now)!;
  const xag = mockInstrument("xag", now)!;
  const ratio = derived("gsr", "XAU/XAG", L("نسبت طلا به نقره", "Gold/Silver ratio"), round(4186.4 / 48.75, 2), -1.16, "x", 2, "DEMO", 60, now);
  const plat = derived("xpt", "XPT/USD", L("پلاتین", "Platinum"), 1582.6, 0.42, "USD/oz", 1, "DEMO", 90, now);
  const emami = mockInstrument("emami", now)!;
  const gold18 = mockInstrument("gold18", now)!;
  const iranItem = (id: string, symbol: string, fa: string, en: string, price: number, chg: number) => ({
    ...derived(id, symbol, L(fa, en), price, chg, "IRT", 0, "STALE", 3 * 3600, now),
    assetClass: "iran" as const,
  });
  const r = rng("gold");
  return {
    spot: [xau, xag, plat, ratio],
    iran: [
      emami,
      iranItem("bahar", "BAHAR", "سکه بهار آزادی", "Bahar Azadi coin", 109200000, 0.44),
      iranItem("half", "NIM", "نیم‌سکه", "Half coin", 61800000, 0.31),
      iranItem("quarter", "ROB", "ربع‌سکه", "Quarter coin", 35600000, 0.12),
      gold18,
      iranItem("mesghal", "MESGHAL", "مثقال طلا", "Gold mesghal", 48700000, 0.58),
    ],
    candles: mockCandles("xau", "1D", 140, now),
    coinPremium: series("gold:premium", 90, 7.8, DAY, 0.05, 0, now, 2),
    centralBanks: [
      { country: L("لهستان", "Poland"), tonnes: 67.2 },
      { country: L("چین", "China"), tonnes: 34.6 },
      { country: L("ترکیه", "Türkiye"), tonnes: 27.1 },
      { country: L("هند", "India"), tonnes: 21.8 },
      { country: L("قزاقستان", "Kazakhstan"), tonnes: 18.4 },
      { country: L("ایران", "Iran"), tonnes: null },
    ],
    etfFlows: ["W-7", "W-6", "W-5", "W-4", "W-3", "W-2", "W-1", "W0"].map((week) => ({ week, tonnes: round((r() - 0.35) * 28, 1) })),
    drivers: [
      { id: "g1", title: L("انتظار کاهش نرخ بهره فدرال رزرو", "Fed rate-cut expectations"), direction: "up", confidence: "MED" },
      { id: "g2", title: L("خرید بانک‌های مرکزی", "Central-bank purchases"), direction: "up", confidence: "MED" },
      { id: "g3", title: L("تقویت شاخص دلار", "Dollar index strength"), direction: "down", confidence: "LOW" },
      { id: "g4", title: L("حباب سکه در بازار داخلی", "Domestic coin premium"), direction: "mixed", confidence: "UNKNOWN" },
    ],
  };
}
