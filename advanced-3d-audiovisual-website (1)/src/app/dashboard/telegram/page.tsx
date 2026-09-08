import { getAllSettings, listAlerts } from "@/lib/queries";
import { PageHeader } from "@/components/dashboard/Shared";
import { TelegramPanel } from "@/components/dashboard/TelegramPanel";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { timeAgo } from "@/lib/utils";
import { Send } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function TelegramPage() {
  const [settings, alerts] = await Promise.all([getAllSettings(), listAlerts(10)]);
  const telegramConfig = (settings.telegram as { botConnected: boolean; chatId: string; dailyReportEnabled: boolean; alertTypes: string[] }) ?? {
    botConnected: false, chatId: "", dailyReportEnabled: true, alertTypes: [],
  };
  const sentAlerts = alerts.filter((a) => a.alert.sentToTelegram);

  return (
    <div>
      <PageHeader
        eyebrow="Companion Interface"
        title="Telegram"
        description="A fast, conversational companion. Ask questions, receive alerts, and confirm real trades — all without opening the dashboard."
      />
      <TelegramPanel initial={telegramConfig} />

      <Card className="mt-6">
        <CardHeader title="Recently Delivered to Telegram" icon={<Send size={16} />} />
        <div className="space-y-2.5">
          {sentAlerts.map(({ alert, token }) => (
            <div key={alert.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/8 bg-white/[0.02] p-3">
              <div>
                <div className="text-sm text-slate-100">{alert.title}</div>
                <div className="mt-0.5 text-xs text-slate-500">{token ? `${token.name} · ` : ""}{timeAgo(alert.createdAt)}</div>
              </div>
              <Badge tone={alert.severity === "critical" ? "danger" : alert.severity === "warning" ? "gold" : "cyan"}>{alert.type.replace("_", " ")}</Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
