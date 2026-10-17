// FILE: 13_missions_batch3/src/contract/unavailable.ts
import type {
  ExecutionMode,
  NewsCenterSnapshot,
  ScienceRadarSnapshot,
  SelfDebugSnapshot,
  SkillMarketSnapshot,
  WeeklyExamSnapshot,
} from "./types";

/**
 * UNAVAILABLE snapshot builders. Used when the contract cannot be loaded or
 * validated. The UI renders an UNAVAILABLE state block — it never throws and
 * never falls back to fake data.
 */

const base = {
  executionMode: "UNKNOWN" as ExecutionMode,
  realTrading: false,
  source: null,
  generatedAt: null,
  demo: false,
};

export function unavailableScienceRadar(): ScienceRadarSnapshot {
  return { ...base, kind: "scienceRadar", items: [] };
}

export function unavailableSelfDebug(): SelfDebugSnapshot {
  return { ...base, kind: "selfDebug", incidents: [] };
}

export function unavailableWeeklyExam(): WeeklyExamSnapshot {
  return { ...base, kind: "weeklyExam", minSampleSize: 1, runs: [] };
}

export function unavailableSkillMarket(): SkillMarketSnapshot {
  return { ...base, kind: "skillMarket", entries: [] };
}

export function unavailableNewsCenter(): NewsCenterSnapshot {
  return { ...base, kind: "newsCenter", staleAfterMinutes: 30, items: [] };
}
