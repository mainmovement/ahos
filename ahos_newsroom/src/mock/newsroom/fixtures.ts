/**
 * Fixtures for the AHOS Newsroom (دیده‌بان · خبرنگاران).
 *
 * RULES FOR THIS FILE
 * -------------------
 * 1. These are *paper* fixtures. No live prices are invented, no market data is
 *    fetched, and no headline here is a trading signal.
 * 2. Only OIL and GOLD carry stories. CRYPTO / EQUITIES are `PLANNED` and carry
 *    `storyCount: null` — never a fabricated number.
 * 3. Every timestamp is explicit ISO-8601. `null` means UNKNOWN on purpose; the
 *    UI renders «ناموجود» and never a zero.
 * 4. URLs are `*.invalid` placeholders rendered as plain text. Nothing here is
 *    ever fetched.
 */

import type {
  Conflict,
  MarketFocus,
  NewsSource,
  NewsroomSnapshot,
  PipelineStage,
  ReporterAgent,
  Story,
} from '@/features/newsroom/lib/types';

/** Reference "now" for the fixture set (Tehran, +03:30). */
export const FIXTURE_NOW = '2026-10-16T12:00:00.000+03:30';

/* -------------------------------------------------------------------------- */
/* Markets                                                                     */
/* -------------------------------------------------------------------------- */

export const FIXTURE_MARKETS: MarketFocus[] = [
  {
    id: 'OIL',
    labelFa: 'نفت',
    labelEn: 'OIL',
    connected: true,
    status: 'LIVE',
    storyCount: null, // filled by the adapter from real story counts
    noteFa: null,
  },
  {
    id: 'GOLD',
    labelFa: 'طلا',
    labelEn: 'GOLD',
    connected: true,
    status: 'LIVE',
    storyCount: null,
    noteFa: null,
  },
  {
    id: 'CRYPTO',
    labelFa: 'رمزارز',
    labelEn: 'CRYPTO',
    connected: false,
    status: 'PLANNED',
    storyCount: null,
    noteFa: 'متصل نیست · PLANNED',
  },
  {
    id: 'EQUITIES',
    labelFa: 'سهام',
    labelEn: 'EQUITIES',
    connected: false,
    status: 'PLANNED',
    storyCount: null,
    noteFa: 'متصل نیست · PLANNED',
  },
];

/* -------------------------------------------------------------------------- */
/* Sources                                                                     */
/* -------------------------------------------------------------------------- */

