/**
 * Central copy deck. Every user-visible string lives here so the page can be
 * proof-read (and translated) in one place.
 */

import type { ClaimStrength, MarketId, PipelineStageId, ReporterRole } from './types';

export const COPY = {
  pageTitle: 'دیده‌بان',
  pageSubtitle: 'خبرنگاران',
  pageTruthLabel: 'TRUTH',
  focusNote: 'فقط نفت و طلا؛ بقیه بازارها فعلاً متصل نیست',
  paperOnly: 'فقط کاغذی · PAPER_ONLY',
  worldCapsule: 'جهان AHOS',
  realityMap: 'نقشهٔ واقعیت',
  readOnlyNote: 'این صفحه فقط خواندنی است؛ هیچ سفارشی ثبت نمی‌شود.',
  demoBannerTitle: 'حالت دمو · DEMO',
  demoBannerBody: 'داده‌های این صفحه از لایهٔ شبیه‌ساز (mock) می‌آیند و در هیچ مجموعِ تأییدی حساب نمی‌شوند.',
  violationTitle: 'تخطی · VIOLATION',
  violationBody:
    'پیکربندی این صفحه فقط‌کاغذی نیست (executionMode/realTrading). تا زمان بازگشت به PAPER_ONLY هیچ خروجی معاملاتی معتبر نیست.',
  loading: 'در حال بارگذاری…',
  errorTitle: 'خطا در دریافت داده',
  errorBody: 'لایهٔ داده پاسخ معتبر نداد. دوباره تلاش کنید؛ مقدار جعلی نمایش داده نمی‌شود.',
  emptyTitle: 'خبری برای نمایش نیست',
  emptyBody: 'هیچ خبری با این پالایه یافت نشد. پالایه را عوض کنید یا پنجرهٔ زمانی را بازتر کنید.',
  unavailableTitle: 'منابع در دسترس نیستند',
  unavailableBody: 'هیچ منبعی خوانده نشد. وضعیت UNKNOWN است و عددی ساخته نمی‌شود.',
  noSelectionTitle: 'خبری انتخاب نشده',
  noSelectionBody: 'یک خبر از کارتابل سمت راست انتخاب کنید تا پروندهٔ آن باز شود.',
  partialSourceRule: 'یک منبع ⇒ هرگز «تأیید‌شده» نیست',
} as const;

export const MARKET_LABEL_FA: Record<MarketId, string> = {
  OIL: 'نفت',
  GOLD: 'طلا',
  CRYPTO: 'رمزارز',
  EQUITIES: 'سهام',
};

export const MARKET_LABEL_EN: Record<MarketId, string> = {
  OIL: 'OIL',
  GOLD: 'GOLD',
  CRYPTO: 'CRYPTO',
  EQUITIES: 'EQUITIES',
};

export const CLAIM_STRENGTH_LABEL_FA: Record<ClaimStrength, string> = {
  STRONG: 'قوی',
  MODERATE: 'متوسط',
  WEAK: 'ضعیف',
  UNKNOWN: 'نامعلوم',
};

export const CLAIM_STRENGTH_LABEL_EN: Record<ClaimStrength, string> = {
  STRONG: 'STRONG',
  MODERATE: 'MODERATE',
  WEAK: 'WEAK',
  UNKNOWN: 'UNKNOWN',
};

/** 0..4 — how many pips of the strength meter are filled. UNKNOWN ⇒ 0. */
export const CLAIM_STRENGTH_LEVEL: Record<ClaimStrength, number> = {
  STRONG: 4,
  MODERATE: 3,
  WEAK: 1,
  UNKNOWN: 0,
};

export const REPORTER_ROLE_LABEL_FA: Record<ReporterRole, string> = {
  wire: 'وایر',
  macro: 'کلان',
  energy: 'انرژی',
  metals: 'فلزات',
};

export const REPORTER_ROLE_LABEL_EN: Record<ReporterRole, string> = {
  wire: 'WIRE',
  macro: 'MACRO',
  energy: 'ENERGY',
  metals: 'METALS',
};

export const PIPELINE_LABEL_FA: Record<PipelineStageId, string> = {
  INGEST: 'دریافت',
  TRIAGE: 'غربال',
  TWO_SOURCE_CHECK: 'بررسی دومنبعی',
  CONFLICT_SCAN: 'پویش تعارض',
  JUDGE_HANDOFF: 'تحویل به قاضی',
};

export const PIPELINE_LABEL_EN: Record<PipelineStageId, string> = {
  INGEST: 'INGEST',
  TRIAGE: 'TRIAGE',
  TWO_SOURCE_CHECK: 'TWO_SOURCE_CHECK',
  CONFLICT_SCAN: 'CONFLICT_SCAN',
  JUDGE_HANDOFF: 'JUDGE_HANDOFF',
};

/** Verbs that exist on this page. Anything outside this list is forbidden. */
export const ALLOWED_VERBS_FA = ['دیدن', 'پالایش', 'خروجیِ فقط‌خواندنی', 'گشودنِ مدرک', 'رونوشتِ شناسه'] as const;

export const PANEL = {
  inbox: 'کارتابل خبر',
  dossier: 'پروندهٔ خبر',
  sources: 'منابع',
  pipeline: 'خط تأیید',
  conflicts: 'تختهٔ تعارض',
  reporters: 'گروه خبرنگاران',
  handoff: 'تحویل به کلاه‌سفیدها',
  markets: 'تمرکز بازار',
  telemetry: 'دورسنجی',
} as const;

export const ACTION = {
  details: 'جزئیات',
  detailsOff: 'بستن جزئیات',
  copyId: 'رونوشتِ شناسه',
  copied: 'شناسه رونوشت شد',
  exportReadOnly: 'خروجیِ فقط‌خواندنی',
  openEvidence: 'گشودنِ مدرک',
  view: 'دیدن',
  close: 'بستن',
  filterAll: 'همه',
  filterConflict: 'تعارض',
  filterDemo: 'دمو',
  retry: 'تلاشِ دوباره',
} as const;
