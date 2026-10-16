/**
 * Presentation rules for the AHOS globe. Every rule here is pure and unit-tested.
 *
 * Truth rules enforced in this module:
 *  - Freshness decides the *shape* as well as the colour, so meaning never relies on colour alone
 *    (LIVE = filled dot, STALE = hollow ring, UNKNOWN = dashed ring, DEMO = diamond).
 *  - A missing number stays missing: `gateMath` reports `known: false` instead of 0% when the gate
 *    has nothing to divide, and `breath` freezes instead of faking a healthy pulse.
 */

import type { Department, Freshness, Gate, Health, MarketNode, Signal } from "../types/globe";

/** Hard caps that keep the dial calm. */
export const HIGHLIGHT_LIMIT = 7;
export const MAX_VISIBLE_ARCS = 12;

export type MarkerShape = "disc" | "ring" | "dashed" | "diamond";

export type MarkerChrome = {
  shape: MarkerShape;
  /** Dot/ring radius in CSS px at the base size. */
  radius: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  strokeDasharray: string | null;
  /** Slow pulse — only LIVE data (and the Tehran anchor) is allowed to pulse. */
  pulse: boolean;
  /** 0..1 base opacity for the recessed state. */
  opacity: number;
};

const GOLD = "#f5d27a";
const GOLD_FILL = "#d4af37";
const AMBER_DIM = "#b98a2e";
const GREY = "#7c8390";
const STEEL = "#8a93a0";
const BLUE_GREY = "#7f93ad";

/**
 * Marker chrome per freshness state. Shapes differ per state on purpose: the dial stays readable
 * for a colour-blind operator and in a greyscale screenshot.
 */
export function freshnessChrome(freshness: Freshness): MarkerChrome {
  switch (freshness) {
    case "LIVE":
      return {
        shape: "disc",
        radius: 4.6,
        fill: GOLD,
        stroke: GOLD_FILL,
        strokeWidth: 1,
        strokeDasharray: null,
        pulse: true,
        opacity: 1,
      };
    case "STALE":
      return {
        shape: "ring",
        radius: 4.4,
        fill: "none",
        stroke: AMBER_DIM,
        strokeWidth: 1.25,
        strokeDasharray: null,
        pulse: false,
        opacity: 0.72,
      };
    case "UNKNOWN":
      return {
        shape: "dashed",
        radius: 4.4,
        fill: "none",
        stroke: GREY,
        strokeWidth: 1.1,
        strokeDasharray: "2 3",
        pulse: false,
        opacity: 0.62,
      };
    case "DEMO":
      return {
        shape: "diamond",
        radius: 4.2,
        fill: BLUE_GREY,
        stroke: "#a9b6c7",
        strokeWidth: 0.9,
        strokeDasharray: null,
        pulse: false,
        opacity: 0.92,
      };
  }
}

export type AttentionChrome = {
  /** Outer halo radius multiplier applied to the marker chrome above. */
  scale: number;
  haloRadius: number;
  haloStroke: string;
  haloOpacity: number;
};

/** Attention is orthogonal to freshness: it adds a halo and enlarges the marker. */
export function attentionChrome(needsAttention: boolean | undefined): AttentionChrome {
  if (!needsAttention) return { scale: 1, haloRadius: 0, haloStroke: "transparent", haloOpacity: 0 };
  return { scale: 1.24, haloRadius: 9.5, haloStroke: GOLD_FILL, haloOpacity: 0.55 };
}

/* ------------------------------------------------------------------ signals */

export type SignalOutcome = Signal["outcome"];

export type SignalChrome = {
  /** Base colour of the arc. */
  stroke: string;
  width: number;
  /** Fraction of the arc that is actually drawn (dissipated arcs stop mid-flight). */
  drawFraction: number;
  /** Opacity at the source end of the drawn arc. */
  startOpacity: number;
  /** Opacity where the drawn arc stops. Dissipated arcs therefore fade out mid-way. */
  endOpacity: number;
  dasharray: string | null;
  /** True for absorbed signals: a gold flash is drawn where the arc meets the gate. */
  flashAtGate: boolean;
};