export const FIXTURE_SOURCES: NewsSource[] = [
  {
    id: 'src-reuters-energy',
    nameFa: 'رویترز · وایر انرژی',
    urlPlaceholder: 'https://example.invalid/wire/reuters-energy',
    credibility: 'A',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:58:00.000+03:30',
    independenceGroup: 'grp-reuters',
    noteFa: 'آخرین خوانش موفق',
  },
  {
    id: 'src-bloomberg-cmdty',
    nameFa: 'بلومبرگ · بازارهای کالا',
    urlPlaceholder: 'https://example.invalid/wire/bloomberg-commodities',
    credibility: 'A',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:57:00.000+03:30',
    independenceGroup: 'grp-bloomberg',
    noteFa: 'آخرین خوانش موفق',
  },
  {
    id: 'src-argus-crude',
    nameFa: 'آرگوس مدیا · قیمت‌گذاری نفت خام',
    urlPlaceholder: 'https://example.invalid/pricing/argus-crude',
    credibility: 'B',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:56:00.000+03:30',
    independenceGroup: 'grp-argus',
    noteFa: 'اشتراک پولی · خوانش دسته‌ای',
  },
  {
    id: 'src-platts-metals',
    nameFa: 'پلاتس · فلزات گران‌بها',
    urlPlaceholder: 'https://example.invalid/pricing/platts-metals',
    credibility: 'B',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:55:00.000+03:30',
    independenceGroup: 'grp-platts',
    noteFa: 'اشتراک پولی · خوانش دسته‌ای',
  },
  {
    id: 'src-eia-weekly',
    nameFa: 'ادارهٔ اطلاعات انرژی آمریکا · گزارش هفتگی',
    urlPlaceholder: 'https://example.invalid/official/eia-weekly-petroleum',
    credibility: 'A',
    status: 'STALE',
    lastReadAt: '2026-10-16T02:40:00.000+03:30',
    independenceGroup: 'grp-eia',
    noteFa: 'آخرین خوانش موفق · اکنون کهنه',
  },
  {
    id: 'src-iea-monthly',
    nameFa: 'آژانس بین‌المللی انرژی · گزارش ماهانه',
    urlPlaceholder: 'https://example.invalid/official/iea-oil-market-report',
    credibility: 'A',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:50:00.000+03:30',
    independenceGroup: 'grp-iea',
    noteFa: 'آخرین خوانش موفق',
  },
  {
    id: 'src-wgc-demand',
    nameFa: 'شورای جهانی طلا · روند تقاضا',
    urlPlaceholder: 'https://example.invalid/official/wgc-demand-trends',
    credibility: 'A',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:52:00.000+03:30',
    independenceGroup: 'grp-wgc',
    noteFa: 'آخرین خوانش موفق',
  },
  {
    id: 'src-lbma-vault',
    nameFa: 'انجمن بازار طلای لندن · آمار خزانه',
    urlPlaceholder: 'https://example.invalid/official/lbma-vault-stats',
    credibility: 'B',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:47:00.000+03:30',
    independenceGroup: 'grp-lbma',
    noteFa: 'آخرین خوانش موفق',
  },
  {
    id: 'src-port-authority',
    nameFa: 'ادارهٔ بندر · بولتن محلی (کنترل‌نشده)',
    urlPlaceholder: 'https://example.invalid/local/port-authority-bulletin',
    credibility: 'C',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:30:00.000+03:30',
    independenceGroup: 'grp-port-local',
    noteFa: 'منبع کنترل‌نشده · فقط برای ردیابی تعارض',
  },
  {
    id: 'src-shipping-desk',
    nameFa: 'میز کشتیرانی · یادداشت بارگیری',
    urlPlaceholder: 'https://example.invalid/desk/shipping-loading-note',
    credibility: 'C',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:28:00.000+03:30',
    independenceGroup: 'grp-shipping-desk',
    noteFa: 'منبع کنترل‌نشده · فقط برای ردیابی تعارض',
  },
  {
    id: 'src-imports-customs',
    nameFa: 'گمرک · جدول واردات (در دسترس نیست)',
    urlPlaceholder: 'https://example.invalid/official/customs-gold-imports',
    credibility: 'UNKNOWN',
    status: 'UNKNOWN',
    lastReadAt: null,
    independenceGroup: 'grp-customs',
    noteFa: 'پاسخی دریافت نشد · زمانِ خوانش نامعلوم',
  },
  {
    id: 'src-rumour-channel',
    nameFa: 'کانال شایعه · بازنشر بدون سند',
    urlPlaceholder: 'https://example.invalid/unvetted/rumour-channel',
    credibility: 'C',
    status: 'REJECTED',
    lastReadAt: '2026-10-16T11:20:00.000+03:30',
    independenceGroup: 'grp-rumour',
    noteFa: 'در غربال رد شد · سند مستقل ندارد',
  },
  {
    id: 'src-simulator',
    nameFa: 'شبیه‌ساز خبر · لایهٔ دمو',
    urlPlaceholder: 'https://example.invalid/mock/newsroom-simulator',
    credibility: 'UNKNOWN',
    status: 'DEMO',
    lastReadAt: '2026-10-16T11:58:00.000+03:30',
    independenceGroup: 'grp-simulator',
    noteFa: 'دادهٔ آزمایشی · در هیچ مجموعی حساب نمی‌شود',
  },
];

/* -------------------------------------------------------------------------- */
/* Stories                                                                     */
/* -------------------------------------------------------------------------- */

