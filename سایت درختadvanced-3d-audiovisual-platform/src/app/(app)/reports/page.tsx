import { PageHeader } from "@/components/page-header";
import { loadReports } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function ReportsPage() {
  const rows = await loadReports();
  return (
    <div>
      <PageHeader
        kicker="Daily intelligence report"
        title="What moved. What was refused. What was learned."
        lede="New names, best fruit, rejects, open and closed papers, PnL, system changes, news, learning engine."
      />
      <div className="space-y-4">
        {rows.map((r) => (
          <article key={r.id} className="panel rounded-3xl p-6">
            <p className="kicker">{r.reportDate}</p>
            <h2 className="font-display mt-2 text-4xl italic">{r.headline}</h2>
            <p className="mt-3 max-w-3xl text-[#efe6d6]/75">{r.body}</p>
            <div className="mt-5 grid grid-cols-2 gap-3 font-mono text-sm md:grid-cols-3">
              {Object.entries(r.metrics).map(([k, v]) => (
                <div key={k} className="rounded-xl border border-[rgba(201,163,106,0.12)] p-3">
                  <div className="text-[10px] uppercase tracking-widest text-[#f3d5a0]/50">{k}</div>
                  <div className="text-xl text-[#fff6e4]">{v}</div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
