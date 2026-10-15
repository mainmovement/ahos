/**
 * Runtime bridge to the design tokens in `src/styles/tokens/tokens.css`.
 * Charts and WebGL read colours from CSS variables so the token file stays
 * the single source of truth.
 */
const FALLBACK: Record<string, string> = {
  "--color-gold-300": "#f0d27e",
  "--color-gold-400": "#e6bf5f",
  "--color-gold-500": "#d4a845",
  "--color-data-300": "#7fe6f4",
  "--color-data-400": "#45d0e6",
  "--color-fg-1": "#f6f0e2",
  "--color-fg-2": "#d3cab7",
  "--color-fg-3": "#9d9585",
  "--color-fg-4": "#6e695f",
  "--color-up": "#3ad29f",
  "--color-down": "#ff5c6c",
  "--color-warn": "#ff9f45",
  "--color-violet": "#a78bfa",
  "--color-info": "#72a7ff",
  "--color-ink-900": "#060b16",
  "--color-ink-950": "#03060e",
  "--color-ink-700": "#13223b",
};

export function readToken(name: string): string {
  if (typeof window === "undefined") return FALLBACK[name] ?? "#ffffff";
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || FALLBACK[name] || "#ffffff";
}

export interface ChartPalette {
  gold: string;
  goldSoft: string;
  goldDeep: string;
  data: string;
  dataSoft: string;
  fg1: string;
  fg2: string;
  fg3: string;
  fg4: string;
  up: string;
  down: string;
  warn: string;
  violet: string;
  info: string;
  bg: string;
  panel: string;
  fontFamily: string;
}

export function readChartPalette(): ChartPalette {
  const fontFamily = typeof window === "undefined" ? "sans-serif" : getComputedStyle(document.body).fontFamily;
  return {
    gold: readToken("--color-gold-400"),
    goldSoft: readToken("--color-gold-300"),
    goldDeep: readToken("--color-gold-500"),
    data: readToken("--color-data-400"),
    dataSoft: readToken("--color-data-300"),
    fg1: readToken("--color-fg-1"),
    fg2: readToken("--color-fg-2"),
    fg3: readToken("--color-fg-3"),
    fg4: readToken("--color-fg-4"),
    up: readToken("--color-up"),
    down: readToken("--color-down"),
    warn: readToken("--color-warn"),
    violet: readToken("--color-violet"),
    info: readToken("--color-info"),
    bg: readToken("--color-ink-950"),
    panel: readToken("--color-ink-900"),
    fontFamily,
  };
}

/** Hex → rgba string helper for canvas/WebGL consumers. */
export function alpha(hex: string, a: number): string {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const n = parseInt(full.slice(0, 6), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}