export const FIXTURE_STORIES: Story[] = [
  {
    id: 'nws-oil-0142',
    headlineFa: 'اوپک‌پلاس سطح تولید را در نشست فصلی بدون تغییر نگه داشت',
    headlineEn: 'OPEC+ holds output levels steady at quarterly session',
    market: 'OIL',
    publishedAt: '2026-10-16T11:52:00.000+03:30',
    claimStrength: 'STRONG',
    sourceIds: ['src-reuters-energy', 'src-bloomberg-cmdty'],
    marketImpactNoteFa: 'ادعای رویدادی؛ هیچ قیمت لحظه‌ای از آن استخراج نشده است.',
    demo: false,
    status: 'LIVE',
    conflictId: null,
  },
  {
    id: 'nws-gold-0098',
    headlineFa: 'ذخایر طلای بانک مرکزی برای سومین ماه پیاپی افزایش یافت',
    headlineEn: 'Central bank gold reserves rise for a third straight month',
    market: 'GOLD',
    publishedAt: '2026-10-16T11:36:00.000+03:30',
    claimStrength: 'STRONG',
    sourceIds: ['src-wgc-demand', 'src-lbma-vault'],
    marketImpactNoteFa: 'ادعای آماری؛ عددِ قیمت در این صفحه تولید نمی‌شود.',
    demo: false,
    status: 'LIVE',
    conflictId: null,
  },
  {
    id: 'nws-oil-0143',
    headlineFa: 'توقف موقت یک خط صادراتی در بندرِ جنوبی',
    headlineEn: 'Temporary halt on a southern export line',
    market: 'OIL',
    publishedAt: '2026-10-16T11:18:00.000+03:30',
    claimStrength: 'WEAK',
    sourceIds: ['src-port-authority', 'src-shipping-desk', 'src-argus-crude'],
    marketImpactNoteFa: 'منابع دربارهٔ حجم توقف اختلاف دارند؛ حل خودکار ممنوع.',
    demo: false,
    status: 'CONFLICT',
    conflictId: 'cfl-oil-0143-volume',
  },
  {
    id: 'nws-gold-0099',
    headlineFa: 'گزارش ماهانه از افت تقاضای فیزیکی طلا در آسیا خبر می‌دهد',
    headlineEn: 'Monthly report flags softer physical gold demand in Asia',
    market: 'GOLD',
    publishedAt: '2026-10-16T10:25:00.000+03:30',
    claimStrength: 'MODERATE',
    sourceIds: ['src-wgc-demand'],
    marketImpactNoteFa: 'تک‌منبعی؛ هرگز «تأیید‌شده» نیست.',
    demo: false,
    status: 'LIVE',
    conflictId: null,
  },
  {
    id: 'nws-oil-0144',
    headlineFa: 'گزارش هفتگی موجودی نفت خام منتشر شد',
    headlineEn: 'Weekly crude inventory report published',
    market: 'OIL',
    publishedAt: '2026-10-16T08:50:00.000+03:30',
    claimStrength: 'STRONG',
    sourceIds: ['src-eia-weekly', 'src-argus-crude'],
    marketImpactNoteFa: 'یکی از دو منبع کهنه است؛ سطح تأیید پایین می‌آید.',
    demo: false,
    status: 'LIVE',
    conflictId: null,
  },
  {
    id: 'nws-gold-0100',
    headlineFa: 'دو گزارش دربارهٔ خروج سرمایه از صندوق‌های طلا اختلاف دارند',
    headlineEn: 'Two reports disagree on gold ETF outflows',
    market: 'GOLD',
    publishedAt: '2026-10-16T06:55:00.000+03:30',
    claimStrength: 'MODERATE',
    sourceIds: ['src-platts-metals', 'src-lbma-vault'],
    marketImpactNoteFa: 'اختلافِ عددی باز است؛ برای قاضی علامت‌گذاری شده.',
    demo: false,
    status: 'CONFLICT',
    conflictId: 'cfl-gold-0100-outflow',
  },
  {
    id: 'nws-oil-0145',
    headlineFa: 'یادداشت آژانس بین‌المللی انرژی دربارهٔ چشم‌انداز تقاضا',
    headlineEn: 'IEA note on the demand outlook',
    market: 'OIL',
    publishedAt: '2026-10-16T04:20:00.000+03:30',
    claimStrength: 'MODERATE',
    sourceIds: ['src-iea-monthly', 'src-platts-metals'],
    marketImpactNoteFa: 'ادعای تحلیلی است، نه سیگنال معاملاتی.',
    demo: false,
    status: 'LIVE',
    conflictId: null,
  },
  {
    id: 'nws-oil-0146',
    headlineFa: 'بازنشرِ شایعه دربارهٔ مذاکرات صادراتی (رد شده)',
    // No English headline for this row on purpose: the UI must render MISSING,
    // not an empty string and not a machine translation.
    headlineEn: null,
    market: 'OIL',
    publishedAt: '2026-10-15T08:00:00.000+03:30',
    claimStrength: 'UNKNOWN',
    sourceIds: ['src-rumour-channel'],
    marketImpactNoteFa: 'در غربال رد شد. فقط برای حسابرسی نمایش داده می‌شود.',
    demo: false,
    status: 'REJECTED',
    conflictId: null,
  },
  {
    id: 'nws-gold-0101',
    headlineFa: 'جدول واردات طلا منتشر نشده است',
    headlineEn: 'Gold import table not published',
    market: 'GOLD',
    publishedAt: null,
    claimStrength: 'UNKNOWN',
    sourceIds: ['src-imports-customs'],
    marketImpactNoteFa: 'زمان انتشار نامعلوم؛ عددی ساخته نمی‌شود.',
    demo: false,
    status: 'UNKNOWN',
    conflictId: null,
  },
  {
    id: 'nws-demo-0001',
    headlineFa: 'خبرِ آزمایشیِ طلا (دادهٔ شبیه‌ساز)',
    headlineEn: 'Sample gold story (simulator data)',
    market: 'GOLD',
    publishedAt: '2026-10-16T11:40:00.000+03:30',
    claimStrength: 'WEAK',
    sourceIds: ['src-simulator', 'src-lbma-vault'],
    marketImpactNoteFa: 'دادهٔ دمو؛ از همهٔ مجموع‌ها حذف شده است.',
    demo: true,
    status: 'DEMO',
    conflictId: null,
  },
];

