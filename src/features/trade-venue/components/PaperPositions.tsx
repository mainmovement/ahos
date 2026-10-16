"use client";
import { tr } from "@/src/lib/i18n";

import { Fragment, useMemo, useState } from "react";
import { TruthChip, SourceChip } from "@/src/components/truth/TruthChip";
import { PermissionChip } from "@/src/components/truth/PermissionChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import { DemoRibbon } from "@/src/components/truth/DemoRibbon";
import { ValueCell } from "@/src/components/truth/ValueCell";
import type { PaperPosition, ViewState, World } from "@/src/features/trade-venue/logic/model";
import { WORLD_LABEL_FA } from "@/src/features/trade-venue/logic/model";
import {
  COLUMN_HINTS,
  SIDE_FA,
  TABLE_LABELS,
} from "@/src/features/trade-venue/logic/labels";
import { ageShort, staleDetail } from "@/src/features/trade-venue/logic/format";
import { rowDisplay } from "@/src/features/trade-venue/logic/rowStatus";
import { RowStatusCell } from "./RowStatusCell";
import { NOT_AUTHORIZED_FA, PERMITTED_FA } from "@/src/features/trade-venue/logic/truth";
import type { StatusFilter, VenueFilters } from "@/src/features/trade-venue/logic/selectors";
import { filterPositions } from "@/src/features/trade-venue/logic/selectors";
import type { EvidencePayload } from "./EvidenceDrawer";
import { FilterBar } from "./FilterBar";

/**
 * Open paper positions.
 *
 * Column discipline: `unrealized` is a *neutral* number (truth rule 8 — no
 * good/bad colouring), the mark carries its own status chip (a STALE or
 * CONFLICT mark is not silently trusted), and permission is its own column
 * («مجاز» / «غیرمجاز») rather than a colour on the row.
 */
export interface PaperPositionsProps {
  rows: readonly PaperPosition[];
  world: World;
  state: ViewState;
  filters: VenueFilters;
  referenceISO: string | null;
  demoForced: boolean;
  onEvidence: (payload: EvidencePayload) => void;
  /* Filter + export live in this panel: they act on the blotter, so they belong
     to it (and the terminal keeps the rows it frees up). */
  onFiltersChange: (filters: VenueFilters) => void;
  onExport: () => void;
  exportedAt: string | null;
  statusOptions: readonly StatusFilter[];
}

