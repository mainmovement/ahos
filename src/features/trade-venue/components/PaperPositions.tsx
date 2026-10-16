"use client";

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
      className="ah-panel ah-panel--focus ah-ribbon-host"
      data-panel="paper-positions"
      aria-label="موقعیت‌های کاغذی باز"
    >
      {/* Ribbon follows the *data*: a simulated book, or a bundle whose rows are
          all DEMO. A mixed book keeps the chip alone (the ribbon would overclaim). */}
      {world === "SIMULATION" ? (
        <DemoRibbon variant="SIMULATED" />
      ) : demoForced ? (
        <DemoRibbon variant="DEMO" />
      ) : null}
      <header className="ah-panel__head">
        <span className="ah-panel__title">موقعیت‌های کاغذی باز</span>
        <span className="ah-panel__title-en" dir="ltr">
          OPEN PAPER POSITIONS
        </span>
        <div className="ah-panel__tools">
          <TruthChip
            status={demoForced ? "DEMO" : world === "SIMULATION" ? "SIMULATED" : "DEMO"}
            size="sm"
            title="دادهٔ این جدول از آداپتور نمایشی می‌آید"
          />
          <span className="ah-chip ah-chip--sm" data-chip="" data-tone="unknown">
            <span className="ah-chip__code" dir="ltr">
              {visible.length}/{rows.length}
            </span>
          </span>
        </div>
      </header>

      <div className="ah-panel__toolbar" data-panel-toolbar="positions">
        <FilterBar
          filters={filters}
          onChange={onFiltersChange}
          onExport={onExport}
          visible={visible.length}
          total={rows.length}
          statusOptions={statusOptions}
        />
        {exportedAt ? (
          <span className="ah-work__hint" data-export-taken="">
            خروجی خواندنی ساخته شد · asOf={exportedAt} · برچسب DEMO در فایل درج شد.
          </span>
        ) : null}
      </div>

      <div className={renderState ? "ah-panel__body" : "ah-panel__body ah-panel__body--tight"}>
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? "دفتر کاغذی در حال خواندن است؛ هیچ عددی تا پایان خواندن نمایش داده نمی‌شود."
                : renderState === "EMPTY"
                  ? "موتور کاغذی هیچ موقعیت بازی ثبت نکرده است."
                  : renderState === "UNAVAILABLE"
                    ? "این بخش در این استقرار در دسترس نیست."
                    : "خواندن دفتر کاغذی ناموفق بود؛ عددی ساخته نمی‌شود."
            }
            hintFa="تنها کارهای ممکن: فیلتر و خروجی خواندنی."
          />
        ) : visible.length === 0 ? (
          <StateBlock
            state="EMPTY"
            bodyFa="با این فیلتر ردیفی مطابقت ندارد. فیلترها را بردارید تا همهٔ ردیف‌ها دیده شود."
          />
        ) : (
          <table className="ah-table ah-table--dense" data-table="positions">
            <thead>
              <tr>
                <th scope="col">{TABLE_LABELS.symbol}</th>
                <th scope="col">{TABLE_LABELS.side}</th>
                <th scope="col">{TABLE_LABELS.qty}</th>
                <th scope="col">{TABLE_LABELS.entry}</th>
                <th scope="col" title={COLUMN_HINTS.mark}>
                  {TABLE_LABELS.mark}
                </th>
                <th scope="col" title={COLUMN_HINTS.unrealized}>
                  {TABLE_LABELS.unrealized}
                </th>
                <th scope="col">{TABLE_LABELS.status}</th>
                <th scope="col" title={`${COLUMN_HINTS.evidence} · ${COLUMN_HINTS.paperAllowed}`}>
                  شاهد / کارها
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => {
                const isOpen = expanded === row.id;
                const rowClass =
                  world === "SIMULATION"
                    ? "ah-table__row--sim"
                    : !row.paperAllowed
                      ? "ah-table__row--demoted"
                      : undefined;
                return (
                  <Fragment key={row.id}>
                    <tr className={rowClass} data-row-id={row.id}>
                      <td title={`${row.symbol} · ${row.symbolFa}`}>
                        <span className="ah-cell-symbol">{row.symbol}</span>
                        <span className="ah-cell-fa">{row.symbolFa}</span>
                        {/* Permission is reported as a chip *on the row*, right
                            where a reader looks for the symbol. Unauthorized
                            rows say «غیرمجاز» and never enter a total. */}
                        {!row.paperAllowed ? (
                          <PermissionChip allowed={false} title={COLUMN_HINTS.paperAllowed} />
                        ) : null}
                      </td>
                      <td title={`${SIDE_FA[row.side]} · ${row.side}`}>
                        <span className="ah-side">{SIDE_FA[row.side]}</span>
                      </td>
                      <td>
                        <ValueCell value={row.qty} fractionDigits={row.qty !== null && row.qty < 1 ? 4 : 2} unit={row.qtyUnit} />
                      </td>
                      <td>
                        <ValueCell value={row.entry} fractionDigits={priceDigits(row.entry)} />
                      </td>
                      <td>
                        <span className="ah-mark-cell">
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
                      <td
                        title={
                          row.status === "STALE"
                            ? staleDetail(row.updatedAt, referenceISO)
                            : `${ageShort(row.updatedAt, referenceISO)} · ${row.updatedAt ?? "نامشخص"}`
                        }
                      >
                        <TruthChip status={row.status} size="sm" hideCode />
                      </td>
                      <td>
                        <span className="ah-cell-actions">
                          {row.evidenceId ? (
                            <span
                              className="ah-mono ah-ev-id"
                              dir="ltr"
                              title={`${row.evidenceId} — کپی با دکمهٔ «شاهد»`}
                            >
                              {shortEvidenceId(row.evidenceId)}
                            </span>
                          ) : (
                            <span
                              className="ah-cell-na"
                              data-missing="true"
                              title="شناسهٔ شاهد ثبت نشده"
                            >
                              —
                            </span>
                          )}
                          <button
                            type="button"
                            className="ah-btn"
                            data-verb="view"
                            aria-expanded={isOpen}
                            onClick={() => setExpanded(isOpen ? null : row.id)}
                          >
                            نمایش
                          </button>
                          <button
                            type="button"
                            className="ah-btn"
                            data-verb="evidence"
                            disabled={!row.evidenceId}
                            onClick={() =>
                              onEvidence({
                                id: row.evidenceId ?? "نامشخص",
                                kind: "position",
                                symbol: row.symbol,
                                status: row.status,
                                sourceId: row.sourceId,
                                updatedAt: row.updatedAt,
                                worldLabel: WORLD_LABEL_FA[row.world],
                                extra: [
                                  { label: "طرف", value: `${row.side} · ${SIDE_FA[row.side]}` },
                                  { label: "دفتر", value: row.venue },
                                  { label: "واحد", value: row.currency ?? "نامشخص" },
                                ],
                              })
                            }
                          >
                            شاهد
                          </button>
                        </span>
                      </td>
                    </tr>
                    {isOpen ? (
                      <tr className="ah-table__detail">
                        <td colSpan={8}>
                          <div className="ah-detail" data-detail-for={row.id}>
                            <span className="ah-detail__k">شناسهٔ شاهد</span>
                            <span className="ah-mono" dir="ltr">
                              {row.evidenceId ?? "—"}
                            </span>
                            <span className="ah-detail__k">منبع</span>
                            <SourceChip sourceId={row.sourceId} demo />
                            <span className="ah-detail__k">طرف</span>
                            <span className="ah-mono" dir="ltr">
                              {row.side}
                            </span>
                            <span className="ah-detail__k">دفتر کاغذی</span>
                            <span className="ah-mono" dir="ltr">
                              {row.venue}
                            </span>
                            <span className="ah-detail__k">واحد نتیجه</span>
                            <span className="ah-mono" dir="ltr">
                              {row.currency ?? "—"}
                            </span>
                            <span className="ah-detail__k">زمان خواندن</span>
                            <span className="ah-mono" dir="ltr">
                              {row.updatedAt ?? "نامشخص"}
                            </span>
                            <span className="ah-detail__k">مجوز کاغذی</span>
                            <span className={row.paperAllowed ? "ah-dim" : "ah-cell-na"}>
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

      <footer className="ah-panel__foot">
        <span className="ah-panel__foot-line">
          موقعیت کاغذی؛ پول واقعی در کار نیست · «—» یعنی نامشخص، نه صفر · نتیجهٔ باز خنثی است و
          رتبه‌بندی نمی‌شود
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
