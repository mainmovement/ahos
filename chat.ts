import { db } from "@/db";
import { chatMessages } from "@/db/schema";
import { desc } from "drizzle-orm";
import { addPaper, addWatch, getState, PaperSecurityDenied } from "./engine";
import { detectControlCommand, gateChatControl, looksLikePaperBuy, recordControlAudit } from "./chat_control_gate";
import {
  canonicalFocusTokenKey,
  findCanonicalDecision,
  loadCanonicalReadModel,
  paperAllowedFromCanonical,
  type CanonicalDecisionView,
} from "./canonical_read_model";
import { commandSnapshot } from "./snapshot";
import { FINAL_USER_LINE } from "./types";
import { blocksFromText, bullet, gap, line, note, title, type ReplyBlock } from "./reply_format";
import { finalizeReply } from "./response_composer";
import {
  ENGINE_OFF_NOTE,
  confidenceFa,
  councilBlocks,
  decisionFa,
  engineNoticeRelevant,
  generalBlocks,
  greetingBlocks,
  healthBlocks,
  helpBlocks,
  isNewsRequest,
  isStopLossQuestion,
  learningBlocks,
  marketBlocks,
  newsBlocks,
  oppBlocks,
  paperBlocks,
  stateFa,
  stopLossBlocks,
  watchBlocks,
  whyBlocks,
  whyCanonicalBlocks,
  type Snap,
} from "./chat_replies";

export type ChatResponse = {
  reply: string;
  /** Same content as `reply`, formatted for Telegram parse_mode=HTML (escaped). */
  replyHtml?: string;
  intent: string;
  evidence: Record<string, unknown>;
  focusToken?: string | null;
};

export type ChatContext = {
  focusToken?: string | null;
  history?: Array<{ role: "user" | "assistant"; content: string }>;
  /** Client-claimed channel: recorded in the audit only, NEVER a grant (GM-04). */
  channel?: string | null;
  /** Client-claimed sender id: hashed in the audit, never stored raw. */
  userId?: string | null;
};

