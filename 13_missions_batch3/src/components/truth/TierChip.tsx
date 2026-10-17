// FILE: 13_missions_batch3/src/components/truth/TierChip.tsx
export interface TierChipProps {
  tier: number;
}

/**
 * Visual tier chip. T0 = 2D tables/SVG only, T1 = solid panels (default),
 * T2+ = decoration/blur allowed. Never implies data quality.
 */
export function TierChip({ tier }: TierChipProps) {
  const safe = tier === 0 || tier === 1 || tier === 2 ? tier : 1;
  const label =
    safe === 0 ? "T0 · جدولی" : safe === 1 ? "T1 · جامد" : "T2 · تزئینی";
  return (
    <span className="ah-chip ah-chip-gold" data-testid="tier-chip" data-tier-chip={safe}>
      {label}
    </span>
  );
}
