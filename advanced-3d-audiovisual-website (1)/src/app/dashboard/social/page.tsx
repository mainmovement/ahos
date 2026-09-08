import { listSocialAgg } from "@/lib/queries";
import { PageHeader } from "@/components/dashboard/Shared";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SocialRadarBars } from "@/components/dashboard/charts/OverviewCharts";
import { formatNumber } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function SocialIntelligencePage() {
  const rows = await listSocialAgg();

  const chartData = rows.slice(0, 8).map((r) => ({ name: r.token.symbol, value: r.engagement }));

  return (
    <div>
      <PageHeader
        eyebrow="Team 07"
        title="Social & Narrative Intelligence"
        description="Engagement volume alone is never treated as a bullish signal — velocity and independence of sources matter more."
      />

      <Card>
        <CardHeader title="Engagement Score by Token" subtitle="Quality-adjusted, not raw mention count" />
        <SocialRadarBars data={chartData} />
      </Card>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {rows.map((r) => (
          <Card key={r.tokenId}>
            <div className="flex items-center justify-between">
              <a href={`/dashboard/tokens/${r.token.id}`} data-cursor-interactive className="flex items-center gap-2.5">
                <span className="text-xl">{r.token.logoEmoji}</span>
                <div>
                  <div className="font-display text-sm font-semibold text-white">{r.token.name}</div>
                  <div className="text-xs text-slate-500">${r.token.symbol}</div>
                </div>
              </a>
              <Badge tone={r.sentiment > 20 ? "good" : r.sentiment < 0 ? "danger" : "neutral"}>
                Sentiment {r.sentiment > 0 ? "+" : ""}{r.sentiment}
              </Badge>
            </div>
            <div className="mt-4 grid grid-cols-4 gap-2 text-center text-xs">
              {[
                ["Mentions", formatNumber(r.mentions)],
                ["Engagement", r.engagement],
                ["Velocity", r.velocity],
                ["Influencer", r.influencer],
              ].map(([label, val]) => (
                <div key={label as string} className="rounded-lg border border-white/8 bg-white/[0.02] p-2">
                  <div className="font-display text-base font-bold text-cyan-300">{val}</div>
                  <div className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
