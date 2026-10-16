import { tr } from "@/src/lib/i18n";
/**
 * DEMO badge — the visible marker for every mock-backed surface.
 * Diagonal striping is mandatory (truth rule) and DEMO rows/values are
 * always excluded from totals.
 */
export function DemoBadge({ label = "داده نمایشی" }: { label?: string }) {
  return (
    <span
      className="wh-chip wh-chip-lg wh-tone-gold wh-demo-stripes"
      data-status="DEMO"
      data-tone="gold"
      title={tr("fa", "whiteHats.ui.DemoBadge_1")}
    >
      <span className="wh-dot" aria-hidden="true" />
      <span>{label}</span>
      <span className="wh-latin text-[12px] opacity-70">DEMO</span>
    </span>
  );
}
