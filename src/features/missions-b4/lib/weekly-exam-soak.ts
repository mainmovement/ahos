import type { WeeklyExamItem, WeeklyExamRun, WeeklyExamSnapshot } from "../contract/types";

export function buildWeeklyExamFromSoak(
  status: Record<string, unknown>,
  generatedAt: string,
): WeeklyExamSnapshot | null {
  const tg = status.last_tier_gate;
  if (!tg || typeof tg !== "object") return null;
  const gate = tg as Record<string, unknown>;
  if (gate.kind !== "tier_gate") return null;
  const day = typeof gate.day === "string" ? gate.day : null;
  const mp = typeof gate.measurable_passed === "number" ? gate.measurable_passed : null;
  const mt = typeof gate.measurable_total === "number" ? gate.measurable_total : null;
  const questions = Array.isArray(gate.open_questions)
    ? gate.open_questions.filter((q): q is string => typeof q === "string")
    : [];
  const items: WeeklyExamItem[] = questions.map((q, i) => ({
    id: `TG-Q${i + 1}`,
    topic: q.length > 240 ? `${q.slice(0, 237)}…` : q,
    answered: "UNKNOWN",
    evidence: mp !== null && mt !== null && mp >= 3 ? "yes" : "no",
    reviewState: gate.ready_for_owner_review === true ? "OWNER_REVIEW" : "OPEN",
    demo: false,
  }));
  const tier = typeof gate.tier === "string" ? gate.tier : "UNKNOWN";
  const run: WeeklyExamRun = {
    id: day ? `tier-gate-${day}` : "tier-gate-latest",
    week: day,
    itemsCount: mt,
    answeredCount: mp,
    withEvidenceCount: mp,
    resultSummary: `tier ${tier}; measurable ${mp ?? "—"}/${mt ?? "—"} (neutral counts, not a pass grade)`,
    state: gate.ok === true ? "PARTIAL" : "RAN",
    items,
    demo: false,
  };
  return {
    kind: "weeklyExam",
    executionMode: "PAPER_ONLY",
    realTrading: false,
    source: "M13_SOAK soak_status.json · last_tier_gate",
    generatedAt,
    demo: false,
    minSampleSize: 3,
    runs: [run],
  };
}
