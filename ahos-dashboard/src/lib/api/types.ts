/**
 * AHOS dashboard — shared data contracts.
 *
 * These types are the ONLY contract between UI components and data. Every
 * function in `src/lib/api/*` returns these shapes; today they are backed by
 * `src/mock/*`, later by the Python canonical read model / Next API routes.
 *
 * Truthfulness rules encoded in the types:
 *  - every payload carries `DataMeta` (source, retrievedAt, status, isMock)
 *  - every value that can be missing is `number | null` (UNKNOWN ≠ 0)
 *  - agent lifecycle ≠ implementation status ≠ verification (orthogonal)
 */

/* ------------------------------------------------------------------ core */

/** Persian is primary; English mirrors it. */
export interface Localized {
  fa: string;
  en: string;
}

export const DATA_STATUSES = ["LIVE", "STALE", "UNKNOWN", "UNAVAILABLE", "DEMO"] as const;
/** Freshness / provenance status of a value or payload. Never fake LIVE. */
export type DataStatus = (typeof DATA_STATUSES)[number];

export interface DataMeta {
  /** Machine id of the source, e.g. `mock/markets` or `dexscreener`. */
  source: string;
  /** Human label for the source. */
  sourceLabel: Localized;
  /** ISO-8601 UTC timestamp when the payload was retrieved; null = unknown. */
  retrievedAt: string | null;
  status: DataStatus;
  /** True when the payload is produced by `src/mock`. */
  isMock: boolean;
  /** Freshness SLA. A LIVE payload older than this is rendered as STALE. */
  ttlSec?: number;
  note?: Localized;
}

export interface DataEnvelope<T> {
  data: T;
  meta: DataMeta;
}

export const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] as const;
export type Severity = (typeof SEVERITIES)[number];

export const CONFIDENCE_LEVELS = ["HIGH", "MED", "LOW", "UNKNOWN"] as const;
export type Confidence = (typeof CONFIDENCE_LEVELS)[number];

/** Mirrors `PROVIDER_HEALTH_STATUSES` in the AHOS repo (`types.ts`). */
export const PROVIDER_HEALTH_STATUSES = [
  "LIVE",
  "DEGRADED",
  "TIMEOUT",
  "RATE_LIMITED",
  "NO_KEY",
  "AUTH_FAILED",
  "NETWORK_UNAVAILABLE",
  "SOURCE_UNAVAILABLE",
  "UNKNOWN",
] as const;
export type ProviderHealthStatus = (typeof PROVIDER_HEALTH_STATUSES)[number];

/** Icon keys resolved to lucide icons by `components/ui/icon.tsx`. */
export type IconKey =
  | "radar"
  | "shield-check"
  | "eye"
  | "ban"
  | "wallet"
  | "activity"
  | "globe"
  | "flame"
  | "coins"
  | "bitcoin"
  | "newspaper"
  | "graduation"
  | "server"
  | "brain"
  | "bot"
  | "gauge"
  | "database"
  | "zap"
  | "landmark"
  | "trending-up"
  | "layers"
  | "cpu"
  | "lock"
  | "file-text"
  | "flask"
  | "network";

export type ValueFormat = "count" | "percent" | "usd" | "usdCompact" | "number" | "score" | "ratio";

/* ------------------------------------------------------------------ KPIs */

export interface Kpi {
  id: string;
  label: Localized;
  value: number | null;
  format: ValueFormat;
  decimals?: number;
  /** Percent change over `deltaWindow`; null = unknown. */
  delta: number | null;
  deltaWindow: Localized;
  polarity: "up-good" | "down-good" | "neutral";
  spark: number[];
  status: DataStatus;
  icon: IconKey;
  hint?: Localized;
}

/* --------------------------------------------------------------- markets */

export type AssetClass = "crypto" | "fx" | "commodity" | "index" | "equity" | "rate" | "iran";

export interface Instrument {
  id: string;
  symbol: string;
  name: Localized;
  assetClass: AssetClass;
  price: number | null;
  /** Percent change over 24h (or session). */
  change24h: number | null;
  high24h: number | null;
  low24h: number | null;
  volume24h: number | null;
  /** Quote unit: USD, IRR, pts, % … */
  quote: string;
  decimals: number;
  status: DataStatus;
  retrievedAt: string | null;
  source: string;
  spark: number[];
}

