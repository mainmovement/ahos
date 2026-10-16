"use client";

import { TruthChip } from "@/src/components/truth/TruthChip";
import { WorldChip } from "@/src/components/truth/WorldChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import type { ViewState, World } from "@/src/features/trade-venue/logic/model";
import { WORLD_LABEL_FA } from "@/src/features/trade-venue/logic/model";
import { EXCLUSION_FA, MISSING_GLYPH, PAPER_NOTE_FA } from "@/src/features/trade-venue/logic/truth";
import type { ResultBlock, VenueTotals } from "@/src/features/trade-venue/logic/selectors";
import { valueText } from "@/src/features/trade-venue/logic/format";

/**
 * «نتیجه کاغذی» — the honesty centrepiece.
 *
 * Design decisions that matter more than the numbers:
 *  · Results are grouped by unit. USD and USDT are never added together, so a
 *    single "grand total" line is only offered when the block holds exactly one
 *    unit — otherwise the card says why it refuses to total.
 *  · DEMO, SIMULATED, UNKNOWN and non-authorized rows are removed *before* any
 *    arithmetic and are reported separately, with reasons, in the footnote.
 *  · When nothing qualifies the card prints «ناموجود», never «۰».
 *  · Realized and unrealized values are neutral text: no green/red, no arrows.
 */
export interface PaperResultCardProps {
  totals: VenueTotals;
  world: World;
  otherWorld: World;
  state: ViewState;
  demoForced: boolean;
}

export function PaperResultCard({
  totals,
  world,
  otherWorld,
  state,
  demoForced,
}: PaperResultCardProps) {
  const renderState =
    state === "LOADING" || state === "ERROR" || state === "UNAVAILABLE" ? state : null;
  const isSim = world === "SIMULATION";

  return (
    <section
      className="ah-panel ah-ribbon-host"
      data-panel="paper-result"
      data-world={world}
      aria-label="نتیجهٔ کاغذی"
    >
      <header className="ah-panel__head">
        <span className="ah-panel__title">
          {isSim ? "نتیجهٔ شبیه‌سازی" : "نتیجهٔ کاغذی"}
        </span>
        <span className="ah-panel__title-en" dir="ltr">
          {isSim ? "SIMULATED RESULT" : "PAPER RESULT"}
        </span>
        <div className="ah-panel__tools">
          <TruthChip status={isSim ? "SIMULATED" : "DEMO"} size="sm" />
          <WorldChip world={world} />
        </div>
      </header>

      <div className="ah-panel__body">
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? "جمع‌ها پس از پایان خواندن ساخته می‌شوند؛ تا آن زمان هیچ عددی نشان داده نمی‌شود."
                : renderState === "UNAVAILABLE"
                  ? "جمع کاغذی در این استقرار در دسترس نیست."
                  : "خواندن دفتر ناموفق بود؛ هیچ جمعی ساخته نمی‌شود."
            }
          />
        ) : (
          <>
            <ResultGroup
              titleFa="نتیجهٔ بسته‌شده (محقق‌شده)"
              titleEn="REALIZED · CLOSED"
              block={totals.closed}
              world={world}
            />
            <div className="ah-result-divider" />
            <ResultGroup
              titleFa="نتیجهٔ باز (نشانه‌نخورده)"
              titleEn="UNREALIZED · OPEN"
              block={totals.open}
              world={world}
            />

            <div className="ah-result-counts">
              <Count labelFa="موقعیت باز" value={totals.counts.openRows} />
              <Count labelFa="ردیف بسته‌شده" value={totals.counts.closedRows} />
              <Count labelFa="بدون مقدار" value={totals.counts.unknownRows} />
              <Count labelFa="غیرمجاز" value={totals.counts.notAuthorizedRows} />
              <Count
                labelFa="خوانده‌نشده (کنار گذاشته)"
                value={totals.counts.withheldRows}
                missingText="نامشخص"
              />
            </div>

            <div className="ah-result-excluded" data-excluded-summary="">
              <div className="ah-result-excluded__head">
                <span>کنار گذاشته‌شده از جمع</span>
                <span className="ah-panel__title-en" dir="ltr">
                  EXCLUDED
                </span>
              </div>
              <p className="ah-state__body ah-one-line" title={describeExclusions(totals)}>
                {describeExclusions(totals)}
              </p>
              <p
                className="ah-state__body ah-one-line"
                title={`ردیف‌های جهان دیگر («${WORLD_LABEL_FA[otherWorld]}») با برچسب «جهان دیگر» کنار گذاشته می‌شوند.`}
              >
                «{WORLD_LABEL_FA[otherWorld]}» سهمی در این جمع ندارد.
              </p>
            </div>

            <p className="ah-note" style={{ marginTop: 10 }} data-paper-note="true">
              <span aria-hidden="true">⛉</span>
              <span>{PAPER_NOTE_FA}</span>
            </p>

            {demoForced ? (
              <p className="ah-state__body" data-demo-forced="true">
                برچسب DEMO به‌صورت دستی/محیطی روشن شده است؛ هیچ سطحی در این صفحه زنده تلقی نمی‌شود.
              </p>
            ) : null}
          </>
        )}
      </div>
    </section>
  );
}

