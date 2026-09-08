import { listPaperTrades, listLearningLogs, getGlobalStats } from "@/lib/queries";
import { PageHeader, KpiCard } from "@/components/dashboard/Shared";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatUsd, formatPercent, timeAgo } from "@/lib/utils";
import { Wallet2, TrendingUp, TrendingDown, Percent, Brain, ThumbsUp, ThumbsDown, SkipForward } from "lucide-react";
import { PnlAreaChart } from "@/components/dashboard/charts/OverviewCharts";
import { EmptyState } from "@/components/dashboard/Shared";

export const dynamic = "force-dynamic";

const patternIcon = { success: ThumbsUp, failure: ThumbsDown, skip: SkipForward } as const;
const patternTone = { success: "good", failure: "danger", skip: "neutral" } as const;

export default async function PaperTradingPage() {
  const [{ trades, events }, learningLogs, stats] = await Promise.all([listPaperTrades(), listLearningLogs(), getGlobalStats()]);

  const open = trades.filter((t) => t.trade.status === "open");
  const closed = trades.filter((t) => t.trade.status === "closed").sort((a, b) => new Date(a.trade.closedAt ?? 0).getTime() - new Date(b.trade.closedAt ?? 0).getTime());
  let cumulative = 0;
  const pnlData = closed.map((t) => {
    cumulative += Number(t.trade.pnlUsd ?? 0);
    return { label: t.token.symbol, pnl: Number(cumulative.toFixed(2)) };
  });
  if (pnlData.length === 0) pnlData.push({ label: "Start", pnl: 0 });

  const winRate = stats.closedTrades > 0 ? Math.round((stats.wins / stats.closedTrades) * 100) : 0;
  const avgReturn =
    closed.length > 0 ? closed.reduce((sum, t) => sum + Number(t.trade.pnlPercent ?? 0), 0) / closed.length : 0;

  return (
    <div>
      <PageHeader
        eyebrow="Sections 16-20"
        title="Paper Trading Engine"
        description="Every opportunity — including skips — is followed through its full lifecycle and turned into a lesson."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Open Positions" value={open.length} icon={<Wallet2 size={16} />} tone="cyan" />
        <KpiCard label="Win Rate" value={`${winRate}%`} icon={<Percent size={16} />} tone="emerald" sub={`${stats.wins}/${stats.closedTrades} closed trades`} />
        <KpiCard label="Avg. Return" value={formatPercent(avgReturn)} icon={avgReturn >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />} tone={avgReturn >= 0 ? "emerald" : "rose"} />
        <KpiCard label="Total P&L" value={formatUsd(stats.totalPnl)} icon={<Wallet2 size={16} />} tone="gold" />
      </div>

      <Card className="mt-6">
        <CardHeader title="Cumulative Performance" subtitle="Realized P&L across closed positions, in sequence" />
        <PnlAreaChart data={pnlData} />
      </Card>

      <Card className="mt-6">
        <CardHeader title="Open Positions" subtitle="Currently being monitored through their lifecycle" />
        {open.length === 0 ? (
          <EmptyState title="No open positions" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-slate-500">
                  <th className="pb-2 font-medium">Token</th>
                  <th className="pb-2 font-medium">Entry</th>
                  <th className="pb-2 font-medium">Stop</th>
                  <th className="pb-2 font-medium">Target 1/2/3</th>
                  <th className="pb-2 font-medium">Size</th>
                  <th className="pb-2 font-medium">Opened</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {open.map(({ trade, token }) => (
                  <tr key={trade.id}>
                    <td className="py-2.5">
                      <a href={`/dashboard/tokens/${token.id}`} data-cursor-interactive className="flex items-center gap-2">
                        <span>{token.logoEmoji}</span>
                        <span className="font-medium text-slate-100">{token.name}</span>
                        <span className="text-slate-500">${token.symbol}</span>
                      </a>
                    </td>
                    <td className="py-2.5 font-mono">{formatUsd(trade.entryPrice)}</td>
                    <td className="py-2.5 font-mono text-rose-300">{trade.stopLoss ? formatUsd(trade.stopLoss) : "—"}</td>
                    <td className="py-2.5 font-mono text-emerald-300">
                      {[trade.target1, trade.target2, trade.target3].filter(Boolean).map((t) => formatUsd(t)).join(" / ")}
                    </td>
                    <td className="py-2.5 font-mono">{formatUsd(trade.positionSizeUsd)}</td>
                    <td className="py-2.5 text-slate-400">{timeAgo(trade.openedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <CardHeader title="Closed Positions" subtitle="Includes correct skips and rejections as learnable outcomes" />
        {closed.length === 0 ? (
          <EmptyState title="No closed positions yet" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-slate-500">
                  <th className="pb-2 font-medium">Token</th>
                  <th className="pb-2 font-medium">Outcome</th>
                  <th className="pb-2 font-medium">Entry / Exit</th>
                  <th className="pb-2 font-medium">P&L</th>
                  <th className="pb-2 font-medium">Reason</th>
                  <th className="pb-2 font-medium">Closed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {closed.map(({ trade, token }) => (
                  <tr key={trade.id}>
                    <td className="py-2.5">
                      <a href={`/dashboard/tokens/${token.id}`} data-cursor-interactive className="flex items-center gap-2">
                        <span>{token.logoEmoji}</span>
                        <span className="font-medium text-slate-100">{token.name}</span>
                      </a>
                    </td>
                    <td className="py-2.5">
                      <Badge tone={trade.outcome === "win" ? "good" : trade.outcome === "loss" ? "danger" : "neutral"}>{trade.outcome}</Badge>
                    </td>
                    <td className="py-2.5 font-mono text-xs">
                      {formatUsd(trade.entryPrice)} → {trade.exitPrice ? formatUsd(trade.exitPrice) : "—"}
                    </td>
                    <td className={`py-2.5 font-mono ${Number(trade.pnlUsd) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {formatUsd(trade.pnlUsd)} ({formatPercent(trade.pnlPercent)})
                    </td>
                    <td className="max-w-[240px] py-2.5 text-xs text-slate-400 line-clamp-2">{trade.reason}</td>
                    <td className="py-2.5 text-slate-400">{timeAgo(trade.closedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <CardHeader title="Trade Lifecycle Log" subtitle="Full event trail per position" />
        <div className="space-y-2">
          {events.slice(0, 12).map((e) => (
            <div key={e.id} className="flex items-center justify-between gap-3 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2 text-xs">
              <span className="text-slate-300"><span className="font-mono text-slate-500">#{e.paperTradeId}</span> · {e.note}</span>
              <span className="shrink-0 text-slate-600">{timeAgo(e.createdAt)}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card className="mt-6">
        <CardHeader title="Learning Loop" subtitle="What AHOS learned from wins, losses, and correct skips" icon={<Brain size={16} />} />
        <div className="grid gap-3 lg:grid-cols-2">
          {learningLogs.map(({ log, token }) => {
            const Icon = patternIcon[log.patternType];
            return (
              <div key={log.id} className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="flex items-center justify-between gap-2">
                  <Badge tone={patternTone[log.patternType]} icon={<Icon size={12} />}>{log.patternType}</Badge>
                  {token && <span className="text-xs text-slate-500">{token.symbol}</span>}
                </div>
                <h4 className="mt-2 text-sm font-semibold text-slate-100">{log.title}</h4>
                <p className="mt-1 text-xs leading-relaxed text-slate-400">{log.description}</p>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
