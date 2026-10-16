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
  LOADING: "در حال خواندن",
  EMPTY: "ردیفی ثبت نشده است",
  ERROR: "خطای خواندن",
  UNKNOWN: "نامشخص",
  UNAVAILABLE: "در دسترس نیست",
  STALE: "داده کهنه است",
  PARTIAL: "خواندن ناقص",
  PLANNED: "برنامه‌ریزی‌شده",
  MISSING: "غایب",
  HISTORICAL: "تاریخی",
  SIMULATED: "شبیه‌سازی",
  CONFLICT: "تناقض منابع",
  REJECTED: "ردشده",
  DEMO: "نمایشی",
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
      className={`ah-state ah-state--${state.toLowerCase()}`}
      data-state-block={state}
      role={state === "ERROR" ? "alert" : "status"}
    >
      <span className="ah-state__icon" aria-hidden="true">
        {ICON[state]}
      </span>
      <div>
        <span className="ah-state__title">
          {title}
          <span className="ah-state__en" dir="ltr">
            {state}
          </span>
        </span>
        {bodyFa ? <p className="ah-state__body">{bodyFa}</p> : null}
        {state === "STALE" ? (
          <p className="ah-state__body">
            آخرین به‌روزرسانی:{" "}
            <span className="ah-mono" dir="ltr">
              {lastUpdateText ?? "نامشخص"}
            </span>
          </p>
        ) : null}
        {hintFa ? <p className="ah-state__body">{hintFa}</p> : null}
      </div>
    </div>
  );
}
