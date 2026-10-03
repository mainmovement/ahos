import { handleChat, type ChatResponse } from "./chat";
import type { ConversationRequest, ConversationResponse } from "./types";

/** Single conversation entry for Web and Telegram clients. */
export async function conversationGateway(
  req: ConversationRequest,
): Promise<ConversationResponse> {
  const message = (req.message || "").trim();
  const now = new Date().toISOString();
  if (!message) {
    return {
      answer: "پیام خالی بود.",
      intent: "empty",
      entities: {},
      focus_token: req.focus_token ?? null,
      referenced_token: req.referenced_token ?? null,
      evidence: { empty: true },
      uncertainty: ["empty"],
      suggested_followups: [],
      timestamp: now,
      conversation_id: req.conversation_id ?? null,
    };
  }
  const result: ChatResponse = await handleChat(message, {
    focusToken: req.focus_token ?? req.referenced_token ?? null,
    history: req.history,
    // Mission 9.5: identity is what the server verified (HMAC or session), not
    // what the client asserted. The asserted channel/user id are still carried
    // through for the audit (`channel_claimed`, hashed id) — never as a grant.
    channel: req.identity?.channel ?? req.channel ?? null,
    userId: req.identity?.userId ?? req.user_id ?? null,
    proven: Boolean(req.identity?.proven),
  });
  return {
    answer: result.reply,
    // Presentation only: same content escaped for Telegram parse_mode=HTML.
    answer_html: result.replyHtml,
    // Phase 7b: confirm-gated owner action (dashboard renders confirm/cancel buttons).
    pending_action: result.pendingAction ?? null,
    intent: result.intent || "unknown",
    entities: { focusToken: result.focusToken ?? null, channel: req.channel },
    focus_token: result.focusToken ?? null,
    referenced_token: req.referenced_token ?? result.focusToken ?? null,
    evidence: result.evidence || {},
    uncertainty: ["UNKNOWN preserved where data missing"],
    suggested_followups: [],
    timestamp: now,
    conversation_id: req.conversation_id ?? null,
  };
}
