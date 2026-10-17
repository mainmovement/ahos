import { tr } from "@/src/lib/i18n";
import { getVenueBundle } from "@/src/mock/trade_venue";
import type { VenueQuery } from "./logic/model";
import { VenueClientRoot } from "./VenueClientRoot";
import { StateGallery } from "./StateGallery";
import { RealPaperPanel } from "../real-paper/components/RealPaperPanel";

/**
 * Trade venue page body. It renders inside the Arena shell (which owns the
 * topbar, sidebar and footer). Server component: decides which bundle to hand
 * to the client tree and builds the human-readable notices.
 */
export interface TradeVenuePageProps {
  query: VenueQuery;
}

export function TradeVenuePage({ query }: TradeVenuePageProps) {
  const bundle = getVenueBundle(query);
  const t = (key: string) => tr("fa", `tradeVenue.${key}`);

  if (query.gallery) {
    return (
      <div className="tv-venue-root" data-tier={query.tier} data-gallery-mode="true" lang="fa" dir="rtl">
        <StateGallery query={query} />
      </div>
    );
  }

  const snapshot = query.world === "SIMULATION" ? bundle.simulation : bundle.realPaper;

  const notices: string[] = [t("notice.demo")];
  if (query.forceDemo) notices.push(t("notice.forced"));
  if (snapshot.telemetry.withheldRows !== null) {
    notices.push(t("notice.withheld").replace("{n}", String(snapshot.telemetry.withheldRows)));
  }
  if (snapshot.paper.some((row) => row.status === "UNKNOWN")) notices.push(t("notice.gap"));

  return (
    <div
      className="tv-venue-root"
      data-tier={query.tier}
      data-demo-forced={query.forceDemo ? "true" : "false"}
      data-state={query.state}
      lang="fa"
      dir="rtl"
    >
      <RealPaperPanel />
      <VenueClientRoot bundle={bundle} query={query} notices={notices} />
    </div>
  );
}