/* -------------------------------------------------------------------------- */
/* Conflicts                                                                   */
/* -------------------------------------------------------------------------- */

export const FIXTURE_CONFLICTS: Conflict[] = [
  {
    id: 'cfl-oil-0143-volume',
    storyId: 'nws-oil-0143',
    topicFa: 'حجم توقف خط صادراتی',
    claimA: {
      sourceId: 'src-port-authority',
      claimFa: 'توقف کاملِ بارگیری تا اطلاع ثانوی',
      value: 'بدون عدد رسمی',
      reportedAt: '2026-10-16T11:18:00.000+03:30',
    },
    claimB: {
      sourceId: 'src-shipping-desk',
      claimFa: 'بارگیری با ظرفیت کاهش‌یافته ادامه دارد',
      value: 'ظرفیت حدود نیمی از حالت عادی',
      reportedAt: '2026-10-16T11:24:00.000+03:30',
    },
    status: 'CONFLICT',
    detectedAt: '2026-10-16T11:26:00.000+03:30',
    noteFa: 'حل خودکار ممنوع؛ فقط قاضی تصمیم می‌گیرد.',
  },
  {
    id: 'cfl-gold-0100-outflow',
    storyId: 'nws-gold-0100',
    topicFa: 'میزان خروج سرمایه از صندوق‌ها',
    claimA: {
      sourceId: 'src-platts-metals',
      claimFa: 'خروج قابل‌توجه در هفتهٔ گذشته',
      value: 'گزارش‌شده: بزرگ',
      reportedAt: '2026-10-16T06:55:00.000+03:30',
    },
    claimB: {
      sourceId: 'src-lbma-vault',
      claimFa: 'خروج اندک و در محدودهٔ نوسان',
      value: 'گزارش‌شده: کوچک',
      reportedAt: '2026-10-16T07:10:00.000+03:30',
    },
    status: 'CONFLICT',
    detectedAt: '2026-10-16T07:12:00.000+03:30',
    noteFa: 'اختلافِ مقیاس؛ هر دو منبع زنده‌اند و هیچ‌کدام ترجیح ندارد.',
  },
];

/* -------------------------------------------------------------------------- */
/* Reporters                                                                   */
/* -------------------------------------------------------------------------- */

