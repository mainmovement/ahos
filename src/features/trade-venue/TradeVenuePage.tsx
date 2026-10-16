import { getVenueBundle } from "@/src/mock/trade_venue";
import type { VenueQuery } from "./logic/model";
import { PAPER_ONLY_CODE } from "./logic/truth";
import { VenueClientRoot } from "./VenueClientRoot";
import { StateGallery } from "./StateGallery";
import { AhosWorldDock } from "./components/AhosWorldDock";
import { DecorativeHall } from "./components/DecorativeHall";
import { RealityMapFooter } from "./components/RealityMapFooter";

/**
 * Trading venue page (Persian: «میدان معامله · کاغذی»).
 *
 * Server component: it owns the *data* decision (which bundle to hand to the
 * client), the quality tier, and the two constant surfaces (dock + footer).
 * Everything reactive lives in `VenueClientRoot`.
 */
export interface TradeVenuePageProps {
  query: VenueQuery;
}

/** A visible build identity so a screenshot can be tied to a revision. */
const TREE_SHA =
  process.env.NEXT_PUBLIC_AHOS_TREE_SHA ?? "tree-sha: local-offline-build";

export function TradeVenuePage({ query }: TradeVenuePageProps) {
  const bundle = getVenueBundle(query);

  const tierClass =
    query.tier === "T0" ? "ah-root--t0" : query.tier === "T1" ? "ah-root--t1" : "ah-root--t2";

  if (query.gallery) {
    return (
      <main
        className={`ah-venue-root ${tierClass}`}
        data-tier={query.tier}
        data-gallery-mode="true"
        lang="fa"
        dir="rtl"
      >
        <StateGallery query={query} />
      </main>
    );
  }

  const snapshot = query.world === "SIMULATION" ? bundle.simulation : bundle.realPaper;

  const notices: string[] = [
    `آداپتور: ${bundle.provenance.adapter} · حالت ${PAPER_ONLY_CODE} · برچسب DEMO برای همهٔ سطوح`,
  ];
  if (query.forceDemo) {
    notices.push("برچسب DEMO با ?demo=1 روشن شده است.");
  }
  if (snapshot.telemetry.withheldRows !== null) {
    notices.push(`${snapshot.telemetry.withheldRows} ردیف کنار گذاشته شده است (خواندن ناقص).`);
  }
  const gapFeed = snapshot.paper.some((row) => row.status === "UNKNOWN");
  if (gapFeed) {
    notices.push("حداقل یک فید قطع است؛ ردیف‌های آن نامشخص می‌مانند و عددی برایشان ساخته نمی‌شود.");
  }

  return (
    <main
      className={`ah-venue-root ${tierClass}`}
      data-tier={query.tier}
      data-demo-forced={query.forceDemo ? "true" : "false"}
      data-state={query.state}
      lang="fa"
      dir="rtl"
    >
      {query.tier === "T2" ? <DecorativeHall /> : null}

      <VenueClientRoot
        bundle={bundle}
        query={query}
        dock={<AhosWorldDock />}
        footer={<RealityMapFooter treeSha={TREE_SHA} tier={query.tier} />}
        notices={notices}
      />
    </main>
  );
}
