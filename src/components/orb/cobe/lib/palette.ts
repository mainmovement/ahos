/**
 * The single colour ramp: shared by the COBE canvas, the SVG fallback and the CSS custom properties
 * in `globals.css` (which mirror these values). Colours only — no data, no state.
 */

export type COBEColour = [number, number, number];

export type GlobePalette = {
  /** Warm dark gold-grey dot field. */
  baseColor: COBEColour;
  /** Gold markers drawn by COBE for LIVE data. */
  markerColor: COBEColour;
  /** Soft gold halo; the dim variant is the resting state, the alert variant lifts on attention. */
  glowColor: COBEColour;
  glowColorAlert: COBEColour;
  /** CSS mirrors. */
  css: {
    gold: string;
    goldBright: string;
    goldSoft: string;
    amberDim: string;
    steel: string;
    grey: string;
    demoBlue: string;
  };
};

export const GLOBE_PALETTE: GlobePalette = {
  baseColor: [0.164, 0.141, 0.094],
  markerColor: [0.96, 0.824, 0.478],
  glowColor: [0.38, 0.29, 0.1],
  glowColorAlert: [0.52, 0.4, 0.13],
  css: {
    gold: "#d4af37",
    goldBright: "#f5d27a",
    goldSoft: "#d9b977",
    amberDim: "#b98a2e",
    steel: "#8a93a0",
    grey: "#7c8390",
    demoBlue: "#7f93ad",
  },
};