export interface Candle {
  /** epoch ms */
  t: number;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
}

export interface MarketBoard {
  instruments: Instrument[];
  /** Candles keyed by instrument id (only for instruments with history). */
  candles: Record<string, Candle[]>;
}

export interface SeriesPoint {
  t: number;
  v: number;
}

export interface NamedSeries {
  id: string;
  label: Localized;
  points: SeriesPoint[];
}

/* -------------------------------------------------------------- equities */

export type EquityRegion = "us" | "eu" | "asia";

export interface SectorPerf {
  id: string;
  name: Localized;
  change: number | null;
  /** Relative weight (0..1) used for heatmap tile size. */
  weight: number;
}

export interface Mover {
  symbol: string;
  name: string;
  price: number | null;
  change: number | null;
  volume: number | null;
  sector: Localized;
}

export interface EquitiesBoard {
  region: EquityRegion;
  indices: Instrument[];
  sectors: SectorPerf[];
  gainers: Mover[];
  losers: Mover[];
  breadth: { advancers: number; decliners: number; unchanged: number } | null;
  performance: NamedSeries[];
  /** Exchange ids (see lib/time/sessions) relevant to this region. */
  exchanges: string[];
}

/* ----------------------------------------------------------- commodities */

export interface DriverNote {
  id: string;
  title: Localized;
  direction: "up" | "down" | "mixed";
  confidence: Confidence;
}

export interface OilBoard {
  benchmarks: Instrument[];
  candles: Candle[];
  spread: SeriesPoint[];
  inventories: { week: string; change: number | null }[];
  opec: { country: Localized; quota: number | null; actual: number | null }[];
  drivers: DriverNote[];
}

export interface GoldBoard {
  spot: Instrument[];
  iran: Instrument[];
  candles: Candle[];
  /** Iranian coin premium over intrinsic value, % */
  coinPremium: SeriesPoint[];
  centralBanks: { country: Localized; tonnes: number | null }[];
  etfFlows: { week: string; tonnes: number | null }[];
  drivers: DriverNote[];
}

/* ---------------------------------------------------------------- crypto */

export interface CryptoBoard {
  totalMarketCap: number | null;
  totalMarketCapChange: number | null;
  btcDominance: number | null;
  volume24h: number | null;
  fearGreed: { value: number | null; label: Localized };
  assets: Instrument[];
  sectors: SectorPerf[];
  funding: { symbol: string; rate: number | null; openInterest: number | null }[];
  stablecoins: { symbol: string; supply: number | null; change7d: number | null }[];
  candles: Candle[];
  dominance: NamedSeries[];
}

/* ------------------------------------------------------ token intelligence */

export type IdentityState = "VERIFIED" | "PROBABLE" | "CONFLICT" | "UNKNOWN";
export type TriState = "YES" | "NO" | "UNKNOWN";
/** Mirrors the Python security overlay states (architecture/security/gate.py). */
export type SecurityGateState = "PASS" | "REJECT" | "INCOMPLETE" | "STALE";
/** Mirrors `DECISIONS` in the AHOS repo `types.ts` (no BUY in the UI). */
export type CanonicalOutcome =
  | "WATCH"
  | "MONITOR_ONLY"
  | "PAPER_CANDIDATE"
  | "REJECT"
  | "ABSTAIN"
  | "INSUFFICIENT_EVIDENCE"
  | "UNKNOWN";

export interface ProviderEvidence {
  provider: string;
  status: ProviderHealthStatus;
  latencyMs: number | null;
  summary: Localized;
}

