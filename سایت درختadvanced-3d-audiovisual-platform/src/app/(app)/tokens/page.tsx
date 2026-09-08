import { PageHeader } from "@/components/page-header";
import { TokenCard } from "@/components/token-card";
import { loadBoard } from "@/lib/queries";
import { groupLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function TokensPage() {
  const board = await loadBoard();
  const groups = ["pre_launch", "newly_launched", "hidden"] as const;

  return (
    <div>
      <PageHeader
        kicker="Discovery"
        title="Three orchards. One gate."
        lede="Group A pre-launch, Group B newly launched, Group C hidden. Loud names sit beside rejects so the board stays honest."
      />
      {groups.map((g) => {
        const rows = board.filter((b) => b.token.tokenGroup === g);
        return (
          <section key={g} className="mb-10">
            <h2 className="font-display mb-4 text-3xl italic">{groupLabel(g)}</h2>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {rows.map((row) => (
                <TokenCard key={row.token.id} token={row.token} score={row.score} />
              ))}
            </div>
            {rows.length === 0 && <Empty label="No fruit in this orchard yet." />}
          </section>
        );
      })}
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return <div className="panel rounded-2xl p-8 text-[#efe6d6]/50">{label}</div>;
}