export const FIXTURE_REPORTERS: ReporterAgent[] = [
  {
    id: 'rpt-wire-01',
    nameFa: 'خبرنگار وایر · یک',
    codeEn: 'wire-rpt-01',
    role: 'wire',
    status: 'LIVE',
    lastRunAt: '2026-10-16T11:58:00.000+03:30',
    attempts: 148,
    pass: 145,
    fail: 3,
    noteFa: 'آخرین اجرا موفق',
  },
  {
    id: 'rpt-energy-01',
    nameFa: 'خبرنگار انرژی · یک',
    codeEn: 'energy-rpt-01',
    role: 'energy',
    status: 'LIVE',
    lastRunAt: '2026-10-16T11:56:00.000+03:30',
    attempts: 96,
    pass: 94,
    fail: 2,
    noteFa: 'آخرین اجرا موفق',
  },
  {
    id: 'rpt-metals-01',
    nameFa: 'خبرنگار فلزات · یک',
    codeEn: 'metals-rpt-01',
    role: 'metals',
    status: 'STALE',
    lastRunAt: '2026-10-16T02:40:00.000+03:30',
    attempts: 88,
    pass: 81,
    fail: 7,
    noteFa: 'آخرین اجرا کهنه است',
  },
  {
    id: 'rpt-macro-01',
    nameFa: 'خبرنگار کلان · یک',
    codeEn: 'macro-rpt-01',
    role: 'macro',
    status: 'LIVE',
    lastRunAt: '2026-10-16T11:50:00.000+03:30',
    attempts: 61,
    pass: 60,
    fail: 1,
    noteFa: 'آخرین اجرا موفق',
  },
  {
    id: 'rpt-wire-02',
    nameFa: 'خبرنگار وایر · دو (ذخیره)',
    codeEn: 'wire-rpt-02',
    role: 'wire',
    status: 'UNKNOWN',
    lastRunAt: null,
    attempts: null,
    pass: null,
    fail: null,
    noteFa: 'زمانِ اجرا نامعلوم؛ شمارنده‌ای ساخته نمی‌شود',
  },
  {
    id: 'rpt-metals-02',
    nameFa: 'خبرنگار فلزات · دو (پشتیبان)',
    codeEn: 'metals-rpt-02',
    role: 'metals',
    status: 'DEMO',
    lastRunAt: '2026-10-16T11:58:00.000+03:30',
    attempts: 12,
    pass: 12,
    fail: 0,
    noteFa: 'عاملِ شبیه‌ساز · دادهٔ دمو',
  },
];

/* -------------------------------------------------------------------------- */
/* Pipeline (per-story; the snapshot carries the default / first story's run)   */
/* -------------------------------------------------------------------------- */

export const FIXTURE_PIPELINE: PipelineStage[] = [
  {
    id: 'INGEST',
    labelFa: 'دریافت',
    labelEn: 'INGEST',
    state: 'DONE',
    completedAt: '2026-10-16T11:52:00.000+03:30',
    detailFa: 'خبر از دو منبعِ زنده دریافت شد',
  },
  {
    id: 'TRIAGE',
    labelFa: 'غربال',
    labelEn: 'TRIAGE',
    state: 'DONE',
    completedAt: '2026-10-16T11:53:00.000+03:30',
    detailFa: 'بازار نفت · ادعای رویدادی',
  },
  {
    id: 'TWO_SOURCE_CHECK',
    labelFa: 'بررسی دومنبعی',
    labelEn: 'TWO_SOURCE_CHECK',
    state: 'DONE',
    completedAt: '2026-10-16T11:54:00.000+03:30',
    detailFa: 'دو منبعِ مستقل با ردهٔ A',
  },
  {
    id: 'CONFLICT_SCAN',
    labelFa: 'پویش تعارض',
    labelEn: 'CONFLICT_SCAN',
    state: 'DONE',
    completedAt: '2026-10-16T11:55:00.000+03:30',
    detailFa: 'هیچ تعارضی یافت نشد',
  },
  {
    id: 'JUDGE_HANDOFF',
    labelFa: 'تحویل به قاضی',
    labelEn: 'JUDGE_HANDOFF',
    state: 'PLANNED',
    completedAt: null,
    detailFa: 'در انتظار اپراتور · فقط‌خواندنی',
  },
];

/* -------------------------------------------------------------------------- */
/* Snapshots                                                                   */
/* -------------------------------------------------------------------------- */

