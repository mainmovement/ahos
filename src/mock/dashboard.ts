import type {
  DashboardSnapshot,
  MarketAsset,
  Candle,
  DemoAnswer,
} from "../lib/api/types";

// Synthetic fixture, not a market observation. All values share this fixed timestamp.
export const provenance = {
  source: "AHOS / synthetic-fixture-v1",
  retrievedAt: "2026-10-16T08:00:00.000Z",
  status: "DEMO" as const,
};
export const dashboard: DashboardSnapshot = {
  provenance,
  metrics: [
    {
      id: "universe",
      title: { fa: "دارایی‌های رصدشده", en: "Assets monitored" },
      value: "247",
      change: "+12.4%",
      note: { fa: "در سناریوی نمونه", en: "in demo scenario" },
      tone: "gold",
      trend: [28, 32, 30, 41, 36, 43, 39, 50, 47, 59, 57, 68],
    },
    {
      id: "evidence",
      title: { fa: "شواهد بررسی‌شده", en: "Evidence reviewed" },
      value: "68",
      change: "+8",
      note: { fa: "نسبت به نمونهٔ قبل", en: "vs previous fixture" },
      tone: "green",
      trend: [22, 26, 25, 29, 35, 33, 42, 39, 48, 52, 51, 59],
    },
    {
      id: "monitor",
      title: { fa: "در انتظار بررسی", en: "Pending review" },
      value: "43",
      change: "17.4%",
      note: { fa: "از مجموعهٔ نمونه", en: "of demo universe" },
      tone: "cyan",
      trend: [36, 34, 43, 41, 50, 42, 47, 44, 48, 42, 45, 43],
    },
    {
      id: "rejected",
      title: { fa: "موارد ردشده", en: "Rejected cases" },
      value: "36",
      change: "14.6%",
      note: { fa: "تصمیم نمونه، نه توصیه", en: "fixture, not advice" },
      tone: "danger",
      trend: [15, 14, 21, 17, 26, 24, 29, 27, 32, 29, 34, 36],
    },
    {
      id: "agents",
      title: { fa: "عامل‌های ثبت‌شده", en: "Registered agents" },
      value: "19",
      change: "04",
      note: { fa: "عامل در این سناریو", en: "agents in this scenario" },
      tone: "gold",
      trend: [3, 3, 5, 5, 8, 8, 10, 12, 12, 15, 17, 19],
    },
    {
      id: "paper",
      title: { fa: "بازده سبد آزمایشی", en: "Paper portfolio return" },
      value: "+4.76%",
      change: "+$476",
      note: {
        fa: "سرمایهٔ فرضی ۱۰٬۰۰۰ دلار",
        en: "on $10,000 virtual capital",
      },
      tone: "green",
      trend: [15, 18, 16, 25, 21, 30, 27, 35, 31, 43, 41, 49],
    },
  ],
  agents: [
    {
      id: "AG-01",
      name: { fa: "دیده‌بان بازار", en: "Market Scout" },
      role: { fa: "گردآوری شواهد", en: "Evidence collection" },
      department: { fa: "هوشمندی بازار", en: "Market intelligence" },
      state: "running",
      implementation: {
        fa: "فقط سناریوی نمایشی؛ پردازشی اجرا نمی‌شود",
        en: "Demo fixture only; no process is running",
      },
      task: {
        fa: "مقایسهٔ حجم معاملات سه دارایی",
        en: "Compare volume across three assets",
      },
      activityAt: "07:58 UTC",
      evidence: "DEMO-EV-014",
      progress: 72,
    },
    {
      id: "AG-02",
      name: { fa: "پژوهشگر زنجیره", en: "Chain Researcher" },
      role: { fa: "تحلیل دادهٔ زنجیره", en: "On-chain research" },
      department: { fa: "مؤسسه پژوهش", en: "Research institute" },
      state: "registered",
      implementation: {
        fa: "ثبت نمایشی؛ بدون اتصال به اجرا",
        en: "Demo registration; runtime disconnected",
      },
      task: { fa: "در انتظار تخصیص مأموریت", en: "Awaiting task assignment" },
      activityAt: "07:52 UTC",
      evidence: "DEMO-EV-009",
      progress: 0,
    },
    {
      id: "AG-03",
      name: { fa: "نگهبان ریسک", en: "Risk Sentinel" },
      role: { fa: "کنترل کیفیت شواهد", en: "Evidence quality checks" },
      department: { fa: "امنیت و ریسک", en: "Security & risk" },
      state: "blocked",
      implementation: {
        fa: "مانع شبیه‌سازی‌شده",
        en: "Simulated blocked state",
      },
      task: {
        fa: "هویت قرارداد تأیید نشده است",
        en: "Contract identity is unconfirmed",
      },
      activityAt: "07:49 UTC",
      evidence: "DEMO-EV-006",
      progress: 35,
    },
    {
      id: "AG-04",
      name: { fa: "تحلیل‌گر پژوهش", en: "Research Analyst" },
      role: { fa: "ارزیابی فرضیه", en: "Hypothesis evaluation" },
      department: { fa: "دانشگاه", en: "University" },
      state: "planned",
      implementation: {
        fa: "پیشنهاد نمایشی؛ پیاده‌سازی نشده",
        en: "Demo proposal; not implemented",
      },
      task: {
        fa: "برنامهٔ آزمون و بازآموزی",
        en: "Evaluation and retraining plan",
      },
      activityAt: "07:30 UTC",
      evidence: "DEMO-PLAN-004",
      progress: 0,
    },
  ],
  alerts: [
    {
      id: "AL-01",
      title: { fa: "شواهد هویتی ناکافی", en: "Insufficient identity evidence" },
      body: {
        fa: "هویت قرارداد نمونه تأیید نشده؛ وضعیت نامشخص به معنای امن نیست.",
        en: "Demo contract identity is unconfirmed. Unknown does not mean safe.",
      },
      severity: "warning",
      time: "07:49",
    },
    {
      id: "AL-02",
      title: { fa: "دادهٔ طلا قدیمی است", en: "Gold data is stale" },
      body: {
        fa: "در این سناریو، آخرین نمونه از محدودهٔ تازگی عبور کرده است.",
        en: "In this scenario, the last sample is outside the freshness threshold.",
      },
      severity: "unknown",
      time: "07:42",
    },
  ],
  news: [
    {
      id: "N-01",
      title: {
        fa: "افزایش توجه پژوهشگران به زیرساخت‌های لایهٔ دوم",
        en: "Researchers turn to layer-two infrastructure",
      },
      category: { fa: "فناوری", en: "Technology" },
      verification: "verified",
      time: "07:55",
      sources: 3,
      body: {
        fa: "خبر کاملاً ساختگی برای نمایش فرایند تطبیق سه منبع. هیچ رویداد واقعی را گزارش نمی‌کند.",
        en: "Fictional story demonstrating a three-source verification workflow. Not a report of a real event.",
      },
    },
    {
      id: "N-02",
      title: {
        fa: "بررسی سناریوی عرضهٔ انرژی در بازار جهانی",
        en: "A global energy-supply scenario under review",
      },
      category: { fa: "انرژی", en: "Energy" },
      verification: "unverified",
      time: "07:40",
      sources: 1,
      body: {
        fa: "نمونهٔ آموزشی با یک منبع فرضی؛ برای نتیجه‌گیری به شواهد بیشتری نیاز است.",
        en: "Educational sample with one hypothetical source. Additional evidence is required.",
      },
    },
    {
      id: "N-03",
      title: {
        fa: "اختلاف داده میان دو گزارش حجم معاملات",
        en: "Two volume reports present conflicting data",
      },
      category: { fa: "بازار", en: "Markets" },
      verification: "conflicting",
      time: "07:21",
      sources: 2,
      body: {
        fa: "دو گزارش ساختگی ناسازگار هستند. اختلاف حفظ می‌شود و تأیید خودکار انجام نمی‌گیرد.",
        en: "Two synthetic reports disagree. Conflict is retained; automatic verification is withheld.",
      },
    },
  ],
  positions: [
    {
      id: "P-01",
      symbol: "BTC",
      quantity: 0.04,
      entry: 67200,
      mark: 68425,
      risk: 1.2,
    },
    {
      id: "P-02",
      symbol: "ETH",
      quantity: 0.8,
      entry: 2480,
      mark: 2615,
      risk: 0.8,
    },
    {
      id: "P-03",
      symbol: "SOL",
      quantity: 10,
      entry: 128.5,
      mark: 142.3,
      risk: 1.5,
    },
  ],
  system: [
    { name: "CPU", value: 24, unit: "%" },
    { name: "Memory", value: 41, unit: "%" },
    { name: "Storage", value: 18, unit: "%" },
  ],
  university: {
    passed: 14,
    failed: 3,
    queued: 2,
    courses: [
      { fa: "تشخیص تعارض شواهد", en: "Evidence conflict detection" },
      { fa: "ارزیابی ریسک نقدشوندگی", en: "Liquidity risk evaluation" },
    ],
  },
};

