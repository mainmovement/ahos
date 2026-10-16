"use client";
import { tr } from "@/src/lib/i18n";

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
      className="tv-panel tv-ribbon-host"
      data-panel="paper-result"
      data-world={world}
      aria-label={tr("fa", "tradeVenue.ui.PaperResultCard_1")}
    >
      <header className="tv-panel__head">
        <span className="tv-panel__title">
          {isSim ? tr("fa", "tradeVenue.ui.PaperResultCard_2") : tr("fa", "tradeVenue.ui.PaperResultCard_1")}
        </span>
        <span className="tv-panel__title-en" dir="ltr">
          {isSim ? "SIMULATED RESULT" : "PAPER RESULT"}
        </span>
        <div className="tv-panel__tools">
          <TruthChip status={isSim ? "SIMULATED" : "DEMO"} size="sm" />
          <WorldChip world={world} />
        </div>
      </header>

      <div className="tv-panel__body">
        {renderState ? (
          <StateBlock
            state={renderState}
            bodyFa={
              renderState === "LOADING"
                ? tr("fa", "tradeVenue.ui.PaperResultCard_3")
                : renderState === "UNAVAILABLE"
                  ? tr("fa", "tradeVenue.ui.PaperResultCard_4")
                  : tr("fa", "tradeVenue.ui.PaperResultCard_5")
            }
          />
        ) : (
          <>
            <ResultGroup
              titleFa={tr("fa", "tradeVenue.ui.PaperResultCard_6")}
              titleEn="REALIZED · CLOSED"
              block={totals.closed}
              world={world}
            />
            <div className="tv-result-divider" />
            <ResultGroup
              titleFa={tr("fa", "tradeVenue.ui.PaperResultCard_7")}
              titleEn="UNREALIZED · OPEN"
              block={totals.open}
              world={world}
            />

            <div className="tv-result-counts">
              <Count labelFa={tr("fa", "tradeVenue.ui.PaperResultCard_8")} value={totals.counts.openRows} />
              <Count labelFa={tr("fa", "tradeVenue.ui.PaperResultCard_9")} value={totals.counts.closedRows} />
              <Count labelFa={tr("fa", "tradeVenue.ui.PaperResultCard_10")} value={totals.counts.unknownRows} />
              <Count labelFa={tr("fa", "tradeVenue.ui.PaperResultCard_11")} value={totals.counts.notAuthorizedRows} />
              <Count
                labelFa={tr("fa", "tradeVenue.ui.PaperResultCard_12")}
                value={totals.counts.withheldRows}
                missingText={tr("fa", "tradeVenue.ui.StateBlock_4")}
              />
            </div>

            <div className="tv-result-excluded" data-excluded-summary="">
              <div className="tv-result-excluded__head">
                <span>{tr("fa", "tradeVenue.ui.PaperResultCard_13")}</span>
                <span className="tv-panel__title-en" dir="ltr">
                  EXCLUDED
                </span>
              </div>
              <p className="tv-state__body tv-one-line" title={describeExclusions(totals)}>
                {describeExclusions(totals)}
              </p>
              <p
                className="tv-state__body tv-one-line"
                title={`ردیف‌های جهان دیگر («${WORLD_LABEL_FA[otherWorld]}») با برچسب «جهان دیگر» کنار گذاشته می‌شوند.`}
              >
                «{WORLD_LABEL_FA[otherWorld]}» سهمی در این جمع ندارد.
              </p>
            </div>

            <p className="tv-note" style={{ marginTop: 10 }} data-paper-note="true">
              <span aria-hidden="true">⛉</span>
              <span>{PAPER_NOTE_FA}</span>
            </p>

            {demoForced ? (
              <p className="tv-state__body" data-demo-forced="true">
                {tr("fa", "tradeVenue.ui.PaperResultCard_14")}
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
    <div className="tv-result-group" data-result-group={titleEn}>
      <div className="tv-result-group__head">
        <span className="tv-result-group__title">{titleFa}</span>
        <span className="tv-panel__title-en" dir="ltr">
          {titleEn}
        </span>
      </div>

      {block.groups.length === 0 ? (
        <div className="tv-kv__row">
          <span className="tv-kv__k">{tr("fa", "tradeVenue.ui.PaperResultCard_15")}</span>
          <span className="tv-kv__v tv-kv__v--na" data-total="missing">
            {MISSING_GLYPH} <small>{tr("fa", "tradeVenue.ui.PaperResultCard_16")}</small>
          </span>
        </div>
      ) : (
        block.groups.map((group) => (
          <div className="tv-kv__row" key={group.unit} data-total-unit={group.unit}>
            <span className="tv-kv__k">
              جمع{" "}
              <span className="tv-chip tv-chip--sm" data-tone="unknown">
                <span className="tv-chip__code" dir="ltr">
                  {group.unit}
                </span>
              </span>
              <span className="tv-kv__en" dir="ltr">
                · {group.totals.included.length} rows
              </span>
            </span>
            <span className="tv-kv__v" data-total="value">
              {group.totals.sum === null ? (
                <span className="tv-cell-na" data-missing="true">
                  {MISSING_GLYPH}
                  <small>{tr("fa", "tradeVenue.ui.PaperResultCard_16")}</small>
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
          className="tv-state__body tv-one-line"
          data-mixed-units="true"
          title={tr("fa", "tradeVenue.ui.PaperResultCard_17")}
        >
          {tr("fa", "tradeVenue.ui.PaperResultCard_18")}
        </p>
      ) : null}

      <p
        className="tv-state__body tv-one-line"
        title={tr("fa", "tradeVenue.ui.PaperResultCard_19")}
      >
        دامنه: {world === "SIMULATION" ? tr("fa", "tradeVenue.ui.PaperResultCard_20") : tr("fa", "tradeVenue.ui.PaperResultCard_21")} · ردیف‌های نمایشی و
        {tr("fa", "tradeVenue.ui.PaperResultCard_22")}
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
    <div className="tv-count">
      <span className="tv-count__k">{labelFa}</span>
      <span className="tv-count__v" data-count-label={labelFa}>
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
  if (reasons.size === 0) return tr("fa", "tradeVenue.ui.PaperResultCard_23");
  return Array.from(reasons.entries())
    .map(([reason, count]) => `${count} ردیف ${reason}`)
    .join(" · ");
}
