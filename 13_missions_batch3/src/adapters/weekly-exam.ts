// FILE: 13_missions_batch3/src/adapters/weekly-exam.ts
/**
 * Adapter for «آزمون هفتگی هوش» (M50). Descriptive only — never a verdict.
 */
import { loadWeeklyExam } from "@/adapters/_contract";
import { unavailableWeeklyExam } from "@/contract/unavailable";
import type { WeeklyExamSnapshot } from "@/contract/types";
import { weeklyExamDemo } from "@/mock/weekly-exam";
import { isDemoForced } from "@/lib/flags";

// BIND AHOS ENDPOINT HERE
// ---------------------------------------------------------------------------
// Intended endpoint : GET /api/arena/weekly-exam
// Response → type   : { minSampleSize, runs: [{ id, week, itemsCount,
//                     answeredCount, withEvidenceCount, resultSummary, state,
//                     items, demo }], ...meta } →
//                     validateWeeklyExam() → WeeklyExamSnapshot
// Error → UNAVAILABLE : fetch/validation failure ⇒ unavailableWeeklyExam()
//                     (page shows the UNAVAILABLE block; nothing is thrown).
// Demo fallback     : only with ?demo=1 and only if the contract is missing —
//                     the mock is labelled DEMO and never presented as real.
// ---------------------------------------------------------------------------
export async function getSnapshot(): Promise<WeeklyExamSnapshot> {
  const section = await loadWeeklyExam();
  if (section) return section;
  if (isDemoForced()) return weeklyExamDemo;
  return unavailableWeeklyExam();
}