export interface TokenDossier {
  tokenKey: string;
  symbol: string;
  name: string;
  chain: string;
  contract: string | null;
  pairAddress: string | null;
  dex: string | null;
  identity: {
    state: IdentityState;
    /** 0..1, null = cannot be computed */
    confidence: number | null;
    evidence: { source: string; matched: boolean | null; note: Localized }[];
  };
  security: {
    gate: SecurityGateState;
    honeypot: TriState;
    sellable: TriState;
    mintable: TriState;
    freezeable: TriState;
    ownership: "RENOUNCED" | "OPEN" | "UNKNOWN";
    flags: Localized[];
  };
  market: {
    priceUsd: number | null;
    change24h: number | null;
    liquidityUsd: number | null;
    volume24h: number | null;
    fdv: number | null;
    holders: number | null;
    ageHours: number | null;
  };
  decision: {
    outcome: CanonicalOutcome;
    score: number | null;
    confidence: Confidence;
    reasons: Localized[];
    risks: Localized[];
    unknowns: Localized[];
    invalidation: Localized[];
  };
  providers: ProviderEvidence[];
  status: DataStatus;
  retrievedAt: string | null;
  spark: number[];
}

/* ----------------------------------------------------------- opportunities */

export interface OpportunityRow {
  tokenKey: string;
  symbol: string;
  chain: string;
  address: string | null;
  outcome: CanonicalOutcome;
  identityState: IdentityState;
  securityState: SecurityGateState;
  confidence: Confidence;
  score: number | null;
  /** 0..1 share of required evidence fields present. */
  evidenceCoverage: number;
  paperAllowed: boolean;
  monitoringOnly: boolean;
  primaryReason: Localized;
  reasons: Localized[];
  risks: Localized[];
  unknowns: Localized[];
  updatedAt: string;
  status: DataStatus;
}

export interface OpportunitiesOverview {
  rows: OpportunityRow[];
  funnel: { stage: Localized; count: number }[];
  authorityNote: Localized;
}

/* ------------------------------------------------------------------ news */

export type VerificationState = "VERIFIED" | "UNVERIFIED" | "CONFLICTING";
export type PipelineStageId = "ingest" | "dedupe" | "translate" | "classify" | "verify" | "publish";
export type Sentiment = "POS" | "NEG" | "NEU" | "UNKNOWN";
export type Importance = "HIGH" | "MED" | "LOW" | "UNKNOWN";

export interface NewsItem {
  id: string;
  title: Localized;
  summary: Localized;
  source: string;
  corroboratingSources: string[];
  publishedAt: string | null;
  category: Localized;
  importance: Importance;
  sentiment: Sentiment;
  verification: VerificationState;
  conflictNote?: Localized;
  relatedAssets: string[];
  stage: PipelineStageId;
  status: DataStatus;
}

export interface NewsPipelineStage {
  id: PipelineStageId;
  label: Localized;
  count: number;
  perHour: number | null;
  backlog: number;
  health: "ok" | "degraded" | "blocked";
  note?: Localized;
}

export interface SourceReliability {
  source: string;
  language: "fa" | "en" | "multi";
  reliability: number | null;
  items24h: number;
  status: ProviderHealthStatus;
}

export interface Newsroom {
  items: NewsItem[];
  pipeline: NewsPipelineStage[];
  sources: SourceReliability[];
}

/* -------------------------------------------------------------- security */

export interface SecurityScan {
  id: string;
  target: string;
  chain: string;
  gate: SecurityGateState;
  flags: Localized[];
  at: string;
  provider: string;
}

export interface SecurityIncident {
  id: string;
  title: Localized;
  severity: Severity;
  at: string;
  state: "OPEN" | "MITIGATED" | "MONITORING" | "CLOSED";
}

export interface ProviderHealth {
  name: string;
  category: Localized;
  status: ProviderHealthStatus;
  latencyMs: number | null;
  availability: number | null;
  lastSuccess: string | null;
  errorCount: number;
}

export interface SecurityOverview {
  gateCounts: Record<SecurityGateState, number>;
  scans: SecurityScan[];
  incidents: SecurityIncident[];
  phishing: { domain: string; imitates: string; detectedAt: string; state: "BLOCKED" | "MONITORING" }[];
  providers: ProviderHealth[];
  flagCounts: { flag: Localized; count: number }[];
  trend: { t: number; pass: number; reject: number; incomplete: number }[];
}

/* --------------------------------------------------------------- agents */

