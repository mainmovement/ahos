/**
 * M-D3 TruthBadge — the presentation of a canonical truth state.
 *
 * Thin by construction: this component renders what
 * `dashboard_truth_badge.ts` decides and nothing else. It holds no state table,
 * no colour list, no precedence — so the styling the selftest asserts and the
 * styling the dashboard renders are literally the same object, not two copies
 * that can drift.
 *
 * The only branch here is the per-state modifier class, which carries the
 * non-colour cue (dashed / dotted / double / bar) that spec §2.3 requires because
 * "colour is never the only cue". Colour, fill and glow come from `styleFor`.
 *
 * Presentation only (AGENTS.md): this shows a state the Python canonical
 * authority already decided. It never derives, gates, or upgrades one.
 */

import { memo, type CSSProperties } from "react";

import {
  badgeForState,
  labelFor,
  styleFor,
  type BadgeState,
} from "@/dashboard_truth_badge";

/** The one non-colour cue per state, as the modifier class from globals.css. */
const MODIFIER: Record<BadgeState, string> = {
  VERIFIED: "truth-badge--ok",
  STALE: "truth-badge--stale",
  UNKNOWN: "truth-badge--unknown",
  CONFLICT: "truth-badge--conflict",
  REJECTED: "truth-badge--rejected",
};

export interface TruthBadgeProps {
  /** A real enum value from the canonical read model or the decision authority. */
  state: string | null | undefined;
  /** Override the label; defaults to the spec §2.3 Persian gloss. */
  label?: string;
  /** Override the tooltip; defaults to "en — fa". */
  title?: string;
}

export const TruthBadge = memo(function TruthBadge({ state, label, title }: TruthBadgeProps) {
  const badge = badgeForState(state);
  const s = styleFor(badge);
  const gloss = labelFor(badge);
  const style = {
    "--badge-color": `var(${s.colorVar})`,
    ...(s.fill !== "none" ? { "--badge-fill": s.fill } : {}),
  } as CSSProperties;
  return (
    <span
      className={`truth-badge ${MODIFIER[badge]}${s.glow ? " truth-badge--glow" : ""}`}
      style={style}
      title={title ?? `${gloss.en} — ${gloss.fa}`}
      data-truth={badge}
    >
      {s.glyph ? <span className="truth-badge__glyph" aria-hidden="true">{s.glyph}</span> : null}
      <span>{label ?? gloss.fa}</span>
    </span>
  );
});
