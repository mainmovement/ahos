import { listSystemStatus } from "@/lib/queries";
import { PageHeader, KpiCard } from "@/components/dashboard/Shared";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { timeAgo } from "@/lib/utils";
import { Activity, CheckCircle2, AlertTriangle, XCircle, Wrench } from "lucide-react";

export const dynamic = "force-dynamic";

const statusMeta: Record<string, { tone: "good" | "gold" | "danger" | "neutral"; icon: typeof CheckCircle2 }> = {
  operational: { tone: "good", icon: CheckCircle2 },
  degraded: { tone: "gold", icon: AlertTriangle },
  down: { tone: "danger", icon: XCircle },
  maintenance: { tone: "neutral", icon: Wrench },
};

const levelTone: Record<string, "danger" | "gold" | "cyan"> = { error: "danger", warning: "gold", info: "cyan" };

export default async function SystemStatusPage() {
  const { components, logs } = await listSystemStatus();

  const operational = components.filter((c) => c.status === "operational").length;
  const degraded = components.filter((c) => c.status === "degraded").length;
  const down = components.filter((c) => c.status === "down").length;
  const avgUptime =
    components.reduce((sum, c) => sum + Number(c.uptimePercent ?? 100), 0) / (components.length || 1);

  const grouped = components.reduce<Record<string, typeof components>>((acc, c) => {
    (acc[c.category] ??= []).push(c);
    return acc;
  }, {});

  return (
    <div>
      <PageHeader
        eyebrow="Self-Debug Loop"
        title="System Status"
        description="Every provider, indexer, and automation layer is monitored. Failures are detected, logged, and routed toward a controlled fix."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Operational" value={operational} icon={<CheckCircle2 size={16} />} tone="emerald" />
        <KpiCard label="Degraded" value={degraded} icon={<AlertTriangle size={16} />} tone="gold" />
        <KpiCard label="Down" value={down} icon={<XCircle size={16} />} tone="rose" />
        <KpiCard label="Avg. Uptime" value={`${avgUptime.toFixed(2)}%`} icon={<Activity size={16} />} tone="cyan" />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        {Object.entries(grouped).map(([category, items]) => (
          <Card key={category}>
            <CardHeader title={category} subtitle={`${items.length} component(s)`} />
            <div className="space-y-2.5">
              {items.map((c) => {
                const meta = statusMeta[c.status];
                const Icon = meta.icon;
                return (
                  <div key={c.id} className="flex items-center justify-between gap-3 rounded-lg border border-white/8 bg-white/[0.02] p-3">
                    <div className="flex items-center gap-2.5">
                      <Icon size={15} className={meta.tone === "good" ? "text-emerald-400" : meta.tone === "gold" ? "text-amber-400" : meta.tone === "danger" ? "text-rose-400" : "text-slate-400"} />
                      <div>
                        <div className="text-sm text-slate-100">{c.name}</div>
                        <div className="text-xs text-slate-500">{c.message}</div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge tone={meta.tone}>{c.status}</Badge>
                      <span className="text-[10px] text-slate-600">{c.latencyMs}ms · {timeAgo(c.lastChecked)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader title="System Logs" subtitle="Most recent 30 events across every component" />
        <div className="space-y-1.5 font-mono text-xs">
          {logs.map((log) => (
            <div key={log.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-white/5 bg-black/20 px-3 py-2">
              <Badge tone={levelTone[log.level] ?? "neutral"} className="w-16 justify-center">{log.level}</Badge>
              <span className="text-slate-500">{c(log.component)}</span>
              <span className="flex-1 text-slate-300">{log.message}</span>
              <span className="text-slate-600">{timeAgo(log.createdAt)}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function c(component: string) {
  return `[${component}]`;
}
