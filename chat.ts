import { db } from "@/db";
import { chatMessages } from "@/db/schema";
import { desc } from "drizzle-orm";
import { addPaper, addWatch, getState, startEngine, stopEngine } from "./engine";
import { faNumber, faPct, faUsd } from "./persian";
import { commandSnapshot } from "./snapshot";
import { FINAL_USER_LINE } from "./types";

export type ChatResponse = {
  reply: string;
  intent: string;
  evidence: Record<string, unknown>;
  focusToken?: string | null;
};

export type ChatContext = {
  focusToken?: string | null;
  history?: Array<{ role: "user" | "assistant"; content: string }>;
};

export async function handleChat(message: string, ctx: ChatContext = {}): Promise<ChatResponse> {
  const text = message.trim();
  const intent = detectIntent(text);
  const snap = await commandSnapshot();
  let focus =
    ctx.focusToken ||
    extractFocusFromHistory(ctx.history) ||
    null;
  let reply = "";
  const evidence: Record<string, unknown> = {
    intent,
    at: new Date().toISOString(),
    focusIn: focus,
  };

  if (intent === "start") {
    await startEngine();
    reply =
      "روشن شد. از همین لحظه چرخه‌ها پشت‌سرهم می‌روند (حدود هر ۷۰ ثانیه) تا خودت بگی توقف. وسط کار وای نمی‌ایستم. اگر پروایدری قطع باشه همان DOWN یا UNKNOWN می‌مونه — چیزی جعل نمی‌کنم. هروقت خواستی خودمونی بپرس: بازار چه خبر؟ فرصت‌ها؟ این توکن چطوره؟";
  } else if (intent === "stop") {
    await stopEngine();
    reply = "متوقف شد. داده‌های قبلی سر جاشون هستن. هر وقت خواستی دوباره بگو شروع کن.";
  } else if (intent === "market") {
    reply = marketReply(snap);
  } else if (intent === "opportunities") {
    reply = oppReply(snap);
    const top = snap.opportunities.find((o) => o.decision === "WATCH");
    if (top) focus = top.tokenKey;
  } else if (intent === "news") {
    reply = newsReply(snap, text);
  } else if (intent === "health") {
    reply = healthReply(snap);
  } else if (intent === "council") {
    reply = councilReply(snap, text, focus);
  } else if (intent === "learning") {
    reply = learningReply(snap);
  } else if (intent === "watchlist") {
    reply = watchReply(snap);
  } else if (intent === "paper_list") {
    reply = paperReply(snap);
  } else if (intent === "whales") {
    const hit = findOpp(snap, text, focus);
    reply = hit
      ? `برای ${hit.symbol}: بدون سند نقش کیف پول، wallet_role=UNKNOWN می‌ماند. تمرکز دارندگان و فشار خرید/فروش استخر فقط وقتی evidence باشد گزارش می‌شود. امنیت فعلی: ${hit.securityStatus}.`
      : "برای نهنگ‌ها سخت‌گیرم: اگر سند نقش کیف پول نباشد می‌گویم wallet_role=UNKNOWN. اسمارت‌مانی جعلی نمی‌سازم. توکن را نام ببر یا اول فرصتی را باز کن تا «این» معنا داشته باشد.";
    if (hit) focus = hit.tokenKey;
  } else if (intent === "watch_add") {
    const hit = findOpp(snap, text, focus);
    if (!hit) {
      reply = "این نماد رو تو فرصت‌های همین چرخه پیدا نکردم. اسم یا سمبل رو دقیق‌تر بگو؛ حدس نمی‌زنم.";
    } else {
      await addWatch({
        tokenKey: hit.tokenKey,
        symbol: hit.symbol,
        chain: hit.chain,
        address: hit.address,
        thesisFa: `پایش به درخواست کاربر: ${text}`,
      });
      reply = `${hit.symbol} روی ${hit.chain} رفت تو واچ‌لیست. حکم فعلی: ${hit.decision} با اطمینان ${hit.confidence}. ${hit.invalidationFa}`;
      evidence.tokenKey = hit.tokenKey;
      focus = hit.tokenKey;
    }
  } else if (intent === "paper_buy") {
    const hit = findOpp(snap, text, focus);
    const price =
      extractNumber(text, /(?:قیمت|با|@)\s*([0-9]+(?:\.[0-9]+)?)/) ??
      (hit?.payload ? num(hit.payload.priceUsd) : null);
    const qty = extractNumber(text, /(?:مقدار|تعداد|تا)\s*([0-9]+(?:\.[0-9]+)?)/);
    if (!hit && !extractSymbol(text)) {
      reply = "برای ثبت خرید کاغذی باید نماد مشخص باشه. خرید واقعی انجام نمی‌دم.";
    } else {
      const symbol = hit?.symbol || extractSymbol(text) || "UNKNOWN";
      const row = await addPaper({
        tokenKey: hit?.tokenKey || `manual:${symbol}`,
        symbol,
        chain: hit?.chain || "unknown",
        address: hit?.address,
        quantity: qty,
        entryPrice: price,
        thesisFa: `خرید کاغذی کاربر: ${text}`,
        targetPrice: extractNumber(text, /(?:هدف|تا)\s*([0-9]+(?:\.[0-9]+)?)/),
      });
      reply = `ثبت شد — فقط کاغذی. نماد ${symbol}. ورود ${price ?? "UNKNOWN"}. مقدار ${qty ?? "UNKNOWN"}. هیچ سفارشی به صرافی نرفت.`;
      evidence.positionId = row.id;
      if (hit) focus = hit.tokenKey;
    }
  } else if (intent === "why" || intent === "token") {
    const hit = findOpp(snap, text, focus);
    reply = hit
      ? whyReply(hit)
      : intent === "why"
        ? "بگو کدوم توکن — یا اول یک فرصت را باز کن تا «این یکی» معنا داشته باشد. بدون مصداق دلیل اختراع نمی‌کنم."
        : "این نماد رو تو کاندیدهای فعلی ندارم. اول شروع رو بزن تا کشف انجام بشه، یا اسم رو دقیق‌تر بگو.";
    if (hit) focus = hit.tokenKey;
  } else if (intent === "reject") {
    const rejected = snap.opportunities.filter((o) => o.decision === "REJECT").slice(0, 5);
    reply = rejected.length
      ? `رد شده‌ها (ضدهایپ):\n${rejected.map((o) => `• ${o.symbol}: ${(o.risksFa || []).slice(0, 2).join(" ")}`).join("\n")}`
      : "تو آخرین چرخه REJECT ثبت نشده یا هنوز چرخه‌ای نیست.";
  } else if (intent === "greeting") {
    reply = greetingReply(snap);
  } else if (intent === "help") {
    reply = helpReply();
  } else {
    const hit = findOpp(snap, text, focus);
    if (hit && isPronounQuery(text)) {
      reply = whyReply(hit);
      focus = hit.tokenKey;
    } else {
      reply = await generalReply(text, snap);
    }
  }

  const state = await getState();
  if (!state.running && intent !== "start" && intent !== "stop" && intent !== "greeting" && intent !== "help") {
    reply += "\n\nموتور الان خاموشه. اگر بخوای خودم از اینجا روشن کنم بگو «شروع کن» — بعدش خودش پشت‌سرهم جمع می‌کنه.";
  }
  reply += `\n\n${FINAL_USER_LINE}`;
  evidence.focusToken = focus;

  try {
    await db.insert(chatMessages).values({ role: "user", content: text, intent, evidence });
    await db.insert(chatMessages).values({ role: "assistant", content: reply, intent, evidence });
  } catch {
    /* DB optional when DATABASE_URL missing */
  }
  return { reply, intent, evidence, focusToken: focus };
}

