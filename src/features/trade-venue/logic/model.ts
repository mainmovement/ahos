/**
 * AHOS · Trade Venue — domain contract (typed adapter surface)
 * ============================================================================
 * These types are the *only* interface between the page and its data. Today the
 * values come from `src/mock/trade_venue`; later the same shape will be produced
 * by the AHOS backend (`/api/command` + `app/api/paper`). See README_MERGE.md
 * for the field-by-field mapping and the adapter swap procedure.
 *
 * Design rules encoded in the types themselves:
 *  - every measurable value is `number | null`  → `null` means UNKNOWN, and the
 *    UI must print «—» / «ناموجود»; a fake `0` is never allowed for unknown.
 *  - every row carries a `status` from the truth enum (paper rows may only use
 *    the statuses that make sense for a paper ledger).
 *  - `updatedAt: string | null` — `null` ⇒ the row is UNKNOWN, never STALE.
 *  - nothing in this contract can express "send an order": there is no order /
 *    approval / sizing type at all, by construction.
 */

/* -------------------------------------------------------------- statuses -- */

/** Truth statuses — the canonical AHOS enum. Nothing outside this list exists. */
export const TRUTH_STATUSES = [
  "LIVE",
  "STALE",
  "UNKNOWN",
  "DEMO",
  "CONFLICT",
  "REJECTED",
] as const;
export type TruthStatus = (typeof TRUTH_STATUSES)[number];

/** Additional per-component states a surface can be in (never truth claims). */
export const COMPONENT_STATES = [
  "UNAVAILABLE",
  "PARTIAL",
  "PLANNED",
  "MISSING",
  "ERROR",
  "EMPTY",
  "LOADING",
  "HISTORICAL",
  "SIMULATED",
] as const;
export type ComponentState = (typeof COMPONENT_STATES)[number];

/** Any status a chip/state component can render. */
export type ChipStatus = TruthStatus | ComponentState;

/* ----------------------------------------------------------------- worlds -- */

/** The two worlds. Both are paper-only; the split is bookkeeping, not money. */
export const WORLDS = ["REAL_PAPER", "SIMULATION"] as const;
export type World = (typeof WORLDS)[number];

export const WORLD_LABEL_FA: Record<World, string> = {
  REAL_PAPER: "کاغذی واقعی",
  SIMULATION: "شبیه‌سازی",
};

export const WORLD_LABEL_EN: Record<World, string> = {
  REAL_PAPER: "REAL-PAPER",
  SIMULATION: "SIMULATION",
};

/* --------------------------------------------------------- execution mode -- */

/**
 * `PAPER_ONLY` is the only mode this page is allowed to operate in. Anything
 * else (a future real desk, a shadow book, an unknown backend answer) must
 * light the VIOLATION bar — see `logic/truth.ts · detectViolation`.
 */
export type ExecutionMode = "PAPER_ONLY" | "SIMULATION" | "SHADOW" | "LIVE" | "UNKNOWN";

/* ------------------------------------------------------------------ rows -- */

export type PositionSide = "LONG" | "SHORT";

/** Closed-out and still-open paper results, as recorded by the paper engine. */
export interface PaperOutcome {
  id: string;
  symbol: string;
  labelFa: string;
  /** Realized result of the sealed paper run. `null` ⇒ UNKNOWN (prints «—»). */
  realized: number | null;
  /** Realized result is measured in this unit. `null` when the unit is unknown. */
  currency: string | null;
  closedTrades: number | null;
  openedTrades: number | null;
  /** Truth status of the record itself (HISTORICAL = sealed, immutable ledger). */
  status: ChipStatus;
  world: World;
  sourceId: string;
  /** ISO-8601 UTC. `null` ⇒ UNKNOWN (the row may not claim STALE). */
  updatedAt: string | null;
  evidenceId: string | null;
}

/** An open paper position (never a real one — see `executionMode`). */
export interface PaperPosition {
  id: string;
  symbol: string;
  symbolFa: string;
  side: PositionSide;
  /** `null` ⇒ UNKNOWN. */
  qty: number | null;
  qtyUnit: string | null;
  /** `null` ⇒ UNKNOWN. */
  entry: number | null;
  entryKind: "OBSERVED" | "SIMULATED" | "UNKNOWN";
  /** `null` ⇒ UNKNOWN; `markStatus` says why. */
  mark: number | null;
  markStatus: ChipStatus;
  /** Unrealized paper result. Neutral number, never coloured good/bad. */
  unrealized: number | null;
  currency: string | null;
  /** `false` ⇒ the row renders «غیرمجاز» and is excluded from every total. */
  paperAllowed: boolean;
  /** Venue/broker the paper engine is mirroring. */
  venue: string;
  status: ChipStatus;
  world: World;
  sourceId: string;
  updatedAt: string | null;
  evidenceId: string | null;
}

/** One line of the fill / activity log. Read-only history, never an order. */
export type FillAction =
  | "PAPER_OPEN"
  | "PAPER_CLOSE"
  | "PAPER_PARTIAL_CLOSE"
  | "PAPER_ADJUST"
  | "PAPER_MARK"
  | "SYSTEM_NOTE";

