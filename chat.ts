import { db } from "@/db";
import { chatMessages } from "@/db/schema";
import { desc } from "drizzle-orm";
import { getState } from "./engine";
import { gateChatControl, recordControlAudit } from "./chat_control_gate";
import {
  canonicalFocusTokenKey,
  findCanonicalDecision,
  type CanonicalDecisionView,
} from "./canonical_read_model";
import { commandSnapshot } from "./snapshot";
import { FINAL_USER_LINE } from "./types";
import { blocksFromText, bullet, gap, line, note, title, type ReplyBlock } from "./reply_format";
import { finalizeReply, phrasedHtml } from "./response_composer";
import { getDefaultPhraser } from "./gemini_phraser";
import { detectMajorAsset, extractDevMissionSummary, extractTicker, isPronounQuery, routeIntent } from "./chat_intent";
import {
  getPendingStore,
  handleConfirmation,
  isOwner,
  parseConfirmation,
  proposalTextFa,
  propose,
  toPublic,
  type ActionDeps,
  type ActionKind,
  type Identity,
  type PublicPendingAction,
  type PendingActionStore,
} from "./chat_actions";
import { getDefaultChatAgent } from "./chat_agent";
import { getConversationMemory, memoryKey, redactSecrets, stripConfirmCodes } from "./chat_memory";
import { getDevMissionStore } from "./dev_missions";
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
  learningBlocks,
  marketBlocks,
  newsBlocks,
  oppBlocks,
  paperBlocks,
  priceBlocks,
  stateFa,
  stopLossBlocks,
  thanksBlocks,
  tradeSignalBlocks,
  watchBlocks,
  whyBlocks,
  whyCanonicalBlocks,
  type Snap,
} from "./chat_replies";

export type ChatResponse = {
  reply: string;
  /** Same content as "reply", formatted for Telegram parse_mode=HTML (escaped). */
  replyHtml?: string;
  intent: string;
  evidence: Record<string, unknown>;
  focusToken?: string | null;
  /** Phase 7b: a confirm-gated owner action awaiting «تایید <code>» (dashboard shows buttons). */
  pendingAction?: PublicPendingAction | null;
};

const AGENT_DOWN_NOTE = "دستیار هوشمند الان در دسترس نیست؛ این پاسخ استاندارد سیستم است.";
const AGENT_UNVERIFIED_NOTE = "پاسخ دستیار هوشمند با داده‌های سیستم تطبیق نداشت؛ این پاسخ استاندارد سیستم است.";

/** Locked (verbatim) reply: refusals, proposals, confirmations. */
async function lockedReply(intent: string, textFa: string) {
  return finalizeReply({ intent, blocks: blocksFromText(textFa), footer: FINAL_USER_LINE, locked: true });
}

/** Persist one exchange. Mission 9.5 m3: secrets and live confirm codes are
 * redacted before the DB write — a key pasted into chat must not land in
 * `chat_messages`, and the proposal text (which carries the one-time code) must
 * not either. The DB is best-effort; a missing DATABASE_URL is fine. */
async function persistChat(text: string, reply: string, intent: string, evidence: Record<string, unknown>) {
  try {
    const cleanUser = stripConfirmCodes(redactSecrets(text));
    const cleanReply = stripConfirmCodes(redactSecrets(reply));
    await db.insert(chatMessages).values({ role: "user", content: cleanUser, intent, evidence });
    await db.insert(chatMessages).values({ role: "assistant", content: cleanReply, intent, evidence });
  } catch {
    /* DB optional when DATABASE_URL missing */
  }
}

export type ChatContext = {
  focusToken?: string | null;
  history?: Array<{ role: "user" | "assistant"; content: string }>;
  /**
   * The RESOLVED channel/user id (Mission 9.5): for a /api/chat call these come
   * from chat_auth.ts — a verified Telegram HMAC or a verified dashboard
   * session — and `proven` records which. For any other caller they are the
   * client's assertion, `proven` is false, and the caller is not the owner.
   * Both are still written to the audit as `channel_claimed` / a hashed id;
   * neither is ever a grant.
   */
  channel?: string | null;
  userId?: string | null;
  proven?: boolean;
};

/**
 * MJ-12: a behaviour-test seam. Overriding the snapshot source and the confirm
 * deps removes every database and network dependency from `handleChat` (the
 * snapshot is the only place it reads live data; the confirm deps are the only
 * place it executes anything), so the confirm-gated control surface can be
 * exercised offline: owner/non-owner, propose/confirm/wrong-code/expired/cancel.
 * The override is process-local and never reachable from a request body.
 */
let testDeps: {
  snapshot?: () => Promise<Snap>;
  actionDeps?: ActionDeps;
  store?: PendingActionStore;
} | null = null;

export function setChatTestDeps(
  d: { snapshot?: () => Promise<Snap>; actionDeps?: ActionDeps; store?: PendingActionStore } | null,
): void {
  testDeps = d;
}

async function takeSnapshot(): Promise<Snap> {
  if (testDeps?.snapshot) return await testDeps.snapshot();
  return await commandSnapshot();
}

