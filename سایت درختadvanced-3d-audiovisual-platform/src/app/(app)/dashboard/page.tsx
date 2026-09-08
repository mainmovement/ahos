import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { ScoreRing } from "@/components/score-ring";
import { TokenCard } from "@/components/token-card";
import { loadDashboard } from "@/lib/queries";
import { decisionLabel, pct, usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const data = await loadDashboard();
  const exceptional = data.board.find((b) => b.token.slug === "goldenfruit") ?? data.board[0];
  const rejects = data.board.filter((b) => b.score?.decision === "reject");
  const ok = data.components.filter((c) => c.status === "ok").length;

  return (
    <div>
      <PageHeader
        kicker="Command"
        title="The board, the gate, the book."
        lede="Single-user chamber. Phase 1 token discovery. Nothing here is a buy button — it is evidence, scored and opposed."
      />

      <div className="grid gap-4 md:grid-cols-4">
        {[
          { k: "Open paper", v: String(data.open.length), s: usd(data.pnl) + " book" },
          { k: "Win / loss", v: `${data.wins}/${data.losses}`, s: "closed papers" },
          { k: "Risk rejects", v: String(rejects.length), s: "gate held" },
          { k: "Roots live", v: `${ok}/${data.components.length}`, s: "providers" },
        ].map((c) => (
          <div key={c.k} className="panel rounded-2xl p-5">
            <div className="kicker">{c.k}</div>
            <div className="font-display mt-2 text-4xl italic">{c.v}</div>
            <div className="mt-1 font-mono text-xs text-[#f3d5a0]/60">{c.s}</div>
          </div>
        ))}
      </div>

      {data.report && (
        <section className="panel mt-6 rounded-3xl p-6">
          <p className="kicker">Daily intelligence</p>
          <h2 className="font-display mt-2 text-3xl italic">{data.report.headline}</h2>
          <p className="mt-3 max-w-3xl text-[#efe6d6]/70">{data.report.body}</p>
        </section>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <section>
          <div className="mb-4 flex items-end justify-between">
            <h2 className="font-display text-3xl italic">Ranked fruit</h2>
            <Link href="/tokens" className="kicker">
              Full discovery →
            </Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {data.board.slice(0, 4).map((row) => (
              <TokenCard key={row.token.id} token={row.token} score={row.score} />
            ))}
          </div>
        </section>

        <aside className="space-y-4">
          {exceptional?.score && (
            <div className="panel rounded-3xl p-6">
              <p className="kicker">Exceptional</p>
              <h3 className="font-display mt-2 text-4xl italic">{exceptional.token.name}</h3>
              <p className="font-mono text-xs text-[#f3d5a0]/70">{exceptional.token.symbol}</p>
              <div className="mt-4 flex justify-between">
                <ScoreRing value={exceptional.score.opportunity} label="OPP" />
                <ScoreRing value={exceptional.score.security} label="SEC" />
                <ScoreRing value={exceptional.score.confidence} label="CONF" />
              </div>
              <p className="mt-4 text-sm text-[#efe6d6]/70">{exceptional.score.thesis}</p>
            </div>
          )}

          <div className="panel rounded-3xl p-6">
            <p className="kicker">Alerts</p>
            <div className="mt-3 space-y-3">
              {data.alerts.map((a) => (
                <Link key={a.id} href="/alerts" className="block border-b border-[rgba(201,163,106,0.08)] pb-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`badge ${a.severity === "critical" ? "reject" : "watch"}`}>{a.severity}</span>
                    <span className="font-mono text-[10px] text-[#f3d5a0]/40">{a.kind}</span>
                  </div>
                  <p className="mt-1 text-sm">{a.title}</p>
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </div>

      <section className="mt-8">
        <h2 className="font-display text-3xl italic">Paper desk</h2>
        <div className="panel mt-4 overflow-hidden rounded-2xl">
          <table className="w-full text-sm">
            <thead className="font-mono text-[11px] uppercase tracking-widest text-[#f3d5a0]/50">
              <tr>
                <th className="px-4 py-3 text-left">Book</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-right">PnL</th>
              </tr>
            </thead>
            <tbody>
              {data.trades.map((t) => {
                const token = data.board.find((b) => b.token.id === t.tokenId)?.token;
                return (
                  <tr key={t.id} className="table-row">
                    <td className="px-4 py-3">
                      {token?.symbol ?? t.tokenId} · {usd(t.capital)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`badge ${t.status}`}>{t.status}</span>
                    </td>
                    <td className={`px-4 py-3 text-right font-mono ${t.pnlUsd >= 0 ? "text-[#4ade80]" : "text-[#fb7185]"}`}>
                      {usd(t.pnlUsd)} ({pct(t.pnlPct)})
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2">
        <div className="panel rounded-2xl p-5">
          <p className="kicker">Learning</p>
          <ul className="mt-3 space-y-3">
            {data.learn.map((l) => (
              <li key={l.id}>
                <span className={`badge ${l.kind === "win" ? "good" : l.kind === "loss" ? "bad" : "watch"}`}>{l.kind}</span>
                <p className="mt-1 text-sm">{l.title}</p>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel rounded-2xl p-5">
          <p className="kicker">GitHub ledger</p>
          <ul className="mt-3 space-y-3">
            {data.github.map((g) => (
              <li key={g.id} className="flex items-start justify-between gap-3 text-sm">
                <span>{g.title}</span>
                <span className="badge">{g.kind}</span>
              </li>
            ))}
          </ul>
          <Link href="/github" className="kicker mt-4 inline-block">
            Operate in GitHub →
          </Link>
        </div>
      </section>

      <p className="mt-10 hidden font-mono text-[10px] text-transparent">{decisionLabel("watch")}</p>
    </div>
  );
}
