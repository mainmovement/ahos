import type { ChatMessage, DataEnvelope } from "./types";
import { fromMock, label } from "./_envelope";
import { mockChatSeed, mockKianReply } from "@/mock/chat";

/**
 * Ask Kian. Client-callable. Real source: POST /api/chat (ConversationResponse
 * in the AHOS repo). The mock responder is rule-based and never claims LIVE.
 */
export async function askKian(message: string, locale: "fa" | "en"): Promise<DataEnvelope<ChatMessage>> {
  return fromMock(mockKianReply(message, locale), "chat", label("پاسخ‌دهنده نمایشی کیان", "Kian demo responder"), 0, 60);
}

export async function getChatSeed(locale: "fa" | "en"): Promise<DataEnvelope<ChatMessage[]>> {
  return fromMock(mockChatSeed(locale), "chat", label("پاسخ‌دهنده نمایشی کیان", "Kian demo responder"), 0, 60);
}
