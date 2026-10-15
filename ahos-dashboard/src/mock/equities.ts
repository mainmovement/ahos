/** MOCK — regional equities boards (US / EU / Asia). */
import type { EquitiesBoard, EquityRegion, Mover, SectorPerf } from "@/lib/api/types";
import { DAY, L, rng, round, series } from "./_seed";
import { mockInstrument } from "./markets";

const SECTORS = [
  { id: "tech", name: L("فناوری", "Technology"), w: 0.3 },
  { id: "fin", name: L("مالی", "Financials"), w: 0.13 },
  { id: "health", name: L("سلامت", "Health care"), w: 0.11 },
  { id: "cons", name: L("کالاهای مصرفی", "Consumer disc."), w: 0.1 },
  { id: "comm", name: L("ارتباطات", "Communication"), w: 0.09 },
  { id: "ind", name: L("صنعتی", "Industrials"), w: 0.08 },
  { id: "energy", name: L("انرژی", "Energy"), w: 0.05 },
  { id: "staples", name: L("کالاهای اساسی", "Staples"), w: 0.05 },
  { id: "util", name: L("خدمات عمومی", "Utilities"), w: 0.03 },
  { id: "mat", name: L("مواد", "Materials"), w: 0.03 },
  { id: "re", name: L("املاک", "Real estate"), w: 0.03 },
];

const REGION_CFG: Record<
  EquityRegion,
  { indices: string[]; exchanges: string[]; movers: [string, string, number, string][]; bias: number }
> = {
  us: {
    indices: ["spx", "ndx", "dji", "rut"],
    exchanges: ["nyse"],
    bias: 0.35,
    movers: [
      ["NVDA", "NVIDIA", 192.4, "tech"],
      ["AAPL", "Apple", 254.1, "tech"],
      ["MSFT", "Microsoft", 521.7, "tech"],
      ["AMZN", "Amazon", 231.9, "cons"],
      ["JPM", "JPMorgan", 309.2, "fin"],
      ["XOM", "Exxon Mobil", 118.6, "energy"],
      ["LLY", "Eli Lilly", 812.3, "health"],
      ["TSLA", "Tesla", 438.5, "cons"],
      ["META", "Meta", 742.8, "comm"],
      ["CAT", "Caterpillar", 486.4, "ind"],
    ],
  },
  eu: {
    indices: ["sx5e", "dax", "cac", "ukx"],
    exchanges: ["xetra", "lse"],
    bias: -0.05,
    movers: [
      ["ASML", "ASML", 842.5, "tech"],
      ["SAP", "SAP", 238.2, "tech"],
      ["MC", "LVMH", 548.9, "cons"],
      ["NOVO-B", "Novo Nordisk", 362.4, "health"],
      ["SHEL", "Shell", 28.7, "energy"],
      ["SIE", "Siemens", 241.3, "ind"],
      ["HSBA", "HSBC", 10.42, "fin"],
      ["AIR", "Airbus", 205.8, "ind"],
      ["TTE", "TotalEnergies", 55.4, "energy"],
      ["ALV", "Allianz", 362.1, "fin"],
    ],
  },
  asia: {
    indices: ["nky", "hsi", "shcomp", "kospi", "nifty", "tedpix"],
    exchanges: ["tse-jp", "hkex", "tse-ir"],
    bias: 0.2,
    movers: [
      ["7203", "Toyota", 2884, "cons"],
      ["2330", "TSMC", 1385, "tech"],
      ["005930", "Samsung", 92400, "tech"],
      ["0700", "Tencent", 642.5, "comm"],
      ["RELIANCE", "Reliance", 1412.6, "energy"],
      ["9984", "SoftBank", 18420, "comm"],
      ["FOLAD", "فولاد مبارکه", 642, "mat"],
      ["KHODRO", "ایران‌خودرو", 2810, "cons"],
      ["SHASTA", "شستا", 1104, "fin"],
      ["FAMELI", "ملی مس", 768, "mat"],
    ],
  },
};

export function mockEquities(region: EquityRegion, now = Date.now()): EquitiesBoard {
  const cfg = REGION_CFG[region];
  const r = rng(`eq:${region}`);
  const indices = cfg.indices.map((id) => mockInstrument(id, now)).filter((x): x is NonNullable<typeof x> => Boolean(x));
  const sectors: SectorPerf[] = SECTORS.map((s) => ({
    id: s.id,
    name: s.name,
    change: round(cfg.bias + (r() - 0.48) * 3.2, 2),
    weight: s.w,
  }));
  const sectorName = (id: string) => SECTORS.find((s) => s.id === id)?.name ?? L("سایر", "Other");
  const movers: Mover[] = cfg.movers.map(([symbol, name, price, sector]) => ({
    symbol,
    name,
    price,
    change: round((r() - 0.45) * 7.5, 2),
    volume: Math.round((0.5 + r() * 4) * 1e6),
    sector: sectorName(sector),
  }));
  const sorted = [...movers].sort((a, b) => (b.change ?? 0) - (a.change ?? 0));
  const performance = indices
    .filter((i) => i.price !== null)
    .slice(0, 4)
    .map((i) => ({
      id: i.id,
      label: i.name,
      points: series(`eqperf:${i.id}`, 120, 100 + (i.change24h ?? 0) * 3, DAY, 0.009, 0.0005, now, 2),
    }));
  return {
    region,
    indices,
    sectors,
    gainers: sorted.slice(0, 5),
    losers: sorted.slice(-5).reverse(),
    breadth: region === "asia" ? { advancers: 1184, decliners: 1306, unchanged: 212 } : region === "eu" ? { advancers: 288, decliners: 301, unchanged: 11 } : { advancers: 312, decliners: 181, unchanged: 7 },
    performance,
    exchanges: cfg.exchanges,
  };
}
