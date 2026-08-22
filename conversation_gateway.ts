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
  });
  return {
    answer: result.reply,
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
