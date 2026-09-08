import { PageHeader } from "@/components/page-header";
import { loadNews } from "@/lib/queries";
import { timeAgo } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function NewsPage() {
  const rows = await loadNews();
  return (
    <div>
      <PageHeader
        kicker="News & journalism"
        title="Source first. Recap last."
        lede="Syndication of a screenshot is not reporting. Rumor stays rumor until a second independent source moves."
      />
      <div className="space-y-4">
        {rows.map((r) => (
          <article key={r.news_items.id} className="panel rounded-2xl p-6">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`badge ${r.news_items.verification}`}>{r.news_items.verification}</span>
              <span className="badge">{r.news_items.sentiment}</span>
              <span className="font-mono text-[11px] text-[#f3d5a0]/40">
                {r.news_items.source} · {timeAgo(r.news_items.createdAt)}
              </span>
            </div>
            <h2 className="font-display mt-3 text-3xl italic">{r.news_items.title}</h2>
            <p className="mt-2 text-[#efe6d6]/70">{r.news_items.summary}</p>
            {r.tokens && <p className="mt-3 kicker">{r.tokens.symbol} · {r.tokens.name}</p>}
          </article>
        ))}
        {rows.length === 0 && <div className="panel rounded-2xl p-8 text-[#efe6d6]/40">No wires yet.</div>}
      </div>
    </div>
  );
}