export function PaperPositions({
  rows,
  world,
  state,
  filters,
  referenceISO,
  demoForced,
  onEvidence,
  onFiltersChange,
  onExport,
  exportedAt,
  statusOptions,
}: PaperPositionsProps) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const visible = useMemo(() => filterPositions(rows, filters), [rows, filters]);

  const renderState =
    state === "LOADING" || state === "EMPTY" || state === "ERROR" || state === "UNAVAILABLE"
      ? state
      : null;

  return (
    <section
      className="tv-panel tv-panel--focus tv-ribbon-host"
      data-panel="paper-positions"
      aria-label={tr("fa", "tradeVenue.ui.PaperPositions_1")}
    >
      {/* Ribbon follows the *data*: a simulated book, or a bundle whose rows are
          all DEMO. A mixed book keeps the chip alone (the ribbon would overclaim). */}
      {world === "SIMULATION" ? (
        <DemoRibbon variant="SIMULATED" />
      ) : demoForced ? (
        <DemoRibbon variant="DEMO" />
      ) : null}
      <header className="tv-panel__head">
        <span className="tv-panel__title">{tr("fa", "tradeVenue.ui.PaperPositions_1")}</span>
        <span className="tv-panel__title-en" dir="ltr">
          OPEN PAPER POSITIONS
        </span>
        <div className="tv-panel__tools">
          <TruthChip
            status={demoForced ? "DEMO" : world === "SIMULATION" ? "SIMULATED" : "DEMO"}
            size="sm"
            title={tr("fa", "tradeVenue.ui.PaperPositions_2")}
          />
          <span className="tv-chip tv-chip--sm" data-chip="" data-tone="unknown">
            <span className="tv-chip__code" dir="ltr">
              {visible.length}/{rows.length}
            </span>
          </span>
        </div>
      </header>

      <div className="tv-panel__toolbar" data-panel-toolbar="positions">
        <FilterBar
          filters={filters}
          onChange={onFiltersChange}
          onExport={onExport}
          visible={visible.length}
          total={rows.length}
          statusOptions={statusOptions}
        />
        {exportedAt ? (
          <span className="tv-work__hint" data-export-taken="">
            خروجی خواندنی ساخته شد · asOf={exportedAt} · برچسب DEMO در فایل درج شد.
          </span>
        ) : null}
      </div>

      <div className={renderState ? "tv-panel__body" : "tv-panel__body tv-panel__body--tight"}>
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? tr("fa", "tradeVenue.ui.PaperPositions_3")
                : renderState === "EMPTY"
                  ? tr("fa", "tradeVenue.ui.PaperPositions_4")
                  : renderState === "UNAVAILABLE"
                    ? tr("fa", "tradeVenue.ui.PaperPositions_5")
                    : tr("fa", "tradeVenue.ui.PaperPositions_6")
            }
            hintFa={tr("fa", "tradeVenue.ui.PaperPositions_7")}
          />
        ) : visible.length === 0 ? (
          <StateBlock
            state="EMPTY"
            bodyFa={tr("fa", "tradeVenue.ui.PaperPositions_8")}
          />
        ) : (
          <table className="tv-table tv-table--dense" data-table="positions">
            <thead>
              <tr>
                <th scope="col">{TABLE_LABELS.symbol}</th>
                <th scope="col">{TABLE_LABELS.side}</th>
                <th scope="col">{TABLE_LABELS.qty}</th>
                <th scope="col" title={COLUMN_HINTS.mark}>
                  {TABLE_LABELS.mark}
                </th>
                <th scope="col" title={COLUMN_HINTS.unrealized}>
                  {TABLE_LABELS.unrealized}
                </th>
                <th scope="col">{TABLE_LABELS.status}</th>
                <th scope="col" title={`${COLUMN_HINTS.evidence} · ${COLUMN_HINTS.paperAllowed}`}>
                  {tr("fa", "tradeVenue.ui.PaperPositions_9")}
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => {
                const isOpen = expanded === row.id;
                const display = rowDisplay({ status: row.status, updatedAt: row.updatedAt, sourceId: row.sourceId, bundleDemo: demoForced });
                const rowClass = [
                  world === "SIMULATION" ? "tv-table__row--sim" : !row.paperAllowed ? "tv-table__row--demoted" : "",
                  display.demo ? "tv-row--demo" : "",
                ].filter(Boolean).join(" ") || undefined;
                return (
                  <Fragment key={row.id}>
                    <tr className={rowClass} data-row-id={row.id} data-row-demo={display.demo ? "true" : "false"}>
                      <td title={`${row.symbol} · ${row.symbolFa}`}>
                        <span className="tv-cell-symbol">{row.symbol}</span>
                        <span className="tv-cell-fa">{row.symbolFa}</span>
                        {/* Permission is reported as a chip *on the row*, right
                            where a reader looks for the symbol. Unauthorized
                            rows say «غیرمجاز» and never enter a total. */}
                        {!row.paperAllowed ? (
                          <PermissionChip allowed={false} title={COLUMN_HINTS.paperAllowed} />
                        ) : null}
                      </td>
                      <td title={`${SIDE_FA[row.side]} · ${row.side}`}>
                        <span className="tv-side">{SIDE_FA[row.side]}</span>
                      </td>
                      <td>
                        <ValueCell value={row.qty} fractionDigits={row.qty !== null && row.qty < 1 ? 4 : 2} unit={row.qtyUnit} />
                      </td>
                      <td>
                        <span className="tv-mark-cell">
                          <ValueCell value={row.mark} fractionDigits={priceDigits(row.mark)} />
                          {row.markStatus !== row.status ? (
                            <TruthChip status={row.markStatus} size="sm" hideCode />
                          ) : null}
                        </span>
                      </td>
                      <td>
                        {/* Neutral: no green/red, no ranking, no arrow icon. */}
                        <ValueCell value={row.unrealized} signed={false} />
                      </td>
                      <td>
                        <RowStatusCell
                          status={display.status}
                          demo={display.demo}
                          updatedAt={row.updatedAt}
                          referenceISO={referenceISO}
                        />
                      </td>
                      <td>
                        <span className="tv-cell-actions">
                          {row.evidenceId ? (
                            <span
                              className="tv-mono tv-ev-id"
                              dir="ltr"
                              title={`${row.evidenceId} — کپی با دکمهٔ «شاهد»`}
                            >
                              {shortEvidenceId(row.evidenceId)}
                            </span>
                          ) : (
                            <span
                              className="tv-cell-na"
                              data-missing="true"
                              title={tr("fa", "tradeVenue.ui.PaperPositions_10")}
                            >
                              —
                            </span>
                          )}
                          <button
                            type="button"
                            className="tv-btn"
                            data-verb="view"
                            aria-expanded={isOpen}
                            onClick={() => setExpanded(isOpen ? null : row.id)}
                          >
                            {tr("fa", "tradeVenue.ui.PaperPositions_11")}
                          </button>
                          <button
                            type="button"
                            className="tv-btn"
                            data-verb="evidence"
                            disabled={!row.evidenceId}
                            onClick={() =>
                              onEvidence({
                                id: row.evidenceId ?? tr("fa", "tradeVenue.ui.StateBlock_4"),
                                kind: "position",
                                symbol: row.symbol,
                                status: row.status,
                                sourceId: row.sourceId,
                                updatedAt: row.updatedAt,
                                worldLabel: WORLD_LABEL_FA[row.world],
                                extra: [
                                  { label: tr("fa", "tradeVenue.ui.PaperPositions_12"), value: `${row.side} · ${SIDE_FA[row.side]}` },
                                  { label: tr("fa", "tradeVenue.ui.PaperPositions_13"), value: row.venue },
                                  { label: tr("fa", "tradeVenue.ui.PaperPositions_14"), value: row.currency ?? tr("fa", "tradeVenue.ui.StateBlock_4") },
                                ],
                              })
                            }
                          >
                            {tr("fa", "tradeVenue.ui.EvidenceDrawer_1")}
                          </button>
                        </span>
                      </td>
                    </tr>
                    {isOpen ? (
                      <tr className="tv-table__detail">
                        <td colSpan={8}>
                          <div className="tv-detail" data-detail-for={row.id}>
                            <span className="tv-detail__k">{tr("fa", "tradeVenue.ui.PaperPositions_15")}</span>
                            <span className="tv-mono" dir="ltr">
                              {row.evidenceId ?? "—"}
                            </span>
                            <span className="tv-detail__k">{tr("fa", "tradeVenue.ui.EvidenceDrawer_11")}</span>
                            <SourceChip sourceId={row.sourceId} demo />
                            <span className="tv-detail__k">{tr("fa", "tradeVenue.ui.PaperPositions_12")}</span>
                            <span className="tv-mono" dir="ltr">
                              {row.side}
                            </span>
                            <span className="tv-detail__k">{tr("fa", "tradeVenue.ui.PaperPositions_16")}</span>
                            <span className="tv-mono" dir="ltr">
                              {row.venue}
                            </span>
                            <span className="tv-detail__k">{tr("fa", "tradeVenue.ui.PaperPositions_17")}</span>
                            <span className="tv-mono" dir="ltr">
                              {row.currency ?? "—"}
                            </span>
                            <span className="tv-detail__k">{tr("fa", "tradeVenue.ui.PaperPositions_18")}</span>
                            <span className="tv-mono" dir="ltr">
                              {row.updatedAt ?? tr("fa", "tradeVenue.ui.StateBlock_4")}
                            </span>
                            <span className="tv-detail__k">{tr("fa", "tradeVenue.ui.OpportunityBook_4")}</span>
                            <span className={row.paperAllowed ? "tv-dim" : "tv-cell-na"}>
                              {row.paperAllowed ? PERMITTED_FA : NOT_AUTHORIZED_FA}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <footer className="tv-panel__foot">
        <span className="tv-panel__foot-line">
          {tr("fa", "tradeVenue.ui.PaperPositions_19")}
          {tr("fa", "tradeVenue.ui.PaperPositions_20")}
        </span>
      </footer>
    </section>
  );
}

/** `EV-PAPER-2026-1016-0001` → `#0001`; the full id stays in the tooltip and
 *  the evidence drawer. An id is never truncated into something ambiguous. */
function shortEvidenceId(id: string): string {
  const match = id.match(/(\d{4})$/);
  return match ? `#${match[1]}` : id.slice(0, 8);
}

/** Price columns keep their native precision (FX needs 4 dp, BTC 0–1 dp). */
function priceDigits(value: number | null): number {
  if (value === null) return 2;
  if (Math.abs(value) >= 1000) return 1;
  if (Math.abs(value) < 1) return 4;
  return 2;
}