export const AGENT_RUNTIME_STATES = [
  "running",
  "idle",
  "blocked",
  "failed",
  "registered",
  "planned",
  "suspended",
] as const;
/** Runtime lifecycle — what the process is doing (NOT authority, NOT trust). */
export type AgentRuntimeState = (typeof AGENT_RUNTIME_STATES)[number];

/** How much of the agent exists in code (from repo docs). */
export type ImplementationStatus = "IMPLEMENTED" | "PARTIAL" | "DOCUMENTED_ONLY" | "PLANNED";

export type VerificationStatus = "UNVERIFIED" | "PASS" | "FAIL" | "INCONCLUSIVE";
export type VerificationKind = "INDEPENDENT" | "SELF_CHECK";

export type DepartmentId =
  | "architecture"
  | "governance"
  | "research"
  | "markets"
  | "security"
  | "quant"
  | "runtime"
  | "product"
  | "verification";

export interface AgentEvent {
  id: string;
  agentId: string;
  at: string;
  kind: "task_started" | "task_completed" | "blocked" | "failed" | "heartbeat" | "registered" | "note";
  text: Localized;
}

export interface Agent {
  id: string;
  code: string;
  name: Localized;
  role: Localized;
  department: DepartmentId;
  implementation: ImplementationStatus;
  runtime: AgentRuntimeState;
  /** 0 = REGISTERED … 4 = TRUSTED_FOR_SCOPE (see AGENT_REGISTRY_MODEL.md) */
  maturity: number;
  currentTask: Localized | null;
  lastActivityAt: string | null;
  capabilities: Localized[];
  limitations: Localized[];
  verification: { status: VerificationStatus; kind: VerificationKind | null };
  metrics: { tasks24h: number | null; successRate: number | null; avgLatencyMs: number | null };
  events: AgentEvent[];
  sourceDoc: string | null;
}

export interface AgentsOverview {
  agents: Agent[];
  departments: { id: DepartmentId; name: Localized }[];
}

/* ------------------------------------------------------------ university */

export interface Student {
  agentId: string;
  name: Localized;
  program: Localized;
  level: number;
  progress: number;
  state: "enrolled" | "examining" | "passed" | "failed" | "retraining";
}

export interface Exam {
  id: string;
  title: Localized;
  agentId: string;
  agentName: Localized;
  score: number | null;
  passMark: number;
  result: "PASS" | "FAIL" | "PENDING";
  kind: VerificationKind;
  at: string;
}

export interface UniversityOverview {
  students: Student[];
  exams: Exam[];
  retraining: { agentId: string; agentName: Localized; reason: Localized; priority: Severity; queuedAt: string }[];
  programs: { id: string; name: Localized; enrolled: number; passRate: number | null }[];
  calibration: { bucket: number; predicted: number; observed: number | null }[];
  passRateTrend: number[];
}

/* -------------------------------------------------------------- research */

export type MissionState =
  | "DRAFT"
  | "PLANNING"
  | "PROPOSED"
  | "AUTHORIZED"
  | "ACTIVE"
  | "WAITING"
  | "BLOCKED"
  | "VERIFICATION"
  | "ACCEPTANCE"
  | "COMPLETE"
  | "FAILED"
  | "CANCELLED"
  | "REJECTED";

export type EpistemicPosture = "KNOWN" | "UNCERTAIN" | "UNKNOWN" | "CONTRADICTORY" | "NOVEL";

export interface ResearchMission {
  id: string;
  title: Localized;
  leadAgentId: string;
  state: MissionState;
  evidence: "NONE" | "PARTIAL" | "SUFFICIENT" | "STALE" | "CONTRADICTED";
  verification: "NOT_REQUESTED" | "PENDING" | "PASS" | "FAIL" | "INCONCLUSIVE";
  verificationKind: VerificationKind | null;
  acceptance: "NOT_REQUIRED" | "PENDING" | "ACCEPTED" | "REJECTED" | "DEFERRED";
  updatedAt: string;
  tags: string[];
}

export interface Hypothesis {
  id: string;
  statement: Localized;
  posture: EpistemicPosture;
  support: number;
  against: number;
  missionId: string;
}

