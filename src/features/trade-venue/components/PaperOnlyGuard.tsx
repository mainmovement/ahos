import { tr } from "@/src/lib/i18n";
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
      className="tv-pill tv-pill--paper"
      data-paper-only="permanent"
      data-dismissible="false"
      dir="rtl"
      title={tr("fa", "tradeVenue.ui.PaperOnlyGuard_1")}
    >
      <span className="tv-pill__lock" aria-hidden="true">
        ⛉
      </span>
      {tr("fa", "tradeVenue.row.paperOnly")}
      <span className="tv-pill__en tv-mono" dir="ltr">
        {PAPER_ONLY_CODE}
      </span>
    </span>
  );
}

/** Inline reassurance line that sits under the positions table. */
export function PaperOnlyNote({ tone = "gold" }: { tone?: "gold" | "sim" }) {
  return (
    <p className="tv-note" data-paper-note="true">
      <span aria-hidden="true">{tone === "sim" ? "◈" : "⛉"}</span>
      <span>{PAPER_NOTE_FA}</span>
      <span className="tv-mono tv-faint" dir="ltr">
        {PAPER_ONLY_FA} · no real money
      </span>
    </p>
  );
}
