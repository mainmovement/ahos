// FILE: 13_missions_batch3/src/mock/weekly-exam/index.ts
/**
 * DEMO fixture for «آزمون هفتگی هوش». Adapter-only — components must never
 * import this module. Neutral numbers only; never a verdict.
 */
import type { WeeklyExamSnapshot } from "@/contract/types";

export const weeklyExamDemo: WeeklyExamSnapshot = {
  kind: "weeklyExam",
  executionMode: "PAPER_ONLY",
  realTrading: false,
  source: "DEMO_FIXTURE",
  generatedAt: "2026-10-16T12:00:00+03:30",
  demo: true,
  minSampleSize: 3,
  runs: [
    {
      id: "we-04",
      week: "1405-W29",
      itemsCount: 4,
      answeredCount: 3,
      withEvidenceCount: 2,
      resultSummary: "۴ مورد · ۳ پاسخ · ۲ با شواهد",
      state: "RAN",
      items: [
        { id: "we-04-a", topic: "ساختار بازار", answered: "yes", evidence: "yes", reviewState: "دیده‌شده", demo: true },
        { id: "we-04-b", topic: "روش آزمون", answered: "yes", evidence: "no", reviewState: "دیده‌شده", demo: true },
        { id: "we-04-c", topic: "داده", answered: "yes", evidence: "yes", reviewState: "در انتظار", demo: true },
        { id: "we-04-d", topic: "ریسک", answered: "no", evidence: "UNKNOWN", reviewState: null, demo: true },
      ],
      demo: true,
    },
    {
      id: "we-03",
      week: "1405-W28",
      itemsCount: 2,
      answeredCount: 1,
      withEvidenceCount: 0,
      resultSummary: "۲ مورد · ۱ پاسخ · ۰ با شواهد",
      state: "PARTIAL",
      items: [
        { id: "we-03-a", topic: "نقدینگی", answered: "yes", evidence: "no", reviewState: "دیده‌شده", demo: true },
        { id: "we-03-b", topic: "کلان", answered: "UNKNOWN", evidence: "UNKNOWN", reviewState: null, demo: true },
      ],
      demo: true,
    },
    {
      id: "we-02",
      week: "1405-W27",
      itemsCount: null,
      answeredCount: null,
      withEvidenceCount: null,
      resultSummary: null,
      state: "NOT_RUN",
      items: [],
      demo: true,
    },
    {
      id: "we-01",
      week: null,
      itemsCount: null,
      answeredCount: null,
      withEvidenceCount: null,
      resultSummary: null,
      state: "UNKNOWN",
      items: [],
      demo: true,
    },
  ],
};
