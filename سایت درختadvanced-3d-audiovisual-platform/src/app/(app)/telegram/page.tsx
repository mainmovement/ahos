import { PageHeader } from "@/components/page-header";
import { TelegramDesk } from "@/components/telegram-desk";
import { loadTelegram } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function TelegramPage() {
  const messages = await loadTelegram();
  return (
    <div>
      <PageHeader
        kicker="Telegram"
        title="The fast mouth of the tree."
        lede="Complementary relay: discovery, security, exit, whale, daily, paper result. The bot never trades. It reports."
      />
      <TelegramDesk initial={messages} />
    </div>
  );
}
