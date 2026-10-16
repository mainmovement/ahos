/**
 * AHOS globe data contract.
 *
 * TRUTH RULES (do not weaken):
 *  - Every datum carries exactly one freshness state: LIVE | STALE | UNKNOWN | DEMO.
 *  - A missing value is never replaced by a plausible-looking default. `null` renders as UNKNOWN.
 *  - `changePct` is optional and nullable: when it is anything other than a finite number the UI
 *    must not print a percentage at all.
 *  - `asOf` is an ISO-8601 timestamp (or null). The UI converts it to a Persian relative time;
 *    it never invents a time.
 */

/** Freshness of a single datum. Never inferred — always stated by the data source. */
export type Freshness = "LIVE" | "STALE" | "UNKNOWN" | "DEMO";

/** A market node rendered on the globe. */
export type MarketNode = {
  id: string;
  nameFa: string;
  nameEn: string;
  lat: number;
  lng: number;
  freshness: Freshness;
  /** ISO-8601 timestamp of the datum, or null when the source did not report one. */
  asOf: string | null;
  /** Percent change, or null/undefined when unknown. Never defaulted to 0. */
  changePct?: number | null;
  needsAttention?: boolean;
};

/** An inter-market signal. `pending` signals have an unknown outcome — that is a real state. */
export type Signal = {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  outcome: "absorbed" | "dissipated" | "pending";
  reasonFa?: string;
  at: string;
};

/** The absorption gate. Both counts are exact as reported; the UI never rounds them into fiction. */
export type Gate = {
  absorbed: number;
  dissipated: number;
  /** Optional operator-set strictness (0..1). When absent it is derived from the counts. */
  strictness?: number;
};

/** Heartbeat of the autonomous loop. `stale: true` freezes glow and pulses. */
export type Health = {
  bpm: number;
  jitterMs: number;
  stale: boolean;
};

/** One of the AHOS departments. Twelve departments = twelve ring ticks. */
export type Department = {
  id: string;
  nameFa: string;
  freshness: Freshness;
  needsAttention: boolean;
};

/** Globe quality preset → map sample count + canvas size. */
export type GlobeQuality = "low" | "medium" | "high";

/** Rendering mode. `map` is an equirectangular dot map built from the same land mask. */
export type GlobeMode = "globe" | "map";

/** UI language. Persian is the default and drives RTL layout. */
export type Lang = "fa" | "en";

export type AhosGlobeProps = {
  markets: MarketNode[];
  signals: Signal[];
  gate: Gate;
  health: Health;
  departments: Department[];
  /** Calm mode (default true): slow rotation, low glow, only what needs attention brightens. */
  calm?: boolean;
  /** Quality preset (default "medium"). */
  quality?: GlobeQuality;
  /** Rendering mode (default "globe"). */
  mode?: GlobeMode;
  /** UI language (default "fa"). */
  lang?: Lang;
  /** Called with the node id when a marker is activated (click / Enter / Space). */
  onSelect?: (id: string) => void;
  /** Extra class for the outer frame. */
  className?: string;
  /**
   * Reference clock in ms for Persian relative times ("۳ دقیقه پیش").
   * Omit in production: the component then uses the browser clock, refreshed every 30 s. Passing a
   * fixed value makes server rendering, tests and screenshots deterministic.
   */
  now?: number;
};

/** One row of the always-available text table (screen readers, low-power devices). */
export type GlobeTableRow = {
  id: string;
  name: string;
  freshness: Freshness;
  asOf: string | null;
  changePct: number | null;
  needsAttention: boolean;
};