export interface ResearchOverview {
  missions: ResearchMission[];
  hypotheses: Hypothesis[];
  papers: { id: string; title: string; venue: string; year: number; relevance: number; state: "QUEUED" | "READ" | "SUMMARIZED" }[];
  experiments: { id: string; title: Localized; state: "RUNNING" | "DONE" | "FAILED" | "QUEUED"; metric: string; value: number | null }[];
}

/* --------------------------------------------------------- paper trading */

export interface PaperPosition {
  id: string;
  symbol: string;
  side: "LONG" | "SHORT";
  qty: number;
  entry: number;
  mark: number | null;
  pnl: number | null;
  pnlPct: number | null;
  stop: number | null;
  target: number | null;
  openedAt: string;
  strategy: Localized;
  status: DataStatus;
}

export interface PaperFill {
  id: string;
  symbol: string;
  side: "LONG" | "SHORT";
  kind: "OPEN" | "CLOSE";
  qty: number;
  price: number;
  pnl: number | null;
  at: string;
  reason: Localized;
}

export interface RiskLimit {
  id: string;
  label: Localized;
  used: number;
  limit: number;
  unit: "pct" | "usd" | "count";
  state: "ok" | "warn" | "breach";
}

export interface PaperAccount {
  mode: "PAPER_ONLY";
  equity: number;
  startingEquity: number;
  cash: number;
  pnlDay: number;
  pnlDayPct: number;
  pnlTotal: number;
  pnlTotalPct: number;
  winRate: number | null;
  tradeCount: number;
  maxDrawdownPct: number | null;
  sharpe: number | null;
  equityCurve: SeriesPoint[];
  positions: PaperPosition[];
  fills: PaperFill[];
  limits: RiskLimit[];
}

/* ------------------------------------------------------------- portfolio */

export interface PortfolioOverview {
  totalValue: number;
  changePct: number | null;
  allocation: { id: string; label: Localized; value: number }[];
  holdings: {
    symbol: string;
    name: Localized;
    assetClass: AssetClass;
    value: number;
    weight: number;
    changePct: number | null;
    pnl: number | null;
  }[];
  performance: NamedSeries[];
  exposure: { label: Localized; pct: number }[];
  risk: { var95Pct: number | null; volatilityPct: number | null; sharpe: number | null; beta: number | null; maxDrawdownPct: number | null };
}

/* ---------------------------------------------------------------- errors */

export const ERROR_STAGES = ["DETECTED", "TRIAGED", "DIAGNOSING", "RECOVERING", "VERIFYING", "RESOLVED", "ESCALATED"] as const;
export type ErrorStage = (typeof ERROR_STAGES)[number];

export interface ErrorIncident {
  id: string;
  title: Localized;
  component: string;
  errorType: string;
  severity: Severity;
  stage: ErrorStage;
  detectedAt: string;
  updatedAt: string;
  retries: number;
  recovery: Localized;
  owner: string;
}

export interface ErrorsOverview {
  incidents: ErrorIncident[];
  mttrMinutes: number | null;
  trend: SeriesPoint[];
}

/* ---------------------------------------------------------------- system */

export interface ServiceStatus {
  id: string;
  name: Localized;
  kind: "process" | "database" | "edge" | "automation" | "external";
  state: "UP" | "DEGRADED" | "DOWN" | "NOT_CONFIGURED" | "UNKNOWN";
  uptimeSec: number | null;
  version: string | null;
  lastHeartbeat: string | null;
  note?: Localized;
}

export interface SystemOverview {
  mode: "PAPER_ONLY";
  services: ServiceStatus[];
  providers: ProviderHealth[];
  cpu: SeriesPoint[];
  memory: SeriesPoint[];
  latency: SeriesPoint[];
  uptimeSec: number | null;
  build: { version: string; commit: string; builtAt: string };
  laneA: { state: "PASS" | "FAIL" | "UNKNOWN"; checkedAt: string | null };
  evidenceFreshnessSec: number | null;
  classification: string;
}

/* ---------------------------------------------- notifications / alerts */

export interface AppNotification {
  id: string;
  title: Localized;
  body: Localized;
  severity: Severity;
  at: string;
  read: boolean;
  href?: string;
}