function ResultGroup({
  titleFa,
  titleEn,
  block,
  world,
}: {
  titleFa: string;
  titleEn: string;
  block: ResultBlock;
  world: World;
}) {
  return (
    <div className="ah-result-group" data-result-group={titleEn}>
      <div className="ah-result-group__head">
        <span className="ah-result-group__title">{titleFa}</span>
        <span className="ah-panel__title-en" dir="ltr">
          {titleEn}
        </span>
      </div>

      {block.groups.length === 0 ? (
        <div className="ah-kv__row">
          <span className="ah-kv__k">جمع</span>
          <span className="ah-kv__v ah-kv__v--na" data-total="missing">
            {MISSING_GLYPH} <small>ناموجود</small>
          </span>
        </div>
      ) : (
        block.groups.map((group) => (
          <div className="ah-kv__row" key={group.unit} data-total-unit={group.unit}>
            <span className="ah-kv__k">
              جمع{" "}
              <span className="ah-chip ah-chip--sm" data-tone="unknown">
                <span className="ah-chip__code" dir="ltr">
                  {group.unit}
                </span>
              </span>
              <span className="ah-kv__en" dir="ltr">
                · {group.totals.included.length} rows
              </span>
            </span>
            <span className="ah-kv__v" data-total="value">
              {group.totals.sum === null ? (
                <span className="ah-cell-na" data-missing="true">
                  {MISSING_GLYPH}
                  <small>ناموجود</small>
                </span>
              ) : (
                valueText(group.totals.sum, { fractionDigits: 2 })
              )}
            </span>
          </div>
        ))
      )}

      {block.mixedUnits ? (
        <p
          className="ah-state__body ah-one-line"
          data-mixed-units="true"
          title="واحدها ناهمگون‌اند؛ جمع کل ارائه نمی‌شود تا عدد ساختگی ساخته نشود. هر واحد جداگانه گزارش می‌شود."
        >
          واحدها ناهمگون‌اند · جمع کل ساخته نمی‌شود.
        </p>
      ) : null}

      <p
        className="ah-state__body ah-one-line"
        title="ردیف‌های نمایشی، نامشخص و بی‌مجوز در این جمع نیستند."
      >
        دامنه: {world === "SIMULATION" ? "کتاب شبیه‌سازی" : "دفتر کاغذی واقعی"} · ردیف‌های نمایشی و
        نامشخص کنار گذاشته شده‌اند.
      </p>
    </div>
  );
}

function Count({
  labelFa,
  value,
  missingText = "—",
}: {
  labelFa: string;
  value: number | null;
  missingText?: string;
}) {
  return (
    <div className="ah-count">
      <span className="ah-count__k">{labelFa}</span>
      <span className="ah-count__v" data-count-label={labelFa}>
        {value === null ? missingText : value}
      </span>
    </div>
  );
}

/** One sentence per exclusion reason, with counts — never a vague footnote. */
function describeExclusions(totals: VenueTotals): string {
  const reasons = new Map<string, number>();
  for (const block of [totals.closed, totals.open]) {
    for (const row of block.excluded) {
      const key = EXCLUSION_FA[row.reason] ?? row.reason;
      reasons.set(key, (reasons.get(key) ?? 0) + 1);
    }
    for (const row of block.unitless) {
      reasons.set(EXCLUSION_FA.NO_UNIT, (reasons.get(EXCLUSION_FA.NO_UNIT) ?? 0) + 1);
    }
  }
  if (reasons.size === 0) return "هیچ ردیفی کنار گذاشته نشده است.";
  return Array.from(reasons.entries())
    .map(([reason, count]) => `${count} ردیف ${reason}`)
    .join(" · ");
}