export const CALM_SNAPSHOT: NewsroomSnapshot = {
  executionMode: 'PAPER_ONLY',
  realTrading: false,
  generatedAt: FIXTURE_NOW,
  markets: FIXTURE_MARKETS,
  stories: FIXTURE_STORIES,
  sources: FIXTURE_SOURCES,
  conflicts: FIXTURE_CONFLICTS,
  reporters: FIXTURE_REPORTERS,
  pipeline: FIXTURE_PIPELINE,
  freshness: {
    storiesAt: FIXTURE_NOW,
    sourcesAt: '2026-10-16T11:58:00.000+03:30',
    conflictsAt: '2026-10-16T07:12:00.000+03:30',
    reportersAt: '2026-10-16T11:58:00.000+03:30',
  },
  telemetry: {
    lastSourceId: 'src-reuters-energy',
    lastReadAt: '2026-10-16T11:58:00.000+03:30',
    storyCount: FIXTURE_STORIES.length,
    demoCount: FIXTURE_STORIES.filter((s) => s.demo).length,
    conflictCount: FIXTURE_CONFLICTS.length,
    adapter: 'mock:newsroom-fixtures',
  },
};

/** EMPTY — the pipeline ran, nothing matched. No invented rows. */
export const EMPTY_SNAPSHOT: NewsroomSnapshot = {
  ...CALM_SNAPSHOT,
  stories: [],
  conflicts: [],
  pipeline: [
    { ...FIXTURE_PIPELINE[0]!, state: 'DONE', detailFa: 'منابع خوانده شدند' },
    { ...FIXTURE_PIPELINE[1]!, state: 'DONE', detailFa: 'هیچ خبری با پالایهٔ جاری مطابقت نداشت' },
    { ...FIXTURE_PIPELINE[2]!, state: 'PLANNED', completedAt: null, detailFa: 'خبری برای بررسی نیست' },
    { ...FIXTURE_PIPELINE[3]!, state: 'PLANNED', completedAt: null, detailFa: 'اجرا نشده' },
    { ...FIXTURE_PIPELINE[4]!, state: 'PLANNED', completedAt: null, detailFa: 'اجرا نشده' },
  ],
  telemetry: {
    ...CALM_SNAPSHOT.telemetry,
    storyCount: 0,
    demoCount: 0,
    conflictCount: 0,
    adapter: 'mock:newsroom-empty',
  },
};

/** UNAVAILABLE — every source unreadable. Truth stays UNKNOWN. */
export const UNAVAILABLE_SNAPSHOT: NewsroomSnapshot = {
  ...CALM_SNAPSHOT,
  sources: FIXTURE_SOURCES.map((s) => ({
    ...s,
    status: 'UNKNOWN' as const,
    lastReadAt: null,
    noteFa: 'پاسخی دریافت نشد · وضعیت UNKNOWN',
  })),
  stories: FIXTURE_STORIES.map((s) => ({
    ...s,
    status: 'UNKNOWN' as const,
    publishedAt: s.publishedAt,
  })),
  conflicts: [],
  pipeline: [
    { ...FIXTURE_PIPELINE[0]!, state: 'UNKNOWN', completedAt: null, detailFa: 'منبعی خوانده نشد' },
    { ...FIXTURE_PIPELINE[1]!, state: 'PLANNED', completedAt: null, detailFa: 'اجرا نشده' },
    { ...FIXTURE_PIPELINE[2]!, state: 'PLANNED', completedAt: null, detailFa: 'اجرا نشده' },
    { ...FIXTURE_PIPELINE[3]!, state: 'PLANNED', completedAt: null, detailFa: 'اجرا نشده' },
    { ...FIXTURE_PIPELINE[4]!, state: 'PLANNED', completedAt: null, detailFa: 'اجرا نشده' },
  ],
  freshness: {
    storiesAt: null,
    sourcesAt: null,
    conflictsAt: null,
    reportersAt: null,
  },
  telemetry: {
    lastSourceId: null,
    lastReadAt: null,
    storyCount: FIXTURE_STORIES.length,
    demoCount: FIXTURE_STORIES.filter((s) => s.demo).length,
    conflictCount: 0,
    adapter: 'mock:newsroom-unavailable',
  },
};

/** VIOLATION — the guard rail demo. Never shippable as a live configuration. */
export const VIOLATION_SNAPSHOT: NewsroomSnapshot = {
  ...CALM_SNAPSHOT,
  executionMode: 'LIVE',
  realTrading: true,
  telemetry: { ...CALM_SNAPSHOT.telemetry, adapter: 'mock:newsroom-violation' },
};
