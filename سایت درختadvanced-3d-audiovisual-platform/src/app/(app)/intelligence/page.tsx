import { PageHeader } from "@/components/page-header";
import { TokenCard } from "@/components/token-card";
import { loadIntelligence } from "@/lib/queries";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function IntelligencePage() {
  const { board, totals } = await loadIntelligence();
  const n = Math.max(totals.n, 1);

  return (
    <div>
      <PageHeader
        kicker="Market intelligence"
        title="Structure before the tape."
        lede="AHOS does not worship volume. It asks whether liquidity is real, whether MC outran the pool, and which narrative is carrying the bid."
      />
      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Avg opportunity", Math.round(totals.opp / n)],
          ["Avg security", Math.round(totals.sec / n)],
          ["Avg confidence", Math.round(totals.conf / n)],
        ].map(([k, v]) => (
          <div key={k} className="panel rounded-2xl p-5">
            <div className="kicker">{k}</div>
            <div className="font-display mt-2 text-5xl italic">{v}</div>
          </div>
        ))}
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="panel rounded-2xl p-5">
          <p className="kicker">Liquidity vs volume</p>
          <p className="mt-3 font-mono text-2xl">{usd(totals.liq)} liq</p>
          <p className="font-mono text-2xl text-[#6ee7f9]">{usd(totals.vol)} vol</p>
        </div>
        <div className="panel rounded-2xl p-5">
          <p className="kicker">Chains / groups / status</p>
          <div className="mt-3 grid grid-cols-3 gap-2 font-mono text-xs">
            <Col map={totals.byChain} />
            <Col map={totals.byGroup} />
            <Col map={totals.byStatus} />
          </div>
        </div>
      </div>
      <h2 className="font-display mt-10 text-3xl italic">Tape</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {board.map((row) => (
          <TokenCard key={row.token.id} token={row.token} score={row.score} />
        ))}
      </div>
    </div>
  );
}

function Col({ map }: { map: Record<string, number> }) {
  return (
    <div className="space-y-1">
      {Object.entries(map).map(([k, v]) => (
        <div key={k} className="flex justify-between gap-2">
          <span className="truncate text-[#efe6d6]/60">{k}</span>
          <span>{v}</span>
        </div>
      ))}
    </div>
  );
}
