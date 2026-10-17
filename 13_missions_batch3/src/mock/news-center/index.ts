// FILE: 13_missions_batch3/src/mock/news-center/index.ts
/**
 * DEMO fixture for «مرکز اخبار آرام». Adapter-only — components must never
 * import this module. Neutral summaries; no sentiment, no trade hints.
 */
import type { NewsCenterSnapshot } from "@/contract/types";

export const newsCenterDemo: NewsCenterSnapshot = {
  kind: "newsCenter",
  executionMode: "PAPER_ONLY",
  realTrading: false,
  source: "DEMO_FIXTURE",
  generatedAt: "2026-10-16T12:00:00+03:30",
  demo: true,
  staleAfterMinutes: 30,
  items: [
    { id: "nw-01", time: "2026-10-16T11:50:00+03:30", sourceName: "خبرگزاری انرژی", topic: "Oil", summary: "گزارش هفتگی ذخایر منتشر شد", reliability: null, demo: true },
    { id: "nw-02", time: "2026-10-16T11:20:00+03:30", sourceName: "بازار فلزات", topic: "Gold", summary: "قیمت‌های نقدی در بازار جهانی به‌روزرسانی شد", reliability: null, demo: true },
    { id: "nw-03", time: "2026-10-16T10:00:00+03:30", sourceName: "تقویم اقتصادی", topic: "Macro", summary: "زمان انتشار شاخص‌های ماهانه اعلام شد", reliability: "میانه", demo: true },
    { id: "nw-04", time: "2026-10-16T08:30:00+03:30", sourceName: "منبع نامشخص", topic: "Other", summary: "خبر عمومی بدون منبع مشخص", reliability: null, demo: true },
    { id: "nw-05", time: "2026-10-16T11:55:00+03:30", sourceName: "خبرگزاری انرژی", topic: "Oil", summary: "آمار حمل‌ونقل دریایی منتشر شد", reliability: null, demo: true },
    { id: "nw-06", time: null, sourceName: "ثبت دستی", topic: "Gold", summary: "یادداشت بدون زمان ثبت شده است", reliability: null, demo: true },
    { id: "nw-07", time: "2026-10-16T09:10:00+03:30", sourceName: "بانک مرکزی", topic: "Macro", summary: "اعلام برنامه انتشار داده‌های پولی", reliability: "رسمی", demo: true },
    { id: "nw-08", time: "2026-10-16T11:58:00+03:30", sourceName: "بازار فلزات", topic: "Gold", summary: "گزارش روزانه تقاضای فیزیکی ثبت شد", reliability: null, demo: true },
  ],
};
