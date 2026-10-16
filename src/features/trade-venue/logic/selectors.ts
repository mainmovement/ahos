/**
 * AHOS · Trade Venue — selectors (pure view-model)
 * ============================================================================
 * Turns a `TradeVenueSnapshot` into exactly what the panels render, with the
 * truth rules applied *before* anything reaches JSX:
 *
 *  · results are grouped by unit (USD ≠ USDT ≠ oz) — a cross-unit grand total is
 *    structurally impossible, and a single-unit block refuses to print a total
 *    when nothing qualified («ناموجود»);
 *  · DEMO / SIMULATED / UNKNOWN / non-authorized rows are removed from totals
 *    and reported in an "excluded" footnote with a reason;
 *  · the filter verbs (search / status / permission) are pure functions so they
 *    can be unit-tested without a DOM;
 *  · the read-only export builds a deterministic CSV from the *filtered* view.
 */

import type {
  FillLogEntry,
  PaperOutcome,
  PaperPosition,
  TradeVenueSnapshot,
  WatchlistItem,
  World,
} from "./model";
import {
  MISSING_GLYPH,
  type ExcludedRow,
  type TotalResult,
  type TotalRow,
  computeTotals,
  isExcludedFromTotals,
} from "./truth";

/* --------------------------------------------------------------- totals -- */

export interface UnitGroup {
  unit: string;
  totals: TotalResult;
}

export interface ResultBlock {
  /** One block per unit present in the data. Never merged across units. */
  groups: UnitGroup[];
  /** Rows with no unit at all — reported, never summed. */
  unitless: ExcludedRow[];
  /** All withheld rows across units, for the footnote. */
  excluded: ExcludedRow[];
  includedCount: number;
  excludedCount: number;
  units: string[];
  /** True when more than one unit is present → no grand total is offered. */
  mixedUnits: boolean;
  /** Only when exactly one unit qualified; otherwise `null` ⇒ «ناموجود». */
  singleUnitTotal: number | null;
  singleUnit: string | null;
}

/**
 * Group rows by unit and total each group independently.
 * A grand total is exposed **only** when the block contains exactly one unit —
 * summing USDT and USD would be a fabricated number, so the UI shows both.
 */
export function selectResultBlock(rows: readonly TotalRow[], world: World): ResultBlock {
  const units = Array.from(
    new Set(rows.filter((row) => row.unit !== null).map((row) => row.unit as string)),
  ).sort();

  const groups: UnitGroup[] = units.map((unit) => ({
    unit,
    totals: computeTotals({ world, unit, rows }),
  }));

  /* Accounting pass, unit-agnostic: every row that is withheld for a *reason*
     (another world, missing permission, DEMO/UNKNOWN/CONFLICT/REJECTED, or no
     value) is reported exactly once here. Deriving this list from the per-unit
     groups would silently lose rows that are excluded by status *and* carry no
     unit — which is precisely the shape of the `?state=UNKNOWN` screen. */
  const accounting = computeTotals({ world, rows });
  const excluded = accounting.excluded;
  const excludedIds = new Set(excluded.map((entry) => entry.id));

  /* Rows that are otherwise sound but have no unit at all: reported, never summed. */
  const unitless = rows
    .filter(
      (row) =>
        row.unit === null &&
        row.world === world &&
        row.allowed &&
        !excludedIds.has(row.id) &&
        !isExcludedFromTotals(row.status) &&
        row.value !== null,
    )
    .map((row) => ({ id: row.id, symbol: row.symbol, value: row.value, reason: "NO_UNIT" as const }));

  const includedCount = groups.reduce((acc, group) => acc + group.totals.included.length, 0);
  const mixedUnits = units.length > 1;
  const single = units.length === 1 ? groups[0] : undefined;

  return {
    groups,
    unitless,
    excluded,
    includedCount,
    excludedCount: new Set([...excludedIds, ...unitless.map((row) => row.id)]).size,
    units,
    mixedUnits,
    singleUnitTotal: single?.totals.sum ?? null,
    singleUnit: single?.unit ?? null,
  };
}

export interface VenueTotals {
  open: ResultBlock;
  closed: ResultBlock;
  counts: {
    openRows: number;
    closedRows: number;
    demoRows: number;
    simulationRows: number;
    unknownRows: number;
    notAuthorizedRows: number;
    withheldRows: number | null;
  };
}

function positionToTotalRow(row: PaperPosition): TotalRow {
  return {
    id: row.id,
    symbol: row.symbol,
    value: row.unrealized,
    status: row.markStatus === "UNKNOWN" ? "UNKNOWN" : row.status,
    world: row.world,
    allowed: row.paperAllowed,
    unit: row.currency,
  };
}

function outcomeToTotalRow(row: PaperOutcome): TotalRow {
  return {
    id: row.id,
    symbol: row.symbol,
    value: row.realized,
    status: row.status,
    world: row.world,
    allowed: true,
    unit: row.currency,
  };
}

export function selectVenueTotals(snapshot: TradeVenueSnapshot, world: World): VenueTotals {
  const open = selectResultBlock(snapshot.paper.map(positionToTotalRow), world);
  const closed = selectResultBlock(snapshot.outcomes.map(outcomeToTotalRow), world);

  const all = [...snapshot.paper, ...snapshot.outcomes];
  return {
    open,
    closed,
    counts: {
      openRows: snapshot.paper.length,
      closedRows: snapshot.outcomes.length,
      demoRows: all.filter((row) => row.status === "DEMO").length,
      simulationRows: all.filter((row) => row.status === "SIMULATED").length,
      unknownRows:
        snapshot.paper.filter((row) => row.status === "UNKNOWN" || row.unrealized === null)
          .length +
        snapshot.outcomes.filter((row) => row.status === "UNKNOWN" || row.realized === null)
          .length,
      notAuthorizedRows: snapshot.paper.filter((row) => !row.paperAllowed).length,
      withheldRows: snapshot.telemetry.withheldRows,
    },
  };
}

