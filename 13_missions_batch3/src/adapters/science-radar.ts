// FILE: 13_missions_batch3/src/adapters/science-radar.ts
/**
 * Adapter for «رادار علم» (M44). Reads its section through the shared loader.
 */
import { loadScienceRadar } from "@/adapters/_contract";
import { unavailableScienceRadar } from "@/contract/unavailable";
import type { ScienceRadarSnapshot } from "@/contract/types";
import { scienceRadarDemo } from "@/mock/science-radar";
import { isDemoForced } from "@/lib/flags";

// BIND AHOS ENDPOINT HERE
// ---------------------------------------------------------------------------
// Intended endpoint : GET /api/arena/science-radar
// Response → type   : { items: [{ id, title, sourceType, topic, foundAt,
//                     relevanceNote, status, sourceText, demo }], ...meta } →
//                     validateScienceRadar() → ScienceRadarSnapshot
// Error → UNAVAILABLE : fetch/validation failure ⇒ unavailableScienceRadar()
//                     (page shows the UNAVAILABLE block; nothing is thrown).
// Demo fallback     : only with ?demo=1 and only if the contract is missing —
//                     the mock is labelled DEMO and never presented as real.
// ---------------------------------------------------------------------------
export async function getSnapshot(): Promise<ScienceRadarSnapshot> {
  const section = await loadScienceRadar();
  if (section) return section;
  if (isDemoForced()) return scienceRadarDemo;
  return unavailableScienceRadar();
}
