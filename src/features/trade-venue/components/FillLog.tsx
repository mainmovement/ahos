"use client";
import { tr } from "@/src/lib/i18n";

import { useMemo } from "react";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import { DemoRibbon } from "@/src/components/truth/DemoRibbon";
import { ValueCell } from "@/src/components/truth/ValueCell";
import type { FillLogEntry, ViewState, World } from "@/src/features/trade-venue/logic/model";
import { ACTION_FA, TABLE_LABELS } from "@/src/features/trade-venue/logic/labels";
import { staleDetail } from "@/src/features/trade-venue/logic/format";
import { rowDisplay } from "@/src/features/trade-venue/logic/rowStatus";
import { RowStatusCell } from "./RowStatusCell";
import type { VenueFilters } from "@/src/features/trade-venue/logic/selectors";
import { filterFillLog } from "@/src/features/trade-venue/logic/selectors";
import type { EvidencePayload } from "./EvidenceDrawer";

/**
 * Fill / activity log — the centre column, and the primary "what happened"
 * surface of the venue. It is a *log*, not an order ticket: every row records
 * something the paper engine already did, each row names its source, and the
 * DEMO / LIVE distinction is a chip rather than a colour on the row.
 */
export interface FillLogProps {
  rows: readonly FillLogEntry[];
  world: World;
  state: ViewState;
  filters: VenueFilters;
  referenceISO: string | null;
  demoForced: boolean;
  onEvidence: (payload: EvidencePayload) => void;
}

export function FillLog({
  rows,
  world,
  state,
  filters,
  referenceISO,
  demoForced,
  onEvidence,
}: FillLogProps) {
  const visible = useMemo(() => filterFillLog(rows, filters), [rows, filters]);
  const renderState =
    state === "LOADING" || state === "EMPTY" || state === "ERROR" || state === "UNAVAILABLE"
      ? state
      : null;

  return (
    <section className="tv-panel tv-ribbon-host" data-panel="fill-log" aria-label={tr("fa", "tradeVenue.ui.FillLog_1")}>
      {world === "SIMULATION" ? (
        <DemoRibbon variant="SIMULATED" />
      ) : demoForced ? (
        <DemoRibbon variant="DEMO" />
      ) : null}
      <header className="tv-panel__head">
        <span className="tv-panel__title">{tr("fa", "tradeVenue.ui.FillLog_2")}</span>
        <span className="tv-panel__title-en" dir="ltr">
          FILL &amp; ACTIVITY LOG
        </span>
        <div className="tv-panel__tools">
          <TruthChip status="DEMO" size="sm" title={tr("fa", "tradeVenue.ui.FillLog_3")} />
          <span className="tv-chip tv-chip--sm" data-chip="" data-tone="unknown">
            <span className="tv-chip__code" dir="ltr">
              {visible.length}/{rows.length}
            </span>
          </span>
        </div>
      </header>

      <div className={renderState ? "tv-panel__body" : "tv-panel__body tv-panel__body--tight"}>
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? tr("fa", "tradeVenue.ui.FillLog_4")
                : renderState === "EMPTY"
                  ? tr("fa", "tradeVenue.ui.FillLog_5")
                  : renderState === "UNAVAILABLE"
                    ? tr("fa", "tradeVenue.ui.FillLog_6")
                    : tr("fa", "tradeVenue.ui.FillLog_7")
            }
          />
        ) : visible.length === 0 ? (
          <StateBlock state="EMPTY" bodyFa={tr("fa", "tradeVenue.ui.FillLog_8")} />
        ) : (
          <table className="tv-table tv-table--dense" data-table="fill-log">
            <thead>
              <tr>
                <th scope="col">{TABLE_LABELS.time}</th>
                <th scope="col">{TABLE_LABELS.symbol}</th>
                <th scope="col">{TABLE_LABELS.action}</th>
                <th scope="col">{TABLE_LABELS.qty}</th>
                <th scope="col">{TABLE_LABELS.price}</th>
                <th scope="col">{TABLE_LABELS.status}</th>
                <th scope="col">{TABLE_LABELS.actions}</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => {
                const display = rowDisplay({ status: row.status, updatedAt: row.at, sourceId: row.sourceId, bundleDemo: demoForced });
                return (
                <tr
                  key={row.id}
                  className={[world === "SIMULATION" ? "tv-table__row--sim" : "", display.demo ? "tv-row--demo" : ""].filter(Boolean).join(" ") || undefined}
                  data-row-id={row.id}
                  data-row-demo={display.demo ? "true" : "false"}
                >
                  <td
                    title={
                      row.status === "STALE"
                        ? `کهنه · ${staleDetail(row.at, referenceISO)}`
                        : tr("fa", "tradeVenue.ui.FillLog_9")
                    }
                  >
                    <span className="tv-mono" dir="ltr">
                      {row.timeTehran}
                    </span>

                  </td>
                  <td>
                    <span className="tv-cell-symbol">{row.symbol}</span>
                  </td>
                  <td title={row.action}>
                    <span className="tv-side">{ACTION_FA[row.action]}</span>
                    {row.noteFa ? <span className="tv-cell-sub tv-dim">{row.noteFa}</span> : null}
                  </td>
                  <td>
                    <ValueCell value={row.qty} fractionDigits={row.qty !== null && Math.abs(row.qty) < 1 ? 4 : 2} />
                  </td>
                  <td>
                    <ValueCell value={row.price} fractionDigits={row.price !== null && Math.abs(row.price) < 1 ? 4 : 2} />
                  </td>
                  <td>
                    <RowStatusCell status={display.status} demo={display.demo} updatedAt={row.at} referenceISO={referenceISO} />
                  </td>
                  <td>
                    <span className="tv-cell-actions">
                      <button
                        type="button"
                        className="tv-btn"
                        data-verb="evidence"
                        disabled={!row.evidenceId}
                        onClick={() =>
                          onEvidence({
                            id: row.evidenceId ?? tr("fa", "tradeVenue.ui.StateBlock_4"),
                            kind: "fill",
                            symbol: row.symbol,
                            status: row.status,
                            sourceId: row.sourceId,
                            updatedAt: row.at,
                            worldLabel: world === "SIMULATION" ? tr("fa", "tradeVenue.ui.StateBlock_11") : tr("fa", "tradeVenue.ui.FillLog_10"),
                            extra: [
                              { label: tr("fa", "tradeVenue.ui.FillLog_11"), value: row.action },
                              { label: tr("fa", "tradeVenue.ui.FillLog_9"), value: row.timeTehran },
                            ],
                          })
                        }
                      >
                        {tr("fa", "tradeVenue.ui.EvidenceDrawer_1")}
                      </button>
                    </span>
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <footer className="tv-panel__foot">
        <span>{tr("fa", "tradeVenue.ui.FillLog_12")}</span>
      </footer>
    </section>
  );
}
