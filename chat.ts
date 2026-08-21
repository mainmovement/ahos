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
};

export async function handleChat(message: string): Promise<ChatResponse> {
  const text = message.trim();
  const intent = detectIntent(text);
  const snap = await commandSnapshot();
  let reply = "";
  const evidence: Record<string, unknown> = { intent, at: new Date().toISOString() };

  if (intent === "start") {
    await startEngine();
    reply = "موتور را روشن کردم. از این لحظه چرخه‌ها خودکار ادامه پیدا می‌کنند تا خودت استاپ بزنی. داده جعلی نمی‌سازم؛ اگر پروایدری نباشد همان UNKNOWN/DOWN می‌ماند.";
  } else if (intent === "stop") {
    await stopEngine();
    reply = "موتور را متوقف کردم. مشاهدات قبلی در پایگاه می‌ماند. برای ادامه، دوباره شروع را بزن.";
  } else if (intent === "market") {
    reply = marketReply(snap);
  } else if (intent === "opportunities") {
    reply = oppReply(snap);
  } else if (intent === "news") {
    reply = newsReply(snap, text);
  } else if (intent === "health") {
    reply = healthReply(snap);
  } else if (intent === "council") {
    reply = councilReply(snap);
  } else if (intent === "learning") {
    reply = learningReply(snap);
  } else if (intent === "watchlist") {
    reply = watchReply(snap);
  } else if (intent === "paper_list") {
    reply = paperReply(snap);
  } else if (intent === "whales") {
    reply =
      "برای نهنگ‌ها قانون سخت است: اگر سند نقش کیف نباشد wallet_role=UNKNOWN. در این چرخه هویت نهنگ جعل نشد. آنچه داریم فقط خرید/فروش استخر (در صورت وجود) و هشدار تمرکز است. بدون کاوشگر اختصاصی با کلید، ادعای اسمارت‌مانی نمی‌کنم.";
  } else if (intent === "watch_add") {
    const hit = findOpp(snap, text);
    if (!hit) {
      reply = "توکن را در فرصت‌های همین چرخه پیدا نکردم. نماد یا بخشی از اسم را دقیق‌تر بگو. چیزی را حدس نمی‌زنم.";
    } else {
      await addWatch({
        tokenKey: hit.tokenKey,
        symbol: hit.symbol,
        chain: hit.chain,
        address: hit.address,
        thesisFa: `پایش به درخواست کاربر: ${text}`,
      });
      reply = `${hit.symbol} روی ${hit.chain} رفت روی واچ‌لیست کاغذی. حکم فعلی ${hit.decision} با اطمینان ${hit.confidence}. ${hit.invalidationFa}`;
      evidence.tokenKey = hit.tokenKey;
    }
  } else if (intent === "paper_buy") {
    const hit = findOpp(snap, text) || findBySymbol(snap, text);
    const price =
      extractNumber(text, /(?:قیمت|با|@)\s*([0-9]+(?:\.[0-9]+)?)/) ??
      (hit?.payload ? num(hit.payload.priceUsd) : null);
    const qty = extractNumber(text, /(?:مقدار|تعداد|تا)\s*([0-9]+(?:\.[0-9]+)?)/);
    if (!hit && !extractSymbol(text)) {
      reply = "برای ثبت خرید کاغذی باید نماد توکن مشخص باشد. خرید واقعی انجام نمی‌شود.";
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
      reply = `ثبت شد به‌صورت PAPER ONLY. نماد ${symbol}. قیمت ورود ${price ?? "UNKNOWN"}. مقدار ${qty ?? "UNKNOWN"}. هیچ سفارش واقعی به صرافی نرفت. اگر قیمت زنده داشته باشیم MFE/MAE را در چرخه‌های بعد پر می‌کنم.`;
      evidence.positionId = row.id;
    }
  } else if (intent === "why") {
    const hit = findOpp(snap, text);
    reply = hit ? whyReply(hit) : "بگو کدام توکن. بدون مصداق، دلیل اختراع نمی‌کنم.";
  } else if (intent === "reject") {
    const rejected = snap.opportunities.filter((o) => o.decision === "REJECT").slice(0, 5);
    reply = rejected.length
      ? `رد شده‌ها (ضدهایپ):\n${rejected.map((o) => `• ${o.symbol}: ${(o.risksFa || []).slice(0, 2).join(" ")}`).join("\n")}`
      : "در آخرین چرخه REJECT ثبت نشده یا هنوز چرخه‌ای نیست.";
  } else if (intent === "token") {
    const hit = findOpp(snap, text);
    reply = hit ? whyReply(hit) : "این نماد را در کاندیدهای فعلی ندارم. اول شروع را بزن تا کشف انجام شود، یا نام را دقیق‌تر بگو.";
  } else {
    reply = await generalReply(text, snap);
  }

  const state = await getState();
  if (!state.running && intent !== "start" && intent !== "stop") {
    reply += "\n\nموتور الان خاموش است. اگر بخواهی خودم از اینجا شروع کنم بگو «شروع کن» تا چرخه‌ها پشت‌سرهم بروند.";
  }
  reply += `\n\n${FINAL_USER_LINE}`;

  await db.insert(chatMessages).values({ role: "user", content: text, intent, evidence });
  await db.insert(chatMessages).values({ role: "assistant", content: reply, intent, evidence });
  return { reply, intent, evidence };
}

