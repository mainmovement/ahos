import { tr } from "@/src/lib/i18n";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { STATUS_FA } from "@/src/features/trade-venue/logic/truth";

/**
 * Placeholder block for component states that carry *no* data by definition:
 * LOADING, EMPTY, ERROR, UNKNOWN, UNAVAILABLE, STALE, PARTIAL, PLANNED,
 * HISTORICAL, MISSING.
 *
 * A state block never fabricates a number. ERROR and UNAVAILABLE replace the
 * table body entirely; LOADING says what is being read; STALE names the last
 * update it *does* know about (or falls back to UNKNOWN).
 */

const ICON: Record<ChipStatus, string> = {
  LOADING: "◌",
  EMPTY: "∅",
  ERROR: "!",
  UNKNOWN: "?",
  UNAVAILABLE: "⊘",
  STALE: "◷",
  PARTIAL: "◐",
  PLANNED: "◻",
  MISSING: "—",
  HISTORICAL: "⟲",
  SIMULATED: "◈",
  LIVE: "●",
  DEMO: "◍",
  CONFLICT: "≠",
  REJECTED: "✕",
};

const TITLE_FA: Partial<Record<ChipStatus, string>> = {
  LOADING: tr("fa", "tradeVenue.ui.StateBlock_1"),
  EMPTY: tr("fa", "tradeVenue.ui.StateBlock_2"),
  ERROR: tr("fa", "tradeVenue.ui.StateBlock_3"),
  UNKNOWN: tr("fa", "tradeVenue.ui.StateBlock_4"),
  UNAVAILABLE: tr("fa", "tradeVenue.ui.StateBlock_5"),
  STALE: tr("fa", "tradeVenue.ui.StateBlock_6"),
  PARTIAL: tr("fa", "tradeVenue.ui.StateBlock_7"),
  PLANNED: tr("fa", "tradeVenue.ui.StateBlock_8"),
  MISSING: tr("fa", "tradeVenue.ui.StateBlock_9"),
  HISTORICAL: tr("fa", "tradeVenue.ui.StateBlock_10"),
  SIMULATED: tr("fa", "tradeVenue.ui.StateBlock_11"),
  CONFLICT: tr("fa", "tradeVenue.ui.StateBlock_12"),
  REJECTED: tr("fa", "tradeVenue.ui.StateBlock_13"),
  DEMO: tr("fa", "tradeVenue.ui.StateBlock_14"),
};

export interface StateBlockProps {
  state: ChipStatus;
  /** Extra explanation in Persian. */
  bodyFa?: string;
  /** What the *next* honest action is — always read-only. */
  hintFa?: string;
  /** Last known update time, printed verbatim (never invented for STALE). */
  lastUpdateText?: string | null;
}

export function StateBlock({ state, bodyFa, hintFa, lastUpdateText }: StateBlockProps) {
  const title = TITLE_FA[state] ?? STATUS_FA[state];
  return (
    <div
      className={`tv-state tv-state--${state.toLowerCase()}`}
      data-state-block={state}
      role={state === "ERROR" ? "alert" : "status"}
    >
      <span className="tv-state__icon" aria-hidden="true">
        {ICON[state]}
      </span>
      <div>
        <span className="tv-state__title">
          {title}
          <span className="tv-state__en" dir="ltr">
            {state}
          </span>
        </span>
        {bodyFa ? <p className="tv-state__body">{bodyFa}</p> : null}
        {state === "STALE" ? (
          <p className="tv-state__body">
            آخرین به‌روزرسانی:{" "}
            <span className="tv-mono" dir="ltr">
              {lastUpdateText ?? tr("fa", "tradeVenue.ui.StateBlock_4")}
            </span>
          </p>
        ) : null}
        {hintFa ? <p className="tv-state__body">{hintFa}</p> : null}
      </div>
    </div>
  );
}
