// FILE: 13_missions_batch3/src/mock/science-radar/index.ts
/**
 * DEMO fixture for «رادار علم». Adapter-only — components must never import
 * this module. Every record is demo:true and is labelled DEMO wherever shown.
 */
import type { ScienceRadarSnapshot } from "@/contract/types";

export const scienceRadarDemo: ScienceRadarSnapshot = {
  kind: "scienceRadar",
  executionMode: "PAPER_ONLY",
  realTrading: false,
  source: "DEMO_FIXTURE",
  generatedAt: "2026-10-16T12:00:00+03:30",
  demo: true,
  items: [
    { id: "sr-01", title: "روش تطبیق نویز بازار در داده‌های کم‌عمق", sourceType: "paper", topic: "بازار", foundAt: "2026-10-15T09:20:00+03:30", relevanceNote: "به ساختار نویز اشاره دارد؛ ارزیابی نشده است", status: "NEW", sourceText: "پیش‌چاپ — نویسندگان دانشگاهی", demo: true },
    { id: "sr-02", title: "کتابخانه محاسبه پارامترهای نوسان", sourceType: "repo", topic: "ابزار", foundAt: "2026-10-14T18:05:00+03:30", relevanceNote: "پیاده‌سازی محاسباتی دارد؛ دیده نشده است", status: "NEW", sourceText: "مخزن عمومی — بدون ادعای کیفیت", demo: true },
    { id: "sr-03", title: "یادداشت دانشگاهی درباره ساختار بازار", sourceType: "university", topic: "بازار", foundAt: "2026-10-13T11:40:00+03:30", relevanceNote: "مرور مفاهیم پایه", status: "REVIEWED", sourceText: "یادداشت آموزشی", demo: true },
    { id: "sr-04", title: "گزارش عامل درباره رفتار نقدینگی", sourceType: "agent", topic: "نقدینگی", foundAt: "2026-10-12T22:15:00+03:30", relevanceNote: "ثبت عامل؛ منبع بیرونی ندارد", status: "UNKNOWN", sourceText: null, demo: true },
    { id: "sr-05", title: "یادداشت وبلاگی درباره تقویم اقتصادی", sourceType: "blog", topic: "کلان", foundAt: "2026-10-11T08:00:00+03:30", relevanceNote: "فقط فهرست رویدادها", status: "DISMISSED", sourceText: "وبلاگ عمومی", demo: true },
    { id: "sr-06", title: "کارگاه روش‌شناسی آزمون فرضیه", sourceType: "university", topic: "روش", foundAt: "2026-10-10T15:30:00+03:30", relevanceNote: "چارچوب مفهومی ارائه می‌دهد", status: "REVIEWED", sourceText: "اسلایدهای کارگاه", demo: true },
    { id: "sr-07", title: "پروژه بازتولید محاسبات آماری", sourceType: "repo", topic: "ابزار", foundAt: "2026-10-09T20:10:00+03:30", relevanceNote: "کد قابل خواندن؛ بدون ارزیابی", status: "NEW", sourceText: "مخزن عمومی", demo: true },
    { id: "sr-08", title: "چکیده مقاله درباره سنجش ریسک بازار", sourceType: "paper", topic: "ریسک", foundAt: null, relevanceNote: "تاریخ یافت‌شدن ثبت نشده است", status: "UNKNOWN", sourceText: "چکیده", demo: true },
  ],
};
