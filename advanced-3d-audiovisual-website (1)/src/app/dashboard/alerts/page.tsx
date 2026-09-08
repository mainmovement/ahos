import { listAlerts } from "@/lib/queries";
import { PageHeader } from "@/components/dashboard/Shared";
import { AlertsList } from "@/components/dashboard/AlertsList";

export const dynamic = "force-dynamic";

export default async function AlertsPage() {
  const rows = await listAlerts(100);
  const serialized = rows.map((r) => ({
    alert: { ...r.alert, createdAt: r.alert.createdAt.toISOString() },
    token: r.token ? { id: r.token.id, name: r.token.name, symbol: r.token.symbol, logoEmoji: r.token.logoEmoji } : null,
  }));

  return (
    <div>
      <PageHeader eyebrow="Notifications" title="Alerts" description="Every discovery, security flag, exit signal, and daily report — in one place." />
      <AlertsList initial={serialized} />
    </div>
  );
}
