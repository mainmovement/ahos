import { listNews } from "@/lib/queries";
import { PageHeader } from "@/components/dashboard/Shared";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { timeAgo } from "@/lib/utils";
import { ExternalLink, Newspaper } from "lucide-react";

export const dynamic = "force-dynamic";

const sentimentTone: Record<string, "good" | "danger" | "neutral"> = { positive: "good", negative: "danger", neutral: "neutral" };

export default async function NewsPage() {
  const rows = await listNews();

  return (
    <div>
      <PageHeader
        eyebrow="Team 06"
        title="News & Journalism Intelligence"
        description="Verified, cross-referenced coverage. Credibility scores reflect source evaluation, not sentiment."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {rows.map(({ news, token }) => (
          <Card key={news.id}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <div className="mt-0.5 rounded-lg border border-white/10 bg-white/5 p-2 text-cyan-300">
                  <Newspaper size={15} />
                </div>
                <div>
                  <h3 className="font-display text-sm font-semibold leading-snug text-white">{news.title}</h3>
                  <p className="mt-1 text-xs text-slate-400">{news.summary}</p>
                </div>
              </div>
              {news.url && <ExternalLink size={14} className="mt-1 shrink-0 text-slate-500" />}
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Badge tone={sentimentTone[news.sentiment]}>{news.sentiment}</Badge>
              <Badge tone="neutral">Credibility {news.credibility}%</Badge>
              {token && <Badge tone="violet">${token.symbol}</Badge>}
              {(news.tags ?? []).map((t) => <Badge key={t} tone="cyan">{t}</Badge>)}
            </div>
            <p className="mt-3 text-[11px] uppercase tracking-wider text-slate-600">{news.source} · {timeAgo(news.publishedAt)}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
