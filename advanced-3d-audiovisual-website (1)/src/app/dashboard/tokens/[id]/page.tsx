import { notFound } from "next/navigation";
import { getTokenDossier } from "@/lib/queries";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge, decisionTone, riskTone } from "@/components/ui/Badge";
import { ScoreGauge, ScoreBar } from "@/components/ui/ScoreGauge";
import { formatUsd, formatPercent, formatNumber, timeAgo } from "@/lib/utils";
import {
  ShieldCheck, ShieldAlert, ShieldX, CircleCheck, CircleX, Flame, TrendingUp, TrendingDown,
  AlertOctagon, Newspaper, Link2, MessagesSquare, ExternalLink,
} from "lucide-react";
import { EmptyState } from "@/components/dashboard/Shared";

export const dynamic = "force-dynamic";

const verificationTone: Record<string, "good" | "gold" | "danger" | "neutral"> = {
  verified: "good", unverified: "gold", rumor: "danger", conflicted: "danger",
};

const stanceTone: Record<string, "good" | "danger" | "neutral" | "gold"> = {
  bullish: "good", bearish: "danger", neutral: "neutral", risk_flag: "danger", insufficient_evidence: "gold",
};

export default async function TokenDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tokenId = Number(id);
  if (Number.isNaN(tokenId)) notFound();
  const dossier = await getTokenDossier(tokenId);
  if (!dossier) notFound();

  const { token, score, security, opinions, evidence, social, onchain, news, trades } = dossier;

  const socialTotals = social.reduce(
    (acc, s) => {
      acc.mentions += s.mentions;
      acc.engagement += s.engagementScore;
      acc.count += 1;
      return acc;
    },
    { mentions: 0, engagement: 0, count: 0 }
  );

  return (
    <div>
      {/* Header */}
      <div className="glass-strong noise-border relative overflow-hidden rounded-3xl p-6 sm:p-8">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_0%_0%,rgba(53,240,208,0.12),transparent_50%)]" />
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <span className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl border border-white/10 bg-white/5 text-3xl">
              {token.logoEmoji}
            </span>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="font-display text-2xl font-bold text-white sm:text-3xl">{token.name}</h1>
                <span className="text-lg text-slate-500">${token.symbol}</span>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <Badge tone="neutral">{token.chain}</Badge>
                {token.narrative && <Badge tone="violet">{token.narrative}</Badge>}
                <span className="font-mono">{token.contractAddress ?? "Contract not yet deployed"}</span>
              </div>
              {token.summary && <p className="mt-3 max-w-2xl text-sm text-slate-300">{token.summary}</p>}
            </div>
          </div>
          {score && (
            <div className="flex flex-col items-end gap-2">
              <Badge tone={decisionTone(score.councilDecision)} className="text-sm">
                Council: {score.councilDecision.replace("_", " ")}
              </Badge>
              <span className="text-xs text-slate-500">Last updated {timeAgo(score.updatedAt)}</span>
            </div>
          )}
        </div>

        <div className="mt-8 grid grid-cols-2 gap-4 border-t border-white/10 pt-6 sm:grid-cols-3 lg:grid-cols-6">
          {[
            ["Price", formatUsd(token.priceUsd)],
            ["24h Change", formatPercent(token.priceChange24h)],
            ["Market Cap", formatUsd(token.marketCapUsd, { compact: true })],
            ["Liquidity", formatUsd(token.liquidityUsd, { compact: true })],
            ["Volume 24h", formatUsd(token.volume24hUsd, { compact: true })],
            ["Holders", formatNumber(token.holders)],
          ].map(([label, value]) => (
            <div key={label}>
              <div className="text-[11px] uppercase tracking-wider text-slate-500">{label}</div>
              <div className="mt-1 font-mono text-sm font-semibold text-slate-100">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Scores */}
      {score ? (
        <div className="mt-6 grid gap-5 xl:grid-cols-3">
          <Card className="flex flex-wrap items-center justify-around gap-6 xl:col-span-1">
            <ScoreGauge value={score.opportunityScore} label="Opportunity" color="#35f0d0" />
            <ScoreGauge value={score.securityScore} label="Security" color="#8b7bff" />
            <ScoreGauge value={score.confidence} label="Confidence" color="#ffc857" />
          </Card>
          <Card className="xl:col-span-2">
            <CardHeader title="Multi-Dimensional Scoring" subtitle="No single number can capture opportunity quality" />
            <div className="grid gap-4 sm:grid-cols-2">
              <ScoreBar label="Liquidity Score" value={score.liquidityScore} color="#35f0d0" />
              <ScoreBar label="Social Momentum" value={score.socialMomentum} color="#ff5fae" />
              <ScoreBar label="Whale Score" value={score.whaleScore} color="#8b7bff" />
              <ScoreBar label="Narrative Score" value={score.narrativeScore} color="#ffc857" />
              <ScoreBar label="Evidence Score" value={score.evidenceScore} color="#35f0a4" />
              <ScoreBar label="Security Score" value={score.securityScore} color="#8b7bff" />
            </div>
          </Card>
        </div>
      ) : (
        <div className="mt-6">
          <EmptyState title="Scoring not yet available" description="This candidate has not completed the council scoring pipeline." />
        </div>
      )}

      {/* WHY / RISKS / REJECT */}
      {score && (
        <div className="mt-6 grid gap-5 lg:grid-cols-3">
          <Card>
            <CardHeader title="Why?" icon={<TrendingUp size={16} />} />
            <ul className="space-y-2.5 text-sm text-slate-300">
              {(score.whyPoints ?? []).map((p, i) => (
                <li key={i} className="flex gap-2"><CircleCheck className="mt-0.5 shrink-0 text-emerald-400" size={15} />{p}</li>
              ))}
            </ul>
          </Card>
          <Card>
            <CardHeader title="Risks" icon={<AlertOctagon size={16} />} />
            <ul className="space-y-2.5 text-sm text-slate-300">
              {(score.riskPoints ?? []).map((p, i) => (
                <li key={i} className="flex gap-2"><ShieldAlert className="mt-0.5 shrink-0 text-amber-400" size={15} />{p}</li>
              ))}
            </ul>
          </Card>
          <Card>
            <CardHeader title="Reject Conditions" icon={<ShieldX size={16} />} />
            <ul className="space-y-2.5 text-sm text-slate-300">
              {(score.rejectConditions ?? []).map((p, i) => (
                <li key={i} className="flex gap-2"><CircleX className="mt-0.5 shrink-0 text-rose-400" size={15} />{p}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      {/* Scenarios */}
      {score && (
        <Card className="mt-6">
          <CardHeader title="Expected Scenarios" icon={<Flame size={16} />} />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Bull", score.bullScenario, "border-emerald-400/30 bg-emerald-400/5 text-emerald-200"],
              ["Base", score.baseScenario, "border-cyan-400/30 bg-cyan-400/5 text-cyan-200"],
              ["Bear", score.bearScenario, "border-amber-400/30 bg-amber-400/5 text-amber-200"],
              ["Extreme Risk", score.extremeRiskScenario, "border-rose-400/30 bg-rose-400/5 text-rose-200"],
            ].map(([label, text, cls]) => (
              <div key={label as string} className={`rounded-xl border p-4 text-xs leading-relaxed ${cls}`}>
                <div className="mb-1.5 font-display text-xs font-bold uppercase tracking-wider">{label}</div>
                {text as string}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Council opinions */}
      <Card className="mt-6">
        <CardHeader title="AI Council Opinions" subtitle={`${opinions.length} of 10 teams have submitted analysis`} icon={<MessagesSquare size={16} />} />
        {opinions.length === 0 ? (
          <EmptyState title="No council opinions yet" />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {opinions.map(({ opinion, team }) => (
              <div key={opinion.id} className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-slate-500">{team.code}</span>
                  <Badge tone={stanceTone[opinion.stance]}>{opinion.stance.replace("_", " ")}</Badge>
                </div>
                <div className="mt-1.5 text-sm font-semibold text-slate-100">{team.name}</div>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{opinion.summary}</p>
                <div className="mt-2 text-[11px] text-slate-500">Confidence: {opinion.confidence}%</div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Security */}
      {security && (
        <Card className="mt-6">
          <CardHeader
            title="Security Analysis"
            subtitle={`Checked ${timeAgo(security.checkedAt)}`}
            icon={security.riskLevel === "critical" || security.riskLevel === "high" ? <ShieldX size={16} /> : <ShieldCheck size={16} />}
            right={<Badge tone={riskTone(security.riskLevel)}>{security.riskLevel} risk</Badge>}
          />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Honeypot", security.honeypot],
              ["Mint Authority", security.mintAuthority],
              ["Freeze Authority", security.freezeAuthority],
              ["Ownership Renounced", security.ownershipRenounced],
              ["Liquidity Locked", security.liquidityLocked],
              ["Hidden Admin Functions", security.hiddenAdminFunctions],
              ["Deployer Rug History", security.deployerRugHistory],
            ].map(([label, val]) => (
              <div key={label as string} className="flex items-center justify-between rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2 text-xs">
                <span className="text-slate-400">{label}</span>
                {val ? <CircleX className="text-rose-400" size={15} /> : <CircleCheck className="text-emerald-400" size={15} />}
              </div>
            ))}
            <div className="flex items-center justify-between rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2 text-xs">
              <span className="text-slate-400">Top Holder Conc.</span>
              <span className="font-mono text-slate-200">{security.topHolderConcentration}%</span>
            </div>
          </div>
          {(security.flags?.length ?? 0) > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {security.flags!.map((f, i) => (
                <Badge key={i} tone="danger">{f}</Badge>
              ))}
            </div>
          )}
          {security.notes && <p className="mt-4 text-xs text-slate-400">{security.notes}</p>}
        </Card>
      )}

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        {/* Evidence */}
        <Card>
          <CardHeader title="Evidence Ledger" subtitle="Evidence before decision" icon={<Newspaper size={16} />} />
          {evidence.length === 0 ? (
            <EmptyState title="No evidence collected yet" />
          ) : (
            <div className="space-y-2.5">
              {evidence.map((e) => (
                <div key={e.id} className="rounded-lg border border-white/8 bg-white/[0.02] p-3 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-slate-200">{e.sourceName}</span>
                    <Badge tone={verificationTone[e.verification]}>{e.verification}</Badge>
                  </div>
                  <p className="mt-1 text-slate-400">{e.title}</p>
                  <p className="mt-1 text-[10px] uppercase tracking-wider text-slate-600">{e.sourceType} · {timeAgo(e.createdAt)}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* On-chain */}
        <Card>
          <CardHeader title="On-Chain Activity" icon={<Link2 size={16} />} />
          {onchain.length === 0 ? (
            <EmptyState title="No on-chain events recorded" />
          ) : (
            <div className="space-y-2.5">
              {onchain.map((e) => (
                <div key={e.id} className="rounded-lg border border-white/8 bg-white/[0.02] p-3 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium capitalize text-slate-200">{e.eventType.replace(/_/g, " ")}</span>
                    <span className="font-mono text-slate-400">{formatUsd(e.amountUsd, { compact: true })}</span>
                  </div>
                  <p className="mt-1 text-slate-400">{e.description}</p>
                  <p className="mt-1 font-mono text-[10px] text-slate-600">{e.walletAddress} · {timeAgo(e.occurredAt)}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        {/* Social summary */}
        <Card>
          <CardHeader title="Social Momentum" subtitle={`${formatNumber(socialTotals.mentions)} mentions tracked across platforms`} />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {social.slice(0, 4).map((s) => (
              <div key={s.id} className="rounded-lg border border-white/8 bg-white/[0.02] p-3 text-center">
                <div className="text-[11px] uppercase tracking-wider text-slate-500">{s.platform}</div>
                <div className="mt-1 font-display text-lg font-bold text-cyan-300">{s.engagementScore}</div>
                <div className="text-[10px] text-slate-500">{formatNumber(s.mentions)} mentions</div>
              </div>
            ))}
          </div>
        </Card>

        {/* News */}
        <Card>
          <CardHeader title="Related News" icon={<Newspaper size={16} />} />
          {news.length === 0 ? (
            <EmptyState title="No related news yet" />
          ) : (
            <div className="space-y-3">
              {news.map((n) => (
                <div key={n.id} className="rounded-lg border border-white/8 bg-white/[0.02] p-3 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-slate-200 line-clamp-1">{n.title}</span>
                    {n.url && <ExternalLink size={12} className="shrink-0 text-slate-500" />}
                  </div>
                  <p className="mt-1 text-slate-400 line-clamp-2">{n.summary}</p>
                  <p className="mt-1 text-[10px] text-slate-600">{n.source} · {timeAgo(n.publishedAt)}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Paper trades */}
      <Card className="mt-6">
        <CardHeader title="Paper Trades" subtitle="Hypothetical positions the council opened for this token" icon={<TrendingDown size={16} />} />
        {trades.length === 0 ? (
          <EmptyState title="No paper trades opened for this token" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-slate-500">
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Entry</th>
                  <th className="pb-2 font-medium">Exit</th>
                  <th className="pb-2 font-medium">P&L</th>
                  <th className="pb-2 font-medium">Opened</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {trades.map((t) => (
                  <tr key={t.id}>
                    <td className="py-2.5"><Badge tone={t.outcome === "win" ? "good" : t.outcome === "loss" ? "danger" : "neutral"}>{t.outcome}</Badge></td>
                    <td className="py-2.5 font-mono">{formatUsd(t.entryPrice)}</td>
                    <td className="py-2.5 font-mono">{t.exitPrice ? formatUsd(t.exitPrice) : "—"}</td>
                    <td className={`py-2.5 font-mono ${Number(t.pnlUsd) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatUsd(t.pnlUsd)}</td>
                    <td className="py-2.5 text-slate-400">{timeAgo(t.openedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
