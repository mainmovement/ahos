import { PageHeader } from "@/components/page-header";
import { TEAMS } from "@/lib/constants";
import { loadCouncil } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function CouncilPage() {
  const votes = await loadCouncil();
  const byToken = new Map<string, typeof votes>();
  for (const v of votes) {
    const key = v.tokens?.slug ?? "unknown";
    const arr = byToken.get(key) ?? [];
    arr.push(v);
    byToken.set(key, arr);
  }

  return (
    <div>
      <PageHeader
        kicker="AI expert council"
        title="Ten rooms. One red team."
        lede="No team decides alone. Discovery → evidence → security → analysis → cross-exam → contrarian → debate → score → confidence → decision."
      />
      <div className="mb-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {TEAMS.map((t) => (
          <article key={t.no} className="panel rounded-2xl p-4">
            <div className="font-mono text-xs text-[#6ee7f9]">{String(t.no).padStart(2, "0")} {t.code}</div>
            <h3 className="mt-2 font-display text-xl italic">{t.name}</h3>
            <p className="mt-2 text-xs text-[#efe6d6]/60">{t.focus}</p>
          </article>
        ))}
      </div>
      {[...byToken.entries()].map(([slug, list]) => (
        <section key={slug} className="mb-8">
          <h2 className="font-display text-3xl italic">{list[0]?.tokens?.name ?? slug}</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {list.map((v) => (
              <article key={v.council_votes.id} className="panel rounded-2xl p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs">{v.council_votes.teamName}</span>
                  <span className={`badge ${v.council_votes.stance}`}>
                    {v.council_votes.stance} {v.council_votes.confidence}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[#efe6d6]/70">{v.council_votes.rationale}</p>
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
