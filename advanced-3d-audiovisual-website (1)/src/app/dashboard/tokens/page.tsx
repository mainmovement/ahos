import { listTokensWithScores } from "@/lib/queries";
import { PageHeader } from "@/components/dashboard/Shared";
import { TokenTable } from "@/components/dashboard/TokenTable";

export const dynamic = "force-dynamic";

export default async function TokensPage() {
  const rows = await listTokensWithScores();

  return (
    <div>
      <PageHeader
        eyebrow="Discovery"
        title="Token Discovery"
        description="Pre-launch signals, newly launched tokens, and hidden existing opportunities — ranked by the council's opportunity score."
      />
      <TokenTable rows={rows} />
    </div>
  );
}