export function signalChrome(outcome: SignalOutcome): SignalChrome {
  switch (outcome) {
    case "absorbed":
      return {
        stroke: GOLD,
        width: 1.4,
        drawFraction: 1,
        startOpacity: 0.62,
        endOpacity: 0.28,
        dasharray: null,
        flashAtGate: true,
      };
    case "dissipated":
      return {
        stroke: STEEL,
        width: 1.1,
        drawFraction: 0.62,
        startOpacity: 0.4,
        endOpacity: 0.12,
        dasharray: null,
        flashAtGate: false,
      };
    case "pending":
      return {
        stroke: "#9fb0c4",
        width: 1.1,
        drawFraction: 1,
        startOpacity: 0.4,
        endOpacity: 0.4,
        dasharray: "5 5",
        flashAtGate: false,
      };
  }
}

/* -------------------------------------------------------------------- gate */

export type GateMath = {
  absorbed: number;
  dissipated: number;
  total: number;
  /** Absorbed share 0..1, or null when there is nothing to divide. */
  absorbedShare: number | null;
  dissipatedShare: number | null;
  /** Strictness 0..1, or null when unknown. */
  strictness: number | null;
  /** True when `strictness` came from the props rather than being derived from the counts. */
  strictnessFromData: boolean;
  /** False when the gate has no counts at all: the UI must then say UNKNOWN, never 0%. */
  known: boolean;
};

function safeCount(value: number): number {
  return Number.isFinite(value) && value > 0 ? value : 0;
}

/**
 * Gate arithmetic. `strictness` is defined as the share of evaluated signals the gate rejected
 * (dissipated / total) — a stricter gate dissipates more. When the operator supplies strictness it
 * is used verbatim (clamped to 0..1); otherwise it is derived, and `strictnessFromData` stays false
 * so the UI can avoid presenting a derived number as a measured one.
 */
export function gateMath(gate: Gate): GateMath {
  const absorbed = safeCount(gate.absorbed);
  const dissipated = safeCount(gate.dissipated);
  const total = absorbed + dissipated;
  const known = total > 0;
  const supplied =
    typeof gate.strictness === "number" && Number.isFinite(gate.strictness)
      ? Math.max(0, Math.min(1, gate.strictness))
      : null;
  return {
    absorbed,
    dissipated,
    total,
    absorbedShare: known ? absorbed / total : null,
    dissipatedShare: known ? dissipated / total : null,
    strictness: supplied !== null ? supplied : known ? dissipated / total : null,
    strictnessFromData: supplied !== null,
    known,
  };
}

/** Percent label for the absorbed share, or `null` when the gate has no counts (render UNKNOWN). */
export function gatePercentText(math: GateMath, format: (value: number) => string): string | null {
  if (math.absorbedShare === null) return null;
  return format(math.absorbedShare * 100);
}

/* --------------------------------------------------------------- heartbeat */

export type Breath = { scale: number; phase: number; frozen: boolean };

/**
 * Golden core glow: scale 1.00 → 1.08, eased, one cycle per breath. A healthy loop at 60 bpm
 * breathes every 5 s (`300 / bpm`, clamped to 2.5–8 s); `jitterMs` wobbles each cycle's length;
 * `stale` (or a non-positive bpm) freezes the glow at rest and the UI shows a flat line instead.
 */
export function breath(tMs: number, health: Health): Breath {
  const bpm = Number.isFinite(health.bpm) && health.bpm > 0 ? health.bpm : 0;
  if (health.stale || bpm === 0) return { scale: 1, phase: 0, frozen: true };
  const period = Math.min(8, Math.max(2.5, 300 / bpm)) * 1000;
  const jitter = Number.isFinite(health.jitterMs) ? Math.min(2000, Math.max(0, health.jitterMs)) : 0;
  // Deterministic per-cycle wobble: cycle index → stable pseudo-random offset in [-1, 1].
  const cycle = Math.floor(tMs / period);
  const wobble = jitter === 0 ? 0 : (Math.sin(cycle * 12.9898) * 43758.5453) % 1;
  const local = (tMs - cycle * period) / period + (wobble * jitter) / period;
  const clamped = Math.min(1, Math.max(0, local));
  const eased = 0.5 - 0.5 * Math.cos(clamped * Math.PI * 2);
  return { scale: 1 + 0.08 * eased, phase: clamped, frozen: false };
}

