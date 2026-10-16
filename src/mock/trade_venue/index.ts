/**
 * AHOS · Trade Venue — mock adapter (the ONLY source of numbers on this page)
 * ============================================================================
 * Production shape: the backend will expose `/api/command` (aggregate read) plus
 * `app/api/paper` (the paper ledger). `getVenueBundle()` below is the seam: swap
 * its body for two `fetch` calls returning the same `TradeVenueSnapshot` shape
 * and the whole page keeps working — see README_MERGE.md § "Mock → API".
 *
 * Nothing here performs I/O. `NEXT_PUBLIC_AHOS_TRADE_VENUE_FORCE_DEMO=1` forces
 * the DEMO ribbon on every surface, which is how a staging deployment can make
 * "this is not live data" impossible to miss.
 */

import type {
  ChipStatus,
  ExecutionMode,
  PaperOutcome,
  PaperPosition,
  TradeVenueSnapshot,
  VenueQuery,
  ViewState,
  WatchlistItem,
  World,
} from "@/src/features/trade-venue/logic/model";
import { applyDemoRibbon } from "@/src/features/trade-venue/logic/truth";
import {
  MOCK_NOW,
  MOCK_TELEMETRY,
  REAL_PAPER_FILL_LOG,
  REAL_PAPER_MARKET_CENTERS,
  REAL_PAPER_OPPORTUNITIES,
  REAL_PAPER_OUTCOMES,
  REAL_PAPER_POSITIONS,
  REAL_PAPER_WATCHLIST,
  SIMULATION_FILL_LOG,
  SIMULATION_OPPORTUNITIES,
  SIMULATION_OUTCOMES,
  SIMULATION_POSITIONS,
  SIMULATION_WATCHLIST,
} from "./fixtures";

export { MOCK_NOW } from "./fixtures";
export { MOCK_SOURCES, sourceById, sourceIds } from "./sources";

/** The two worlds, both paper-only. */
export interface VenueBundle {
  realPaper: TradeVenueSnapshot;
  simulation: TradeVenueSnapshot;
  /** Provenance notes shown in the footer / telemetry strip. */
  provenance: {
    adapter: string;
    isFixture: true;
    forcedBy: "query" | "env" | "none";
  };
}

const FALLBACK_ISO = MOCK_NOW;

function isoShift(baseISO: string, minutes: number): string {
  return new Date(new Date(baseISO).getTime() - minutes * 60_000).toISOString();
}

/* ------------------------------------------------------------- transforms -- */

/** ISO shift used by the STALE / HISTORICAL variants. `null` stays `null`. */
function shiftIso(value: string | null, minutes: number): string | null {
  return value ? isoShift(value, minutes) : null;
}

/** Rows whose "status is fine, the clock isn't" keep DEMO/UNKNOWN untouched. */
function degradeStatus(status: ChipStatus): ChipStatus {
  return status === "DEMO" || status === "UNKNOWN" ? status : "STALE";
}

/** LOADING / EMPTY / ERROR / UNAVAILABLE all render before any number exists. */
function emptySnapshot(
  world: World,
  state: ViewState,
): Pick<
  TradeVenueSnapshot,
  "paper" | "fillLog" | "outcomes" | "watchlist" | "opportunities" | "marketCenters"
> {
  const centers =
    state === "UNAVAILABLE"
      ? REAL_PAPER_MARKET_CENTERS.map((center) => ({
          ...center,
          state: "UNAVAILABLE" as ChipStatus,
          lastReadAt: null,
          rows: null,
          noteFa: "دسترسی به این بازار در این استقرار وجود ندارد",
        }))
      : REAL_PAPER_MARKET_CENTERS;
  return {
    paper: [],
    fillLog: [],
    outcomes: [],
    watchlist: [],
    opportunities: [],
    marketCenters: centers,
  };
}

function baseForWorld(world: World) {
  return world === "SIMULATION"
    ? {
        paper: SIMULATION_POSITIONS,
        fillLog: SIMULATION_FILL_LOG,
        outcomes: SIMULATION_OUTCOMES,
        watchlist: SIMULATION_WATCHLIST,
        opportunities: SIMULATION_OPPORTUNITIES,
        marketCenters: REAL_PAPER_MARKET_CENTERS,
      }
    : {
        paper: REAL_PAPER_POSITIONS,
        fillLog: REAL_PAPER_FILL_LOG,
        outcomes: REAL_PAPER_OUTCOMES,
        watchlist: REAL_PAPER_WATCHLIST,
        opportunities: REAL_PAPER_OPPORTUNITIES,
        marketCenters: REAL_PAPER_MARKET_CENTERS,
      };
}

