/**
 * AHOS · Trade Venue — truth rules (pure functions, unit-tested)
 * ============================================================================
 * Every visual claim on the page funnels through this module. The rules are
 * non-negotiable and enforced by `tests/*.test.ts`:
 *
 *  1. UNKNOWN is grey. It is *never* green.
 *  2. Missing values render «—» / «ناموجود». A fake `0` is forbidden.
 *  3. DEMO rows are excluded from every total (and are labelled DEMO).
 *  4. SIMULATION rows are excluded from REAL-PAPER totals.
 *  5. STALE requires a timestamp. No timestamp ⇒ UNKNOWN.
 *  6. `realTrading === true` or `executionMode !== "PAPER_ONLY"` ⇒ VIOLATION bar.
 *  7. No control may imply live money. Only read-only verbs exist.
 *  8. The UI never ranks or colours a result as good/bad.
 */

import type {
  ChipStatus,
  ExecutionMode,
  TradeVenueSnapshot,
  TruthStatus,
  World,
} from "./model";
import { COMPONENT_STATES, TRUTH_STATUSES } from "./model";

/* ------------------------------------------------------------- vocabulary -- */

/** Persian label shown next to every chip (Latin code stays beside it). */
export const STATUS_FA: Record<ChipStatus, string> = {
  LIVE: "زنده",
  STALE: "کهنه",
  UNKNOWN: "نامشخص",
  DEMO: "نمایشی",
  CONFLICT: "تناقض",
  REJECTED: "ردشده",
  UNAVAILABLE: "ناموجود",
  PARTIAL: "ناقص",
  PLANNED: "برنامه‌ریزی‌شده",
  MISSING: "غایب",
  ERROR: "خطا",
  EMPTY: "خالی",
  LOADING: "در حال بارگذاری",
  HISTORICAL: "تاریخی",
  SIMULATED: "شبیه‌سازی",
};

/**
 * Tone tags drive colour. `live` is the *only* green tone in the system, and
 * UNKNOWN / UNAVAILABLE / PLANNED / MISSING / SIMULATED never reach it.
 */
export type Tone =
  | "live"
  | "info"
  | "neutral"
  | "unknown"
  | "stale"
  | "conflict"
  | "danger"
  | "sim";

export const STATUS_TONE: Record<ChipStatus, Tone> = {
  LIVE: "live",
  STALE: "stale",
  UNKNOWN: "unknown",
  DEMO: "neutral",
  CONFLICT: "conflict",
  REJECTED: "danger",
  UNAVAILABLE: "unknown",
  PARTIAL: "unknown",
  PLANNED: "unknown",
  MISSING: "unknown",
  ERROR: "danger",
  EMPTY: "unknown",
  LOADING: "unknown",
  HISTORICAL: "info",
  SIMULATED: "sim",
};

/** The literal placeholders allowed for "no value". Never `0`, never `""`. */
export const MISSING_GLYPH = "—";
export const MISSING_LABEL_FA = "ناموجود";
export const UNKNOWN_LABEL_FA = "نامشخص";
export const NOT_CONNECTED_FA = "متصل نیست";
export const NOT_AUTHORIZED_FA = "غیرمجاز";
export const PERMITTED_FA = "مجاز";
export const PAPER_ONLY_FA = "فقط کاغذی";
export const PAPER_ONLY_CODE = "PAPER_ONLY";
export const PAPER_NOTE_FA = "موقعیت کاغذی؛ پول واقعی در کار نیست";
export const PAPER_NOTE_EN = "Paper position — no real money involved.";

/** A status is green only if LIVE. Everything else is explicitly not-green. */
export function isGreen(status: ChipStatus): boolean {
  return STATUS_TONE[status] === "live";
}

/** True for the statuses that must never be summed into a total. */
export function isExcludedFromTotals(status: ChipStatus): boolean {
  return (
    status === "DEMO" ||
    /* A conflicted row has two disagreeing values, and a rejected row has been
       refused by the judge: summing either one would invent a number. */
    status === "CONFLICT" ||
    status === "REJECTED" ||
    status === "SIMULATED" ||
    status === "UNKNOWN" ||
    status === "UNAVAILABLE" ||
    status === "MISSING" ||
    status === "ERROR" ||
    status === "LOADING" ||
    status === "EMPTY" ||
    status === "PLANNED"
  );
}

export function isTruthStatus(value: unknown): value is TruthStatus {
  return typeof value === "string" && (TRUTH_STATUSES as readonly string[]).includes(value);
}

export function isChipStatus(value: unknown): value is ChipStatus {
  return (
    isTruthStatus(value) ||
    (typeof value === "string" && (COMPONENT_STATES as readonly string[]).includes(value))
  );
}

