import { tr } from "@/src/lib/i18n";
import { StateBlock } from "@/src/components/truth/StateBlock";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { TelemetryStrip } from "./components/TelemetryStrip";
import { getVenueBundle } from "@/src/mock/trade_venue";
import type { VenueQuery, ViewState } from "./logic/model";
import { countRows } from "./logic/truth";
import { summarizeTelemetry, selectVenueTotals } from "./logic/selectors";

const GALLERY_STATES: readonly ViewState[] = [
  "DEFAULT",
  "LOADING",
  "EMPTY",
  "ERROR",
  "UNKNOWN",
  "UNAVAILABLE",
  "STALE",
  "PARTIAL",
  "HISTORICAL",
];

/**
 * State gallery (`?all=1`): every component state the venue can be in, rendered
 * side by side from the same adapter. It exists so a reviewer — or a screenshot
 * run — can see LOADING / EMPTY / ERROR / UNKNOWN / UNAVAILABLE / STALE /
 * PARTIAL / HISTORICAL without fabricating any state by hand.
 */
export function StateGallery({ query }: { query: VenueQuery }) {
  return (
    <div className="tv-gallery" data-gallery="">
      <header className="tv-topbar" style={{ position: "static" }}>
        <div className="tv-topbar__row">
          <div className="tv-brand">
            <span className="tv-brand__title">{tr("fa", "tradeVenue.ui.StateGallery_1")}</span>
            <span className="tv-brand__sub">{tr("fa", "tradeVenue.ui.StateGallery_2")}</span>
          </div>
          <TruthChip status="DEMO" />
          <span className="tv-pill tv-pill--paper">{tr("fa", "tradeVenue.ui.StateGallery_3")}</span>
          <span className="tv-spacer" />
          <span className="tv-pill tv-pill--tier" dir="ltr">
            TIER {query.tier}
          </span>
        </div>
      </header>

      <div className="tv-gallery__grid">
        {GALLERY_STATES.map((state) => {
          const stateQuery: VenueQuery = { ...query, state, gallery: false };
          const bundle = getVenueBundle(stateQuery);
          const snapshot = bundle.realPaper;
          const totals = selectVenueTotals(snapshot, "REAL_PAPER");
          /* Why rows were withheld from the totals: one code per reason, so the
             gallery shows the ledger of what was left out without a wall of text. */
          const exclusionCodes = Array.from(
            [...totals.closed.excluded, ...totals.open.excluded]
              .reduce(
                (acc, entry) => acc.set(entry.reason, (acc.get(entry.reason) ?? 0) + 1),
                new Map<string, number>(),
              )
              .entries(),
          ).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
          const telemetry = summarizeTelemetry(snapshot);
          const isRenderState =
            state === "LOADING" ||
            state === "EMPTY" ||
            state === "ERROR" ||
            state === "UNAVAILABLE";

          return (
            <section className="tv-panel" key={state} data-gallery-state={state}>
              <header className="tv-panel__head">
                <span className="tv-panel__title" dir="ltr">
                  {state}
                </span>
                <div className="tv-panel__tools">
                  <TruthChip status={state === "DEFAULT" ? "DEMO" : state} size="sm" />
                  <span className="tv-chip tv-chip--sm" data-chip="" data-tone="unknown">
                    <span className="tv-chip__code" dir="ltr">
                      rows={countRows(snapshot)}
                    </span>
                  </span>
                </div>
              </header>
              <div className="tv-panel__body">
                {isRenderState ? (
                  <StateBlock
                    state={state}
                    bodyFa={tr("fa", "tradeVenue.ui.StateGallery_4")}
                  />
                ) : (
                  <div className="tv-kv">
                    <div className="tv-kv__row">
                      <span className="tv-kv__k">{tr("fa", "tradeVenue.ui.StateGallery_5")}</span>
                      <span className="tv-kv__v">
                        {totals.closed.groups
                          .map((group) => `${group.unit}:${group.totals.sum ?? "—"}`)
                          .join(" / ") || "—"}
                      </span>
                    </div>
                    <div className="tv-kv__row">
                      <span className="tv-kv__k">{tr("fa", "tradeVenue.ui.StateGallery_6")}</span>
                      <span className="tv-kv__v">{totals.closed.units.join(" / ") || "—"}</span>
                    </div>
                    <div className="tv-kv__row">
                      <span className="tv-kv__k">{tr("fa", "tradeVenue.ui.StateGallery_7")}</span>
                      <span className="tv-kv__v">
                        {totals.closed.excludedCount + totals.open.excludedCount}
                      </span>
                    </div>
                    <div className="tv-kv__row tv-kv__row--wrap">
                      <span className="tv-kv__k">{tr("fa", "tradeVenue.ui.StateGallery_8")}</span>
                      <span className="tv-kv__v" data-exclusion-breakdown="true">
                        {exclusionCodes.length === 0 ? (
                          <span className="tv-kv__v--na">—</span>
                        ) : (
                          <span className="tv-kv__codes">
                            {exclusionCodes.map(([reason, count]) => (
                              <span className="tv-kv__code" key={reason}>
                                {reason}
                                <b>{count}</b>
                              </span>
                            ))}
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                )}
                <TelemetryStrip summary={telemetry} referenceISO={snapshot.freshness.readAt} tier={query.tier} />
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
