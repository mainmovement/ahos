"use client";

import { TruthChip, SourceChip } from "@/src/components/truth/TruthChip";
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
    <section className="ah-panel" data-panel="opportunities" aria-label="دفتر نامزدها">
      <header className="ah-panel__head">
        <span className="ah-panel__title">دفتر نامزدها</span>
        <span className="ah-panel__title-en" dir="ltr">
          CANDIDATE BOOK · PERMISSION &amp; CANONICAL STATUS
        </span>
        <div className="ah-panel__tools">
          <TruthChip status="DEMO" size="sm" />
          {rows[0] ? <WorldChip world={rows[0].world} /> : null}
          <span className="ah-chip ah-chip--sm" data-chip="" data-tone="unknown">
            <span className="ah-chip__code" dir="ltr">
              {rows.length}
            </span>
          </span>
        </div>
      </header>

      <div className={renderState ? "ah-panel__body" : "ah-panel__body ah-panel__body--tight"}>
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa="دفتر نامزدها در دسترس نیست؛ هیچ نامزدی حدس زده نمی‌شود."
          />
        ) : rows.length === 0 ? (
          <StateBlock state="EMPTY" bodyFa="هیچ نامزدی ثبت نشده است." />
        ) : (
          <table className="ah-table ah-table--narrow" data-table="opportunities">
            <thead>
              <tr>
                <th scope="col">نماد</th>
                <th scope="col">مجوز کاغذی</th>
                <th scope="col">وضعیت کانونیک</th>
                <th scope="col">منبع</th>
                <th scope="col">عمر</th>
                <th scope="col">کارها</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.symbol}-${row.evidenceId ?? "na"}`} data-row-id={row.symbol}>
                  <td title={`${row.symbol} · ${row.symbolFa}`}>
                    <span className="ah-cell-symbol">{row.symbol}</span>
                    <span className="ah-cell-fa">{row.symbolFa}</span>
                  </td>
                  <td>
                    <PermissionChip allowed={row.paperAllowed} />
                  </td>
                  <td>
                    <TruthChip status={row.canonicalStatus} size="sm" />
                  </td>
                  <td>
                    <SourceChip sourceId={row.sourceId} demo />
                  </td>
                  <td>
                    <span className="ah-mono" dir="ltr">
                      {ageShort(row.updatedAt, referenceISO)}
                    </span>
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
                            kind: "opportunity",
                            symbol: row.symbol,
                            status: row.canonicalStatus,
                            sourceId: row.sourceId,
                            updatedAt: row.updatedAt,
                            worldLabel: row.world === "SIMULATION" ? "شبیه‌سازی" : "کاغذی واقعی",
                            extra: [
                              {
                                label: "مجوز کاغذی",
                                value: row.paperAllowed ? PERMITTED_FA : NOT_AUTHORIZED_FA,
                              },
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
        <span>
          مجوز کاغذی یک پرچم گزارشی است، نه کنترل اجرایی: این جدول هیچ راهی برای فرستادن چیزی ندارد.
        </span>
      </footer>
    </section>
  );
}