export type AlertTier = "INFO" | "WATCH" | "HIGH_ATTENTION" | "SECURITY";

export interface AlertItem {
  id: string;
  tier: AlertTier;
  title: Localized;
  detail: Localized;
  symbol?: string;
  at: string;
  status: DataStatus;
}

/* ------------------------------------------------------------------ chat */

export interface ChatEvidence {
  label: string;
  source: string;
  status: DataStatus;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  at: string;
  intent?: string;
  evidence?: ChatEvidence[];
  uncertainty?: string[];
  followups?: string[];
}

/* ------------------------------------------------------------ governance */

export type AcceptanceState = "PENDING" | "ACCEPTED" | "REJECTED" | "DEFERRED" | "EXPIRED";

export interface GovernanceOverview {
  policyVersion: string;
  constitution: { id: string; title: Localized; summary: Localized }[];
  approvals: { id: string; title: Localized; requestedBy: string; state: AcceptanceState; at: string; scope: string }[];
  audit: { id: string; at: string; actor: string; action: Localized; target: string; hash: string }[];
  boundaries: { surface: Localized; may: Localized; mustNot: Localized }[];
}

/* ---------------------------------------------------------------- memory */

export interface MemoryOverview {
  items: {
    id: string;
    title: Localized;
    kind: "lesson" | "pattern" | "source-trust" | "calibration";
    state: "CANDIDATE" | "PROMOTED" | "REVOKED" | "EXPIRED";
    confidence: Confidence;
    source: string;
    at: string;
  }[];
  learning: NamedSeries[];
  counts: { candidates: number; promoted: number; revoked: number; expired: number };
}

/* --------------------------------------------------------------- reports */

export interface ReportItem {
  id: string;
  title: Localized;
  kind: "daily" | "weekly" | "audit" | "research" | "incident";
  state: "READY" | "GENERATING" | "FAILED" | "SCHEDULED";
  generatedAt: string | null;
  pages: number | null;
  author: string;
  summary: Localized;
}

/* -------------------------------------------------------------- workshop */

export interface WorkshopOverview {
  builds: { id: string; target: string; state: "PASS" | "FAIL" | "RUNNING" | "QUEUED"; durationSec: number | null; at: string; commit: string }[];
  tests: { suite: string; passed: number; failed: number; skipped: number; durationSec: number }[];
  stack: { name: string; version: string; license: string; role: Localized }[];
  issues: { id: string; title: Localized; severity: Severity; state: "OPEN" | "IN_PROGRESS" | "BLOCKED" | "DONE" }[];
}

/* --------------------------------------------------------- digital world */

export interface DigitalWorldOverview {
  graph: {
    nodes: { id: string; name: string; category: "chain" | "protocol" | "stablecoin" | "bridge" | "oracle"; value: number }[];
    links: { source: string; target: string; value: number }[];
  };
  chains: {
    id: string;
    name: string;
    tvl: number | null;
    change7d: number | null;
    tps: number | null;
    fees24h: number | null;
    status: DataStatus;
  }[];
  totals: { tvl: number | null; stablecoinSupply: number | null; dexVolume24h: number | null; activeAddresses: number | null };
  activity: NamedSeries[];
}

/* ------------------------------------------------------------------ earth */

export interface FinancialCenter {
  id: string;
  name: Localized;
  lat: number;
  lng: number;
  timeZone: string;
  exchangeId: string | null;
  indexSymbol: string | null;
  indexChange: number | null;
  /** Visual tier: 1 = primary hub. */
  tier: 1 | 2 | 3;
}

export interface IranIndicator {
  id: string;
  label: Localized;
  value: number | null;
  unit: Localized;
  change: number | null;
  decimals: number;
  status: DataStatus;
  retrievedAt: string | null;
  source: string;
}

export interface EarthOverview {
  centers: FinancialCenter[];
  links: { from: string; to: string }[];
  iran: { indicators: IranIndicator[]; summary: Localized };
}

/* ----------------------------------------------------------------- search */

export interface SearchEntry {
  id: string;
  kind: "instrument" | "token" | "agent" | "news";
  label: string;
  sublabel: Localized;
  href: string;
}
