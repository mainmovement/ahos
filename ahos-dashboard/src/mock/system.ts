/** MOCK — system/runtime, errors, notifications and alerts. */
import type { AlertItem, AppNotification, ErrorsOverview, SystemOverview } from "@/lib/api/types";
import { HOUR, L, MINUTE, bounded, minutesAgo, series } from "./_seed";
import { mockProviders } from "./security";

export function mockSystem(now = Date.now()): SystemOverview {
  return {
    mode: "PAPER_ONLY",
    services: [
      { id: "engine", name: L("موتور چرخه (Next.js)", "Cycle engine (Next.js)"), kind: "process", state: "UP", uptimeSec: 44_160, version: "W44", lastHeartbeat: minutesAgo(0.2, now) },
      { id: "python", name: L("مرجع کانونی پایتون", "Python canonical authority"), kind: "process", state: "UP", uptimeSec: 44_020, version: "lane-b", lastHeartbeat: minutesAgo(0.5, now) },
      { id: "research", name: L("کارگر پژوهشی ایزوله", "Isolated research worker"), kind: "process", state: "UP", uptimeSec: 12_400, version: "2b", lastHeartbeat: minutesAgo(1, now) },
      { id: "postgres", name: L("پایگاه داده PostgreSQL", "PostgreSQL database"), kind: "database", state: "UP", uptimeSec: 302_400, version: "16", lastHeartbeat: minutesAgo(0.3, now) },
      { id: "telegram", name: L("ربات تلگرام", "Telegram bot"), kind: "edge", state: "NOT_CONFIGURED", uptimeSec: null, version: null, lastHeartbeat: null, note: L("توکن BotFather لازم است", "BotFather token required") },
      { id: "n8n", name: L("خودکارسازی n8n", "n8n automation"), kind: "automation", state: "UNKNOWN", uptimeSec: null, version: null, lastHeartbeat: null, note: L("عملیاتی بودن ادعا نشده", "Operational status not claimed") },
      { id: "translate", name: L("سرویس ترجمه", "Translation service"), kind: "external", state: "DEGRADED", uptimeSec: null, version: null, lastHeartbeat: minutesAgo(18, now), note: L("محدودیت سهمیه", "Quota limited") },
    ],
    providers: mockProviders(now),
    cpu: bounded("sys:cpu", 60, 18, 64, MINUTE, now),
    memory: bounded("sys:mem", 60, 52, 71, MINUTE, now),
    latency: bounded("sys:lat", 60, 120, 640, MINUTE, now),
    uptimeSec: 44_160,
    build: { version: "0.1.0-demo", commit: "ee325ea", builtAt: new Date(now - 2 * HOUR).toISOString() },
    laneA: { state: "PASS", checkedAt: minutesAgo(35, now) },
    evidenceFreshnessSec: 128,
    classification: "INTEGRATION_READY",
  };
}

export function mockErrors(now = Date.now()): ErrorsOverview {
  return {
    incidents: [
      { id: "ERR-311", title: L("وقفه زمانی GeckoTerminal", "GeckoTerminal timeout burst"), component: "providers.ts", errorType: "TIMEOUT", severity: "MEDIUM", stage: "RECOVERING", detectedAt: minutesAgo(26, now), updatedAt: minutesAgo(3, now), retries: 4, recovery: L("کاهش هم‌روندی و بک‌آف نمایی", "Reduced concurrency + exponential backoff"), owner: "agent.discovery-scout" },
      { id: "ERR-310", title: L("سهمیه ترجمه تمام شد", "Translation quota exhausted"), component: "news.ts", errorType: "RATE_LIMITED", severity: "LOW", stage: "DIAGNOSING", detectedAt: minutesAgo(18, now), updatedAt: minutesAgo(5, now), retries: 2, recovery: L("صف‌بندی تا بازنشانی سهمیه", "Queue until quota reset"), owner: "agent.news-pipeline" },
      { id: "ERR-309", title: L("اتصال ربات تلگرام ناموفق", "Telegram bot connect failed"), component: "telegram_ai", errorType: "AUTH_FAILED", severity: "HIGH", stage: "ESCALATED", detectedAt: minutesAgo(95, now), updatedAt: minutesAgo(90, now), retries: 3, recovery: L("نیازمند اقدام مالک: توکن BotFather", "Owner action required: BotFather token"), owner: "human" },
      { id: "ERR-308", title: L("تعارض هویت PEPE2", "PEPE2 identity conflict"), component: "architecture/identity", errorType: "IDENTITY_CONFLICT", severity: "MEDIUM", stage: "VERIFYING", detectedAt: minutesAgo(130, now), updatedAt: minutesAgo(20, now), retries: 0, recovery: L("REJECT ایمن تا رفع تعارض", "Fail-closed REJECT until resolved"), owner: "agent.org.10-token-security-scam-intelligence" },
      { id: "ERR-307", title: L("شبکه TON در دسترس نیست", "TON network unavailable"), component: "providers.ts", errorType: "NETWORK_UNAVAILABLE", severity: "LOW", stage: "TRIAGED", detectedAt: minutesAgo(60 * 72, now), updatedAt: minutesAgo(60, now), retries: 18, recovery: L("علامت‌گذاری STALE و توقف تصمیم", "Marked STALE, decisions withheld"), owner: "agent.discovery-scout" },
      { id: "ERR-306", title: L("خطای تجزیه RSS نیکی", "Nikkei RSS parse error"), component: "news.ts", errorType: "PARSE_ERROR", severity: "LOW", stage: "RESOLVED", detectedAt: minutesAgo(60 * 5, now), updatedAt: minutesAgo(60 * 4, now), retries: 1, recovery: L("به‌روزرسانی انتخابگر", "Selector updated"), owner: "agent.news-pipeline" },
      { id: "ERR-305", title: L("تأخیر پایگاه داده > ۲ ثانیه", "DB latency > 2s"), component: "postgres", errorType: "LATENCY", severity: "MEDIUM", stage: "DETECTED", detectedAt: minutesAgo(2, now), updatedAt: minutesAgo(2, now), retries: 0, recovery: L("در انتظار تریاژ", "Awaiting triage"), owner: "agent.org.14-agent-runtime-engineering" },
    ],
    mttrMinutes: 47,
    trend: series("err:trend", 24, 7, HOUR, 0.18, 0, now, 0),
  };
}

