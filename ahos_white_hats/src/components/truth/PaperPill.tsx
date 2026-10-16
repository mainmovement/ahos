/**
 * Permanent, non-dismissible PAPER_ONLY pill.
 * Truth rule: always visible in the topbar — there is no code path that
 * removes it, because there is no code path that enables real trading here.
 */
export function PaperPill() {
  return (
    <span
      className="ah-chip ah-chip-lg ah-tone-gold select-none"
      data-testid="paper-only-pill"
      title="این صفحه در حالت فقط‌کاغذی قفل است؛ هیچ کنترل اجرایی وجود ندارد."
      aria-label="فقط کاغذی · PAPER_ONLY"
    >
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="5" y="10.5" width="14" height="9.5" rx="2" stroke="currentColor" strokeWidth="2" />
        <path d="M8 10.5V8a4 4 0 1 1 8 0v2.5" stroke="currentColor" strokeWidth="2" />
      </svg>
      <span>فقط کاغذی</span>
      <span className="ah-latin text-[8.5px] opacity-70">PAPER_ONLY</span>
    </span>
  );
}
