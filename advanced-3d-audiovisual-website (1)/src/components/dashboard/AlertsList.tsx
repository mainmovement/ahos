"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Check, Bell, ShieldAlert, TrendingUp, Newspaper, LogOut, Server, FileText, Waves } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { timeAgo } from "@/lib/utils";
import { useAudio } from "@/components/system/AudioProvider";
import { EmptyState } from "@/components/dashboard/Shared";

type AlertRow = {
  alert: {
    id: number; type: string; severity: "info" | "warning" | "critical"; title: string; message: string;
    isRead: boolean; sentToTelegram: boolean; createdAt: string;
  };
  token: { id: number; name: string; symbol: string; logoEmoji: string | null } | null;
};

const typeIcons: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  discovery: TrendingUp, opportunity: TrendingUp, security: ShieldAlert, whale: Waves,
  news: Newspaper, exit: LogOut, system: Server, daily_report: FileText,
};

export function AlertsList({ initial }: { initial: AlertRow[] }) {
  const [rows, setRows] = useState(initial);
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const { play } = useAudio();

  async function markRead(id: number, isRead: boolean) {
    setRows((prev) => prev.map((r) => (r.alert.id === id ? { ...r, alert: { ...r.alert, isRead } } : r)));
    play.click();
    await fetch("/api/alerts", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, isRead }),
    });
  }

  const visible = filter === "all" ? rows : rows.filter((r) => !r.alert.isRead);
  const unreadCount = rows.filter((r) => !r.alert.isRead).length;

  return (
    <div>
      <div className="mb-5 flex items-center gap-2">
        {(["all", "unread"] as const).map((f) => (
          <button
            key={f}
            data-cursor-interactive
            onClick={() => {
              setFilter(f);
              play.nav();
            }}
            className={`rounded-full border px-4 py-1.5 text-xs font-medium capitalize transition-colors ${
              filter === f ? "border-cyan-300/50 bg-cyan-300/10 text-cyan-200" : "border-white/10 text-slate-400 hover:text-slate-200"
            }`}
          >
            {f} {f === "unread" && unreadCount > 0 ? `(${unreadCount})` : ""}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState title="No alerts" description="You're all caught up." icon={<Bell size={20} />} />
      ) : (
        <div className="space-y-3">
          {visible.map(({ alert, token }) => {
            const Icon = typeIcons[alert.type] ?? Bell;
            return (
              <motion.div
                key={alert.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`glass noise-border flex items-start gap-4 rounded-2xl p-4 ${!alert.isRead ? "border-cyan-300/30" : ""}`}
              >
                <div
                  className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl border ${
                    alert.severity === "critical" ? "border-rose-400/30 bg-rose-400/10 text-rose-300"
                    : alert.severity === "warning" ? "border-amber-400/30 bg-amber-400/10 text-amber-300"
                    : "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                  }`}
                >
                  <Icon size={17} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-slate-100">{alert.title}</h3>
                    <div className="flex items-center gap-2">
                      <Badge tone={alert.severity === "critical" ? "danger" : alert.severity === "warning" ? "gold" : "cyan"}>{alert.severity}</Badge>
                      {alert.sentToTelegram && <Badge tone="neutral">Sent to Telegram</Badge>}
                    </div>
                  </div>
                  <p className="mt-1 text-sm text-slate-400">{alert.message}</p>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-slate-600">
                      {token ? `${token.logoEmoji} ${token.name} · ` : ""}
                      {timeAgo(alert.createdAt)}
                    </span>
                    {!alert.isRead && (
                      <button
                        data-cursor-interactive
                        onClick={() => markRead(alert.id, true)}
                        className="flex items-center gap-1 text-xs text-cyan-300 hover:text-cyan-200"
                      >
                        <Check size={13} /> Mark read
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