export async function handleChat(message: string, ctx: ChatContext = {}): Promise<ChatResponse> {
  const text = message.trim();
  const identity: Identity = {
    channel: ctx.channel ?? null,
    userId: ctx.userId ?? null,
    proven: Boolean(ctx.proven),
  };
  const memKey = memoryKey(identity.channel, identity.userId);
  const memory = getConversationMemory();
  const store = testDeps?.store ?? getPendingStore();
  const missions = getDevMissionStore();

  // Phase 7b: whole-message «تایید <code>» / «لغو» for a pending owner action.
  // Executes only via chat_actions.ts (same functions as the dashboard buttons), audited.
  const confirmation = parseConfirmation(text);
  if (confirmation) {
    const r = await handleConfirmation(store, confirmation, identity, text,
      testDeps?.actionDeps ? { deps: testDeps.actionDeps } : {});
    const out = await lockedReply("confirm", r.replyFa);
    const evidence = { intent: "confirm", at: new Date().toISOString(), confirm: { op: confirmation.op, executed: r.executed, kind: r.kind } };
    memory.append(memKey, text, out.plain);
    await persistChat(text, out.plain, "confirm", evidence);
    return { reply: out.plain, replyHtml: out.html, intent: "confirm", evidence, focusToken: ctx.focusToken ?? null, pendingAction: null };
  }

  const intent = detectIntent(text);

  // GM-04 capability gate (whole-message detection; «stop loss» is never a stop).
  // Mission 9.5: the owner decision uses the SERVER-VERIFIED identity only.
  // Non-owners are refused and audited. Owners (a Telegram admin id proven by
  // the bot's HMAC, or a verified dashboard session) get a confirm-gated
  // proposal instead (owner authority decision 2026-10-02, pending
  // سپهر/قاسم/رضا review). Dashboard buttons unchanged.
  const gate = gateChatControl({ intent, text, channelClaimed: ctx.channel, userId: ctx.userId });
  if (gate.controlled && !isOwner(identity)) {
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
    const refusal = await lockedReply(intent, gate.replyFa ?? "");
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
  if (gate.controlled) {
    // Phase 7b (owner authority decision 2026-10-02): the owner gets a confirm-gated
    // proposal instead of a refusal. Nothing runs until «تایید <code>».
    const kind: ActionKind = intent === "start" ? "engine_start" : intent === "stop" ? "engine_stop" : "paper_buy";
    const params: { symbol?: string | null; tokenKey?: string | null; chain?: string | null; address?: string | null } = {};
    if (kind === "paper_buy") {
      const s0 = await takeSnapshot();
      const hit = findOpp(s0, text, ctx.focusToken ?? null);
      Object.assign(params, { symbol: hit?.symbol ?? extractSymbol(text), tokenKey: hit?.tokenKey ?? null, chain: hit?.chain ?? null, address: hit?.address ?? null });
    }
    const r = propose(store, kind, params, identity, text);
    const msg = r.ok
      ? proposalTextFa(r.action)
      : "برای ثبت خرید کاغذی، نماد توکنی را بنویس که در فهرست بررسی سیستم باشد. هیچ تغییری اعمال نشد.";
    const out = await lockedReply("proposal", msg);
    const evidence = { intent, at: new Date().toISOString(), control: { capability: gate.capability, decision: r.ok ? "PROPOSED" : "DENIED" } };
    memory.append(memKey, text, out.plain);
    await persistChat(text, out.plain, "proposal", evidence);
    return { reply: out.plain, replyHtml: out.html, intent: "proposal", evidence, focusToken: ctx.focusToken ?? null, pendingAction: r.ok ? toPublic(r.action) : null };
  }
  const snap = await takeSnapshot();
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

  // Phase 7b: conversational agent first (Gemini + whitelisted read tools +
  // confirm-gated proposals). Any failure → deterministic path below + honest note.
  const agent = getDefaultChatAgent();
  let agentNote: string | null = null;
  if (agent) {
    const agentStarted = Date.now();
    const r = await agent.run({ text, snap, history: memory.get(memKey), identity, store, missions, footer: FINAL_USER_LINE });
    evidence.agent = { ok: r.ok, reason: r.ok ? "OK" : r.reason, toolsUsed: r.toolsUsed, steps: r.steps, model: r.ok ? r.model : null, latencyMs: Date.now() - agentStarted };
    if (r.ok) {
      const out = r.locked
        ? await lockedReply(r.proposal ? "proposal" : "agent", r.plain)
        : { plain: r.plain + "\n\n— " + FINAL_USER_LINE, html: phrasedHtml(r.plain + "\n\n— " + FINAL_USER_LINE, FINAL_USER_LINE) };
      const agentIntent = r.proposal ? "proposal" : "agent";
      evidence.composer = r.locked ? "deterministic" : "gemini_agent";
      memory.append(memKey, text, r.plain);
      await persistChat(text, out.plain, agentIntent, evidence);
      return { reply: out.plain, replyHtml: out.html, intent: agentIntent, evidence, focusToken: focus, pendingAction: r.proposal ? toPublic(r.proposal) : null };
    }
    if (r.reason !== "CIRCUIT_OPEN" || agent.isOpen()) {
      agentNote = r.reason.startsWith("VALIDATION") ? AGENT_UNVERIFIED_NOTE : AGENT_DOWN_NOTE;
    }
  }

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
  } else if (intent === "price") {
    blocks = priceBlocks(snap, detectMajorAsset(text), extractTicker(text));
  } else if (intent === "trade_signal") {
    // PAPER_ONLY: no leverage / long-short / TP-SL signals, no coin picks.
    blocks = tradeSignalBlocks();
  } else if (intent === "thanks") {
    blocks = thanksBlocks();
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
    // Phase 7b: watchlist writes from chat are confirm-gated too (owner only).
    const hit = findOpp(snap, text, focus);
    if (!hit) {
      blocks = [line("این نماد در فهرست فعلی نیست. نماد را دقیق‌تر بنویس؛ حدس نمی‌زنم.")];
    } else {
      const r = propose(store, "watch_add", { symbol: hit.symbol, tokenKey: hit.tokenKey, chain: hit.chain, address: hit.address }, identity, text);
      if (r.ok) {
        const out = await lockedReply("proposal", proposalTextFa(r.action));
        memory.append(memKey, text, out.plain);
        await persistChat(text, out.plain, "proposal", evidence);
        return { reply: out.plain, replyHtml: out.html, intent: "proposal", evidence, focusToken: hit.tokenKey, pendingAction: toPublic(r.action) };
      }
      blocks = [line("⛔ افزودن به واچ‌لیست فقط برای مالک سیستم مجاز است. هیچ تغییری اعمال نشد.")];
      focus = hit.tokenKey;
    }
  } else if (intent === "dev_mission") {
    // Phase 8 (deterministic fallback when the conversational agent is off):
    // an engineering-work request becomes a confirm-gated dev mission (owner only).
    const summary = extractDevMissionSummary(text);
    if (!summary) {
      blocks = [line("درخواستی برای ثبت پیدا نشد؛ لطفاً دقیق‌تر بنویس که چه کاری می‌خواهی انجام شود.")];
    } else {
      const r = propose(store, "dev_mission", { missionSummaryFa: summary }, identity, text);
      if (r.ok) {
        const out = await lockedReply("proposal", proposalTextFa(r.action));
        memory.append(memKey, text, out.plain);
        await persistChat(text, out.plain, "proposal", evidence);
        return { reply: out.plain, replyHtml: out.html, intent: "proposal", evidence, focusToken: ctx.focusToken ?? null, pendingAction: toPublic(r.action) };
      }
      blocks = [line("⛔ ثبت ماموریت توسعه فقط برای مالک سیستم مجاز است. هیچ تغییری اعمال نشد.")];
    }
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
  // Shared composer for dashboard chat and Telegram. Phase 6: the Gemini phraser
  // may rewrite the grounded draft; validatePhrased() guards it and any failure
  // falls back to the deterministic text (see gemini_phraser.ts).
  if (agentNote) blocks.unshift(note(agentNote), gap());
  // When the agent just failed, Gemini is likely down too: skip the phraser.
  const phraser = agentNote ? null : getDefaultPhraser();
  const phraseStarted = Date.now();
  // trade_signal is a PAPER_ONLY policy reply: locked so no phraser can add a coin pick.
  const composed = await finalizeReply({ intent, blocks, footer: FINAL_USER_LINE, locked: intent === "trade_signal" }, phraser);
  const reply = composed.plain;
  const replyHtml = composed.html;
  evidence.composer = composed.composer;
  if (phraser) {
    evidence.phraser = {
      used: composed.composer === phraser.name,
      rejected: composed.phraserRejected ?? null,
      reason: phraser.stats.lastReason,
      model: composed.composer === phraser.name ? phraser.stats.lastModel : null,
      latencyMs: Date.now() - phraseStarted,
    };
  }
  evidence.focusToken = focus;

  memory.append(memKey, text, reply);
  await persistChat(text, reply, intent, evidence);
  return { reply, replyHtml, intent, evidence, focusToken: focus, pendingAction: null };
}

export async function chatHistory(limit = 24) {
  try {
    const rows = await db.select().from(chatMessages).orderBy(desc(chatMessages.id)).limit(limit);
    return rows.reverse();
  } catch {
    return [];
  }
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
  // Phase 7: the router lives in chat_intent.ts (pure, regression-tested).
  // Order is kept: GM-04 control/paper_buy first, then trade_signal, stop_loss,
  // reject (رد شد|چرا رد|reject) before why (چرا|دلیل|شواهد|explain), price, ...
  return routeIntent(text, {
    isReject: (t) => /(رد شد|چرا رد|reject)/i.test(t),
    isWhy: (t) => /(چرا|دلیل|شواهد|explain)/i.test(t),
  });
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
