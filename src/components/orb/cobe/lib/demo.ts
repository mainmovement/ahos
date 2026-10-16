/**
 * Deterministic DEMO dataset for the AHOS globe demo page.
 *
 * Everything here is invented on purpose and labelled DEMO or (for the demo scenario) authored by
 * hand. Timestamps are derived from a caller-supplied clock so screenshots and tests are stable,
 * and no value is ever presented as live market data. The page shows a permanent "DEMO DATA" badge.
 */

import nodesJson from "./market-nodes.json";
import type {
  Department,
  Freshness,
  Gate,
  GlobeQuality,
  Health,
  Lang,
  MarketNode,
  Signal,
} from "../types/globe";

type NodeSeed = {
  id: string;
  nameFa: string;
  nameEn: string;
  lat: number;
  lng: number;
  /** Scenario-independent DEMO state. */
  freshness: Freshness;
  changePct: number | null;
  minutesAgo: number | null;
  attention: boolean;
};

type RawNode = (typeof nodesJson)[number];

const SEEDS: Record<string, Omit<NodeSeed, "id" | "nameFa" | "nameEn" | "lat" | "lng">> = {
  tehran: { freshness: "LIVE", changePct: 0.42, minutesAgo: 1, attention: true },
  newyork: { freshness: "LIVE", changePct: -0.31, minutesAgo: 2, attention: false },
  london: { freshness: "LIVE", changePct: 0.18, minutesAgo: 2, attention: false },
  frankfurt: { freshness: "LIVE", changePct: 0.07, minutesAgo: 3, attention: false },
  dubai: { freshness: "LIVE", changePct: 0.63, minutesAgo: 1, attention: false },
  mumbai: { freshness: "LIVE", changePct: -0.12, minutesAgo: 4, attention: false },
  singapore: { freshness: "DEMO", changePct: 0.21, minutesAgo: 5, attention: false },
  hongkong: { freshness: "LIVE", changePct: 1.94, minutesAgo: 2, attention: true },
  tokyo: { freshness: "LIVE", changePct: 0.44, minutesAgo: 2, attention: false },
  sydney: { freshness: "LIVE", changePct: -0.05, minutesAgo: 6, attention: false },
  saopaulo: { freshness: "UNKNOWN", changePct: null, minutesAgo: null, attention: false },
  johannesburg: { freshness: "STALE", changePct: 0.02, minutesAgo: 47, attention: false },
  moscow: { freshness: "STALE", changePct: -1.12, minutesAgo: 26, attention: true },
  riyadh: { freshness: "LIVE", changePct: 0.29, minutesAgo: 1, attention: false },
};

export const DEMO_NODES: readonly RawNode[] = nodesJson;

export const DEMO_DEPARTMENTS: readonly Department[] = [
  { id: "market-analysis", nameFa: "تحلیل بازار", freshness: "LIVE", needsAttention: false },
  { id: "opportunity-radar", nameFa: "رادار فرصت", freshness: "LIVE", needsAttention: false },
  { id: "risk", nameFa: "مدیریت ریسک", freshness: "LIVE", needsAttention: true },
  { id: "gate", nameFa: "دروازه‌ی سیگنال", freshness: "LIVE", needsAttention: true },
  { id: "news", nameFa: "هوش خبری", freshness: "STALE", needsAttention: true },
  { id: "liquidity", nameFa: "پایش نقدینگی", freshness: "LIVE", needsAttention: false },
  { id: "correlation", nameFa: "همبستگی دارایی‌ها", freshness: "DEMO", needsAttention: false },
  { id: "counterparty", nameFa: "ریسک طرف مقابل", freshness: "LIVE", needsAttention: false },
  { id: "paper-execution", nameFa: "اجرای کاغذی", freshness: "LIVE", needsAttention: false },
  { id: "compliance", nameFa: "انطباق و قواعد", freshness: "LIVE", needsAttention: false },
  { id: "data-infra", nameFa: "زیرساخت داده", freshness: "LIVE", needsAttention: false },
  { id: "system-health", nameFa: "سلامت سیستم", freshness: "LIVE", needsAttention: false },
];

type SignalSeed = {
  id: string;
  from: string;
  to: string;
  outcome: Signal["outcome"];
  reasonFa?: string;
  minutesAgo: number;
};

