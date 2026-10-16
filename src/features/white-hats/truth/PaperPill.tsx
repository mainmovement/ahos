import { tr } from "@/src/lib/i18n";
/**
 * Permanent, non-dismissible PAPER_ONLY pill.
 * Truth rule: always visible in the topbar — there is no code path that
 * removes it, because there is no code path that enables real trading here.
 */
export function PaperPill() {
  return (
    <span
      className="wh-chip wh-chip-lg wh-tone-gold select-none"
      data-testid="paper-only-pill"
      title={tr("fa", "whiteHats.ui.PaperPill_1")}
      aria-label={tr("fa", "whiteHats.ui.PaperPill_2")}
    >
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="5" y="10.5" width="14" height="9.5" rx="2" stroke="currentColor" strokeWidth="2" />
        <path d="M8 10.5V8a4 4 0 1 1 8 0v2.5" stroke="currentColor" strokeWidth="2" />
      </svg>
      <span>{tr("fa", "whiteHats.ui.PaperPill_3")}</span>
      <span className="wh-latin text-[12px] opacity-70">PAPER_ONLY</span>
    </span>
  );
}
