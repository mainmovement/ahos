// FILE: 13_missions_batch3/src/adapters/_contract.ts
/**
 * Shared contract loader — the ONLY module allowed to fetch the contract JSON.
 * Components and features must never import the JSON file directly.
 *
 * BIND AHOS ENDPOINT HERE (document root):
 *   Intended endpoint : GET /api/arena/contract   (or any AHOS mirror of the
 *                       single merged contract document)
 *   Current source    : /contract/ahos-arena-contract.example.json (static DEMO)
 *   Response → type   : JSON document validated by validateContract()
 *   Error → UNAVAILABLE : any network/parse/validation failure returns null.
 *                       Callers substitute their UNAVAILABLE snapshot. Nothing
 *                       is thrown to the UI and nothing is fabricated.
 */
import {
  validateNewsCenter,
  validateScienceRadar,
  validateSelfDebug,
  validateSkillMarket,
  validateWeeklyExam,
} from "@/contract/validate";
import type {
  NewsCenterSnapshot,
  ScienceRadarSnapshot,
  SelfDebugSnapshot,
  SkillMarketSnapshot,
  WeeklyExamSnapshot,
} from "@/contract/types";

export const CONTRACT_URL = "/contract/ahos-arena-contract.example.json";

async function loadRoot(): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch(CONTRACT_URL, { cache: "no-store" });
    if (!res.ok) return null;
    const raw: unknown = await res.json();
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return null;
    return raw as Record<string, unknown>;
  } catch {
    return null;
  }
}

/** Per-section typed loaders. null ⇒ UNAVAILABLE at the call site. */
export async function loadScienceRadar(): Promise<ScienceRadarSnapshot | null> {
  const root = await loadRoot();
  if (!root) return null;
  return validateScienceRadar(root.scienceRadar, root);
}

export async function loadSelfDebug(): Promise<SelfDebugSnapshot | null> {
  const root = await loadRoot();
  if (!root) return null;
  return validateSelfDebug(root.selfDebug, root);
}

export async function loadWeeklyExam(): Promise<WeeklyExamSnapshot | null> {
  const root = await loadRoot();
  if (!root) return null;
  return validateWeeklyExam(root.weeklyExam, root);
}

export async function loadSkillMarket(): Promise<SkillMarketSnapshot | null> {
  const root = await loadRoot();
  if (!root) return null;
  return validateSkillMarket(root.skillMarket, root);
}

export async function loadNewsCenter(): Promise<NewsCenterSnapshot | null> {
  const root = await loadRoot();
  if (!root) return null;
  return validateNewsCenter(root.newsCenter, root);
}
