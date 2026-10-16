"use client";

import { useMemo } from "react";
import { SourceChip, TruthChip } from "@/src/components/truth/TruthChip";
import { PermissionChip } from "@/src/components/truth/PermissionChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import { ValueCell } from "@/src/components/truth/ValueCell";
import type { ViewState, WatchlistItem, World } from "@/src/features/trade-venue/logic/model";
import { NOT_AUTHORIZED_FA } from "@/src/features/trade-venue/logic/truth";
import { ageShort, signedPct, staleDetail } from "@/src/features/trade-venue/logic/format";
import type { VenueFilters } from "@/src/features/trade-venue/logic/selectors";
import { filterWatchlist } from "@/src/features/trade-venue/logic/selectors";

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
    <section className="ah-panel" data-panel="watchlist" aria-label="فهرست پیگیری">
      <header className="ah-panel__head">
        <span className="ah-panel__title">فهرست پیگیری</span>
        <span className="ah-panel__title-en" dir="ltr">
          WATCHLIST
        </span>
        <div className="ah-panel__tools">
          <TruthChip status={world === "SIMULATION" ? "SIMULATED" : "DEMO"} size="sm" />
          <span className="ah-chip ah-chip--sm" data-chip="" data-tone="unknown">
            <span className="ah-chip__code" dir="ltr">
              {visible.length}
            </span>
          </span>
        </div>
      </header>

      <div className="ah-panel__body">
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? "فهرست پیگیری در حال خواندن است."
                : renderState === "UNAVAILABLE"
                  ? "فهرست پیگیری در این استقرار در دسترس نیست."
                  : "خواندن فهرست پیگیری ناموفق بود."
            }
          />
        ) : visible.length === 0 ? (
          <StateBlock
            state="EMPTY"
            bodyFa="این فهرست خالی است یا فیلتر فعلی چیزی باقی نگذاشته است."
          />
        ) : (
          <div className="ah-list" data-table="watchlist">
            {visible.map((row) => (
              /* Two lines per symbol: quote on top, provenance underneath.
                 Nothing is squeezed, and provenance never loses a column. */
              <div className="ah-list__row ah-list__row--stack" key={row.symbol} data-row-id={row.symbol}>
                <div className="ah-list__line">
                  <span className="ah-list__sym">{row.symbol}</span>
                  <span className="ah-list__fa">{row.symbolFa}</span>
                  <span className="ah-list__tail">
                    <ValueCell
                      value={row.price}
                      fractionDigits={row.price !== null && Math.abs(row.price) < 1 ? 4 : 2}
                      labelMissing={false}
                    />
                    <span className="ah-mono ah-dim" data-change="neutral">
                      {signedPct(row.changePct)}
                    </span>
                  </span>
                </div>
                <div className="ah-list__line ah-list__line--meta">
                  {!row.paperAllowed ? <PermissionChip allowed={false} /> : null}
                  <TruthChip status={row.status} size="sm" hideCode />
                  <SourceChip sourceId={row.sourceId} demo />
                  <span className="ah-faint ah-cell-sub" dir="ltr" title={row.updatedAt ?? "نامشخص"}>
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

      <footer className="ah-panel__foot">
        <span>عدد درصد بدون رنگ‌آمیزی خوب/بد نشان داده می‌شود؛ این صفحه داوری نمی‌کند.</span>
      </footer>
    </section>
  );
}
