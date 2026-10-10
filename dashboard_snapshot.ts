/**
 * M-D4 — the shared snapshot vocabulary for the dashboard shell.
 *
 * `CommandCenter.tsx` owns every fetch, every action and all session state; the
 * shell components it composes are presentational and receive their data as
 * props. This module is the one place those shapes are declared, so a component
 * cannot drift from what the API actually returns — and so `app/api/command`'s
 * `commandSnapshot()` and the view layer keep a single spelling of every field.
 *
 * The fields mirror `snapshot.ts`'s output exactly; nothing here is aspirational.
 * A field the snapshot does not emit is not added here.
 */

// ------------------------------------------------------- the command snapshot --

export type Dim = { nameFa: string; status: string; evidenceFa: string };

export type Opp = {
  id: number;
  tokenKey: string;
  symbol: string;
  name: string | null;
  chain: string;
  address: string | null;
  decision: string;
  rankScore: number | null;
  confidence: string;
  securityStatus: string;
  evidenceCoverage: number | null;
  reasonsFa: string[] | null;
  risksFa: string[] | null;
  unknownsFa: string[] | null;
  invalidationFa: string | null;
  missingFa: string[] | null;
  councilVerdict: string | null;
  disagreement: boolean;
  payload: Record<string, unknown> | null;
  canonicalStatus?: string;
  canonicalOutcome?: string | null;
  identityState?: string | null;
  securityState?: string | null;
  paperAllowed?: boolean;
  canonicalUnavailable?: boolean;
};

export type News = {
  id: number;
  source: string;
  sourceUrl: string | null;
  titleOriginal: string;
  titleFa: string | null;
  summaryFa: string | null;
  publishedAt: string | null;
  importance: string;
  category: string;
  sentiment: string;
};

export type Provider = {
  provider: string;
  category: string;
  status: string;
  latencyMs: number | null;
  itemCount: number | null;
  messageFa: string | null;
};

export type CanonicalDecision = {
  tokenKey: string;
  symbol: string | null;
  chain: string | null;
  address: string | null;
  outcome: string;
  identityState: string | null;
  securityState: string | null;
  confidence: string | null;
  opportunityScore: number | null;
  paperAllowed: boolean;
  isPositive: boolean;
  monitoringOnly: boolean;
  primaryReason: string | null;
};

export type WatchItem = { id: number; symbol: string; chain: string; thesisFa: string | null };

export type PaperPosition = {
  id: number;
  symbol: string;
  status: string;
  entryPrice: number | null;
  lastPrice: number | null;
  maxFavorable: number | null;
  maxAdverse: number | null;
};

export type CouncilRow = {
  tokenKey: string;
  verdict: string;
  summaryFa: string;
  watchCount: number;
  rejectCount: number;
  abstainCount: number;
};

export type TeamRow = { id: string; fa: string; size: number };

export type Snap = {
  generatedAt: string;
  state: {
    running: boolean;
    lastCycleAt: string | null;
    lastCycleStatus: string;
    cycleCount: number;
    lastError: string | null;
    intervalSec: number;
  };
  cycle: {
    id: number;
    status: string;
    durationMs: number | null;
    tokenCount: number | null;
    newsCount: number | null;
    opportunityCount: number | null;
    unknownShare: number | null;
    notesFa: string | null;
  } | null;
  market: {
    regime: string;
    fearGreed: number | null;
    fearGreedLabel: string | null;
    btcPrice: number | null;
    btcChange24h: number | null;
    ethPrice: number | null;
    ethChange24h: number | null;
    solPrice: number | null;
    solChange24h: number | null;
    totalMcap: number | null;
    btcDominance: number | null;
    defiTvl: number | null;
  } | null;
  opportunities: Opp[];
  canonicalReadModel?: {
    status: string;
    reason: string | null;
    generatedTs: number | null;
    decisionCount: number;
    stale: boolean;
    authorityVersion: string | null;
  };
  overlayCensus?: {
    pythonDecisionCount: number;
    tsOpportunityCount: number;
    matched: number;
    unmatchedTs: number;
    unmatchedPython: number;
    note: string;
  };
  canonicalDecisions?: CanonicalDecision[];
  news: News[];
  providers: Provider[];
  watchlist: WatchItem[];
  paper: PaperPosition[];
  lessons: Array<{ id: number; titleFa: string; bodyFa: string }>;
  findings: Array<{ id: number; titleFa: string; evidenceFa: string; severity: string }>;
  council: CouncilRow[];
  health: { dimensions: Dim[] };
  blocked: Array<{ item: string; status: string }>;
  teams: TeamRow[];
};

