"use client";
import { tr } from "@/src/lib/i18n";

import { rowDisplay } from "@/src/features/trade-venue/logic/rowStatus";
import { RowStatusCell } from "./RowStatusCell";

import { useMemo } from "react";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { PermissionChip } from "@/src/components/truth/PermissionChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import { ValueCell } from "@/src/components/truth/ValueCell";
import type { ChipStatus, ViewState, WatchlistItem, World } from "@/src/features/trade-venue/logic/model";
import { NOT_AUTHORIZED_FA } from "@/src/features/trade-venue/logic/truth";
import { ageShort, signedPct, staleDetail } from "@/src/features/trade-venue/logic/format";
import type { VenueFilters } from "@/src/features/trade-venue/logic/selectors";
import { filterWatchlist } from "@/src/features/trade-venue/logic/selectors";

function watchDisplay(row: { status: ChipStatus; updatedAt: string | null; sourceId: string }) {
  return rowDisplay({ status: row.status, updatedAt: row.updatedAt, sourceId: row.sourceId });
}

/**
 * Watchlist — "what the desk is looking at", never "what to touch".
 * A change percentage is printed as a signed neutral number with no green/red
 * treatment, and an unknown price is «—», never `0.00`.
 */
export interface WatchlistPanelProps {
  rows: readonly WatchlistItem[];
  world: World;
  state: ViewState;
  filters: VenueFilters;
  referenceISO: string | null;
}

export function WatchlistPanel({ rows, world, state, filters, referenceISO }: WatchlistPanelProps) {
  const visible = useMemo(() => filterWatchlist(rows, filters), [rows, filters]);
  const renderState =
    state === "LOADING" || state === "ERROR" || state === "UNAVAILABLE" ? state : null;

  return (
    <section className="tv-panel" data-panel="watchlist" aria-label={tr("fa", "tradeVenue.ui.WatchlistPanel_1")}>
      <header className="tv-panel__head">
        <span className="tv-panel__title">{tr("fa", "tradeVenue.ui.WatchlistPanel_1")}</span>
        <span className="tv-panel__title-en" dir="ltr">
          WATCHLIST
        </span>
        <div className="tv-panel__tools">
          <TruthChip status={world === "SIMULATION" ? "SIMULATED" : "DEMO"} size="sm" />
          <span className="tv-chip tv-chip--sm" data-chip="" data-tone="unknown">
            <span className="tv-chip__code" dir="ltr">
              {visible.length}
            </span>
          </span>
        </div>
      </header>

      <div className="tv-panel__body">
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? tr("fa", "tradeVenue.ui.WatchlistPanel_2")
                : renderState === "UNAVAILABLE"
                  ? tr("fa", "tradeVenue.ui.WatchlistPanel_3")
                  : tr("fa", "tradeVenue.ui.WatchlistPanel_4")
            }
          />
        ) : visible.length === 0 ? (
          <StateBlock
            state="EMPTY"
            bodyFa={tr("fa", "tradeVenue.ui.WatchlistPanel_5")}
          />
        ) : (
          <div className="tv-list" data-table="watchlist">
            {visible.map((row) => (
              /* Two lines per symbol: quote on top, provenance underneath.
                 Nothing is squeezed, and provenance never loses a column. */
              <div className="tv-list__row tv-list__row--stack" key={row.symbol} data-row-id={row.symbol}>
                <div className="tv-list__line">
                  <span className="tv-list__sym">{row.symbol}</span>
                  <span className="tv-list__fa">{row.symbolFa}</span>
                  <span className="tv-list__tail">
                    <ValueCell
                      value={row.price}
                      fractionDigits={row.price !== null && Math.abs(row.price) < 1 ? 4 : 2}
                      labelMissing={false}
                    />
                    <span className="tv-mono tv-dim" data-change="neutral">
                      {signedPct(row.changePct)}
                    </span>
                  </span>
                </div>
                <div className="tv-list__line tv-list__line--meta">
                  {!row.paperAllowed ? <PermissionChip allowed={false} /> : null}
                  <RowStatusCell {...watchDisplay(row)} updatedAt={row.updatedAt} referenceISO={referenceISO} />
                  <span className="tv-faint tv-cell-sub" dir="ltr" title={row.updatedAt ?? tr("fa", "tradeVenue.ui.StateBlock_4")}>
                    {row.status === "STALE"
                      ? staleDetail(row.updatedAt, referenceISO)
                      : ageShort(row.updatedAt, referenceISO)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <footer className="tv-panel__foot">
        <span>{tr("fa", "tradeVenue.ui.WatchlistPanel_6")}</span>
      </footer>
    </section>
  );
}
