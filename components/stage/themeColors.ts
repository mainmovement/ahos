/**
 * M-D5.2 — the 3D mirror of the M-D3 design tokens.
 *
 * CLAUDE_DASHBOARD_2050's M-D3 upgrade: "design tokens as CSS variables plus a
 * TSL uniform mirror so 2D and 3D share the same palette." This module is that
 * mirror for the stage: it converts `dashboard_tokens.ts`'s hex tables into the
 * values three.js consumes, and it holds *no* colour of its own.
 *
 * Every colour here traces to a token; the selftest asserts that mechanically by
 * re-reading the token tables, so a hex cannot drift into the scene from
 * anywhere else. That matters because the prototype review (M-D5.1) found a
 * scene whose decoration used `#ff5fae` and `#35f0d0` — pinks and cyans sitting
 * on top of CONFLICT's and VERIFIED's status hexes, used as ornament. Spec §2.3
 * forbids that outright, and this module is how the stage cannot do it again:
 * the scene's palette *is* the token table.
 *
 * Status colours are deliberately NOT mirrored here. They belong to the truth
 * badge, which renders as DOM (spec §3: "No Persian text is rendered as WebGL
 * text"), and they must never be used as decoration. A 3D object has no business
 * reading `--ahos-status-verified`.
 */
import * as THREE from "three";

import { IMPERIAL, NEON, resolveTheme, type ThemeName, type ThemeTokens } from "@/dashboard_tokens";

/**
 * A theme's tokens as three.js values. `null` travels through as `null` — a
 * token the theme's spec table does not give is absent, not invented, and the
 * stage decides what an absent token means (usually: do not draw that thing).
 */
export interface ThemeColors {
  bg: THREE.Color;
  panel: THREE.Color;
  panelEdge: THREE.Color | null;
  text: THREE.Color;
  textMuted: THREE.Color;
  gold: THREE.Color;
  goldHi: THREE.Color | null;
  crimson: THREE.Color | null;
  crimsonHi: THREE.Color | null;
  ember: THREE.Color | null;
  accent: THREE.Color | null;
  accent2: THREE.Color | null;
  /** The theme's own name, for uniforms that switch on it. */
  name: ThemeName;
}

function toColor(hex: string): THREE.Color {
  return new THREE.Color(hex);
}

/**
 * Convert one token table. Kept pure-ish (it allocates) and exported so the
 * selftest can drive both themes and assert the mapping is total.
 */
export function colorsForTokens(name: ThemeName, t: ThemeTokens): ThemeColors {
  return {
    name,
    bg: toColor(t.bg),
    panel: toColor(t.panel),
    panelEdge: t.panelEdge === null ? null : toColor(t.panelEdge),
    text: toColor(t.text),
    textMuted: toColor(t.textMuted),
    gold: toColor(t.gold),
    goldHi: t.goldHi === null ? null : toColor(t.goldHi),
    crimson: t.crimson === null ? null : toColor(t.crimson),
    crimsonHi: t.crimsonHi === null ? null : toColor(t.crimsonHi),
    ember: t.ember === null ? null : toColor(t.ember),
    accent: t.accent === null ? null : toColor(t.accent),
    accent2: t.accent2 === null ? null : toColor(t.accent2),
  };
}

export const IMPERIAL_COLORS: ThemeColors = colorsForTokens("imperial", IMPERIAL);
export const NEON_COLORS: ThemeColors = colorsForTokens("neon", NEON);

export function stageColors(theme: string | null | undefined): ThemeColors {
  return resolveTheme(theme) === "neon" ? NEON_COLORS : IMPERIAL_COLORS;
}

/**
 * A gold that is allowed to glow, and only gold. Spec §2: "Brand gold and
 * crimson are never used as status", and §2.3: status colours are never
 * decoration — so the one ornamental glow the stage may use is the brand metal,
 * and it is handed out from here rather than re-mixed at each call site.
 */
export function goldEmissive(c: ThemeColors): THREE.Color {
  return c.goldHi ?? c.gold;
}

/**
 * The stage's mood light: the warm sunset rim the Imperial concept is lit by
 * (§2.1, `ember` "Sunset rim light in 3D, boot horizon"). Neon has no ember
 * token, and rather than invent one the Neon theme is rim-lit by its own
 * `accent` — which is the token its table *does* give. An absent token becomes
 * a different real token, never a fabricated hex.
 */
export function rimLight(c: ThemeColors): THREE.Color {
  return c.ember ?? c.accent ?? c.gold;
}

/**
 * `panelEdge` as a line colour, falling back to a 15%-toward-text blend when
 * the theme gives no edge token — the same derivation `dashboard_tokens.ts`
 * documents for CSS, applied here so the 3D hairline and the 2D hairline cannot
 * disagree.
 */
export function edgeColor(c: ThemeColors): THREE.Color {
  if (c.panelEdge !== null) return c.panelEdge;
  return new THREE.Color().lerpColors(c.panel, c.text, 0.15);
}
