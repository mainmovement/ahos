import { getGlobalStats, listTokensWithScores } from "@/lib/queries";
import { RevealCard } from "@/components/ui/Card";
import { Badge, decisionTone } from "@/components/ui/Badge";
import { formatUsd, formatPercent } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Radar, ShieldCheck, TrendingUp, Wallet2 } from "lucide-react";

export async function LiveStats() {
  const [stats, tokens] = await Promise.all([getGlobalStats(), listTokensWithScores()]);
  const top = tokens.slice(0, 4);

  const kpis = [
    { label: "Tokens Tracked", value: stats.tokensTracked, icon: Radar },
    { label: "Currently Watching", value: stats.watching, icon: TrendingUp },
    { label: "Rejected by Risk Gate", value: stats.rejected, icon: ShieldCheck },
    { label: "Paper P&L", value: formatUsd(stats.totalPnl), icon: Wallet2 },
  ];

  return (
    <section id="stats" className="relative py-32">
      <div className="mx-auto max-w-7xl px-6">
        <RevealCard>
          <span className="text-xs font-medium uppercase tracking-[0.3em] text-gold">Live From The Database</span>
          <h2 className="mt-4 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
            This isn&apos;t a mockup. <span className="text-gradient">It&apos;s live intelligence.</span>
          </h2>
          <p className="mt-5 max-w-2xl text-slate-300">
            Every number below is queried directly from the AHOS database in real time.
          </p>
        </RevealCard>

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {kpis.map((kpi, i) => (
            <RevealCard key={kpi.label} delay={i * 0.05}>
              <div className="glass noise-border rounded-2xl p-5">
                <kpi.icon className="text-cyan-300" size={20} />
                <div className="mt-4 font-display text-3xl font-bold text-white">{kpi.value}</div>
                <div className="mt-1 text-xs text-slate-400">{kpi.label}</div>
              </div>
            </RevealCard>
          ))}
        </div>

        <RevealCard delay={0.15} className="mt-6">
          <div className="glass-strong noise-border overflow-hidden rounded-2xl">
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
              <h3 className="font-display text-sm font-semibold text-white">Top Ranked Opportunities</h3>
              <Button href="/dashboard/tokens" variant="ghost" size="sm">
                View all →
              </Button>
            </div>
            <div className="divide-y divide-white/5">
              {top.map(({ token, score }) => (
                <a
                  key={token.id}
                  href={`/dashboard/tokens/${token.id}`}
                  data-cursor-interactive
                  className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 transition-colors hover:bg-white/[0.03]"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{token.logoEmoji}</span>
                    <div>
                      <div className="text-sm font-semibold text-white">
                        {token.name} <span className="text-slate-500">${token.symbol}</span>
                      </div>
                      <div className="text-xs text-slate-500">
                        {token.chain} · {token.narrative}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="font-mono text-sm text-white">{formatUsd(token.priceUsd)}</div>
                      <div className={`text-xs ${Number(token.priceChange24h) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {formatPercent(token.priceChange24h)}
                      </div>
                    </div>
                    <div className="w-16 text-right font-display text-lg font-bold text-cyan-300">
                      {score?.opportunityScore ?? "—"}
                    </div>
                    {score && <Badge tone={decisionTone(score.councilDecision)}>{score.councilDecision.replace("_", " ")}</Badge>}
                  </div>
                </a>
              ))}
            </div>
          </div>
        </RevealCard>
      </div>
    </section>
  );
}
