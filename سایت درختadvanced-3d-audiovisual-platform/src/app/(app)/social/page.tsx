import { PageHeader } from "@/components/page-header";
import { loadSocial } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function SocialPage() {
  const rows = await loadSocial();
  return (
    <div>
      <PageHeader
        kicker="Social & narrative"
        title="Engagement is not demand."
        lede="Mention velocity without aged unique accounts is inventory. Team 07 treats raids as a bearish authenticity print."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {rows.map((r) => (
          <article key={r.social_signals.id} className="panel rounded-2xl p-5">
            <div className="flex items-center justify-between">
              <span className="kicker">{r.social_signals.platform}</span>
              <span className={`badge ${r.social_signals.authenticity === "synthetic" ? "bad" : "good"}`}>
                {r.social_signals.authenticity}
              </span>
            </div>
            <h3 className="font-display mt-3 text-3xl italic">{r.tokens?.name ?? "Network"}</h3>
            <p className="font-mono text-sm text-[#6ee7f9]">
              {r.social_signals.metric} {r.social_signals.value} · vel {r.social_signals.velocity}x
            </p>
            <p className="mt-3 text-sm text-[#efe6d6]/65">{r.social_signals.note}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