export async function chatHistory(limit = 24) {
  const rows = await db.select().from(chatMessages).orderBy(desc(chatMessages.id)).limit(limit);
  return rows.reverse();
}

function detectIntent(text: string): string {
  const t = text.toLowerCase();
  if (/(^|\s)(شروع|استارت|start|روشن)(\s|$)/i.test(text) && !/خرید/.test(text)) return "start";
  if (/(توقف|استاپ|stop|خاموش)/i.test(text)) return "stop";
  if (/(زیر نظر|واچ|watch)/i.test(text)) return "watch_add";
  if (/(خریدم|خرید کاغذی|ثبت خرید|paper)/i.test(text)) return "paper_buy";
  if (/(پورتف|موقعیت|کاغذی‌ها)/i.test(text)) return "paper_list";
  if (/(واچ‌لیست|watchlist|تحت نظر)/i.test(text)) return "watchlist";
  if (/(چرا|دلیل|شواهد|explain)/i.test(text)) return "why";
  if (/(رد شد|چرا رد|reject)/i.test(text)) return "reject";
  if (/(خبر|اخبار|news)/i.test(text)) return "news";
  if (/(فرصت|بهترین|پامپ|opportunity)/i.test(text)) return "opportunities";
  if (/(نهنگ|whale)/i.test(text)) return "whales";
  if (/(شورا|کارشناس|تیم|council)/i.test(text)) return "council";
  if (/(سلامت|وضعیت سیستم|health|کالیبر)/i.test(text)) return "health";
  if (/(درس|یاد گرفت|اشتباه|hindsight|learning)/i.test(text)) return "learning";
  if (/(بازار|رژیم|بیت‌کوین|بیتکوین|اتریوم|سولانا|btc|eth|sol)/i.test(t)) return "market";
  if (/[a-z]{2,10}/i.test(text) && /(توکن|امن|تحلیل|قیمت)/.test(text)) return "token";
  return "general";
}

function marketReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  const m = snap.market;
  if (!m) return "هنوز اسنپ‌شات بازار ندارم — INSUFFICIENT_EVIDENCE. یک‌بار شروع را بزن تا از CoinGecko/Binance/Alternative.me جمع کنم.";
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
  if (!snap.opportunities.length) return "فرصتی در حافظه نیست. یا موتور روشن نشده یا پروایدرها DOWN بوده‌اند.";
  if (!list.length) {
    return `کاندید WATCH ندارم. ${rejected} مورد رد شد. highest-score-wins خاموش است؛ هایپ به‌تنهایی بالا نمی‌آید.`;
  }
  return [
    "بهترین‌ها یعنی «قابل پایش با شواهد بهتر»، نه خرید:",
    ...list.map(
      (o, i) =>
        `${i + 1}) ${o.symbol} روی ${o.chain} — ${o.decision} / ${o.confidence} / امنیت ${o.securityStatus}. پوشش شواهد ${faNumber((o.evidenceCoverage || 0) * 100, 0)}٪. ${(o.reasonsFa || [])[0] || ""} ریسک: ${(o.risksFa || [])[0] || "UNKNOWN"}`,
    ),
    `${rejected} توکن رد شدند (ضدهایپ).`,
  ].join("\n");
}

