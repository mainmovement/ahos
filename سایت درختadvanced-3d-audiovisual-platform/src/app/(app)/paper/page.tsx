import { PageHeader } from "@/components/page-header";
import { PaperActions } from "@/components/paper-actions";
import { loadPaper } from "@/lib/queries";
import { pct, usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function PaperPage() {
  const rows = await loadPaper();
  const pnl = rows.reduce((a, r) => a + r.paper_trades.pnlUsd, 0);
  const closed = rows.filter((r) => r.paper_trades.status !== "open");
  const wins = closed.filter((r) => r.paper_trades.pnlUsd > 0).length;

  return (
    <div>
      <PageHeader
        kicker="Paper desk"
        title="Hypothesis with a stop."
        lede="AHOS does not buy in phase 1. It opens a virtual book, watches the lifecycle, then writes a post-mortem. Skip is a result."
      />
      <div className="mb-6 grid gap-4 md:grid-cols-3">
        <div className="panel rounded-2xl p-5">
          <div className="kicker">Book PnL</div>
          <div className={`font-display mt-2 text-4xl italic ${pnl >= 0 ? "text-[#4ade80]" : "text-[#fb7185]"}`}>{usd(pnl)}</div>
        </div>
        <div className="panel rounded-2xl p-5">
          <div className="kicker">Closed win rate</div>
          <div className="font-display mt-2 text-4xl italic">{closed.length ? Math.round((wins / closed.length) * 100) : 0}%</div>
        </div>
        <div className="panel rounded-2xl p-5">
          <div className="kicker">Open books</div>
          <div className="font-display mt-2 text-4xl italic">{rows.filter((r) => r.paper_trades.status === "open").length}</div>
        </div>
      </div>
      <PaperActions />
      <div className="mt-6 space-y-4">
        {rows.map((r) => {
          const t = r.paper_trades;
          const width = Math.min(100, Math.abs(t.pnlPct) * 3);
          return (
            <article key={t.id} className="panel rounded-3xl p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="font-display text-3xl italic">{r.tokens?.name}</h3>
                  <p className="font-mono text-xs text-[#f3d5a0]/60">
                    {r.tokens?.symbol} · {usd(t.capital)} · entry {t.entry}
                  </p>
                </div>
                <span className={`badge ${t.status}`}>{t.status}</span>
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/5">
                <div className={`h-full ${t.pnlUsd >= 0 ? "bg-[#4ade80]" : "bg-[#fb7185]"}`} style={{ width: `${width}%` }} />
              </div>
              <p className={`mt-2 font-mono ${t.pnlUsd >= 0 ? "text-[#4ade80]" : "text-[#fb7185]"}`}>
                {usd(t.pnlUsd)} ({pct(t.pnlPct)})
              </p>
              <p className="mt-2 text-sm text-[#efe6d6]/65">{t.notes}</p>
              <p className="mt-2 font-mono text-[11px] text-[#f3d5a0]/40">
                Stop {t.stop} · T1 {t.target1} · T2 {t.target2} · T3 {t.target3}
              </p>
            </article>
          );
        })}
      </div>
    </div>
  );
}