export function mockNotifications(now = Date.now()): AppNotification[] {
  return [
    { id: "nt1", title: L("هشدار امنیتی: هانی‌پات", "Security: honeypot detected"), body: L("PEPE2 روی اتریوم رد شد (REJECT).", "PEPE2 on Ethereum was rejected."), severity: "HIGH", at: minutesAgo(4, now), read: false, href: "/security" },
    { id: "nt2", title: L("خط لوله خبر مسدود شد", "News pipeline blocked"), body: L("سهمیه ترجمه تمام شده است.", "Translation quota exhausted."), severity: "MEDIUM", at: minutesAgo(18, now), read: false, href: "/news" },
    { id: "nt3", title: L("آزمون دانشگاه: مردود", "University exam: FAIL"), body: L("خط لوله خبر در آزمون تشخیص تناقض مردود شد.", "News pipeline failed the conflict-detection exam."), severity: "LOW", at: minutesAgo(300, now), read: false, href: "/university" },
    { id: "nt4", title: L("نامزد کاغذی جدید", "New paper candidate"), body: L("AEROX توسط مرجع کانونی مجاز شد (کاغذی).", "AEROX allowed by canonical authority (paper)."), severity: "INFO", at: minutesAgo(360, now), read: true, href: "/opportunities" },
    { id: "nt5", title: L("اقدام مالک لازم است", "Owner action required"), body: L("توکن ربات تلگرام تنظیم نشده است.", "Telegram bot token is not configured."), severity: "HIGH", at: minutesAgo(90, now), read: true, href: "/errors" },
  ];
}

export function mockAlerts(now = Date.now()): AlertItem[] {
  return [
    { id: "al1", tier: "SECURITY", title: L("هانی‌پات — PEPE2", "Honeypot — PEPE2"), detail: L("مالیات فروش ۹۹٪، مالکیت باز", "99% sell tax, open ownership"), symbol: "PEPE2", at: minutesAgo(4, now), status: "DEMO" },
    { id: "al2", tier: "HIGH_ATTENTION", title: L("حجم غیرعادی — SOL", "Unusual volume — SOL"), detail: L("حجم ۲٫۴ برابر میانگین ۷ روزه", "Volume 2.4× 7-day average"), symbol: "SOL", at: minutesAgo(11, now), status: "DEMO" },
    { id: "al3", tier: "WATCH", title: L("ورود به پایش — JUPX", "Entered WATCH — JUPX"), detail: L("تصمیم مرجع کانونی: WATCH", "Canonical decision: WATCH"), symbol: "JUPX", at: minutesAgo(23, now), status: "DEMO" },
    { id: "al4", tier: "INFO", title: L("داده کهنه — TONX", "Stale data — TONX"), detail: L("آخرین بررسی ۳ روز پیش؛ UNKNOWN ≠ امن", "Last check 3 days ago; UNKNOWN ≠ safe"), symbol: "TONX", at: minutesAgo(38, now), status: "STALE" },
  ];
}