/* -------------------------------------------------------- marker selection */

export type MarkerSelection = {
  /** Ids that render bright and (for LIVE) animated. Never more than HIGHLIGHT_LIMIT. */
  highlighted: readonly string[];
  /** Ids that render recessed (only when calm mode is off, where every node stays visible). */
  recessed: readonly string[];
  /** Ids collapsed into the "+N" chip (calm mode only). */
  hidden: readonly string[];
};

function relevance(node: MarketNode): number {
  const freshness: Record<Freshness, number> = { LIVE: 3, DEMO: 2, STALE: 1.5, UNKNOWN: 1 };
  const attention = node.needsAttention ? 1000 : 0;
  const magnitude = typeof node.changePct === "number" && Number.isFinite(node.changePct) ? Math.abs(node.changePct) : 0;
  return attention + freshness[node.freshness] * 10 + Math.min(magnitude, 9);
}

function byRelevance(a: MarketNode, b: MarketNode): number {
  const delta = relevance(b) - relevance(a);
  return delta !== 0 ? delta : a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

/**
 * Calm mode (default) surfaces only what needs attention — at most HIGHLIGHT_LIMIT markets — and
 * collapses the rest into the "+N" chip. Outside calm mode every node stays visible but at most
 * HIGHLIGHT_LIMIT of them are allowed to be bright, so no state can ever produce a noisy dial.
 */
export function selectMarkers(markets: readonly MarketNode[], calm: boolean): MarkerSelection {
  const ordered = [...markets].sort(byRelevance);
  const candidates = calm ? ordered.filter((m) => m.needsAttention) : ordered;
  const highlighted = candidates.slice(0, HIGHLIGHT_LIMIT).map((m) => m.id);
  const parked = ordered.filter((m) => !highlighted.includes(m.id)).map((m) => m.id);
  return {
    highlighted,
    recessed: calm ? [] : parked,
    hidden: calm ? parked : [],
  };
}

/** Signals worth drawing, ordered by relevance and capped at MAX_VISIBLE_ARCS. */
export function selectSignals(
  signals: readonly Signal[],
  markets: readonly MarketNode[],
  limit = MAX_VISIBLE_ARCS,
): Signal[] {
  const attention = new Set(markets.filter((m) => m.needsAttention).map((m) => m.id));
  const outcomeWeight: Record<SignalOutcome, number> = { absorbed: 3, pending: 2, dissipated: 1 };
  const weight = (signal: Signal) =>
    (attention.has(signal.fromNodeId) || attention.has(signal.toNodeId) ? 100 : 0) +
    outcomeWeight[signal.outcome] * 10;
  return [...signals]
    .sort((a, b) => {
      const delta = weight(b) - weight(a);
      if (delta !== 0) return delta;
      const time = (b.at ?? "").localeCompare(a.at ?? "");
      if (time !== 0) return time;
      return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
    })
    .slice(0, Math.max(0, limit));
}

/** True when any department needs attention — used for the subtlest "attention" cues. */
export function departmentsNeedingAttention(departments: readonly Department[]): Department[] {
  return departments.filter((d) => d.needsAttention);
}

/** Rank used to sort the text table so the most urgent market is always first. */
export function tableOrder(markets: readonly MarketNode[]): MarketNode[] {
  return [...markets].sort((a, b) => {
    if (!!b.needsAttention !== !!a.needsAttention) return b.needsAttention ? 1 : -1;
    return byRelevance(a, b);
  });
}