export interface FillLogEntry {
  id: string;
  /** Pre-formatted Tehran wall-clock (deterministic — no client clock involved). */
  timeTehran: string;
  /** ISO-8601 UTC. `null` ⇒ UNKNOWN. */
  at: string | null;
  symbol: string;
  action: FillAction;
  qty: number | null;
  price: number | null;
  notional: number | null;
  currency: string | null;
  sourceId: string;
  status: ChipStatus;
  world: World;
  evidenceId: string | null;
  noteFa: string | null;
}

export interface WatchlistItem {
  symbol: string;
  symbolFa: string;
  /** `null` ⇒ UNKNOWN ⇒ «—». */
  price: number | null;
  /** `null` ⇒ UNKNOWN ⇒ «—». Never a rounded-to-zero fake. */
  changePct: number | null;
  status: ChipStatus;
  sourceId: string;
  updatedAt: string | null;
  paperAllowed: boolean;
}

/** The candidate book: what the paper engine is *allowed* to mirror. */
export interface Opportunity {
  symbol: string;
  symbolFa: string;
  /** Not a control — a permission flag reported by the backend. */
  paperAllowed: boolean;
  canonicalStatus: ChipStatus;
  world: World;
  sourceId: string;
  updatedAt: string | null;
  evidenceId: string | null;
}

/**
 * Per-market command centre. Grey / «متصل نیست» unless a feed really exists.
 * `metrics` is intentionally absent: an unconnected market has *no* numbers to
 * invent, so the type refuses to carry any.
 */
export interface MarketCenter {
  id: string;
  code: string;
  nameFa: string;
  state: ChipStatus;
  feeds: readonly string[];
  lastReadAt: string | null;
  rows: number | null;
  noteFa: string | null;
}

/* ---------------------------------------------------------------- bundle -- */

export interface TradeVenueFreshness {
  /** ISO-8601 UTC of the read that produced the bundle. `null` ⇒ UNKNOWN. */
  readAt: string | null;
  /** Age of the oldest row still shown, in seconds. `null` ⇒ UNKNOWN. */
  oldestRowAgeSec: number | null;
  /** Age of the newest row, in seconds. `null` ⇒ UNKNOWN. */
  newestRowAgeSec: number | null;
}

export interface TradeVenueTelemetry {
  sourceId: string;
  /** ISO-8601 UTC. `null` ⇒ UNKNOWN ⇒ prints «نامشخص». */
  lastReadAt: string | null;
  rows: number;
  /** How many rows the adapter withheld (partial reads / permissions). */
  withheldRows: number | null;
  demoRows: number;
  simulationRows: number;
  unknownRows: number;
}

/**
 * The single typed adapter surface. `src/mock/trade_venue` produces it today;
 * the real backend will produce the identical shape (README_MERGE.md § mapping).
 */
export interface TradeVenueSnapshot {
  /** `PAPER_ONLY` in every legal state. Anything else triggers VIOLATION. */
  executionMode: ExecutionMode;
  /** Must be `false`. `true` triggers VIOLATION (red full-width bar). */
  realTrading: boolean;
  /** Global permission flag from the backend. */
  paperAllowed: boolean;
  asOf: string | null;
  /** True when the bundle is a fixture (always true for this build). */
  isDemo: boolean;
  /** True when DEMO was forced by `?demo=1` or the env flag. */
  demoForced: boolean;
  /** Canonical world of this bundle. */
  world: World;
  freshness: TradeVenueFreshness;
  telemetry: TradeVenueTelemetry;
  paper: readonly PaperPosition[];
  fillLog: readonly FillLogEntry[];
  outcomes: readonly PaperOutcome[];
  watchlist: readonly WatchlistItem[];
  opportunities: readonly Opportunity[];
  marketCenters: readonly MarketCenter[];
}

/* ---------------------------------------------------------------- views -- */

/** Component-state variants the page can be asked to render (gallery / tests). */
export const VIEW_STATES = [
  "DEFAULT",
  "LOADING",
  "EMPTY",
  "ERROR",
  "UNKNOWN",
  "UNAVAILABLE",
  "STALE",
  "PARTIAL",
  "HISTORICAL",
] as const;
export type ViewState = (typeof VIEW_STATES)[number];

export type QualityTier = "T0" | "T1" | "T2";

/** Query-derived render request (parsed server-side, never trusted blindly). */
export interface VenueQuery {
  /** `?demo=1` forces DEMO everywhere. */
  forceDemo: boolean;
  /** `?state=…` */
  state: ViewState;
  /** `?tier=…` */
  tier: QualityTier;
  /** Initial world; the tab control may switch it afterwards. */
  world: World;
  /** `?violation=1` forces a non-paper report — used by the state gallery. */
  forceViolation: boolean;
  /** `?all=1` renders the whole state gallery instead of one venue screen. */
  gallery: boolean;
  /** `?world=simulation` convenience alias for `world=SIMULATION`. */
  resolvedFrom: string;
}