/**
 * Applies a `?state=` variant to one world's rows.
 * Data-level states (UNKNOWN / STALE / PARTIAL / HISTORICAL) rewrite the rows;
 * render-level states (LOADING / EMPTY / ERROR / UNAVAILABLE) drop them and let
 * the panel components render an honest placeholder instead of an empty table.
 */
function buildSnapshot(params: {
  world: World;
  state: ViewState;
  forceDemo: boolean;
  forceViolation: boolean;
}): TradeVenueSnapshot {
  const { world, state, forceDemo, forceViolation } = params;
  const base = baseForWorld(world);
  const isSim = world === "SIMULATION";

  /* Both worlds are paper-only books; the world switch is bookkeeping, not an
     execution mode. Only an explicit violation report leaves PAPER_ONLY. */
  const executionMode: ExecutionMode = forceViolation ? "LIVE" : "PAPER_ONLY";
  // The gallery can force a violation report; the *legal* value is always false.
  const realTrading = forceViolation;

  const common = {
    executionMode,
    realTrading,
    paperAllowed: !forceViolation,
    asOf: state === "LOADING" || state === "ERROR" ? null : FALLBACK_ISO,
    isDemo: true,
    demoForced: forceDemo,
    world,
  } as const;

  if (state === "LOADING" || state === "EMPTY" || state === "ERROR" || state === "UNAVAILABLE") {
    return {
      ...common,
      freshness: {
        readAt: state === "EMPTY" ? FALLBACK_ISO : null,
        oldestRowAgeSec: null,
        newestRowAgeSec: null,
      },
      telemetry: {
        ...MOCK_TELEMETRY,
        lastReadAt: state === "EMPTY" ? FALLBACK_ISO : null,
        rows: 0,
        withheldRows: null,
        demoRows: 0,
        unknownRows: 0,
      },
      ...emptySnapshot(world, state),
    };
  }

  if (state === "UNKNOWN") {
    /* Rule 2 in bulk: no value may survive, and no row may claim a timestamp. */
    return {
      ...common,
      freshness: { readAt: null, oldestRowAgeSec: null, newestRowAgeSec: null },
      telemetry: {
        ...MOCK_TELEMETRY,
        lastReadAt: null,
        rows: base.paper.length + base.fillLog.length + base.outcomes.length,
        withheldRows: null,
        demoRows: 0,
        unknownRows: base.paper.length + base.fillLog.length + base.outcomes.length,
      },
      paper: base.paper.map(
        (row) =>
          ({
            ...row,
            qty: null,
            entry: null,
            entryKind: "UNKNOWN",
            mark: null,
            markStatus: "UNKNOWN",
            unrealized: null,
            currency: null,
            status: "UNKNOWN",
            updatedAt: null,
            evidenceId: null,
          }) as PaperPosition,
      ),
      fillLog: base.fillLog.map((row) => ({
        ...row,
        qty: null,
        price: null,
        notional: null,
        currency: null,
        status: "UNKNOWN" as ChipStatus,
        at: null,
        timeTehran: "—",
        evidenceId: null,
      })),
      outcomes: base.outcomes.map(
        (row) =>
          ({
            ...row,
            realized: null,
            currency: null,
            closedTrades: null,
            openedTrades: null,
            status: "UNKNOWN",
            updatedAt: null,
            evidenceId: null,
          }) as PaperOutcome,
      ),
      watchlist: base.watchlist.map(
        (row) =>
          ({
            ...row,
            price: null,
            changePct: null,
            status: "UNKNOWN",
            updatedAt: null,
          }) as WatchlistItem,
      ),
      opportunities: base.opportunities.map((row) => ({
        ...row,
        canonicalStatus: "UNKNOWN" as ChipStatus,
        updatedAt: null,
        evidenceId: null,
      })),
      marketCenters: base.marketCenters.map((center) => ({
        ...center,
        state: center.state === "DEMO" || center.state === "PARTIAL" ? "UNKNOWN" : center.state,
        lastReadAt: null,
        rows: null,
      })),
    };
  }

  if (state === "STALE") {
    const minutes = 92;
    return {
      ...common,
      freshness: {
        readAt: FALLBACK_ISO,
        oldestRowAgeSec: minutes * 60 + 640,
        newestRowAgeSec: minutes * 60,
      },
      telemetry: {
        ...MOCK_TELEMETRY,
        lastReadAt: isoShift(FALLBACK_ISO, minutes),
        rows: base.paper.length + base.fillLog.length + base.outcomes.length,
        withheldRows: null,
      },
      paper: base.paper.map((row) => ({
        ...row,
        status: degradeStatus(row.status),
        markStatus: row.markStatus === "UNKNOWN" ? "UNKNOWN" : "STALE",
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      fillLog: base.fillLog.map((row) => ({
        ...row,
        status: degradeStatus(row.status),
        at: shiftIso(row.at, minutes),
      })),
      outcomes: base.outcomes.map((row) => ({
        ...row,
        status: degradeStatus(row.status),
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      watchlist: base.watchlist.map((row) => ({
        ...row,
        status: degradeStatus(row.status),
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      opportunities: base.opportunities.map((row) => ({
        ...row,
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      marketCenters: base.marketCenters.map((center) =>
        center.state === "DEMO" ? { ...center, state: "STALE" as ChipStatus } : center,
      ),
    };
  }

  if (state === "PARTIAL") {
    const keepFirst = <T,>(rows: readonly T[], keep: number): T[] =>
      rows.slice(0, Math.max(0, Math.min(rows.length, keep)));
    const paper = keepFirst(base.paper, Math.max(1, base.paper.length - 2));
    const fillLog = keepFirst(base.fillLog, Math.max(1, base.fillLog.length - 3));
    const outcomes = keepFirst(base.outcomes, Math.max(1, base.outcomes.length - 2));
    const withheld = base.paper.length + base.fillLog.length + base.outcomes.length - (paper.length + fillLog.length + outcomes.length);
    return {
      ...common,
      freshness: { readAt: FALLBACK_ISO, oldestRowAgeSec: 1320, newestRowAgeSec: 20 },
      telemetry: {
        ...MOCK_TELEMETRY,
        lastReadAt: FALLBACK_ISO,
        rows: paper.length + fillLog.length + outcomes.length,
        withheldRows: withheld,
      },
      paper: paper.map(
        (row) =>
          ({
            ...row,
            markStatus: row.markStatus === "LIVE" ? "PARTIAL" : row.markStatus,
            status: row.status === "LIVE" ? "PARTIAL" : row.status,
          }) as PaperPosition,
      ),
      fillLog,
      outcomes,
      watchlist: base.watchlist,
      opportunities: base.opportunities,
      marketCenters: base.marketCenters.map((center) =>
        center.state === "DEMO" ? { ...center, state: "PARTIAL" as ChipStatus } : center,
      ),
    };
  }

  if (state === "HISTORICAL") {
    const minutes = 2 * 24 * 60;
    return {
      ...common,
      freshness: {
        readAt: FALLBACK_ISO,
        oldestRowAgeSec: minutes * 60,
        newestRowAgeSec: minutes * 60,
      },
      telemetry: { ...MOCK_TELEMETRY, lastReadAt: isoShift(FALLBACK_ISO, minutes) },
      paper: base.paper.map((row) => ({
        ...row,
        status: "HISTORICAL",
        markStatus: "HISTORICAL",
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      fillLog: base.fillLog.map((row) => ({
        ...row,
        status: "HISTORICAL",
        at: shiftIso(row.at, minutes),
      })),
      outcomes: base.outcomes.map((row) => ({
        ...row,
        status: "HISTORICAL",
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      watchlist: base.watchlist.map((row) => ({
        ...row,
        status: "HISTORICAL",
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      opportunities: base.opportunities.map((row) => ({
        ...row,
        canonicalStatus: "HISTORICAL" as ChipStatus,
        updatedAt: shiftIso(row.updatedAt, minutes),
      })),
      marketCenters: base.marketCenters.map((center) => ({
        ...center,
        state: center.state === "PLANNED" ? center.state : ("HISTORICAL" as ChipStatus),
      })),
    };
  }

  /* DEFAULT — the calm, fully-populated desk. */
  return {
    ...common,
    freshness: { readAt: FALLBACK_ISO, oldestRowAgeSec: 2292, newestRowAgeSec: 14 },
    telemetry: MOCK_TELEMETRY,
    ...base,
  };
}

function forcedByEnv(): boolean {
  return process.env.NEXT_PUBLIC_AHOS_TRADE_VENUE_FORCE_DEMO === "1";
}

/**
 * Single entry point used by the page. Deterministic: same `VenueQuery` in →
 * same bytes out (no ambient clock, no randomness, no I/O).
 */
export function getVenueBundle(query: VenueQuery): VenueBundle {
  const envForced = forcedByEnv();
  const forceDemo = query.forceDemo || envForced;

  const build = (world: World): TradeVenueSnapshot => {
    const snapshot = buildSnapshot({
      world,
      state: query.state,
      forceDemo,
      forceViolation: query.forceViolation,
    });
    return forceDemo ? applyDemoRibbon(snapshot) : snapshot;
  };

  return {
    realPaper: build("REAL_PAPER"),
    simulation: build("SIMULATION"),
    provenance: {
      adapter: "src/mock/trade_venue/index.ts",
      isFixture: true,
      forcedBy: query.forceDemo ? "query" : envForced ? "env" : "none",
    },
  };
}

/** Worlds in display order for the tab control. */
export const WORLD_ORDER: readonly World[] = ["REAL_PAPER", "SIMULATION"];
