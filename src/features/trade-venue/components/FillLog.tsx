"use client";

import { useMemo } from "react";
import { SourceChip, TruthChip } from "@/src/components/truth/TruthChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import { DemoRibbon } from "@/src/components/truth/DemoRibbon";
import { ValueCell } from "@/src/components/truth/ValueCell";
import type { FillLogEntry, ViewState, World } from "@/src/features/trade-venue/logic/model";
import { ACTION_FA, TABLE_LABELS } from "@/src/features/trade-venue/logic/labels";
import { staleDetail } from "@/src/features/trade-venue/logic/format";
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
    <section className="ah-panel ah-ribbon-host" data-panel="fill-log" aria-label="گزارش رخدادها">
      {world === "SIMULATION" ? (
        <DemoRibbon variant="SIMULATED" />
      ) : demoForced ? (
        <DemoRibbon variant="DEMO" />
      ) : null}
      <header className="ah-panel__head">
        <span className="ah-panel__title">گزارش رخداد / فعالیت</span>
        <span className="ah-panel__title-en" dir="ltr">
          FILL &amp; ACTIVITY LOG
        </span>
        <div className="ah-panel__tools">
          <TruthChip status="DEMO" size="sm" title="آداپتور نمایشی" />
          <span className="ah-chip ah-chip--sm" data-chip="" data-tone="unknown">
            <span className="ah-chip__code" dir="ltr">
              {visible.length}/{rows.length}
            </span>
          </span>
        </div>
      </header>

      <div className={renderState ? "ah-panel__body" : "ah-panel__body ah-panel__body--tight"}>
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? "گزارش رخداد در حال خواندن است."
                : renderState === "EMPTY"
                  ? "هیچ رخدادی در بازهٔ خوانده‌شده ثبت نشده است."
                  : renderState === "UNAVAILABLE"
                    ? "گزارش رخداد در این استقرار در دسترس نیست."
                    : "خواندن گزارش رخداد ناموفق بود؛ هیچ ردیفی حدس زده نمی‌شود."
            }
          />
        ) : visible.length === 0 ? (
          <StateBlock state="EMPTY" bodyFa="ردیفی با این فیلتر پیدا نشد." />
        ) : (
          <table className="ah-table ah-table--dense" data-table="fill-log">
            <thead>
              <tr>
                <th scope="col">{TABLE_LABELS.time}</th>
                <th scope="col">{TABLE_LABELS.symbol}</th>
                <th scope="col">{TABLE_LABELS.action}</th>
                <th scope="col">{TABLE_LABELS.qty}</th>
                <th scope="col">{TABLE_LABELS.price}</th>
                <th scope="col">{TABLE_LABELS.notional}</th>
                <th scope="col">{TABLE_LABELS.status}</th>
                <th scope="col">{TABLE_LABELS.source}</th>
                <th scope="col">{TABLE_LABELS.actions}</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr
                  key={row.id}
                  className={world === "SIMULATION" ? "ah-table__row--sim" : undefined}
                  data-row-id={row.id}
                >
                  <td
                    title={
                      row.status === "STALE"
                        ? `کهنه · ${staleDetail(row.at, referenceISO)}`
                        : "زمان تهران"
                    }
                  >
                    <span className="ah-mono" dir="ltr">
                      {row.timeTehran}
                    </span>

                  </td>
                  <td>
                    <span className="ah-cell-symbol">{row.symbol}</span>
                  </td>
                  <td title={row.action}>
                    <span className="ah-side">{ACTION_FA[row.action]}</span>
                    {row.noteFa ? <span className="ah-cell-sub ah-dim">{row.noteFa}</span> : null}
                  </td>
                  <td>
                    <ValueCell value={row.qty} fractionDigits={row.qty !== null && Math.abs(row.qty) < 1 ? 4 : 2} />
                  </td>
                  <td>
                    <ValueCell value={row.price} fractionDigits={row.price !== null && Math.abs(row.price) < 1 ? 4 : 2} />
                  </td>
                  <td data-cell="notional">
                    <ValueCell
                      value={row.notional}
                      fractionDigits={2}
                      unit={row.currency}
                      stacked
                    />
                  </td>
                  <td>
                    <TruthChip status={row.status} size="sm" hideCode />
                  </td>
                  <td>
                    <SourceChip sourceId={row.sourceId} demo />
                  </td>
                  <td>
                    <span className="ah-cell-actions">
                      <button
                        type="button"
                        className="ah-btn"
                        data-verb="evidence"
                        disabled={!row.evidenceId}
                        onClick={() =>
                          onEvidence({
                            id: row.evidenceId ?? "نامشخص",
                            kind: "fill",
                            symbol: row.symbol,
                            status: row.status,
                            sourceId: row.sourceId,
                            updatedAt: row.at,
                            worldLabel: world === "SIMULATION" ? "شبیه‌سازی" : "کاغذی واقعی",
                            extra: [
                              { label: "رخداد", value: row.action },
                              { label: "زمان تهران", value: row.timeTehran },
                            ],
                          })
                        }
                      >
                        شاهد
                      </button>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <footer className="ah-panel__foot">
        <span>این گزارش «چه شد» را می‌گوید، نه «چه چیزی را بفرست». هیچ ردیفی قابلیت اجرا ندارد.</span>
      </footer>
    </section>
  );
}
