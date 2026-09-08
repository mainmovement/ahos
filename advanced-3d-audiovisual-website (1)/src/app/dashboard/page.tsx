import { getGlobalStats, listTokensWithScores, listAlerts, listPaperTrades } from "@/lib/queries";
import { PageHeader, KpiCard } from "@/components/dashboard/Shared";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge, decisionTone } from "@/components/ui/Badge";
import { OpportunityBarChart, DecisionPieChart, PnlAreaChart } from "@/components/dashboard/charts/OverviewCharts";
import { formatUsd, formatPercent, timeAgo } from "@/lib/utils";
import { Radar, ShieldCheck, TrendingUp, Wallet2, Bell, Rocket } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const dynamic = "force-dynamic";

export default async function DashboardOverviewPage() {
  const [stats, tokens, { alert: alerts }, { trades }] = await Promise.all([
    getGlobalStats(),
    listTokensWithScores(),
    listAlerts(6).then((rows) => ({ alert: rows })),
    listPaperTrades(),
  ]);

  const barData = tokens.slice(0, 6).map((t) => ({
    name: t.token.symbol,
    opportunity: t.score?.opportunityScore ?? 0,
    security: t.score?.securityScore ?? 0,
  }));

  const decisionCounts: Record<string, number> = {};
  for (const t of tokens) {
    const d = t.score?.councilDecision ?? "insufficient_evidence";
    decisionCounts[d] = (decisionCounts[d] ?? 0) + 1;
  }
  const decisionColors: Record<string, string> = {
    strong_buy: "#35f0a4", watch: "#35f0d0", insufficient_evidence: "#ffc857", reject: "#ff4d6d", skip: "#64748b",
  };
  const pieData = Object.entries(decisionCounts).map(([name, value]) => ({
    name: name.replace("_", " "), value, color: decisionColors[name] ?? "#94a3b8",
  }));

  const closedTrades = trades
    .filter((t) => t.trade.status === "closed")
    .sort((a, b) => new Date(a.trade.closedAt ?? 0).getTime() - new Date(b.trade.closedAt ?? 0).getTime());
  let cumulative = 0;
  const pnlData = closedTrades.map((t) => {
    cumulative += Number(t.trade.pnlUsd ?? 0);
    return { label: t.token.symbol, pnl: Number(cumulative.toFixed(2)) };
  });
  if (pnlData.length === 0) pnlData.push({ label: "Start", pnl: 0 });

  const topTokens = tokens.slice(0, 5);
  const winRate = stats.closedTrades > 0 ? Math.round((stats.wins / stats.closedTrades) * 100) : 0;

  return (
    <div>
      <PageHeader
        eyebrow="Overview"
        title="Intelligence Command Center"
        description="Real-time snapshot of discovery, council decisions, security screening and paper trading performance."
        right={
          <Button href="/dashboard/tokens" size="sm" icon={<Rocket size={15} />}>
            View Discovery Feed
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Tokens Tracked" value={stats.tokensTracked} icon={<Radar size={16} />} tone="cyan" sub="Across all discovery groups" />
        <KpiCard label="Watching" value={stats.watching} icon={<TrendingUp size={16} />} tone="violet" sub="Awaiting further confirmation" />
        <KpiCard label="Rejected by Risk Gate" value={stats.rejected} icon={<ShieldCheck size={16} />} tone="rose" sub="Critical security overrides" />
        <KpiCard label="Paper Trading P&L" value={formatUsd(stats.totalPnl)} icon={<Wallet2 size={16} />} tone="emerald" sub={`${winRate}% win rate · ${stats.closedTrades} closed`} />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Top Candidates — Opportunity vs Security" subtitle="Highest ranked tokens right now" />
          <OpportunityBarChart data={barData} />
        </Card>
        <Card>
          <CardHeader title="Council Decisions" subtitle="Distribution across all tracked tokens" />
          <DecisionPieChart data={pieData} />
        </Card>
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Paper Trading — Cumulative P&L" subtitle="Realized profit & loss across closed positions" />
          <PnlAreaChart data={pnlData} />
        </Card>
        <Card>
          <CardHeader title="Recent Alerts" subtitle="Latest signals from the council" icon={<Bell size={15} />} right={<Button href="/dashboard/alerts" variant="ghost" size="sm">All →</Button>} />
          <div className="space-y-3">
            {alerts.map(({ alert }) => (
              <div key={alert.id} className="rounded-xl border border-white/8 bg-white/[0.02] p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-slate-100 line-clamp-1">{alert.title}</span>
                  <Badge tone={alert.severity === "critical" ? "danger" : alert.severity === "warning" ? "gold" : "cyan"}>{alert.severity}</Badge>
                </div>
                <p className="mt-1 text-[11px] text-slate-500">{timeAgo(alert.createdAt)}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader title="Ranked Opportunities" subtitle="Full evidence-backed scoring for the current watchlist" />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wider text-slate-500">
                <th className="pb-3 font-medium">Token</th>
                <th className="pb-3 font-medium">Price</th>
                <th className="pb-3 font-medium">24h</th>
                <th className="pb-3 font-medium">Opportunity</th>
                <th className="pb-3 font-medium">Confidence</th>
                <th className="pb-3 font-medium">Decision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {topTokens.map(({ token, score }) => (
                <tr key={token.id} className="group">
                  <td className="py-3">
                    <a href={`/dashboard/tokens/${token.id}`} data-cursor-interactive className="flex items-center gap-2 group-hover:text-cyan-300">
                      <span>{token.logoEmoji}</span>
                      <span className="font-medium text-slate-100 group-hover:text-cyan-300">{token.name}</span>
                      <span className="text-slate-500">${token.symbol}</span>
                    </a>
                  </td>
                  <td className="py-3 font-mono text-slate-200">{formatUsd(token.priceUsd)}</td>
                  <td className={`py-3 font-mono ${Number(token.priceChange24h) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {formatPercent(token.priceChange24h)}
                  </td>
                  <td className="py-3 font-display font-semibold text-cyan-300">{score?.opportunityScore ?? "—"}</td>
                  <td className="py-3 text-slate-300">{score?.confidence ?? "—"}</td>
                  <td className="py-3">{score && <Badge tone={decisionTone(score.councilDecision)}>{score.councilDecision.replace("_", " ")}</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
