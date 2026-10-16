/**
 * Quality tiers.
 *
 * T0 — 2D tables and hairlines only. No blur, no gradients, no decoration.
 *      Still fully readable and fully honest; used for low-power / wireframes.
 * T1 — Solid panels, subtle borders, still no blur (default).
 * T2 — Glass panels (backdrop blur), gold glow, decorative depth. Decoration
 *      never carries data.
 */

export type Tier = 0 | 1 | 2;

export const DEFAULT_TIER: Tier = 1;

export const TIERS: readonly Tier[] = [0, 1, 2] as const;

export function parseTier(raw: string | null | undefined): Tier {
  if (raw === '0') return 0;
  if (raw === '2') return 2;
  return DEFAULT_TIER;
}

/** `true` when decorative (non-data-carrying) chrome is allowed. */
export function decorativeChrome(tier: Tier): boolean {
  return tier >= 2;
}