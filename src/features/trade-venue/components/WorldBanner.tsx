"use client";
import { tr } from "@/src/lib/i18n";

import { TruthChip } from "@/src/components/truth/TruthChip";
import type { ViewState, World } from "@/src/features/trade-venue/logic/model";

/**
 * The banner stack above the work area. It answers, in order:
 *   1. is this data demo/simulated at all? (DEMO / SIMULATED ribbon line)
 *   2. is the current `?state=` variant something other than the calm default?
 *   3. what does the adapter know about freshness right now?
 * Every banner is informational — none of them is a dismissal target.
 */
export interface WorldBannerProps {
  world: World;
  state: ViewState;
  demoForced: boolean;
  isFixture: boolean;
}

const STATE_NOTES: Partial<Record<ViewState, string>> = {
  LOADING: tr("fa", "tradeVenue.ui.WorldBanner_1"),
  EMPTY: tr("fa", "tradeVenue.ui.WorldBanner_2"),
  ERROR: tr("fa", "tradeVenue.ui.WorldBanner_3"),
  UNKNOWN: tr("fa", "tradeVenue.ui.WorldBanner_4"),
  UNAVAILABLE: tr("fa", "tradeVenue.ui.WorldBanner_5"),
  STALE: tr("fa", "tradeVenue.ui.WorldBanner_6"),
  PARTIAL: tr("fa", "tradeVenue.ui.WorldBanner_7"),
  HISTORICAL: tr("fa", "tradeVenue.ui.WorldBanner_8"),
};

export function WorldBanner({ world, state, demoForced, isFixture }: WorldBannerProps) {
  const isSim = world === "SIMULATION";
  const stateNote = STATE_NOTES[state];

  return (
    <div className="tv-banners" data-banners="">
      {isSim ? (
        <div className="tv-banner tv-banner--sim" data-banner="simulation">
          <span className="tv-banner__code" dir="ltr">
            SIMULATED
          </span>
          <span>
            {tr("fa", "tradeVenue.ui.WorldBanner_9")}
            {tr("fa", "tradeVenue.ui.WorldBanner_10")}
          </span>
          <TruthChip status="SIMULATED" size="sm" />
        </div>
      ) : null}

      {isFixture ? (
        <div className="tv-banner" data-banner="demo">
          <span className="tv-banner__code" dir="ltr">
            DEMO
          </span>
          <span>
            {tr("fa", "tradeVenue.ui.WorldBanner_11")}
            {demoForced ? tr("fa", "tradeVenue.ui.WorldBanner_12") : ""}. هیچ عدد زندهٔ
            {tr("fa", "tradeVenue.ui.WorldBanner_13")}
          </span>
          <TruthChip status="DEMO" size="sm" />
        </div>
      ) : null}

      {stateNote ? (
        <div className="tv-banner tv-banner--state" data-banner="state" data-state={state}>
          <span className="tv-banner__code" dir="ltr">
            {state}
          </span>
          <span>{stateNote}</span>
        </div>
      ) : null}

    </div>
  );
}
