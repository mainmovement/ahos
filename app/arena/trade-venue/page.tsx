import Link from "next/link";
import { tr } from "../../../src/lib/i18n";
import { TradeVenuePage } from "../../../src/features/trade-venue/TradeVenuePage";
import { readVenueSearchParams } from "../../../src/features/trade-venue/logic/search-params";

/** Arena route /arena/trade-venue. Read-only, paper-only; mock adapter (DEMO). */
export default async function ArenaTradeVenueRoute({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = readVenueSearchParams(await searchParams);
  return (
    <div dir="rtl" lang="fa" style={{ background: "#080b10", minHeight: "100dvh" }}>
      <nav
        aria-label={tr("fa", "tradeVenue.title")}
        style={{ display: "flex", gap: 12, alignItems: "center", padding: "8px 16px", color: "#ecece7", fontFamily: "Vazirmatn, Inter, sans-serif", fontSize: 13, borderBottom: "1px solid rgba(217,185,119,.16)" }}
      >
        <Link href="/arena" style={{ color: "#d9b977" }}>{tr("fa", "tradeVenue.back")}</Link>
        <span>{tr("fa", "tradeVenue.title")}</span>
        <span>{tr("fa", "tradeVenue.note")}</span>
      </nav>
      <TradeVenuePage query={query} />
    </div>
  );
}