/**
 * STALE ⇒ a timestamp is mandatory. Anything stale-shaped without a timestamp
 * is downgraded to UNKNOWN (rule 5), so the UI can never print "stale" without
 * saying *how* stale.
 */
export function staleOrUnknown(updatedAt: string | null): TruthStatus {
  return updatedAt ? "STALE" : "UNKNOWN";
}

/* -------------------------------------------------------------- execution -- */

export interface ExecutionReport {
  executionMode: ExecutionMode;
  realTrading: boolean;
}

/**
 * Rule 6. The venue is legal only in PAPER_ONLY with `realTrading === false`.
 * Any other combination is a violation that must be surfaced, not hidden.
 */
export function isPaperSafe(report: ExecutionReport): boolean {
  return report.executionMode === "PAPER_ONLY" && report.realTrading === false;
}

export interface ViolationReport {
  /** Machine code, also used as a test hook. */
  code: "REAL_TRADING_FLAG" | "NON_PAPER_MODE" | "BOTH";
  modes: ExecutionMode[];
  realTrading: boolean;
  headlineFa: string;
  detailFa: string;
  detailEn: string;
}

/** Returns `null` when the venue is paper-safe, otherwise the violation. */
export function detectViolation(report: ExecutionReport): ViolationReport | null {
  const realTrading = report.realTrading === true;
  const badMode = report.executionMode !== "PAPER_ONLY";
  if (!realTrading && !badMode) return null;

  const code =
    realTrading && badMode ? "BOTH" : realTrading ? "REAL_TRADING_FLAG" : "NON_PAPER_MODE";

  const modeFa: Record<ExecutionMode, string> = {
    PAPER_ONLY: "فقط کاغذی",
    SIMULATION: "شبیه‌سازی",
    SHADOW: "سایه",
    LIVE: "زنده (پول واقعی)",
    UNKNOWN: "نامشخص",
  };

  const headlineFa =
    code === "BOTH"
      ? "وضعیت اجرا خارج از چارچوب فقط‌کاغذی است"
      : code === "REAL_TRADING_FLAG"
        ? "پرچم معاملهٔ واقعی فعال است"
        : "حالت اجرا فقط‌کاغذی نیست";

  const detailFa = [
    `حالت اجرا: ${modeFa[report.executionMode]}`,
    `معاملهٔ واقعی: ${realTrading ? "فعال" : "غیرفعال"}`,
    "این صفحهٔ کاغذی هیچ کنترلی برای معاملهٔ واقعی ندارد؛ تا رفع تخطی، همهٔ اعداد نمایشی تلقی می‌شوند.",
  ].join(" · ");

  const detailEn = `executionMode=${report.executionMode} · realTrading=${String(
    realTrading,
  )} · VIOLATION — paper venue must never carry live execution state`;

  return { code, modes: [report.executionMode], realTrading, headlineFa, detailFa, detailEn };
}

/* --------------------------------------------------------- value hygiene -- */

/**
 * Rule 2. Formats a possibly-unknown number.
 *  - `null` / `undefined` / `NaN` / `Infinity` ⇒ `—` (plus «ناموجود» optionally)
 *  - otherwise a Latin-digit, tabular figure.
 * A genuine `0` renders as `0` (it is a *known* zero, not a missing value).
 */
export interface FormattedValue {
  text: string;
  kind: "value" | "missing";
}

export function formatValue(
  value: number | null | undefined,
  opts: { fractionDigits?: number; signed?: boolean } = {},
): FormattedValue {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return { text: MISSING_GLYPH, kind: "missing" };
  }
  const digits = opts.fractionDigits ?? 2;
  const fixed = Math.abs(value).toFixed(digits);
  const [intPart = "0", frac] = fixed.split(".");
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const body = frac ? `${grouped}.${frac}` : grouped;
  const sign = value < 0 ? "-" : opts.signed ? "+" : "";
  return { text: `${sign}${body}`, kind: "value" };
}

/** Convenience: `formatValue(…).text`. */
export function valueText(
  value: number | null | undefined,
  opts?: { fractionDigits?: number; signed?: boolean },
): string {
  return formatValue(value, opts).text;
}

/* ---------------------------------------------------------------- totals -- */

export interface TotalRow {
  id: string;
  symbol: string;
  value: number | null;
  status: ChipStatus;
  world: World;
  /** `false` ⇒ the row has no paper permission ⇒ never summed («غیرمجاز»). */
  allowed: boolean;
  /** Unit of the value (USD, USDT, oz…). `null` ⇒ unknown unit. */
  unit: string | null;
}

/** Why a row was kept out of a total. Always shown in the footnote. */
export type ExclusionReason =
  | ChipStatus
  | "NOT_AUTHORIZED"
  | "OTHER_WORLD"
  | "OTHER_UNIT"
  | "NO_UNIT"
  | "NO_VALUE";

