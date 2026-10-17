// FILE: 13_missions_batch3/src/adapters/news-center.ts
/**
 * Adapter for «مرکز اخبار آرام» (M18.N). Information only — never a signal.
 */
import { loadNewsCenter } from "@/adapters/_contract";
import { unavailableNewsCenter } from "@/contract/unavailable";
import type { NewsCenterSnapshot } from "@/contract/types";
import { newsCenterDemo } from "@/mock/news-center";
import { isDemoForced } from "@/lib/flags";

// BIND AHOS ENDPOINT HERE
// ---------------------------------------------------------------------------
// Intended endpoint : GET /api/arena/news-center
// Response → type   : { staleAfterMinutes, items: [{ id, time, sourceName,
//                     topic, summary, reliability, demo }], ...meta } →
//                     validateNewsCenter() → NewsCenterSnapshot
// Error → UNAVAILABLE : fetch/validation failure ⇒ unavailableNewsCenter()
//                     (page shows the UNAVAILABLE block; nothing is thrown).
// Demo fallback     : only with ?demo=1 and only if the contract is missing —
//                     the mock is labelled DEMO and never presented as real.
// ---------------------------------------------------------------------------
export async function getSnapshot(): Promise<NewsCenterSnapshot> {
  const section = await loadNewsCenter();
  if (section) return section;
  if (isDemoForced()) return newsCenterDemo;
  return unavailableNewsCenter();
}
