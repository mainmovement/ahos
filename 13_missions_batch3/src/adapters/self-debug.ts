// FILE: 13_missions_batch3/src/adapters/self-debug.ts
/**
 * Adapter for «خطایابی خودکار» (M46). READ-ONLY: no restart, no patch, no apply.
 */
import { loadSelfDebug } from "@/adapters/_contract";
import { unavailableSelfDebug } from "@/contract/unavailable";
import type { SelfDebugSnapshot } from "@/contract/types";
import { selfDebugDemo } from "@/mock/self-debug";
import { isDemoForced } from "@/lib/flags";

// BIND AHOS ENDPOINT HERE
// ---------------------------------------------------------------------------
// Intended endpoint : GET /api/arena/self-debug
// Response → type   : { incidents: [{ id, time, component, errorSignature,
//                     diagnosisNote, status, evidencePath, timeline,
//                     logExcerpt, demo }], ...meta } →
//                     validateSelfDebug() → SelfDebugSnapshot
// Error → UNAVAILABLE : fetch/validation failure ⇒ unavailableSelfDebug()
//                     (page shows the UNAVAILABLE block; nothing is thrown).
// Demo fallback     : only with ?demo=1 and only if the contract is missing —
//                     the mock is labelled DEMO and never presented as real.
// ---------------------------------------------------------------------------
export async function getSnapshot(): Promise<SelfDebugSnapshot> {
  const section = await loadSelfDebug();
  if (section) return section;
  if (isDemoForced()) return selfDebugDemo;
  return unavailableSelfDebug();
}
