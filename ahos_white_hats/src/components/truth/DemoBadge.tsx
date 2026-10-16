/**
 * DEMO badge — the visible marker for every mock-backed surface.
 * Diagonal striping is mandatory (truth rule) and DEMO rows/values are
 * always excluded from totals.
 */
export function DemoBadge({ label = "داده نمایشی" }: { label?: string }) {
  return (
    <span
      className="ah-chip ah-chip-lg ah-tone-gold ah-demo-stripes"
      data-status="DEMO"
      data-tone="gold"
      title="این سطح از داده‌ها فقط آداپتور نمایشی است و در هیچ مجموعه‌ای شمرده نمی‌شود."
    >
      <span className="ah-dot" aria-hidden="true" />
      <span>{label}</span>
      <span className="ah-latin text-[8.5px] opacity-70">DEMO</span>
    </span>
  );
}
