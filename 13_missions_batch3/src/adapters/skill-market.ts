// FILE: 13_missions_batch3/src/adapters/skill-market.ts
/**
 * Adapter for «بازار مهارت و افزونه» (M52). Catalog is display-only.
 */
import { loadSkillMarket } from "@/adapters/_contract";
import { unavailableSkillMarket } from "@/contract/unavailable";
import type { SkillMarketSnapshot } from "@/contract/types";
import { skillMarketDemo } from "@/mock/skill-market";
import { isDemoForced } from "@/lib/flags";

// BIND AHOS ENDPOINT HERE
// ---------------------------------------------------------------------------
// Intended endpoint : GET /api/arena/skill-market   (catalog read only — there
//                     is NO install/enable/update/remove endpoint by design)
// Response → type   : { entries: [{ id, name, kind, version, source,
//                     installState, permissions, reviewState, reason, demo }],
//                     ...meta } → validateSkillMarket() → SkillMarketSnapshot
// Error → UNAVAILABLE : fetch/validation failure ⇒ unavailableSkillMarket()
//                     (page shows the UNAVAILABLE block; nothing is thrown).
// Demo fallback     : only with ?demo=1 and only if the contract is missing —
//                     the mock is labelled DEMO and never presented as real.
// ---------------------------------------------------------------------------
export async function getSnapshot(): Promise<SkillMarketSnapshot> {
  const section = await loadSkillMarket();
  if (section) return section;
  if (isDemoForced()) return skillMarketDemo;
  return unavailableSkillMarket();
}
