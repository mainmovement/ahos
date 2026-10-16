"use client";
import { tr } from "@/src/lib/i18n";

import { TruthChip, SourceChip } from "@/src/components/truth/TruthChip";
import { rowDisplay } from "@/src/features/trade-venue/logic/rowStatus";
import { RowStatusCell } from "./RowStatusCell";
import { PermissionChip } from "@/src/components/truth/PermissionChip";
import { WorldChip } from "@/src/components/truth/WorldChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import type { Opportunity, ViewState } from "@/src/features/trade-venue/logic/model";
import { NOT_AUTHORIZED_FA, PERMITTED_FA } from "@/src/features/trade-venue/logic/truth";
import { ageShort } from "@/src/features/trade-venue/logic/format";
import type { EvidencePayload } from "./EvidenceDrawer";

/**
 * Candidate book (`opportunities[]`): what the paper engine is *allowed* to
 * mirror. Two independent facts are shown side by side — the permission flag
 * (`paperAllowed`) and the canonical status of the candidate — because a
 * candidate can be canonical and still not be paper-authorized.
 */
export function OpportunityBook({
  rows,
  state,
  referenceISO,
  onEvidence,
}: {
  rows: readonly Opportunity[];
  state: ViewState;
  referenceISO: string | null;
  onEvidence: (payload: EvidencePayload) => void;
}) {
  const renderState =
    state === "LOADING" || state === "ERROR" || state === "UNAVAILABLE" ? state : null;

  return (
    <section className="tv-panel" data-panel="opportunities" aria-label={tr("fa", "tradeVenue.ui.OpportunityBook_1")}>
      <header className="tv-panel__head">
        <span className="tv-panel__title">{tr("fa", "tradeVenue.ui.OpportunityBook_1")}</span>
        <span className="tv-panel__title-en" dir="ltr">
          CANDIDATE BOOK · PERMISSION &amp; CANONICAL STATUS
        </span>
        <div className="tv-panel__tools">
          <TruthChip status="DEMO" size="sm" />
          {rows[0] ? <WorldChip world={rows[0].world} /> : null}
          <span className="tv-chip tv-chip--sm" data-chip="" data-tone="unknown">
            <span className="tv-chip__code" dir="ltr">
              {rows.length}
            </span>
          </span>
        </div>
      </header>

      <div className={renderState ? "tv-panel__body" : "tv-panel__body tv-panel__body--tight"}>
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={tr("fa", "tradeVenue.ui.OpportunityBook_2")}
          />
        ) : rows.length === 0 ? (
          <StateBlock state="EMPTY" bodyFa={tr("fa", "tradeVenue.ui.OpportunityBook_3")} />
        ) : (
          <table className="tv-table tv-table--narrow" data-table="opportunities">
            <thead>
              <tr>
                <th scope="col">{tr("fa", "tradeVenue.ui.EvidenceDrawer_9")}</th>
                <th scope="col">{tr("fa", "tradeVenue.ui.OpportunityBook_4")}</th>
                <th scope="col">{tr("fa", "tradeVenue.ui.OpportunityBook_5")}</th>
                <th scope="col">{tr("fa", "tradeVenue.ui.EvidenceDrawer_11")}</th>
                <th scope="col">{tr("fa", "tradeVenue.ui.OpportunityBook_6")}</th>
                <th scope="col">{tr("fa", "tradeVenue.ui.OpportunityBook_7")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.symbol}-${row.evidenceId ?? "na"}`} data-row-id={row.symbol}>
                  <td title={`${row.symbol} · ${row.symbolFa}`}>
                    <span className="tv-cell-symbol">{row.symbol}</span>
                    <span className="tv-cell-fa">{row.symbolFa}</span>
                  </td>
                  <td>
                    <PermissionChip allowed={row.paperAllowed} />
                  </td>
                  <td>
                    <RowStatusCell status={rowDisplay({ status: row.canonicalStatus, updatedAt: row.updatedAt, sourceId: row.sourceId }).status} demo={rowDisplay({ status: row.canonicalStatus, updatedAt: row.updatedAt, sourceId: row.sourceId }).demo} updatedAt={row.updatedAt} referenceISO={referenceISO} />
                  </td>
                  <td>
                    <SourceChip sourceId={row.sourceId} demo />
                  </td>
                  <td>
                    <span className="tv-mono" dir="ltr">
                      {ageShort(row.updatedAt, referenceISO)}
                    </span>
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
                            kind: "opportunity",
                            symbol: row.symbol,
                            status: row.canonicalStatus,
                            sourceId: row.sourceId,
                            updatedAt: row.updatedAt,
                            worldLabel: row.world === "SIMULATION" ? tr("fa", "tradeVenue.ui.StateBlock_11") : tr("fa", "tradeVenue.ui.FillLog_10"),
                            extra: [
                              {
                                label: tr("fa", "tradeVenue.ui.OpportunityBook_4"),
                                value: row.paperAllowed ? PERMITTED_FA : NOT_AUTHORIZED_FA,
                              },
                            ],
                          })
                        }
                      >
                        {tr("fa", "tradeVenue.ui.EvidenceDrawer_1")}
                      </button>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <footer className="tv-panel__foot">
        <span>
          {tr("fa", "tradeVenue.ui.OpportunityBook_8")}
        </span>
      </footer>
    </section>
  );
}