function newsReply(snap: Awaited<ReturnType<typeof commandSnapshot>>, text: string): string {
  let items = snap.news;
  if (/solana|سولانا/i.test(text)) items = items.filter((n) => n.relatedChains?.includes("solana") || /سولانا|solana/i.test(`${n.titleFa} ${n.titleOriginal}`));
  if (/bitcoin|بیت/i.test(text)) items = items.filter((n) => n.relatedTokens?.includes("BTC") || /بیت‌کوین|bitcoin/i.test(`${n.titleFa} ${n.titleOriginal}`));
  const top = items.slice(0, 6);
  if (!top.length) return "خبری مطابق فیلتر تو در حافظه نیست — SOURCE_UNAVAILABLE یا هنوز جمع نشده.";
  return ["اخبار با بازنویسی فارسی (عنوان اصلی حفظ شده):", ...top.map((n) => `• ${n.titleFa} — ${n.source} — اهمیت ${n.importance} — ${n.summaryFa}`)].join("\n");
}

function healthReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  const lines = snap.health.dimensions.map((d) => `• ${d.nameFa}: ${d.status} — ${d.evidenceFa}`);
  return [`وضعیت سیستم (۱۲ بُعد، یک نمره فریبنده نمی‌سازم):`, ...lines, `چرخه‌ها: ${snap.state.cycleCount}. آخرین: ${snap.state.lastCycleStatus}.`].join("\n");
}

function councilReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  if (!snap.council.length) return "هنوز گزارش شورا نیست. بعد از اولین چرخه، اختلاف ۱۰ تیم را می‌بینی.";
  const c = snap.council[0];
  return `آخرین حکم شورا برای ${c.tokenKey}: ${c.verdict}. WATCH=${c.watchCount} REJECT=${c.rejectCount} ABSTAIN=${c.abstainCount}. ${c.summaryFa} اختلاف مخفی نشد.`;
}

function learningReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  if (!snap.lessons.length && !snap.outcomes.length) {
    return "هنوز درس افق‌بسته ندارم. پیش‌بینی‌ها باید به افق برسند تا outcome واقعی ساخته شود. No peeking.";
  }
  return ["درس‌های ثبت‌شده:", ...snap.lessons.slice(0, 5).map((l) => `• ${l.titleFa}: ${l.bodyFa}`)].join("\n");
}

function watchReply(snap: Awaited<ReturnType<typeof commandSnapshot>>): string {
  if (!snap.watchlist.length) return "واچ‌لیست خالی است. بگو «این توکن را زیر نظر بگیر».";
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
  const hit = findOpp(snap, text);
  if (hit) return whyReply(hit);
  const m = snap.market;
  return [
    "من AHOS هستم؛ مثل یک همکار صریح. حدس را به‌جای داده نمی‌گذارم.",
    m
      ? `الان رژیم ${m.regime} است، بیت‌کوین ${faUsd(m.btcPrice)} (${faPct(m.btcChange24h)}).`
      : "اسنپ‌شات بازار هنوز UNKNOWN است.",
    snap.opportunities.length
      ? `${snap.opportunities.filter((o) => o.decision === "WATCH").length} کاندید پایش و ${snap.opportunities.filter((o) => o.decision === "REJECT").length} رد در آخرین چرخه.`
      : "فرصتی جمع نشده.",
    snap.news[0] ? `تازه‌ترین خبر فارسی: ${snap.news[0].titleFa}` : "خبری نیست.",
    "می‌توانی بپرسی: بازار چه خبر؟ فرصت‌ها؟ این توکن را زیر نظر بگیر. خریدم. اخبار سولانا. شورا چه گفت. سیستم کجاش لنگ می‌زند.",
    `پیامت را این‌طور فهمیدم که گفتگو عمومی است («${text.slice(0, 80)}»). اگر منظورت چیز دیگری است همان را خودمانی بگو.`,
  ].join(" ");
}

function findOpp(snap: Awaited<ReturnType<typeof commandSnapshot>>, text: string) {
  const up = text.toUpperCase();
  return (
    snap.opportunities.find((o) => up.includes(o.symbol.toUpperCase())) ||
    snap.opportunities.find((o) => o.name && text.includes(o.name)) ||
    null
  );
}

function findBySymbol(snap: Awaited<ReturnType<typeof commandSnapshot>>, text: string) {
  return findOpp(snap, text);
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