// ----------------------------------------------------------- the alert banner --

export type WebAlertBanner = {
  active: boolean;
  reason?: string;
  ageSec: number | null;
  lastToken: string | null;
  payload: {
    symbol: string | null;
    chain: string | null;
    decision: string | null;
    canonicalSecurityState: string | null;
  } | null;
  disclaimerFa: string;
};

export const INACTIVE_ALERT: WebAlertBanner = {
  active: false,
  ageSec: null,
  lastToken: null,
  payload: null,
  disclaimerFa: "هشدار فرصت پایش است — سیگنال خرید واقعی نیست. PAPER ONLY.",
};

// ------------------------------------------------------------- the launcher ----

export type LauncherComponent = {
  status?: string;
  detail?: string;
  pid?: number | null;
  started_ts?: number | null;
};

export type LauncherSnapshot = {
  status: {
    action?: string;
    ts?: string;
    overall?: string;
    paper_only?: boolean;
    dashboard_url?: string;
    components?: Record<string, LauncherComponent>;
  } | null;
  staleAfterSec?: number;
} | null;

// ---------------------------------------------------------------- the chat -----

// REDTEAM-19 F1: no confirm code in API responses; `ref` is revealed to this
// session on click.
export type PendingActionView = { ref: string; kind: string; summaryFa: string; expiresAt: string };

export type ChatMsg = { role: "user" | "assistant"; content: string; pending?: PendingActionView | null };

// ------------------------------------------------- Persian numeral formatting --
//
// Spec §3: numerals are Persian. Every number the dashboard renders goes
// through one of these, so a Latin digit cannot reach the UI by accident — and
// "نامشخص" (unknown) is what an absent or non-finite value renders as, never 0
// and never an empty string.

const faFmt = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 2 });
const faFmt0 = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 });
const faFmt6 = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 6 });

export function faNum(n: number | null | undefined, d = 2): string {
  if (n == null || !Number.isFinite(n)) return "نامشخص";
  if (d === 0) return faFmt0.format(n);
  if (d >= 6) return faFmt6.format(n);
  return faFmt.format(n);
}

export function faUsd(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "نامشخص";
  const a = Math.abs(n);
  if (a >= 1e12) return `${faNum(n / 1e12)} ت دلار`;
  if (a >= 1e9) return `${faNum(n / 1e9)} م‌م دلار`;
  if (a >= 1e6) return `${faNum(n / 1e6)} م دلار`;
  if (a >= 1e3) return `${faNum(n / 1e3)} ه دلار`;
  return `${faNum(n, n < 1 ? 6 : 2)} دلار`;
}

export function faPct(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "نامشخص";
  return `${n > 0 ? "+" : ""}${faNum(n)}٪`;
}

/**
 * An age in seconds rendered in Persian with a unit, for STALE copy (spec §7:
 * "۳ دقیقه پیش"). Returns "نامعلوم" for an absent timestamp rather than "0".
 */
export function faAgeSec(sec: number | null | undefined, nowMs: number): string {
  if (sec == null || !Number.isFinite(sec)) return "نامعلوم";
  const s = Math.max(0, Math.round(sec));
  if (s < 60) return `${faNum(s, 0)} ثانیه پیش`;
  if (s < 3600) return `${faNum(Math.round(s / 60), 0)} دقیقه پیش`;
  if (s < 86400) return `${faNum(Math.round(s / 3600), 0)} ساعت پیش`;
  return `${faNum(Math.round(s / 86400), 0)} روز پیش`;
}
