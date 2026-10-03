/**
 * Phase 7: pure chat intent helpers + router (no I/O, no decisions).
 *
 * Routing only decides WHICH read-only reply builder answers a message. It never
 * performs actions. GM-04: engine control and paper_buy detection stay in
 * chat_control_gate.ts and are checked before any new intent, so the gate in
 * chat.ts still sees (and refuses + audits) every control command.
 *
 * chat.ts keeps `detectIntent()` as the entry point and passes the reject/why
 * predicates (their order is pinned by tests/test_canonical_read_model.py).
 */
import { detectControlCommand, looksLikePaperBuy } from "./chat_control_gate";
import { cleanSummaryFa } from "./dev_missions";
import { isNewsRequest, isStopLossQuestion } from "./chat_replies";

export type MajorAsset = "BTC" | "ETH" | "SOL";

/** Lowercase, Arabic→Persian letters, ZWNJ/tatweel → space/none, collapsed spaces. */
export function normalizeIntentText(text: string): string {
  return String(text ?? "")
    .normalize("NFKC")
    .replace(/[\u200b\u200d\u2060\ufeff]/g, "")
    .replace(/\u200c/g, " ")
    .replace(/\u0640/g, "")
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/[ۀة]/g, "ه")
    .replace(/[؟?!.,،:;«»"'()]/g, " ")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

const BTC_RE = /(بیت ?کو?ی?ی?ن|بیتکوین|\bbtc\b|\bbitcoin\b|\bxbt\b)/;
const ETH_RE = /(اتریوم|اتریم|\beth\b|\bethereum\b|\bether\b)/;
const SOL_RE = /(سولانا|\bsol\b|\bsolana\b)/;

/** First major asset mentioned (BTC/ETH/SOL), or null. Handles بیت کوین/بیتکوین/بیت کویین/BTC/bitcoin. */
export function detectMajorAsset(text: string): MajorAsset | null {
  const t = normalizeIntentText(text);
  const hits: Array<[MajorAsset, number]> = [];
  for (const [a, re] of [["BTC", BTC_RE], ["ETH", ETH_RE], ["SOL", SOL_RE]] as Array<[MajorAsset, RegExp]>) {
    const m = t.match(re);
    if (m && m.index !== undefined) hits.push([a, m.index]);
  }
  hits.sort((x, y) => x[1] - y[1]);
  return hits.length ? hits[0][0] : null;
}

const PRICE_WORD_RE = /(قیمت|چنده|چقدر|چقد|چند است|چند دلار|چند شد|چند شده|چند تومن|نرخ|\bprice\b|how much)/;

/** Latin ticker-like token (e.g. PEPE) — used for "price of <symbol>" questions. */
export function extractTicker(text: string): string | null {
  const m = String(text ?? "").match(/\b([A-Za-z][A-Za-z0-9]{1,11})\b/);
  if (!m) return null;
  const s = m[1].toUpperCase();
  if (["PRICE", "HOW", "MUCH", "USD", "USDT", "THE", "NOW"].includes(s)) return null;
  return s;
}

/** «قیمت بیت کویین الان چقدر هست؟», «BTC چنده», «price of eth» … */
export function isPriceQuestion(text: string): boolean {
  const t = normalizeIntentText(text);
  if (!PRICE_WORD_RE.test(t)) return false;
  return detectMajorAsset(text) !== null || extractTicker(text) !== null;
}

const TRADE_STRONG_RE =
  /(فیوچرز|فیوچر|فیچرز|فیوچرس|\bfutures?\b|اهرم|لوریج|لورج|\bleverage\b|\blong\b|\bshort\b|لانگ|شورت|(^| )سل( |$)|\bsell\b|حد سود|تارگت سود|تی پی|\btp\b|take ?profit|سیگنال|\bsignal\b|مارجین|\bmargin\b|چند درصد (?:بزنم|وارد|بذارم|بگذارم))/;
const PICK_RE = /(معرفی کن|معرفی کنید|پیشنهاد بده|پیشنهاد بدید|بهم بگو چی|کدوم ارز|کدام ارز|یه ارز|یک ارز|چی بخرم|چی بزنم)/;

/**
 * Requests for trading signals (leverage/futures, long/short, take-profit +
 * stop-loss, "pick me a coin and tell me the TP/SL"). PAPER_ONLY: never answered
 * with a signal. Takes priority over stop-loss and opportunities.
 */
export function isTradeSignalRequest(text: string): boolean {
  const t = normalizeIntentText(text);
  if (TRADE_STRONG_RE.test(t)) return true;
  const sl = isStopLossQuestion(t);
  if (PICK_RE.test(t) && (sl || /(سود|درصد)/.test(t))) return true;
  return false;
}

const THANKS_RE = /(مرسی|ممنون|ممنونم|سپاس|سپاسگزارم|تشکر|متشکرم|دمت گرم|دستت درد نکنه|\bthanks?\b|\bthank you\b|\bthx\b|\bmerci\b)/g;

/** True when the message is only a thank-you (no other question in it). */
export function isThanksOnly(text: string): boolean {
  const t = normalizeIntentText(text);
  if (!t.match(THANKS_RE)) return false;
  const rest = t.replace(THANKS_RE, " ").replace(/(خیلی|زیاد|عزیز|داداش|رفیق|جان|از|شما|تو|بابت|همه چی|ازت|ازتون|واقعا|یه دنیا|🙏|❤️|👍)/g, " ").replace(/\s+/g, "").trim();
  return rest.length <= 2;
}

const GREETING_HEAD_RE = /^(سلام|درود|هی|hello|hi|hey)(\s|$|[!.،,؟?])/i;

/** Strips a leading greeting ("سلام، قیمت BTC چنده؟" → "قیمت BTC چنده؟"); "" when only a greeting. */
export function stripGreeting(text: string): string {
  let t = String(text ?? "").trim();
  if (!GREETING_HEAD_RE.test(t)) return t;
  t = t.replace(/^(سلام|درود|هی|hello|hi|hey)[\s!.،,؟?]*/i, "");
  t = t.replace(/^(علیکم|عزیز|دوست من|رفیق|داداش)[\s!.،,؟?]*/i, "");
  t = t.replace(/^(خوبی|چطوری|خسته نباشی|وقت بخیر|صبح بخیر|عصر بخیر|شب بخیر)[\s!.،,؟?]*/i, "");
  return t.trim();
}

export function isPronounQuery(text: string): boolean {
  return /(این یکی|همون|همین|این توکن|همون توکن|این چطوره|خوبه\؟|ریسکش)/i.test(text);
}

// Phase 8: engineering-work requests. Deliberately conservative — a false positive
// hijacks a normal market conversation, a false negative just falls through to the
// conversational agent (which can call submit_dev_mission itself). Requires BOTH a
// development topic and an explicit build/request verb, so complaints and questions
// ("چرا برنامه ارور میده؟", "داده‌ها آپدیت شدن؟") do not match.
const DEV_TOPIC_RE = /(دانشگاه|دانش گاه|عامل(ها|های)?|اجنت|agents?|سیستم|توسعه|آپدیت|اپدیت|به روزرسانی|به‌روزرسانی|فیچر|قابلیت جدید|ماموریت توسعه|مهندس|کد ?نویس|university|features?|engineering)/;
const DEV_VERB_RE = /(بساز|ساختن|اضافه کن|اضافه شود|آپدیت کن|اپدیت کن|بنویس|نوشتن|راه انداز|راه‌انداز|راه بنداز|بنداز|پیاده کن|پیاده‌سازی|بهتر کن|بهبود بده|فعال کن|راه‌اندازی کن|توسعه بده|\bbuild\b|\bcreate\b|\badd\b|\bimplement\b|\bupdate\b|\boperationalize\b|\bset up\b)/;
// MN-12: inspection/status requests are not engineering work even when they name a
// dev topic — "سیستم رو چک کن", "agents رو بررسی کن" must stay normal conversation.
const DEV_NEGATIVE_RE = /(چک کن|چک کردن|بررسی کن|بررسی کنم|کنترل کن|وضعیت|گزارش|عیب ?یابی|دیباگ|اشکال ?زدایی|check|inspect|debug|status)/i;

/** "دانشگاه رو بساز", "عامل‌ها رو راه بنداز", "add a feature for gold alerts" … */
export function isDevMissionRequest(text: string): boolean {
  const t = normalizeIntentText(text);
  if (!t) return false;
  if (DEV_NEGATIVE_RE.test(t)) return false;
  return DEV_TOPIC_RE.test(t) && DEV_VERB_RE.test(t);
}

/** The mission summary shown to the owner (and stored after confirmation). */
export function extractDevMissionSummary(text: string): string {
  return cleanSummaryFa(text);
}

export type IntentPredicates = {
  /** "why was X rejected" (checked before isWhy). */
  isReject: (text: string) => boolean;
  isWhy: (text: string) => boolean;
};

/** Full router. Pure. Order matters; see comments. */
export function routeIntent(raw: string, p: IntentPredicates): string {
  const original = String(raw ?? "");
  // Greeting prefix followed by a real question → route the question.
  const afterGreeting = stripGreeting(original);
  if (afterGreeting.replace(/[\s!.،,؟?🙏👋]/g, "") === "" && original.trim() !== "") return "greeting";
  const text = afterGreeting;
  if (/^(خوبی|چطوری|حالت چطوره|چه خبر)[\s!.،,؟?]*$/i.test(text.trim())) return "greeting";
  if (isThanksOnly(text)) return "thanks";
  if (/(راهنما|کمک|چه کار|چیکار میکنی|help|commands)/i.test(text)) return "help";
  // GM-04: explicit whole-message commands only (checked before every new intent).
  const control = detectControlCommand(text);
  if (control) return control;
  const n = normalizeIntentText(text);
  // Viewing the watchlist must not be mistaken for adding to it ("واچ لیست" contains "واچ").
  if (/(واچ ?لیست|watchlist|تحت نظر)/i.test(n)) return "watchlist";
  if (/(زیر نظر|واچ|watch)/i.test(text)) return "watch_add";
  if (looksLikePaperBuy(text)) return "paper_buy";
  // Trading-signal requests outrank stop-loss / opportunities (PAPER_ONLY refusal-style reply).
  if (isTradeSignalRequest(text)) return "trade_signal";
  // Phase 8: engineering-work request → confirm-gated dev mission (owner only).
  if (isDevMissionRequest(text)) return "dev_mission";
  if (/(پورتف|موقعیت|کاغذی‌ها|کاغذی ها)/i.test(text)) return "paper_list";
  if (isStopLossQuestion(text)) return "stop_loss";
  if (p.isReject(text)) return "reject";
  if (p.isWhy(text)) return "why";
  if (isPriceQuestion(text)) return "price";
  if (isNewsRequest(text)) return "news";
  if (/(فرصت|بهترین|پامپ|opportunity|چی بخرم|معرفی کن)/i.test(text)) return "opportunities";
  if (/(نهنگ|whale)/i.test(text)) return "whales";
  if (/(شورا|کارشناس|تیم|council)/i.test(text)) return "council";
  if (/(سلامت|وضعیت سیستم|health|کالیبر)/i.test(text)) return "health";
  if (/(درس|یاد گرفت|اشتباه|hindsight|learning)/i.test(text)) return "learning";
  if (/(بازار|رژیم|بیت‌کوین|بیتکوین|اتریوم|سولانا|btc|eth|sol)/i.test(text.toLowerCase()) || detectMajorAsset(text)) return "market";
  if (/[a-z]{2,10}/i.test(text) && /(توکن|امن|تحلیل|قیمت)/.test(text)) return "token";
  if (isPronounQuery(text)) return "why";
  return "general";
}
