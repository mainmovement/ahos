import { PageHeader } from "@/components/page-header";
import { loadOnchain } from "@/lib/queries";
import { usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function OnchainPage() {
  const { events, whales } = await loadOnchain();
  return (
    <div>
      <PageHeader
        kicker="On-chain"
        title="Wallets do not tweet."
        lede="Holder graphs, LP adds, failed sells, deployer silence. One chain source can yield whale, holder, transfer, and contract intelligence."
      />
      <h2 className="font-display text-3xl italic">Whale tape</h2>
      <div className="panel mt-4 overflow-hidden rounded-2xl">
        <table className="w-full text-sm">
          <thead className="font-mono text-[11px] uppercase tracking-widest text-[#f3d5a0]/50">
            <tr>
              <th className="px-4 py-3 text-left">Token</th>
              <th className="px-4 py-3 text-left">Action</th>
              <th className="px-4 py-3 text-right">USD</th>
            </tr>
          </thead>
          <tbody>
            {whales.map((w) => (
              <tr key={w.whale_moves.id} className="table-row">
                <td className="px-4 py-3">{w.tokens?.symbol}</td>
                <td className="px-4 py-3">
                  {w.whale_moves.action} · {w.whale_moves.wallet}
                  <div className="text-xs text-[#efe6d6]/50">{w.whale_moves.note}</div>
                </td>
                <td className="px-4 py-3 text-right font-mono">{usd(w.whale_moves.amountUsd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 className="font-display mt-10 text-3xl italic">Events</h2>
      <div className="mt-4 space-y-3">
        {events.map((e) => (
          <article key={e.onchain_events.id} className="panel rounded-2xl p-4">
            <div className="flex justify-between gap-3 font-mono text-xs text-[#6ee7f9]">
              <span>{e.onchain_events.kind}</span>
              <span>{e.tokens?.symbol}</span>
            </div>
            <p className="mt-2">{e.onchain_events.note}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