export interface ExcludedRow {
  id: string;
  symbol: string;
  value: number | null;
  reason: ExclusionReason;
}

export interface TotalResult {
  /** Sum over included rows. `null` ⇒ nothing to sum ⇒ «ناموجود». */
  sum: number | null;
  included: TotalRow[];
  /** Rows withheld from the sum, with the reason, for the "excluded" footnote. */
  excluded: ExcludedRow[];
  excludedValue: number | null;
  /** True when at least one excluded row was DEMO (rule 3). */
  hadDemo: boolean;
  /** True when at least one excluded row was SIMULATED (rule 4). */
  hadSimulation: boolean;
  /** True when at least one withheld row had no value (never summed as 0). */
  hadUnknown: boolean;
  /** True when at least one withheld row was not paper-allowed. */
  hadNotAuthorized: boolean;
}

export interface TotalsInput {
  /** Which book is being totalled. SIMULATION rows never enter REAL_PAPER. */
  world: World;
  /**
   * Unit the call is summing. Values in different units are *never* added
   * together — the caller groups by unit and asks once per group.
   * `null` ⇒ only unit-less rows qualify (they end up excluded as NO_UNIT).
   * `undefined` ⇒ deliberately ignore the unit dimension (tests only).
   */
  unit?: string | null;
  rows: readonly TotalRow[];
}

/**
 * Rules 3 + 4 (+ unit hygiene). Sums paper results while structurally excluding:
 *   · rows of the *other* world (SIMULATION never touches REAL-PAPER totals and
 *     vice versa)                                   → reason "OTHER_WORLD"
 *   · DEMO / UNKNOWN / UNAVAILABLE / REJECTED / …    → reason = its status
 *   · rows in another (or an unknown) unit           → "OTHER_UNIT" / "NO_UNIT"
 *   · rows without a value                           → reason "NO_VALUE"
 *   · rows without paper permission                  → reason "NOT_AUTHORIZED"
 *
 * SIMULATED is treated as *native* inside the SIMULATION world (that is what
 * that book is) and as excluded inside REAL_PAPER — which is exactly rule 4.
 * Returns `sum: null` (never `0`) when nothing qualifies: an empty total must
 * read «ناموجود», not «۰».
 */
export function computeTotals({ world, unit, rows }: TotalsInput): TotalResult {
  const included: TotalRow[] = [];
  const excluded: ExcludedRow[] = [];
  let excludedValue: number | null = null;
  let hadDemo = false;
  let hadSimulation = false;
  let hadUnknown = false;
  let hadNotAuthorized = false;

  for (const row of rows) {
    const wrongWorld = row.world !== world;
    const noValue = row.value === null || !Number.isFinite(row.value);
    const simNative = row.status === "SIMULATED" && world === "SIMULATION";
    const blockedStatus = simNative ? false : isExcludedFromTotals(row.status);
    const notAuthorized = row.allowed === false;
    let unitReason: ExclusionReason | null = null;
    if (unit !== undefined) {
      if (row.unit === null) unitReason = "NO_UNIT";
      else if (unit !== null && row.unit !== unit) unitReason = "OTHER_UNIT";
    }

    if (row.status === "DEMO") hadDemo = true;
    if (row.status === "SIMULATED") hadSimulation = true;
    if (noValue || row.status === "UNKNOWN") hadUnknown = true;
    if (notAuthorized) hadNotAuthorized = true;

    let reason: ExclusionReason | null = null;
    if (wrongWorld) reason = "OTHER_WORLD";
    else if (notAuthorized) reason = "NOT_AUTHORIZED";
    else if (blockedStatus) reason = row.status;
    else if (unitReason) reason = unitReason;
    else if (noValue) reason = "NO_VALUE";

    if (reason) {
      excluded.push({ id: row.id, symbol: row.symbol, value: row.value, reason });
      const withheld = row.value;
      if (!noValue && withheld !== null) excludedValue = (excludedValue ?? 0) + withheld;
      continue;
    }
    included.push(row);
  }

  const sum = included.length
    ? included.reduce((acc, row) => acc + (row.value ?? 0), 0)
    : null;

  return {
    sum,
    included,
    excluded,
    excludedValue,
    hadDemo,
    hadSimulation,
    hadUnknown,
    hadNotAuthorized,
  };
}