// Deterministic synthetic series: no random jitter, no live simulation.
const series = (base: number, volatility: number) =>
  Array.from(
    { length: 48 },
    (_, i) =>
      +(
        base *
        (1 +
          Math.sin(i * 0.55) * volatility +
          Math.sin(i * 1.8) * volatility * 0.2 +
          (i * volatility) / 15)
      ).toFixed(2),
  );
export const markets: MarketAsset[] = [
  {
    symbol: "BTC",
    name: { fa: "بیت‌کوین", en: "Bitcoin" },
    category: "crypto",
    price: 68425,
    change: 2.84,
    volume: "28.4B",
    freshness: "DEMO",
    history: series(66000, 0.012),
    unit: "USD",
  },
  {
    symbol: "ETH",
    name: { fa: "اتریوم", en: "Ethereum" },
    category: "crypto",
    price: 2615,
    change: 1.62,
    volume: "12.8B",
    freshness: "DEMO",
    history: series(2510, 0.013),
    unit: "USD",
  },
  {
    symbol: "SOL",
    name: { fa: "سولانا", en: "Solana" },
    category: "crypto",
    price: 142.3,
    change: 4.21,
    volume: "2.1B",
    freshness: "DEMO",
    history: series(131, 0.02),
    unit: "USD",
  },
  {
    symbol: "XAU",
    name: { fa: "طلای جهانی", en: "Spot Gold" },
    category: "gold",
    price: 2658.4,
    change: 0.73,
    volume: "184M",
    freshness: "STALE",
    history: series(2590, 0.008),
    unit: "USD / oz",
  },
  {
    symbol: "BRENT",
    name: { fa: "نفت برنت", en: "Brent Crude" },
    category: "oil",
    price: 74.82,
    change: -1.12,
    volume: "92M",
    freshness: "DEMO",
    history: series(76, -0.005),
    unit: "USD / bbl",
  },
  {
    symbol: "SPX",
    name: { fa: "اس‌اندپی ۵۰۰", en: "S&P 500" },
    category: "us",
    price: 5815.3,
    change: 0.48,
    volume: "4.2B",
    freshness: "DEMO",
    history: series(5740, 0.004),
    unit: "points",
  },
  {
    symbol: "DAX",
    name: { fa: "دکس آلمان", en: "DAX" },
    category: "eu",
    price: 19465,
    change: -0.32,
    volume: "1.7B",
    freshness: "DEMO",
    history: series(19520, -0.003),
    unit: "points",
  },
  {
    symbol: "N225",
    name: { fa: "نیکی ژاپن", en: "Nikkei 225" },
    category: "asia",
    price: 38981,
    change: 0.65,
    volume: "2.6B",
    freshness: "UNKNOWN",
    history: series(38500, 0.004),
    unit: "points",
  },
];
// Anchor the synthetic close to the displayed fixture quote.
markets.forEach(asset => { const factor = asset.price / asset.history[asset.history.length - 1]; asset.history = asset.history.map(value => +(value * factor).toFixed(2)); });

