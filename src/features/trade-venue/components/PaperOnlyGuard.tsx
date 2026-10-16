import { PAPER_ONLY_CODE, PAPER_ONLY_FA, PAPER_NOTE_FA } from "@/src/features/trade-venue/logic/truth";

/**
 * The permanent PAPER_ONLY marker.
 *
 * Deliberately *not* a button and deliberately *not* dismissible: there is no
 * state in which this page can claim to touch real money, so there is no state
 * in which the marker should disappear. `data-dismissible="false"` is asserted
 * by the tests.
 */
export function PaperOnlyPill() {
  return (
    <span
      className="ah-pill ah-pill--paper"
      data-paper-only="permanent"
      data-dismissible="false"
      dir="rtl"
      title="این میز فقط کاغذی است؛ هیچ مسیر سفارش واقعی وجود ندارد."
    >
      <span className="ah-pill__lock" aria-hidden="true">
        ⛉
      </span>
      {"فقط کاغذی"}
      <span className="ah-pill__en ah-mono" dir="ltr">
        {PAPER_ONLY_CODE}
      </span>
    </span>
  );
}

/** Inline reassurance line that sits under the positions table. */
export function PaperOnlyNote({ tone = "gold" }: { tone?: "gold" | "sim" }) {
  return (
    <p className="ah-note" data-paper-note="true">
      <span aria-hidden="true">{tone === "sim" ? "◈" : "⛉"}</span>
      <span>{PAPER_NOTE_FA}</span>
      <span className="ah-mono ah-faint" dir="ltr">
        {PAPER_ONLY_FA} · no real money
      </span>
    </p>
  );
}
