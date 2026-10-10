/**
 * M-D3 truth badge — the precedence that makes an honest state impossible to
 * style as success.
 *
 * AHOS's law is `UNKNOWN > fabricated`: a state the system could not measure is
 * never shown as a measurement. The two-source rule sharpens it for the display
 * layer — one source renders as UNKNOWN, disagreement renders as CONFLICT, and
 * neither is ever styled, glyphed, or sounded like a PASS. This module is that
 * contract as data.
 *
 * Precedence is fixed and one-directional:
 *
 *     REJECTED > CONFLICT > UNKNOWN > STALE > VERIFIED
 *
 * A display may only *downgrade* along that chain, never upgrade. A REJECTED
 * token and a CONFLICT seen together show CONFLICT — not REJECTED, and certainly
 * not VERIFIED. A VERIFIED token whose evidence went stale shows STALE. An
 * unrecognised enum value shows UNKNOWN, because a value the code does not
 * understand is exactly the case where pretending to know would be a fabrication.
 *
 * The colours and shapes are spec §2.3, which fixes them for *both* themes and
 * forbids using them as decoration ("Status colours are identical in both themes
 * and are never used as decoration"). That is what makes the badge the badge:
 * `--ahos-status-verified` is the turquoise of a two-source PASS and nothing else
 * in either theme reaches for it.
 *
 * This is presentation-only by law (AGENTS.md: TS creates no recommendation
 * authority). Nothing here gates a token, scores one, or decides anything about
 * a market. The Python canonical authority decides; this decides only how an
 * already-decided state is *shown*.
 */

import type { TruthStatus } from "./dashboard_truth.ts";

/** The badge states, ordered from most severe to least. */
export const BADGE_STATES = [
  "REJECTED",
  "CONFLICT",
  "UNKNOWN",
  "STALE",
  "VERIFIED",
] as const;

export type BadgeState = (typeof BADGE_STATES)[number];

/**
 * The status palette, spec §2.3. Fixed in both themes; never decoration.
 *
 * `var` is the CSS custom property every theme shares, `hex` the spec's literal
 * value, which `globals.css` must define verbatim — the selftest asserts that the
 * stylesheet and this table agree, so the two cannot drift.
 */
export interface StatusColour {
  state: BadgeState;
  /** The shared CSS variable the components read. */
  var: string;
  /** The spec's hex, asserted against `globals.css`. */
  hex: string;
}

export const STATUS_COLOURS: Record<BadgeState, StatusColour> = {
  VERIFIED: { state: "VERIFIED", var: "--ahos-status-verified", hex: "#2EC4A6" },
  UNKNOWN: { state: "UNKNOWN", var: "--ahos-status-unknown", hex: "#9AA3B2" },
  CONFLICT: { state: "CONFLICT", var: "--ahos-status-conflict", hex: "#E07BE8" },
  STALE: { state: "STALE", var: "--ahos-status-stale", hex: "#B8A27A" },
  REJECTED: { state: "REJECTED", var: "--ahos-status-rejected", hex: "#FF5A4E" },
};

/** A rank where higher means more severe, for the precedence comparison. */
const RANK: Record<BadgeState, number> = {
  REJECTED: 4,
  CONFLICT: 3,
  UNKNOWN: 2,
  STALE: 1,
  VERIFIED: 0,
};

/**
 * Map the *real* enum values of the canonical read model onto badge states.
 *
 * Every key below is a value that is actually declared somewhere in the
 * authority chain — `canonical_read_model.ts` (`CanonicalReadStatus`),
 * `architecture/identity/types.py` (`IdentityState`),
 * `architecture/security/gate.py` (`SecurityState`),
 * `architecture/decision/authority.py` (`CanonicalOutcome`), or the council's
 * verdict in `architecture/knowledge/feedback.py`. Nothing here is invented: a
 * value a reader cannot find in those sources would be a fabrication in the very
 * module that exists to prevent them, and the selftest re-reads those
 * declarations and asserts every key is among them.
 *
 * A value absent from this table maps to UNKNOWN, and that fall-through is doing
 * real work. `CanonicalOutcome`'s SKIP, HIGH_RISK, MONITOR_ONLY and NO_TRADE are
 * deliberately *not* listed: they are abstentions and risk judgements, not
 * measurements, and showing one as anything but UNKNOWN would claim a
 * verification the decision did not make. Only BUY is a positive outcome
 * (`POSITIVE_OUTCOMES = frozenset({CanonicalOutcome.BUY})`).
 */
