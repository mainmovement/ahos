import { PageHeader } from "@/components/page-header";
import { ChatDesk } from "@/components/chat-desk";
import { loadChat } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function ChatPage() {
  const messages = await loadChat();
  return (
    <div>
      <PageHeader
        kicker="AI chat"
        title="Ask the chamber."
        lede="Local council engine. Optional cloud models later. Rumor is tagged. Unknown is spoken. No FOMO."
      />
      <ChatDesk initial={messages} />
    </div>
  );
}
