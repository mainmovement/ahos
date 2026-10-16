import DashboardShell from "../../../src/components/layout/DashboardShell";
import { TradeVenuePage } from "../../../src/features/trade-venue/TradeVenuePage";
import { readVenueSearchParams } from "../../../src/features/trade-venue/logic/search-params";

/** Arena route /arena/trade-venue. Read-only, paper-only; mock adapter (DEMO). Rendered inside the Arena shell. */
export default async function ArenaTradeVenueRoute({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = readVenueSearchParams(await searchParams);
  return (
    <DashboardShell activeId="trade-venue">
      <TradeVenuePage query={query} />
    </DashboardShell>
  );
}
