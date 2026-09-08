import { db } from "@/db";
import { settings, systemLogs } from "@/db/schema";
import { eq } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function POST() {
  try {
    const [row] = await db.select().from(settings).where(eq(settings.key, "telegram"));
    const config = (row?.value as { chatId?: string }) ?? {};
    const botToken = process.env.TELEGRAM_BOT_TOKEN;

    const message =
      "🤖 AHOS test message — if you can read this, your Telegram companion is wired correctly.";

    if (botToken && config.chatId) {
      const res = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: config.chatId, text: message }),
      });
      const data = await res.json();
      if (!data.ok) {
        await db.insert(systemLogs).values({ level: "error", component: "Telegram Bot Gateway", message: `Send failed: ${data.description ?? "unknown error"}` });
        return Response.json({ ok: false, error: data.description ?? "Telegram API rejected the message." }, { status: 502 });
      }
      await db.insert(systemLogs).values({ level: "info", component: "Telegram Bot Gateway", message: "Test message delivered successfully." });
      return Response.json({ ok: true, mode: "live" });
    }

    // No bot token / chat id configured yet — simulate so the UI flow is always testable.
    await db.insert(systemLogs).values({
      level: "warning",
      component: "Telegram Bot Gateway",
      message: "Simulated test message (TELEGRAM_BOT_TOKEN or chat ID not configured).",
    });
    return Response.json({ ok: true, mode: "simulated" });
  } catch (err) {
    console.error(err);
    return Response.json({ ok: false, error: "Could not reach the Telegram gateway." }, { status: 500 });
  }
}