export function fixtureCandles(symbol: string): Candle[] {
  const asset = markets.find((item) => item.symbol === symbol) ?? markets[0];
  return asset.history.map((close, i, values) => {
    const open = values[Math.max(0, i - 1)];
    return {
      time: `${String(Math.floor(i / 2)).padStart(2, "0")}:${i % 2 ? "30" : "00"}`,
      open,
      close,
      high: +(Math.max(open, close) * 1.002).toFixed(2),
      low: +(Math.min(open, close) * 0.998).toFixed(2),
      volume: 180 + ((i * 137) % 420),
    };
  });
}
export const answers: Record<
  "risk" | "market" | "agents" | "default",
  DemoAnswer
> = {
  risk: {
    answer: {
      fa: "در سناریوی نمونه، هویت یک قرارداد نامشخص است و دادهٔ طلا قدیمی است. نامشخص ≠ امن. این متن پاسخ از پیش نوشته‌شده است، نه تحلیل زنده یا توصیهٔ سرمایه‌گذاری.",
      en: "This fixture has an unconfirmed contract identity and stale gold data. Unknown ≠ safe. This is a scripted response, not live analysis or investment advice.",
    },
    source: "DEMO / alerts fixture",
  },
  market: {
    answer: {
      fa: "در دادهٔ ساختگی، تغییر بیت‌کوین ‎+۲٫۸۴٪ و برنت ‎−۱٫۱۲٪ است. این اعداد قیمت واقعی نیستند. برای جزئیات، دارایی را در جدول انتخاب کنید.",
      en: "Synthetic changes: Bitcoin +2.84%, Brent −1.12%. These are not real prices. Select an asset in the table to explore the fixture.",
    },
    source: "DEMO / markets fixture",
  },
  agents: {
    answer: {
      fa: "چهار عامل نمایشی در این صفحه وجود دارد: در حال اجرا، ثبت‌شده، مسدود و برنامه‌ریزی‌شده. هیچ عامل واقعی اجرا نمی‌شود. برای مشاهدهٔ نقش و مأموریت، روی عامل بزنید.",
      en: "Four demo agents illustrate running, registered, blocked and planned states. No real agents are executing. Select an agent to inspect its role and task.",
    },
    source: "DEMO / agents fixture",
  },
  default: {
    answer: {
      fa: "من در این نسخه یک دستیار نمایشی با پاسخ‌های محدود هستم، نه مدل هوش مصنوعی متصل. می‌توانید دربارهٔ بازار، ریسک یا عامل‌ها بپرسید. هیچ دستور یا معامله‌ای اجرا نمی‌کنم.",
      en: "I am a limited scripted demo, not a connected AI model. Ask about markets, risk or agents. I cannot execute instructions or trades.",
    },
    source: "DEMO / scripted assistant",
  },
};
