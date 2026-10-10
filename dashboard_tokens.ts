/**
 * M-D3 design tokens — the two owner-approved themes, as the spec's exact hexes.
 *
 * The source of truth is `reports/grok/dashboard/DASHBOARD_DESIGN_SPEC.md` §2.1
 * (Imperial) and §2.2 (Neon). Every value below is that table's hex, verbatim.
 * Where the spec gives a theme no value for a token, the token is `null` and the
 * CSS variable is *derived* from the tokens the spec does give — never invented,
 * and every derivation is marked `DERIVED` where it is produced, so a reader can
 * check each value against the spec and can tell the given from the derived.
 *
 * Tokens are data, not styling logic. Components read them through the CSS
 * variables in `globals.css` (`[data-theme="..."]`), which is the only place the
 * theme actually switches. This module is the single source for those variables'
 * values, so the selftests and the CSS stay in lockstep by construction.
 *
 * Status colours are NOT here: §2.3 makes them identical in both themes and
 * "never used as decoration", so they live in `dashboard_truth_badge.ts` beside
 * the badge contract that consumes them.
 */

/** The owner-approved default theme (spec §2.1, refs 1+4). */
export const DEFAULT_THEME = "imperial" as const;

export type ThemeName = "imperial" | "neon";

/**
 * The shared token system (spec §2: "Two themes share one token system").
 *
 * A field is `null` when that theme's table in the spec has no row for it. `gold`
 * is the one accent the spec gives for both, and it gives the same hex both times.
 */
export interface ThemeTokens {
  /** Scene clear colour / page background. */
  bg: string;
  /** Lacquer panel surface. */
  panel: string;
  /** 1px hairline between surfaces; null when the spec gives no edge row. */
  panelEdge: string | null;
  /** Body text. */
  text: string;
  /** Secondary text — labels, captions. */
  textMuted: string;
  /** Emblem / ornament / focus ring; given for both themes, same hex. */
  gold: string;
  /** Specular highlight, hover; Imperial only. */
  goldHi: string | null;
  /** Velvet fill, banner surfaces — never text; Imperial only. */
  crimson: string | null;
  /** Large display text ≥24px and selected-tab underline; Imperial only. */
  crimsonHi: string | null;
  /** Sunset rim light in 3D, boot horizon — not a status; Imperial only. */
  ember: string | null;
  /** Neon signature accent (cyan). */
  accent: string | null;
  /** Neon second accent. */
  accent2: string | null;
}

/**
 * Imperial: "شاهنشاهی" — black, crimson and gold. The owner's default.
 * Every value is spec §2.1.
 */
export const IMPERIAL: ThemeTokens = {
  bg: "#0B0709",
  panel: "#160E12",
  panelEdge: "#3A2A1C",
  text: "#EFE4CC",
  textMuted: "#A99A80",
  gold: "#D4AF5A",
  goldHi: "#F1D58E",
  crimson: "#9E1C26",
  crimsonHi: "#D2343E",
  ember: "#E8834A",
  accent: null,
  accent2: null,
};

/**
 * Neon: "نئون" — cyan on near-black. Gold is carried over at the spec's shared
 * hex. The spec gives Neon no `panel-edge`, `gold-hi`, `crimson` or `ember`, so
 * those stay null rather than being approximated.
 */
export const NEON: ThemeTokens = {
  bg: "#040714",
  panel: "#0A1330",
  panelEdge: null,
  text: "#E6F6FF",
  textMuted: "#8FA6C8",
  gold: "#D4AF5A",
  goldHi: null,
  crimson: null,
  crimsonHi: null,
  ember: null,
  accent: "#3FD0FF",
  accent2: "#4C82FF",
};

export const THEMES: Record<ThemeName, ThemeTokens> = {
  imperial: IMPERIAL,
  neon: NEON,
};

/**
 * Every hex the spec gives, so a selftest can assert them against §2.1/§2.2 and
 * notice if a spec edit is not carried into the token table.
 */
export const TOKEN_HEXES: ReadonlySet<string> = new Set<string>([
  ...Object.values(IMPERIAL).filter((v): v is string => typeof v === "string"),
  ...Object.values(NEON).filter((v): v is string => typeof v === "string"),
]);

/**
 * DERIVED — a hairline colour for a theme the spec gives no edge row for.
 *
 * The rule is stated, not tuned: the edge is the panel blended 15% toward the
 * theme's own body text, which keeps the hairline in the panel's hue family and
 * keeps it below the text's contrast class. It is only ever used where
 * `panelEdge` is null; a spec-given edge always wins.
 */
export function deriveEdge(panel: string, text: string): string {
  return blend(panel, text, 0.15);
}

/** Blend `from` toward `to` by `amount` (0 = from, 1 = to), in hex. */
export function blend(from: string, to: string, amount: number): string {
  const a = parseHex(from);
  const b = parseHex(to);
  const mix = a.map((av, i) => Math.round(av + (b[i] - av) * amount));
  return ("#" + mix.map((v) => v.toString(16).padStart(2, "0")).join("")).toUpperCase();
}

function parseHex(hex: string): [number, number, number] {
  const h = hex.trim().replace(/^#/, "");
  const full = h.length === 3
    ? h.split("").map((c) => c + c).join("")
    : h;
  if (full.length !== 6) {
    throw new Error(`blend: not a hex colour: ${hex}`);
  }
  const n = parseInt(full, 16);
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff];
}

/**
 * CSS custom properties, one per token, for a theme's `[data-theme]` block.
 *
 * Derived values are emitted with their derivation inline in the value's comment
 * at the call site (globals.css), not hidden here.
 */
export function themeCssVariables(theme: ThemeName): Record<string, string> {
  const t = THEMES[theme];
  const vars: Record<string, string> = {
    "--ahos-bg": t.bg,
    "--ahos-panel": t.panel,
    "--ahos-text": t.text,
    "--ahos-text-muted": t.textMuted,
    "--ahos-gold": t.gold,
  };
  // Tokens the spec gives this theme are emitted verbatim.
  if (t.panelEdge) vars["--ahos-border"] = t.panelEdge;
  if (t.goldHi) vars["--ahos-gold-hi"] = t.goldHi;
  if (t.crimson) vars["--ahos-crimson"] = t.crimson;
  if (t.crimsonHi) vars["--ahos-crimson-hi"] = t.crimsonHi;
  if (t.ember) vars["--ahos-ember"] = t.ember;
  if (t.accent) vars["--ahos-accent"] = t.accent;
  if (t.accent2) vars["--ahos-accent-2"] = t.accent2;
  // DERIVED where the spec is silent: Neon has no panel-edge row in §2.2.
  if (!t.panelEdge) vars["--ahos-border"] = deriveEdge(t.panel, t.text);
  return vars;
}

/** Resolve a theme name, falling back to the owner-approved default. */
export function resolveTheme(name: string | null | undefined): ThemeName {
  return name === "neon" ? "neon" : "imperial";
}