export async function handleChat(message: string, ctx: ChatContext = {}): Promise<ChatResponse> {
  const text = message.trim();
  const intent = detectIntent(text);

  // GM-04 capability gate (deny-by-default). The chat path cannot prove it is the
  // local dashboard (shared bearer token, client-supplied channel), so engine
  // start/stop and paper_buy are refused here for EVERY channel. Dashboard
  // buttons (/api/engine, /api/paper) are unchanged. Audited with hashed ids.
  const gate = gateChatControl({ intent, text, channelClaimed: ctx.channel, userId: ctx.userId });
  if (gate.controlled) {
    recordControlAudit({
      surface: "chat",
      intent,
      capability: gate.capability,
      decision: "REFUSED",
      reason: gate.reason,
      channelClaimed: ctx.channel,
      userId: ctx.userId,
      text,
    });
    // Locked: control refusals are always shown verbatim (never rephrased).
    const refusal = await finalizeReply({ intent, blocks: blocksFromText(gate.replyFa ?? ""), footer: FINAL_USER_LINE, locked: true });
    return {
      reply: refusal.plain,
      replyHtml: refusal.html,
      intent,
      evidence: {
        intent,
        at: new Date().toISOString(),
        control: { gm: "GM-04", capability: gate.capability, decision: "REFUSED", reason: gate.reason },
      },
      focusToken: ctx.focusToken ?? null,
    };
  }
  const snap = await commandSnapshot();
  let focus =
    ctx.focusToken ||
    extractFocusFromHistory(ctx.history) ||
    null;
  let blocks: ReplyBlock[] = [];
  const evidence: Record<string, unknown> = {
    intent,
    at: new Date().toISOString(),
    focusIn: focus,
  };

  if (intent === "market") {
    blocks = marketBlocks(snap);
  } else if (intent === "opportunities") {
    blocks = oppBlocks(snap);
    const fromCanon = canonicalFocusTokenKey(snap.canonicalDecisions ?? []);
    const top =
      snap.opportunities.find((o) => o.decision === "BUY") ||
      snap.opportunities.find((o) => o.decision === "WATCH" || o.decision === "MONITOR_ONLY");
    if (fromCanon) focus = fromCanon;
    else if (top) focus = top.tokenKey;
  } else if (intent === "news") {
    blocks = newsBlocks(snap, text);
  } else if (intent === "stop_loss") {
    const hit = findOpp(snap, text, focus);
    blocks = stopLossBlocks(hit);
    if (hit) focus = hit.tokenKey;
  } else if (intent === "health") {
    blocks = healthBlocks(snap);
  } else if (intent === "council") {
    blocks = councilBlocks(snap, findOpp(snap, text, focus));
  } else if (intent === "learning") {
    blocks = learningBlocks(snap);
  } else if (intent === "watchlist") {
    blocks = watchBlocks(snap);
  } else if (intent === "paper_list") {
    blocks = paperBlocks(snap);
  } else if (intent === "whales") {
    const hit = findOpp(snap, text, focus);
    blocks = hit
      ? [
          title(`🐋 نهنگ‌ها — ${hit.symbol}`),
          line("نقش کیف پول‌های بزرگ مشخص نیست (سندی ثبت نشده)؛ اسمارت‌مانی را حدس نمی‌زنم."),
          bullet(`امنیت فعلی: ${stateFa(hit.securityStatus)}`),
        ]
      : [
          title("🐋 نهنگ‌ها"),
          line("بدون سند نقش کیف پول چیزی نمی‌سازم. نماد توکن را بنویس تا همان را بررسی کنم."),
        ];
    if (hit) focus = hit.tokenKey;
  } else if (intent === "watch_add") {
    const hit = findOpp(snap, text, focus);
    if (!hit) {
      blocks = [line("این نماد در فهرست فعلی نیست. نماد را دقیق‌تر بنویس؛ حدس نمی‌زنم.")];
    } else {
      await addWatch({
        tokenKey: hit.tokenKey,
        symbol: hit.symbol,
        chain: hit.chain,
        address: hit.address,
        thesisFa: `پایش به درخواست کاربر: ${text}`,
      });
      blocks = [
        title(`👀 ${hit.symbol} به واچ‌لیست اضافه شد`),
        bullet(`شبکه: ${hit.chain}`),
        bullet(`حکم فعلی: ${decisionFa(hit.decision)} · اطمینان: ${confidenceFa(hit.confidence)}`),
        hit.invalidationFa ? bullet(`شرط ابطال: ${hit.invalidationFa}`) : gap(),
      ];
      evidence.tokenKey = hit.tokenKey;
      focus = hit.tokenKey;
    }
  } else if (intent === "paper_buy") {
    // Unreachable from chat while the GM-04 gate refuses PAPER_WRITE (above).
    // Kept as defence in depth: even if reached, only canonical BUY may record paper.
    let reply = "";
    const hit = findOpp(snap, text, focus);
    const price =
      extractNumber(text, /(?:قیمت|با|@)\s*([0-9]+(?:\.[0-9]+)?)/) ??
      (hit?.payload ? num(hit.payload.priceUsd) : null);
    const qty = extractNumber(text, /(?:مقدار|تعداد|تا)\s*([0-9]+(?:\.[0-9]+)?)/);
    if (!hit && !extractSymbol(text)) {
      reply = "برای ثبت خرید کاغذی باید نماد مشخص باشه. خرید واقعی انجام نمی‌دم.";
    } else {
      const model = await loadCanonicalReadModel();
      if (!paperAllowedFromCanonical(model, hit?.chain, hit?.address || null)) {
        // Internal reason code CANONICAL_PAPER_DENIED is kept in evidence, not in user text.
        evidence.paperDenied = "CANONICAL_PAPER_DENIED";
        reply = "خرید کاغذی ثبت نشد: فقط وقتی حکم سیستم «خرید» باشد ثبت کاغذی مجاز است.";
      } else {
        const symbol = hit?.symbol || extractSymbol(text) || "UNKNOWN";
        try {
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
          reply = `ثبت شد — فقط کاغذی. نماد ${symbol}. ورود ${price ?? "نامشخص"}. مقدار ${qty ?? "نامشخص"}. هیچ سفارشی به صرافی نرفت.`;
          evidence.positionId = row.id;
          if (hit) focus = hit.tokenKey;
        } catch (err) {
          if (err instanceof PaperSecurityDenied) {
            reply = `خرید کاغذی ثبت نشد: بررسی امنیت تأیید نشده (${err.canonicalSecurityState}).`;
          } else {
            reply = "خرید کاغذی ثبت نشد — خطا در ثبت. خرید واقعی انجام نشد.";
          }
        }
      }
    }
    blocks = blocksFromText(reply);
  } else if (intent === "why" || intent === "token") {
    const hit = findOpp(snap, text, focus);
    const canonHit = hit ? null : findCanonicalDecision(snap.canonicalDecisions ?? [], text, focus);
    if (hit) {
      blocks = whyBlocks(hit);
      focus = hit.tokenKey;
    } else if (canonHit) {
      blocks = whyCanonicalReply(canonHit);
      focus = canonHit.tokenKey;
    } else {
      blocks = [
        line(
          intent === "why"
            ? "کدام توکن؟ نماد را بنویس (مثلاً «چرا PEPE؟»). بدون مصداق، دلیل نمی‌سازم."
            : "این نماد در فهرست فعلی نیست. نماد را دقیق‌تر بنویس.",
        ),
      ];
    }
  } else if (intent === "reject") {
    const rejectedCanon = (snap.canonicalDecisions ?? [])
      .filter((d) => d.outcome === "REJECT")
      .slice(0, 5);
    const rejectedOpp = snap.opportunities.filter((o) => o.decision === "REJECT").slice(0, 5);
    if (rejectedCanon.length) {
      blocks = [
        title("🚫 توکن‌های رد شده"),
        ...rejectedCanon.map((d) =>
          bullet(
            `${d.symbol || "نامشخص"} (${d.chain || "نامشخص"}) — امنیت: ${stateFa(d.securityState)}${d.primaryReason ? ` — ${d.primaryReason}` : ""}`,
          ),
        ),
      ];
    } else if (rejectedOpp.length) {
      blocks = [
        title("🚫 توکن‌های رد شده"),
        ...rejectedOpp.map((o) => bullet(`${o.symbol}: ${(o.risksFa || []).slice(0, 2).join(" ") || "دلیل ثبت نشده"}`)),
      ];
    } else {
      blocks = [line("در آخرین بررسی توکنی رد نشده، یا هنوز بررسی‌ای انجام نشده.")];
    }
  } else if (intent === "greeting") {
    blocks = greetingReply(snap);
  } else if (intent === "help") {
    blocks = helpReply();
  } else {
    const hit = findOpp(snap, text, focus);
    const canonHit = hit ? null : findCanonicalDecision(snap.canonicalDecisions ?? [], text, focus);
    if (hit && isPronounQuery(text)) {
      blocks = whyBlocks(hit);
      focus = hit.tokenKey;
    } else if (canonHit && isPronounQuery(text)) {
      blocks = whyCanonicalReply(canonHit);
      focus = canonHit.tokenKey;
    } else {
      blocks = await generalReply(text, snap);
    }
  }

  let running = false;
  try {
    const state = await getState();
    running = Boolean(state?.running);
  } catch {
    running = false;
  }
  // Engine-off notice only where it matters (help/greeting, opportunities,
  // system health, or the user asked about the engine) — not on every reply.
  if (!running && engineNoticeRelevant(intent, text)) {
    blocks.push(gap(), note(ENGINE_OFF_NOTE));
  }
  // Shared composer for dashboard chat and Telegram. No phraser is configured
  // (LLM seam documented in response_composer.ts); deterministic text is final.
  const composed = await finalizeReply({ intent, blocks, footer: FINAL_USER_LINE });
  const reply = composed.plain;
  const replyHtml = composed.html;
  evidence.composer = composed.composer;
  evidence.focusToken = focus;

  try {
    await db.insert(chatMessages).values({ role: "user", content: text, intent, evidence });
    await db.insert(chatMessages).values({ role: "assistant", content: reply, intent, evidence });
  } catch {
    /* DB optional when DATABASE_URL missing */
  }
  return { reply, replyHtml, intent, evidence, focusToken: focus };
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
  // GM-04: explicit whole-message commands only ("stop loss", "start-up" never match).
  const control = detectControlCommand(text);
  if (control) return control;
  if (/(زیر نظر|واچ|watch)/i.test(text)) return "watch_add";
  if (looksLikePaperBuy(text)) return "paper_buy";
  if (/(پورتف|موقعیت|کاغذی‌ها)/i.test(text)) return "paper_list";
  if (/(واچ‌لیست|watchlist|تحت نظر)/i.test(text)) return "watchlist";
  if (isStopLossQuestion(text)) return "stop_loss";
  if (/(رد شد|چرا رد|reject)/i.test(text)) return "reject";
  if (/(چرا|دلیل|شواهد|explain)/i.test(text)) return "why";
  // "بازار چه خبر؟" is a market question, not a news request.
  if (isNewsRequest(text)) return "news";
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

function greetingReply(snap: Snap): ReplyBlock[] {
  const status = snap.canonicalReadModel?.status;
  const n =
    status === "AVAILABLE"
      ? (snap.canonicalDecisions ?? []).filter((d) => d.outcome && d.outcome !== "REJECT").length
      : null;
  return greetingBlocks(n);
}

function helpReply(): ReplyBlock[] {
  return helpBlocks();
}

function whyCanonicalReply(d: CanonicalDecisionView): ReplyBlock[] {
  return whyCanonicalBlocks(d);
}

async function generalReply(text: string, snap: Snap): Promise<ReplyBlock[]> {
  const hit = findOpp(snap, text, null);
  if (hit) return whyBlocks(hit);
  const buyCount = (snap.canonicalDecisions ?? []).filter((d) => d.outcome === "BUY").length;
  return generalBlocks(buyCount);
}

function findOpp(
  snap: Snap,
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
