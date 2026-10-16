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
    <div className="ah-gallery" data-gallery="">
      <header className="ah-topbar" style={{ position: "static" }}>
        <div className="ah-topbar__row">
          <div className="ah-brand">
            <span className="ah-brand__title">گالری حالت‌ها · میدان معامله</span>
            <span className="ah-brand__sub">STATE GALLERY · همهٔ حالت‌ها از یک آداپتور</span>
          </div>
          <TruthChip status="DEMO" />
          <span className="ah-pill ah-pill--paper">فقط کاغذی · PAPER_ONLY</span>
          <span className="ah-spacer" />
          <span className="ah-pill ah-pill--tier" dir="ltr">
            TIER {query.tier}
          </span>
        </div>
      </header>

      <div className="ah-gallery__grid">
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
            <section className="ah-panel" key={state} data-gallery-state={state}>
              <header className="ah-panel__head">
                <span className="ah-panel__title" dir="ltr">
                  {state}
                </span>
                <div className="ah-panel__tools">
                  <TruthChip status={state === "DEFAULT" ? "DEMO" : state} size="sm" />
                  <span className="ah-chip ah-chip--sm" data-chip="" data-tone="unknown">
                    <span className="ah-chip__code" dir="ltr">
                      rows={countRows(snapshot)}
                    </span>
                  </span>
                </div>
              </header>
              <div className="ah-panel__body">
                {isRenderState ? (
                  <StateBlock
                    state={state}
                    bodyFa="این حالت قبل از وجود هر عددی رندر می‌شود؛ جدول جای خود را به این بلوک می‌دهد."
                  />
                ) : (
                  <div className="ah-kv">
                    <div className="ah-kv__row">
                      <span className="ah-kv__k">جمع واحد اصلی (نتیجهٔ بسته)</span>
                      <span className="ah-kv__v">
                        {totals.closed.groups
                          .map((group) => `${group.unit}:${group.totals.sum ?? "—"}`)
                          .join(" / ") || "—"}
                      </span>
                    </div>
                    <div className="ah-kv__row">
                      <span className="ah-kv__k">واحدها</span>
                      <span className="ah-kv__v">{totals.closed.units.join(" / ") || "—"}</span>
                    </div>
                    <div className="ah-kv__row">
                      <span className="ah-kv__k">کنار گذاشته‌شده</span>
                      <span className="ah-kv__v">
                        {totals.closed.excludedCount + totals.open.excludedCount}
                      </span>
                    </div>
                    <div className="ah-kv__row ah-kv__row--wrap">
                      <span className="ah-kv__k">کنارگذاری به‌دلیل وضعیت</span>
                      <span className="ah-kv__v" data-exclusion-breakdown="true">
                        {exclusionCodes.length === 0 ? (
                          <span className="ah-kv__v--na">—</span>
                        ) : (
                          <span className="ah-kv__codes">
                            {exclusionCodes.map(([reason, count]) => (
                              <span className="ah-kv__code" key={reason}>
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