/* -------------------------------------------------------------- filters -- */

export type StatusFilter = "ALL" | "LIVE" | "STALE" | "UNKNOWN" | "DEMO" | "CONFLICT" | "REJECTED" | "SIMULATED";

export interface VenueFilters {
  /** Free-text symbol search (case-insensitive, matches Latin or Persian). */
  query: string;
  status: StatusFilter;
  /** Show only rows the paper engine is allowed to mirror. */
  onlyAllowed: boolean;
}

export const DEFAULT_FILTERS: VenueFilters = { query: "", status: "ALL", onlyAllowed: false };

function matchesQuery(haystack: readonly (string | null)[], query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) return true;
  return haystack.some((value) => value?.toLowerCase().includes(needle) === true);
}

export function filterPositions(
  rows: readonly PaperPosition[],
  filters: VenueFilters,
): PaperPosition[] {
  return rows.filter((row) => {
    if (filters.onlyAllowed && !row.paperAllowed) return false;
    if (filters.status !== "ALL" && row.status !== filters.status) return false;
    return matchesQuery([row.symbol, row.symbolFa, row.venue, row.id], filters.query);
  });
}

export function filterFillLog(
  rows: readonly FillLogEntry[],
  filters: VenueFilters,
): FillLogEntry[] {
  return rows.filter((row) => {
    if (filters.status !== "ALL" && row.status !== filters.status) return false;
    return matchesQuery([row.symbol, row.action, row.sourceId, row.id], filters.query);
  });
}

export function filterWatchlist(
  rows: readonly WatchlistItem[],
  filters: VenueFilters,
): WatchlistItem[] {
  return rows.filter((row) => {
    if (filters.onlyAllowed && !row.paperAllowed) return false;
    if (filters.status !== "ALL" && row.status !== filters.status) return false;
    return matchesQuery([row.symbol, row.symbolFa, row.sourceId], filters.query);
  });
}

/* --------------------------------------------------------------- export -- */

/**
 * Read-only CSV export of the *filtered* view. Every export carries the DEMO
 * provenance banner and the paper-only note as comment lines, so a file that
 * leaves the page can never be mistaken for a live blotter.
 */
export function buildExportCsv(params: {
  positions: readonly PaperPosition[];
  fillLog: readonly FillLogEntry[];
  asOf: string | null;
  world: World;
  demoForced: boolean;
}): string {
  const { positions, fillLog, asOf, world, demoForced } = params;
  const lines: string[] = [];
  lines.push("# AHOS TRADE VENUE — EXPORT (READ-ONLY)");
  lines.push("# DEMO / FIXTURE DATA — NOT A LIVE BLOTTER");
  lines.push("# موقعیت کاغذی؛ پول واقعی در کار نیست");
  lines.push(`# world=${world} demoForced=${String(demoForced)} asOf=${asOf ?? MISSING_GLYPH}`);
  lines.push("");
  lines.push(
    [
      "kind",
      "symbol",
      "side",
      "qty",
      "entry",
      "mark",
      "result_value",
      "unit",
      "paper_allowed",
      "status",
      "source_id",
      "updated_at",
      "evidence_id",
      "time_tehran",
    ].join(","),
  );
  for (const row of positions) {
    lines.push(
      [
        "position",
        row.symbol,
        row.side,
        cell(row.qty),
        cell(row.entry),
        cell(row.mark),
        cell(row.unrealized),
        row.currency ?? "",
        String(row.paperAllowed),
        row.status,
        row.sourceId,
        row.updatedAt ?? "",
        row.evidenceId ?? "",
        "",
      ].join(","),
    );
  }
  for (const row of fillLog) {
    lines.push(
      [
        "fill",
        row.symbol,
        row.action,
        cell(row.qty),
        cell(row.price),
        "",
        cell(row.notional),
        row.currency ?? "",
        "",
        row.status,
        row.sourceId,
        row.at ?? "",
        row.evidenceId ?? "",
        row.timeTehran,
      ].join(","),
    );
  }
  return `${lines.join("\n")}\n`;
}

function cell(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "" : String(value);
}

/* ------------------------------------------------------------- telemetry -- */

export interface TelemetrySummary {
  sourceId: string;
  lastReadAt: string | null;
  rows: number;
  withheldRows: number | null;
  demoRows: number;
  simulationRows: number;
  unknownRows: number;
  world: World;
  soldAs: "FIXTURE";
}

export function summarizeTelemetry(snapshot: TradeVenueSnapshot): TelemetrySummary {
  return {
    sourceId: snapshot.telemetry.sourceId,
    lastReadAt: snapshot.telemetry.lastReadAt,
    rows: snapshot.telemetry.rows,
    withheldRows: snapshot.telemetry.withheldRows,
    demoRows: snapshot.telemetry.demoRows,
    simulationRows: snapshot.telemetry.simulationRows,
    unknownRows: snapshot.telemetry.unknownRows,
    world: snapshot.world,
    soldAs: "FIXTURE",
  };
}

/* ----------------------------------------------------------------- misc -- */

/** Rows that need a visible "why is this grey" explanation, per panel. */
export function countAttention(rows: readonly { status: string }[]): number {
  return rows.filter(
    (row) => row.status === "STALE" || row.status === "UNKNOWN" || row.status === "CONFLICT",
  ).length;
}
