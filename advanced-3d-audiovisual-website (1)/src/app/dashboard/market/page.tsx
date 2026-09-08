import { listTokensWithScores } from "@/lib/queries";
import { PageHeader, KpiCard } from "@/components/dashboard/Shared";
import { Card } from "@/components/ui/Card";
import { Badge, decisionTone } from "@/components/ui/Badge";
import { formatUsd, formatPercent, formatNumber } from "@/lib/utils";
import { DollarSign, Droplets, Activity, Users } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function MarketIntelligencePage() {
  const rows = await listTokensWithScores();

  const totalMcap = rows.reduce((sum, r) => sum + Number(r.token.marketCapUsd ?? 0), 0);
  const totalLiquidity = rows.reduce((sum, r) => sum + Number(r.token.liquidityUsd ?? 0), 0);
  const totalVolume = rows.reduce((sum, r) => sum + Number(r.token.volume24hUsd ?? 0), 0);
  const totalHolders = rows.reduce((sum, r) => sum + Number(r.token.holders ?? 0), 0);

  const sorted = [...rows].sort((a, b) => Number(b.token.volume24hUsd) - Number(a.token.volume24hUsd));

  return (
    <div>
      <PageHeader
        eyebrow="Team 02"
        title="Market Intelligence"
        description="Tokenomics, liquidity structure, and price action across every tracked candidate."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Aggregate Market Cap" value={formatUsd(totalMcap, { compact: true })} icon={<DollarSign size={16} />} tone="cyan" />
        <KpiCard label="Aggregate Liquidity" value={formatUsd(totalLiquidity, { compact: true })} icon={<Droplets size={16} />} tone="violet" />
        <KpiCard label="24h Volume" value={formatUsd(totalVolume, { compact: true })} icon={<Activity size={16} />} tone="gold" />
        <KpiCard label="Total Holders" value={formatNumber(totalHolders)} icon={<Users size={16} />} tone="emerald" />
      </div>

      <Card className="mt-6">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wider text-slate-500">
                <th className="pb-3 font-medium">Token</th>
                <th className="pb-3 font-medium">Price</th>
                <th className="pb-3 font-medium">24h</th>
                <th className="pb-3 font-medium">Market Cap</th>
                <th className="pb-3 font-medium">Liquidity</th>
                <th className="pb-3 font-medium">Volume 24h</th>
                <th className="pb-3 font-medium">Holders</th>
                <th className="pb-3 font-medium">Council</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {sorted.map(({ token, score }) => (
                <tr key={token.id} className="hover:bg-white/[0.02]">
                  <td className="py-3">
                    <a href={`/dashboard/tokens/${token.id}`} data-cursor-interactive className="flex items-center gap-2">
                      <span>{token.logoEmoji}</span>
                      <span className="font-medium text-slate-100">{token.name}</span>
                      <span className="text-slate-500">${token.symbol}</span>
                    </a>
                  </td>
                  <td className="py-3 font-mono text-slate-200">{formatUsd(token.priceUsd)}</td>
                  <td className={`py-3 font-mono ${Number(token.priceChange24h) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {formatPercent(token.priceChange24h)}
                  </td>
                  <td className="py-3 font-mono text-slate-300">{formatUsd(token.marketCapUsd, { compact: true })}</td>
                  <td className="py-3 font-mono text-slate-300">{formatUsd(token.liquidityUsd, { compact: true })}</td>
                  <td className="py-3 font-mono text-slate-300">{formatUsd(token.volume24hUsd, { compact: true })}</td>
                  <td className="py-3 text-slate-300">{formatNumber(token.holders)}</td>
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
