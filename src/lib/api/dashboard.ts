import {
  answers,
  dashboard,
  markets,
  fixtureCandles,
  provenance,
} from "../../mock/dashboard";
import type {
  Candle,
  DashboardSnapshot,
  DemoAnswer,
  MarketAsset,
  Provenance,
} from "./types";

// Replace this boundary with validated backend reads. Components never import fixtures.
export function getDashboardSnapshot(): DashboardSnapshot {
  return structuredClone(dashboard);
}
export function getMarkets(category?: MarketAsset["category"]): MarketAsset[] {
  return structuredClone(
    category ? markets.filter((asset) => asset.category === category) : markets,
  );
}
export function getMarketCandles(symbol: string): Candle[] {
  return fixtureCandles(symbol);
}
export function getDemoProvenance(): Provenance {
  return { ...provenance };
}
export function getDemoAnswer(question: string): DemoAnswer {
  const key = /risk|ریسک|امنیت|خطر/i.test(question)
    ? "risk"
    : /market|price|بازار|قیمت/i.test(question)
      ? "market"
      : /agent|عامل/i.test(question)
        ? "agents"
        : "default";
  return structuredClone(answers[key]);
}