/** Persian label for an exclusion reason, used in the totals footnote. */
export const EXCLUSION_FA: Record<ExclusionReason, string> = {
  OTHER_WORLD: "جهان دیگر",
  NOT_AUTHORIZED: NOT_AUTHORIZED_FA,
  OTHER_UNIT: "واحد دیگر",
  NO_UNIT: "واحد نامشخص",
  NO_VALUE: "بدون مقدار",
  LIVE: STATUS_FA.LIVE,
  STALE: STATUS_FA.STALE,
  UNKNOWN: STATUS_FA.UNKNOWN,
  DEMO: STATUS_FA.DEMO,
  CONFLICT: STATUS_FA.CONFLICT,
  REJECTED: STATUS_FA.REJECTED,
  UNAVAILABLE: STATUS_FA.UNAVAILABLE,
  PARTIAL: STATUS_FA.PARTIAL,
  PLANNED: STATUS_FA.PLANNED,
  MISSING: STATUS_FA.MISSING,
  ERROR: STATUS_FA.ERROR,
  EMPTY: STATUS_FA.EMPTY,
  LOADING: STATUS_FA.LOADING,
  HISTORICAL: STATUS_FA.HISTORICAL,
  SIMULATED: STATUS_FA.SIMULATED,
};

/* ------------------------------------------------------------ permissions -- */

/** Rule 8 helper: `paperAllowed === false` rows print «غیرمجاز». */
export function permissionLabel(paperAllowed: boolean): string {
  return paperAllowed ? "مجاز" : NOT_AUTHORIZED_FA;
}

/* ------------------------------------------------------------- verbs/a11y -- */

/**
 * Rule 7. The complete vocabulary of interactive affordances the venue page may
 * render. `data-verb` on every control is asserted against this list by tests.
 */
export const ALLOWED_VERBS = [
  "view",
  "filter",
  "export",
  "evidence",
  "copy_id",
  "close",
  "mute",
  "tier",
  "tab",
  "link",
] as const;
export type AllowedVerb = (typeof ALLOWED_VERBS)[number];

/**
 * Anything matching this list may never appear in the rendered markup
 * (English or Persian) — it would imply live money.
 */
export const FORBIDDEN_CONTROL_PATTERNS: readonly RegExp[] = [
  /\bbuy\b/i,
  /\bsell\b/i,
  /\bshort\s*open\b/i,
  /\bplace[\s_-]?order\b/i,
  /\bsubmit[\s_-]?order\b/i,
  /\bmarket[\s_-]?order\b/i,
  /\blimit[\s_-]?order\b/i,
  /\bapprove\b/i,
  /\bsize\s*(position|order)\b/i,
  /\benable[\s_-]?(real|live)[\s_-]?trading\b/i,
  /\bgo[\s_-]?live\b/i,
  /خرید/,
  /فروش/,
  /ثبت\s*سفارش/,
  /سفارش\s*(خرید|فروش|گذاری)/,
  /تأیید\s*معامله/,
  /فعال‌سازی\s*معامله/,
];

/** Returns the first forbidden pattern found in `text`, or `null`. */
export function findForbiddenControl(text: string): RegExp | null {
  for (const pattern of FORBIDDEN_CONTROL_PATTERNS) {
    if (pattern.test(text)) return pattern;
  }
  return null;
}

/* -------------------------------------------------------------- snapshot -- */

/**
 * Rule 3 at bundle level: marks every mock-backed row DEMO.
 * Used by `?demo=1` and by the `NEXT_PUBLIC_AHOS_TRADE_VENUE_FORCE_DEMO` flag so
 * an environment can guarantee no surface ever looks live.
 */
export function applyDemoRibbon(snapshot: TradeVenueSnapshot): TradeVenueSnapshot {
  const demote = <T extends { status: ChipStatus }>(row: T): T => ({ ...row, status: "DEMO" });
  return {
    ...snapshot,
    isDemo: true,
    demoForced: true,
    paper: snapshot.paper.map(demote),
    fillLog: snapshot.fillLog.map(demote),
    outcomes: snapshot.outcomes.map(demote),
    watchlist: snapshot.watchlist.map(demote),
    opportunities: snapshot.opportunities.map((row) => ({ ...row, canonicalStatus: "DEMO" as const })),
    marketCenters: snapshot.marketCenters.map((center) =>
      center.state === "PLANNED" || center.state === "UNAVAILABLE"
        ? center
        : { ...center, state: "DEMO" as const },
    ),
    telemetry: {
      ...snapshot.telemetry,
      demoRows:
        snapshot.paper.length +
        snapshot.fillLog.length +
        snapshot.outcomes.length +
        snapshot.watchlist.length +
        snapshot.opportunities.length,
      unknownRows: 0,
    },
  };
}

/** Row count shown in the telemetry strip (one number, no ambiguity). */
export function countRows(snapshot: TradeVenueSnapshot): number {
  return (
    snapshot.paper.length +
    snapshot.fillLog.length +
    snapshot.outcomes.length +
    snapshot.watchlist.length +
    snapshot.opportunities.length
  );
}