export const STATE_TO_BADGE: Record<string, BadgeState> = {
  // CanonicalReadStatus (canonical_read_model.ts) — also the fallback the read
  // model emits for identityState/securityState when the live row is absent.
  AVAILABLE: "VERIFIED",
  UNAVAILABLE: "UNKNOWN",
  STALE: "STALE",

  // IdentityState (architecture/identity/types.py) — the two-source arbiter
  VERIFIED: "VERIFIED",
  CONFLICT: "CONFLICT",
  UNRESOLVED: "UNKNOWN",        // not enough independent sources
  INVALID: "UNKNOWN",           // the sources disagreed about validity itself
  UNSUPPORTED: "UNKNOWN",       // the chain is not one identity can resolve

  // SecurityState (architecture/security/gate.py) — the security overlay
  PASS: "VERIFIED",
  REJECT: "REJECTED",
  INCOMPLETE: "UNKNOWN",

  // CanonicalOutcome (architecture/decision/authority.py)
  BUY: "VERIFIED",
  INSUFFICIENT_EVIDENCE: "UNKNOWN",

  // Council verdict (architecture/knowledge/feedback.py) — DISAGREEMENT IS A
  // RESULT: it is shown as a conflict, never averaged away into a consensus.
  DISAGREEMENT: "CONFLICT",
};

/**
 * An unknown enum maps to UNKNOWN, never to VERIFIED.
 *
 * Anything not in the table is by definition unrecognised, and showing it as
 * anything better than UNKNOWN would claim a measurement the code did not make.
 */
export function badgeForState(state: string | null | undefined): BadgeState {
  if (typeof state !== "string") return "UNKNOWN";
  const key = state.trim().toUpperCase();
  if (!key) return "UNKNOWN";
  return STATE_TO_BADGE[key] ?? "UNKNOWN";
}

/**
 * The precedence: the most severe of the candidate states wins.
 *
 * Downgrade-only. There is no argument to this function that produces VERIFIED
 * from an input that contained CONFLICT, UNKNOWN or REJECTED — which is the
 * invariant the selftest proves.
 */
export function worstOf(...states: (BadgeState | string | null | undefined)[]): BadgeState {
  let worst: BadgeState = "VERIFIED";
  for (const s of states) {
    const b = typeof s === "string" && BADGE_STATES.includes(s as BadgeState)
      ? (s as BadgeState)
      : badgeForState(s);
    if (RANK[b] > RANK[worst]) worst = b;
  }
  return worst;
}

/**
 * A VERIFIED token whose evidence went stale is STALE, not VERIFIED.
 *
 * Reuses `dashboard_truth`'s freshness verdict rather than re-deriving age, so
 * there is one definition of stale and the badge and the freshness pill cannot
 * disagree.
 */
export function applyFreshness(
  state: string | null | undefined,
  fresh: TruthStatus,
): BadgeState {
  const base = badgeForState(state);
  if (RANK[base] >= RANK["UNKNOWN"]) return base;   // already at or below UNKNOWN
  return fresh === "STALE" || fresh === "UNKNOWN" || fresh === "VIOLATION"
    ? (fresh === "VIOLATION" ? "REJECTED" : fresh === "UNKNOWN" ? "UNKNOWN" : "STALE")
    : base;
}

/**
 * The non-colour cue for a state. Spec §2.3: "colour is never the only cue".
 * Every state has a distinct border treatment, so the badge reads in monochrome
 * and reads to a colour-blind reader.
 */
export type BorderShape = "solid" | "dashed" | "double" | "dotted" | "bar";

/**
 * The visual contract for a badge state.
 *
 * `kind` is the only thing styling may branch on. Crucially, VERIFIED is the
 * *only* state whose kind is "success" — there is no second path to a success
 * style, so UNKNOWN and CONFLICT cannot be made to look right by any caller.
 */
export interface BadgeStyle {
  state: BadgeState;
  /** The visual class: only VERIFIED is "success". */
  kind: "success" | "warning" | "danger" | "neutral";
  /** The glyph, or null for states that must not show a tick. */
  glyph: string | null;
  /** The CSS variable for the state's §2.3 colour. */
  colorVar: string;
  /** The border treatment; spec §2.3's shape column. */
  border: BorderShape;
  /** The fill pattern; spec §2.3's pattern column, as a CSS value. */
  fill: string;
  /** Whether the badge glows. Only VERIFIED glows. */
  glow: boolean;
  /** The sound id, or null for states that must not play the success sound. */
  soundId: string | null;
}

