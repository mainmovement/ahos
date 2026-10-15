import type { Metadata } from "next";
import { getChatSeed } from "@/lib/api/chat";
import { getAlerts } from "@/lib/api/system";
import { ChatView } from "@/components/views/chat-view";

export const metadata: Metadata = { title: "گفتگو با کیان · Kian Chat" };

export default async function ChatPage() {
  const [fa, en, alerts] = await Promise.all([getChatSeed("fa"), getChatSeed("en"), getAlerts()]);
  return <ChatView seed={{ fa: fa.data, en: en.data }} alerts={alerts} />;
}