export async function chatHistory(limit = 24) {
  try {
    const rows = await db.select().from(chatMessages).orderBy(desc(chatMessages.id)).limit(limit);
    return rows.reverse();
  } catch {
    return [];
  }
}

function isPronounQuery(text: string): boolean {
  return /(این یکی|همون|همین|این توکن|همون توکن|این چطوره|خوبه\؟|ریسکش)/i.test(text);
}

function extractFocusFromHistory(
  history?: Array<{ role: "user" | "assistant"; content: string }>,
): string | null {
  if (!history?.length) return null;
  for (let i = history.length - 1; i >= 0; i--) {
    const m = history[i].content.match(/\b([A-Z]{2,12})\b/);
    if (m && !/[آ-ی]/.test(m[1])) return m[1];
  }
  return null;
}

function detectIntent(text: string): string {
  const t = text.toLowerCase();
  if (/^(سلام|درود|هی|hello|hi|hey)(\s|$|[!.،,])/i.test(text.trim()) || /چطوری|خوبی/.test(text)) return "greeting";
  if (/(راهنما|کمک|چه کار|چیکار میکنی|help|commands)/i.test(text)) return "help";
  if (/(^|\s)(شروع|استارت|start|روشن)(\s|$)/i.test(text) && !/خرید/.test(text)) return "start";
  if (/(توقف|استاپ|stop|خاموش)/i.test(text)) return "stop";
  if (/(زیر نظر|واچ|watch)/i.test(text)) return "watch_add";
  if (/(خریدم|خرید کاغذی|ثبت خرید|paper)/i.test(text)) return "paper_buy";
  if (/(پورتف|موقعیت|کاغذی‌ها)/i.test(text)) return "paper_list";
  if (/(واچ‌لیست|watchlist|تحت نظر)/i.test(text)) return "watchlist";
  if (/(چرا|دلیل|شواهد|explain)/i.test(text)) return "why";
  if (/(رد شد|چرا رد|reject)/i.test(text)) return "reject";
  if (/(خبر|اخبار|news)/i.test(text)) return "news";
  if (/(فرصت|بهترین|پامپ|opportunity|چی بخرم)/i.test(text)) return "opportunities";
  if (/(نهنگ|whale)/i.test(text)) return "whales";
  if (/(شورا|کارشناس|تیم|council)/i.test(text)) return "council";
  if (/(سلامت|وضعیت سیستم|health|کالیبر)/i.test(text)) return "health";
  if (/(درس|یاد گرفت|اشتباه|hindsight|learning)/i.test(text)) return "learning";
  if (/(بازار|رژیم|بیت‌کوین|بیتکوین|اتریوم|سولانا|btc|eth|sol)/i.test(t)) return "market";
  if (/[a-z]{2,10}/i.test(text) && /(توکن|امن|تحلیل|قیمت)/.test(text)) return "token";
  if (isPronounQuery(text)) return "why";
  return "general";
}

function greetingReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  const running = snap.state?.running;
  const n = snap.opportunities?.filter((o) => o.decision === "WATCH").length ?? 0;
  return [
    "سلام! من AHOS هستم — همون همکار صریح که حدس رو جای داده نمی‌ذاره.",
    running
      ? `الان موتور روشنه و ${n} کاندید پایش تو آخرین چرخه دارم.`
      : "موتور فعلاً خاموشه؛ بگو «شروع کن» تا جمع‌آوری شروع بشه.",
    "می‌تونی خودمونی بپرسی: بازار چه خبر؟ فرصت‌ها؟ اخبار سولانا؟ این توکن رو تحت نظر بگیر. سیستم کجاش لنگه؟",
    "خرید واقعی انجام نمی‌دم — فقط کاغذی و پایش.",
  ].join(" ");
}

function helpReply(): string {
  return [
    "چی می‌تونی ازم بپرسی:",
    "• بازار / بیت‌کوین / اتریوم / سولانا",
    "• بهترین فرصت‌ها / پامپ / چی بخرم (فقط پایش — نه سفارش واقعی)",
    "• اخبار / اخبار سولانا",
    "• این توکن رو تحت نظر بگیر / خرید کاغذی ثبت کن",
    "• شورا چه گفت / نهنگ‌ها / سلامت سیستم / درس‌ها",
    "• شروع کن / توقف",
    "مثل چت عادی حرف بزن؛ اگر داده نباشه می‌گم UNKNOWN.",
  ].join("\n");
}

function marketReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  const m = snap.market;
  if (!m) return "هنوز اسنپ‌شات بازار ندارم — INSUFFICIENT_EVIDENCE. یک‌بار شروع رو بزن تا از منابع آزاد جمع کنم.";
  return [
    `بازار الان (شواهد زنده، نه حدس): رژیم ${m.regime}.`,
    `بیت‌کوین ${faUsd(m.btcPrice)} (${faPct(m.btcChange24h)}).`,
    `اتریوم ${faUsd(m.ethPrice)} (${faPct(m.ethChange24h)}).`,
    `سولانا ${faUsd(m.solPrice)} (${faPct(m.solChange24h)}).`,
    `ارزش کل بازار ${faUsd(m.totalMcap)}، دامیننس بیت‌کوین ${faNumber(m.btcDominance, 1)}٪.`,
    `ترس/طمع: ${m.fearGreed ?? "UNKNOWN"} (${m.fearGreedLabel ?? "UNKNOWN"}).`,
    `TVL دیفای: ${faUsd(m.defiTvl)}.`,
    "این‌ها زمینه است، نه سیگنال خرید.",
  ].join(" ");
}

function oppReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  const list = snap.opportunities.filter((o) => o.decision === "WATCH").slice(0, 5);
  const rejected = snap.opportunities.filter((o) => o.decision === "REJECT").length;
  if (!snap.opportunities.length) return "فرصتی در حافظه نیست. یا موتور روشن نشده یا پروایدرها DOWN بودن.";
  if (!list.length) {
    return `کاندید WATCH ندارم. ${rejected} مورد رد شد. highest-score-wins خاموشه؛ هایپ به‌تنهایی بالا نمی‌آد.`;
  }
  return [
    "بهترین‌ها یعنی «قابل پایش با شواهد بهتر»، نه خرید:",
    ...list.map(
      (o, i) =>
        `${i + 1}) ${o.symbol} روی ${o.chain} — ${o.decision} / ${o.confidence} / امنیت ${o.securityStatus}. پوشش شواهد ${faNumber((o.evidenceCoverage || 0) * 100, 0)}٪. ${(o.reasonsFa || [])[0] || ""} ریسک: ${(o.risksFa || [])[0] || "UNKNOWN"}`,
    ),
    `${rejected} توکن رد شدن (ضدهایپ).`,
  ].join("\n");
}

function newsReply(snap: Awaited<ReturnType<typeof commandSnapshot>>, text: string): string {
  let items = snap.news;
  if (/solana|سولانا/i.test(text))
    items = items.filter(
      (n) => n.relatedChains?.includes("solana") || /سولانا|solana/i.test(`${n.titleFa} ${n.titleOriginal}`),
    );
  if (/bitcoin|بیت/i.test(text))
    items = items.filter(
      (n) => n.relatedTokens?.includes("BTC") || /بیت‌کوین|bitcoin/i.test(`${n.titleFa} ${n.titleOriginal}`),
    );
  const top = items.slice(0, 6);
  if (!top.length) return "خبری مطابق فیلتر تو در حافظه نیست — SOURCE_UNAVAILABLE یا هنوز جمع نشده.";
  return [
    "اخبار با بازنویسی فارسی (عنوان اصلی حفظ شده):",
    ...top.map((n) => `• ${n.titleFa} — ${n.source} — اهمیت ${n.importance} — ${n.summaryFa}`),
  ].join("\n");
}

function healthReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  const lines = snap.health.dimensions.map((d) => `• ${d.nameFa}: ${d.status} — ${d.evidenceFa}`);
  return [`وضعیت سیستم (ابعاد جدا، یک نمره فریبنده نمی‌سازم):`, ...lines, `چرخه‌ها: ${snap.state.cycleCount}. آخرین: ${snap.state.lastCycleStatus}.`].join("\n");
}

function councilReply(
  snap: Awaited<ReturnType<typeof commandSnapshot>>,
  text: string,
  focus: string | null,
): string {
  if (!snap.council.length) return "هنوز گزارش شورا نیست. بعد از اولین چرخه، اختلاف ۱۰ تیم رو می‌بینی.";
  const hit = findOpp(snap, text, focus);
  const c =
    (hit && snap.council.find((x) => x.tokenKey === hit.tokenKey)) || snap.council[0];
  return `آخرین حکم شورا برای ${c.tokenKey}: ${c.verdict}. WATCH=${c.watchCount} REJECT=${c.rejectCount} ABSTAIN=${c.abstainCount}. ${c.summaryFa} اختلاف مخفی نشد.`;
}

function learningReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  if (!snap.lessons.length) {
    return "هنوز درس افق‌بسته ندارم. پیش‌بینی‌ها باید به افق برسن تا outcome واقعی ساخته بشه. No peeking.";
  }
  return ["درس‌های ثبت‌شده:", ...snap.lessons.slice(0, 5).map((l) => `• ${l.titleFa}: ${l.bodyFa}`)].join("\n");
}

function watchReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  if (!snap.watchlist.length) return "واچ‌لیست خالی است. بگو «این توکن را تحت نظر بگیر».";
  return snap.watchlist.map((w) => `• ${w.symbol} (${w.chain}) — ${w.thesisFa || "بدون تز"}`).join("\n");
}

function paperReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  const open = snap.paper.filter((p) => p.status === "OPEN");
  if (!open.length) return "موقعیت کاغذی باز ندارم.";
  return open
    .map((p) => {
      const pnl =
        p.entryPrice && p.lastPrice ? faPct(((p.lastPrice - p.entryPrice) / p.entryPrice) * 100) : "UNKNOWN";
      return `• ${p.symbol} ورود ${p.entryPrice ?? "UNKNOWN"} آخرین ${p.lastPrice ?? "UNKNOWN"} بازده ${pnl} MFE ${p.maxFavorable ?? "UNKNOWN"} MAE ${p.maxAdverse ?? "UNKNOWN"}`;
    })
    .join("\n");
}

function whyReply(o: Awaited<ReturnType<typeof commandSnapshot>>["opportunities"][number]): string {
  return [
    `${o.symbol} روی ${o.chain}: تصمیم ${o.decision} با اطمینان ${o.confidence}. امنیت ${o.securityStatus}. حکم شورا ${o.councilVerdict}${o.disagreement ? " (اختلاف‌دار)" : ""}.`,
    `چرا؟ ${(o.reasonsFa || []).join(" ")}`,
    `ریسک‌ها: ${(o.risksFa || []).join(" ")}`,
    `UNKNOWNها: ${(o.unknownsFa || []).join(" ") || "ثبت نشده"}`,
    `داده کم: ${(o.missingFa || []).join("، ") || "—"}`,
    `ابطال: ${o.invalidationFa}`,
    "این توصیه خرید واقعی نیست.",
  ].join("\n");
}

async function generalReply(text: string, snap: Awaited<ReturnType<typeof commandSnapshot>>): Promise<string> {
  const hit = findOpp(snap, text, null);
  if (hit) return whyReply(hit);
  const m = snap.market;
  const q = text.slice(0, 120);
  return [
    "فهمیدم چی گفتی — مثل همکار جواب می‌دم، نه ربات خشک.",
    m
      ? `الان رژیم ${m.regime} است، بیت‌کوین ${faUsd(m.btcPrice)} (${faPct(m.btcChange24h)}).`
      : "اسنپ‌شات بازار هنوز UNKNOWN است.",
    snap.opportunities.length
      ? `${snap.opportunities.filter((o) => o.decision === "WATCH").length} کاندید پایش و ${snap.opportunities.filter((o) => o.decision === "REJECT").length} رد در آخرین چرخه.`
      : "فرصتی جمع نشده.",
    snap.news[0] ? `تازه‌ترین خبر فارسی: ${snap.news[0].titleFa}` : "خبری نیست.",
    `اگر منظورت چیز دقیق‌تری بود از «${q}»، همون رو شفاف‌تر بگو: فرصت‌ها؟ یک توکن خاص؟ وضعیت سیستم؟`,
  ].join(" ");
}

function findOpp(
  snap: Awaited<ReturnType<typeof commandSnapshot>>,
  text: string,
  focus: string | null,
) {
  const up = text.toUpperCase();
  const bySymbol =
    snap.opportunities.find((o) => up.includes(o.symbol.toUpperCase())) ||
    snap.opportunities.find((o) => o.name && text.includes(o.name)) ||
    null;
  if (bySymbol) return bySymbol;
  if (focus) {
    const byFocus =
      snap.opportunities.find((o) => o.tokenKey === focus || o.symbol.toUpperCase() === focus.toUpperCase()) ||
      null;
    if (byFocus && (isPronounQuery(text) || !extractSymbol(text))) return byFocus;
  }
  return null;
}

function extractSymbol(text: string): string | null {
  const m = text.toUpperCase().match(/\b[A-Z]{2,12}\b/);
  return m ? m[0] : null;
}

function extractNumber(text: string, re: RegExp): number | null {
  const m = text.match(re);
  if (!m) return null;
  const n = Number(m[1]);
  return Number.isFinite(n) ? n : null;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}