/**
 * VERIFIED, per §2.3: solid border, ✓ check glyph, solid fill at 16% — and the
 * only state that glows, because glow is the celebration of a two-source PASS and
 * an unmeasured state has nothing to celebrate.
 */
const SUCCESS: BadgeStyle = {
  state: "VERIFIED",
  kind: "success",
  glyph: "✓",
  colorVar: STATUS_COLOURS.VERIFIED.var,
  border: "solid",
  fill: `color-mix(in srgb, var(${STATUS_COLOURS.VERIFIED.var}) 16%, transparent)`,
  glow: true,
  soundId: "verified",
};

/**
 * The style for a badge state. This table is the whole contract: it is read by
 * `components/TruthBadge.tsx` and asserted by the selftest, so the test is not
 * checking a copy of the styling — it is checking the styling.
 *
 * REJECTED's glyph is ✕ rather than §2.3's octagon because no monochrome octagon
 * has reliable coverage in the bundled font stack; the octagon's stop-sign
 * meaning is carried instead by the `bar` border shape (a solid red bar), which
 * is the other cue §2.3 names for that row.
 */
export function styleFor(state: BadgeState): BadgeStyle {
  switch (state) {
    case "VERIFIED":
      return SUCCESS;
    case "STALE":
      return {
        state: "STALE",
        kind: "warning",
        glyph: "◷",
        colorVar: STATUS_COLOURS.STALE.var,
        border: "dotted",          // §2.3: dotted border
        fill: "none",              // §2.3: 50% desaturated — see the component
        glow: false,
        soundId: null,
      };
    case "UNKNOWN":
      return {
        state: "UNKNOWN",
        kind: "neutral",
        glyph: "?",
        colorVar: STATUS_COLOURS.UNKNOWN.var,
        border: "dashed",          // §2.3: dashed border
        fill: `repeating-linear-gradient(45deg, var(${STATUS_COLOURS.UNKNOWN.var}) 0 1px, transparent 1px 6px)`,  // §2.3: 45° hatch
        glow: false,
        soundId: null,
      };
    case "CONFLICT":
      return {
        state: "CONFLICT",
        kind: "danger",
        glyph: "⚠",
        colorVar: STATUS_COLOURS.CONFLICT.var,
        border: "double",          // §2.3: double border
        fill: "none",              // §2.3: zig-zag edge — the border carries it
        glow: false,
        soundId: "conflict",
      };
    case "REJECTED":
      return {
        state: "REJECTED",
        kind: "danger",
        glyph: "✕",
        colorVar: STATUS_COLOURS.REJECTED.var,
        border: "bar",             // §2.3: solid red bar
        fill: `color-mix(in srgb, var(${STATUS_COLOURS.REJECTED.var}) 16%, transparent)`,
        glow: false,
        soundId: "rejected",
      };
  }
}

/**
 * Convenience: state straight to its style, skipping the explicit badge step.
 */
export function styleForState(state: string | null | undefined): BadgeStyle {
  return styleFor(badgeForState(state));
}

/**
 * The one-line label for a state, English and Persian, for the badge's title.
 * The Persian glosses are the spec §2.3 labels in parentheses; a state without
 * one falls back to the English label rather than to an empty string, because a
 * tooltip that says nothing is worse than one that says the English word.
 */
export function labelFor(state: BadgeState): { en: string; fa: string } {
  const labels: Record<BadgeState, { en: string; fa: string }> = {
    VERIFIED: { en: "Verified by two independent sources", fa: "تأییدشده" },
    STALE: { en: "Evidence is stale", fa: "کهنه" },
    UNKNOWN: { en: "Unknown — not enough evidence", fa: "نامعلوم" },
    CONFLICT: { en: "Sources conflict", fa: "تعارض" },
    REJECTED: { en: "Rejected", fa: "رد" },
  };
  return labels[state];
}

/**
 * The two-source law as a display predicate: is this state one the display may
 * never upgrade past UNKNOWN — i.e. one that can only ever be shown as less than
 * a measurement?
 *
 * CONFLICT and REJECTED are true results (the council: "DISAGREEMENT IS A
 * RESULT"), so they may alert; UNKNOWN is the absence of a measurement and this
 * predicate is the reason it may not so much as sound.
 */
export function isUnmeasured(state: BadgeState): boolean {
  return RANK[state] >= RANK["UNKNOWN"];
}