const SIGNAL_SEEDS: readonly SignalSeed[] = [
  {
    id: "sig-dubai-tehran",
    from: "dubai",
    to: "tehran",
    outcome: "absorbed",
    reasonFa: "همبستگی نفت و شاخص تهران بالای آستانه",
    minutesAgo: 2,
  },
  { id: "sig-moscow-frankfurt", from: "moscow", to: "frankfurt", outcome: "dissipated", reasonFa: "نقدینگی اروپا ضعیف", minutesAgo: 21 },
  { id: "sig-hongkong-tokyo", from: "hongkong", to: "tokyo", outcome: "absorbed", reasonFa: "جریان خرید آسیا", minutesAgo: 4 },
  { id: "sig-singapore-hongkong", from: "singapore", to: "hongkong", outcome: "absorbed", minutesAgo: 7 },
  { id: "sig-newyork-london", from: "newyork", to: "london", outcome: "pending", reasonFa: "در انتظار باز شدن بازار آتی", minutesAgo: 3 },
  { id: "sig-london-frankfurt", from: "london", to: "frankfurt", outcome: "absorbed", minutesAgo: 9 },
  { id: "sig-mumbai-dubai", from: "mumbai", to: "dubai", outcome: "dissipated", reasonFa: "دروازه سخت‌گیر شد", minutesAgo: 12 },
  { id: "sig-saopaulo-johannesburg", from: "saopaulo", to: "johannesburg", outcome: "pending", reasonFa: "داده‌ی سائوپائولو نامشخص است", minutesAgo: 6 },
  { id: "sig-tokyo-sydney", from: "tokyo", to: "sydney", outcome: "dissipated", reasonFa: "سیگنال پیش از دروازه تحلیل رفت", minutesAgo: 15 },
  { id: "sig-riyadh-dubai", from: "riyadh", to: "dubai", outcome: "absorbed", reasonFa: "همبستگی منطقه‌ای", minutesAgo: 5 },
];

export type DemoScenario = {
  calm: boolean;
  staleFeed: boolean;
  jitter: boolean;
  gateBurst: boolean;
  allClear: boolean;
  mapMode: boolean;
  quality: GlobeQuality;
  lang: Lang;
};

export const DEFAULT_SCENARIO: DemoScenario = {
  calm: true,
  staleFeed: false,
  jitter: false,
  gateBurst: false,
  allClear: false,
  mapMode: false,
  quality: "medium",
  lang: "fa",
};

export type DemoData = {
  markets: MarketNode[];
  signals: Signal[];
  gate: Gate;
  health: Health;
  departments: Department[];
};

/** Builds the demo dataset for a scenario, relative to a reference clock (`nowMs`). */
export function buildDemoData(scenario: DemoScenario, nowMs: number): DemoData {
  const iso = (minutesAgo: number | null) =>
    minutesAgo === null ? null : new Date(nowMs - minutesAgo * 60_000).toISOString();

  const markets: MarketNode[] = DEMO_NODES.filter((node) => !("probe" in node && node.probe)).map((node) => {
    const seed = SEEDS[node.id] ?? {
      freshness: "UNKNOWN" as Freshness,
      changePct: null,
      minutesAgo: null,
      attention: false,
    };
    if (scenario.allClear) {
      return {
        id: node.id,
        nameFa: node.nameFa,
        nameEn: node.nameEn,
        lat: node.lat,
        lng: node.lng,
        freshness: "LIVE",
        asOf: iso(2),
        changePct: seed.changePct ?? 0,
        needsAttention: false,
      };
    }
    if (scenario.staleFeed) {
      return {
        id: node.id,
        nameFa: node.nameFa,
        nameEn: node.nameEn,
        lat: node.lat,
        lng: node.lng,
        freshness: "STALE",
        asOf: iso(Math.max(45, (seed.minutesAgo ?? 10) + 45)),
        changePct: seed.changePct,
        needsAttention: seed.attention || node.id === "london" || node.id === "mumbai",
      };
    }
    return {
      id: node.id,
      nameFa: node.nameFa,
      nameEn: node.nameEn,
      lat: node.lat,
      lng: node.lng,
      freshness: seed.freshness,
      asOf: iso(seed.minutesAgo),
      changePct: seed.changePct,
      needsAttention: seed.attention,
    };
  });

  const gate: Gate = scenario.allClear
    ? { absorbed: 74, dissipated: 9, strictness: 0.35 }
    : scenario.gateBurst
      ? { absorbed: 44, dissipated: 63 }
      : scenario.staleFeed
        ? { absorbed: 0, dissipated: 0 }
        : { absorbed: 62, dissipated: 17 };

  const health: Health = scenario.staleFeed
    ? { bpm: 0, jitterMs: 0, stale: true }
    : scenario.jitter
      ? { bpm: 96, jitterMs: 320, stale: false }
      : { bpm: 62, jitterMs: 40, stale: false };

  const departments: Department[] = DEMO_DEPARTMENTS.map((department) => {
    if (scenario.allClear) {
      return { ...department, freshness: "LIVE", needsAttention: false };
    }
    if (scenario.staleFeed) {
      return { ...department, freshness: "STALE", needsAttention: true };
    }
    if (scenario.gateBurst) {
      // A rejection burst spreads: five departments need attention (risk, gate, data-infra,
      // liquidity, counterparty) while the absorbed/dissipated counts flip — see the gate readout.
      return {
        ...department,
        needsAttention:
          department.id === "risk" ||
          department.id === "gate" ||
          department.id === "data-infra" ||
          department.id === "liquidity" ||
          department.id === "counterparty",
      };
    }
    return { ...department };
  });

  const signals: Signal[] = SIGNAL_SEEDS.map((seed) => ({
    id: seed.id,
    fromNodeId: seed.from,
    toNodeId: seed.to,
    outcome: scenario.allClear ? "absorbed" : scenario.gateBurst && seed.outcome === "absorbed" ? "dissipated" : seed.outcome,
    ...(seed.reasonFa ? { reasonFa: seed.reasonFa } : {}),
    at: iso(seed.minutesAgo) ?? new Date(nowMs).toISOString(),
  }));

  return { markets, signals, gate, health, departments };
}
