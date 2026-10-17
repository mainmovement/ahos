// FILE: 13_missions_batch3/src/mock/skill-market/index.ts
/**
 * DEMO fixture for «بازار مهارت و افزونه». Adapter-only — components must
 * never import this module. Catalog display only; nothing is installable here.
 */
import type { SkillMarketSnapshot } from "@/contract/types";

export const skillMarketDemo: SkillMarketSnapshot = {
  kind: "skillMarket",
  executionMode: "PAPER_ONLY",
  realTrading: false,
  source: "DEMO_FIXTURE",
  generatedAt: "2026-10-16T12:00:00+03:30",
  demo: true,
  entries: [
    { id: "sk-01", name: "تحلیل‌گر سری زمانی", kind: "skill", version: "0.3.1", source: "ثبت داخلی", installState: "INSTALLED", permissions: ["خواندن داده بازار"], reviewState: "REVIEWED", reason: "بررسی متن قرارداد انجام شد", demo: true },
    { id: "sk-02", name: "افزونه گزارش‌ساز", kind: "plugin", version: "1.0.0", source: "ثبت داخلی", installState: "AVAILABLE", permissions: ["خواندن فایل گزارش", "نوشتن فایل خروجی"], reviewState: "UNREVIEWED", reason: null, demo: true },
    { id: "sk-03", name: "افزونه اتصال داده", kind: "plugin", version: "0.9.2", source: "خارجی", installState: "BLOCKED", permissions: ["دسترسی شبکه", "خواندن متغیرهای محیطی"], reviewState: "REJECTED", reason: "درخواست دسترسی بیش از نیاز", demo: true },
    { id: "sk-04", name: "مهارت خلاصه‌ساز", kind: "skill", version: "0.2.0", source: "ثبت داخلی", installState: "AVAILABLE", permissions: ["خواندن متن"], reviewState: "REVIEWED", reason: null, demo: true },
    { id: "sk-05", name: "افزونه زمان‌بند", kind: "plugin", version: "1.2.4", source: "ثبت داخلی", installState: "INSTALLED", permissions: ["خواندن زمان‌بندی"], reviewState: "REVIEWED", reason: "متن مجوز بررسی شد", demo: true },
    { id: "sk-06", name: "مهارت تطبیق الگو", kind: "skill", version: null, source: "خارجی", installState: "UNKNOWN", permissions: [], reviewState: "UNREVIEWED", reason: null, demo: true },
    { id: "sk-07", name: "افزونه آرشیو", kind: "plugin", version: "0.5.0", source: "ثبت داخلی", installState: "AVAILABLE", permissions: ["نوشتن آرشیو"], reviewState: "REJECTED", reason: null, demo: true },
    { id: "sk-08", name: "مهارت مقایسه‌گر", kind: "skill", version: "0.1.7", source: "ثبت داخلی", installState: "BLOCKED", permissions: ["خواندن داده"], reviewState: "UNREVIEWED", reason: null, demo: true },
  ],
};
