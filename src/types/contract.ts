/**
 * AHOS — canonical data contract (v1)
 * ===================================
 *
 * What this file is
 * -----------------
 * The single source of truth for every shape the AHOS command-center UI renders.
 * It is deliberately dependency-free: no Zod, no io-ts, no runtime library, no
 * network. Copy `types/contract.ts` into a Next.js 16 / React 19 / TS-strict app
 * and it compiles as-is.
 *
 * The law of this contract
 * ------------------------
 * 1. **Never fabricate.** A value that was not observed does not exist. It is
 *    `null` and its freshness is `"UNKNOWN"`. There is no zero-fill, no
 *    last-known-good masquerading as current, no pretty guess.
 * 2. **Every observed field carries its own provenance.** Numbers, strings,
 *    booleans, arrays and enums that come from the world are wrapped in
 *    `Observed<T>`, which always carries `freshness` + `asOf`.
 * 3. **Paper-only.** `ExecutionMode` has exactly one legal member
 *    (`"PAPER_ONLY"`) and `LiveTradingState` exactly one (`"DISABLED"`). Money
 *    records must extend `MoneyBearing`, which forces a `paperNoticeKey` — the
 *    i18n key of the notice that has to be rendered next to the money.
 * 4. **DEMO is a first-class freshness.** Sample data is not "live-ish"; it is
 *    explicitly `DEMO`, and the UI must show the DEMO chip whenever it renders it.
 *
 * Which fields are `Observed<T>` and which are not
 * ------------------------------------------------
 * *Observed* (carries `freshness` + `asOf` of its own): everything measured,
 * quoted, computed, claimed or reported — prices, volumes, PnL, states, scores,
 * counts, timestamps of real-world events, human-readable observations.
 *
 * *Structural* (no freshness of its own): primary keys, foreign keys, schema
 * version, the `demo` flag, and the i18n notice key. These are not claims about
 * the world; they are how the record is addressed. They are still covered by the
 * record-level `freshness` + `asOf` inherited from `EntityBase`, so no field in
 * this contract is ever rendered without an explicit timestamp behind it.
 *
 * `scripts/validate.mjs` mechanically enforces that split: it parses this file,
 * compares every interface field-by-field against the runtime schema mirror in
 * `scripts/schema.mjs`, and fails if a field's `Observed<>`-ness disagrees.
 */

/* ------------------------------------------------------------------------- *
 * 0. Primitives
 * ------------------------------------------------------------------------- */

/** Version tag stamped on every record and every mock file. */
export const CONTRACT_VERSION = "ahos.contract/1";
export type ContractVersion = typeof CONTRACT_VERSION;

/**
 * ISO-8601 timestamp in UTC, always with an explicit `Z`.
 * Canonical form produced by this pack: `2026-10-15T12:00:00.000Z`.
 * Validated by `isIsoTimestamp()` and by `scripts/validate.mjs`.
 */
export type IsoTimestamp = string;

const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/;

/** True when `s` is a parseable, UTC, ISO-8601 timestamp string. */
export function isIsoTimestamp(s: string): boolean {
  if (!ISO_RE.test(s)) return false;
  const t = Date.parse(s);
  return Number.isFinite(t);
}

/**
 * Freshness of an observed value.
 * - `LIVE`    — observed now, within the staleness budget of its feed.
 * - `STALE`   — really observed, but older than the budget. Shown, never trusted silently.
 * - `UNKNOWN` — not observed. `value` MUST be `null`. Never rendered as a number.
 * - `DEMO`    — synthetic sample data. Never a claim about any real market.
 */
export const FRESHNESS = ["LIVE", "STALE", "UNKNOWN", "DEMO"] as const;
export type Freshness = (typeof FRESHNESS)[number];

/** Freshness values plus the paper-trading marker used by status chips. */
export const CHIP_KINDS = ["LIVE", "STALE", "UNKNOWN", "DEMO", "PAPER"] as const;
export type ChipKind = (typeof CHIP_KINDS)[number];

/** The only execution mode this build may run in. Real money is not reachable. */
export const EXECUTION_MODES = ["PAPER_ONLY"] as const;
export type ExecutionMode = (typeof EXECUTION_MODES)[number];

/** The only state live trading may be in. */
export const LIVE_TRADING_STATES = ["DISABLED"] as const;
export type LiveTradingState = (typeof LIVE_TRADING_STATES)[number];

/** Data honesty policy identifier, surfaced in Settings and in the health panel. */
export const DATA_PRINCIPLES = ["UNKNOWN_OVER_FABRICATED"] as const;
export type DataPrinciple = (typeof DATA_PRINCIPLES)[number];

/** Unit of a money/number field. `_PAPER` units are simulation accounting only. */
export const MONEY_UNITS = ["USDT_PAPER", "USD_PAPER", "PERCENT", "BPS", "COUNT", "NONE"] as const;
export type MoneyUnit = (typeof MONEY_UNITS)[number];

/** A bilingual human-readable string carried by data (not by the UI dictionary). */
export interface LocalizedText {
  fa: string;
  en: string;
}

/** Where an observation came from. Never a URL in this pack: no network calls. */
export interface ObservedSource {
  provider: string;
  feed: string;
  transport: string;
}

/**
 * The freshness envelope. Every observed field in this contract is one of these.
 *
 * Invariants (enforced by `scripts/validate.mjs` and by the constructors below):
 * - `freshness === "UNKNOWN"` ⟺ `value === null`
 * - `asOf` is a valid UTC ISO-8601 timestamp and never in the future
 * - `freshness === "LIVE"` requires a real observation: it is forbidden in mock data
 */
export interface Observed<T> {
  value: T | null;
  freshness: Freshness;
  asOf: IsoTimestamp;
  source?: ObservedSource;
  note?: string;
}

/** Type guard: is this a well-formed freshness envelope? (Shallow, runtime-safe.) */
export function isObserved(x: unknown): x is Observed<unknown> {
  if (typeof x !== "object" || x === null) return false;
  const o = x as Record<string, unknown>;
  if (typeof o["freshness"] !== "string") return false;
  if (!(FRESHNESS as readonly string[]).includes(o["freshness"])) return false;
  if (typeof o["asOf"] !== "string" || !isIsoTimestamp(o["asOf"])) return false;
  return "value" in o;
}

/** Type guard narrowing an envelope to one that actually holds a value. */
export function hasValue<T>(o: Observed<T>): o is Observed<T> & { value: T } {
  return o.value !== null && o.freshness !== "UNKNOWN";
}

/** Construct an UNKNOWN observation. There is no way to give it a value. */
export function unknownOf<T>(asOf: IsoTimestamp, note?: string): Observed<T> {
  const obs: Observed<T> = { value: null, freshness: "UNKNOWN", asOf };
  if (note !== undefined) obs.note = note;
  return obs;
}

/** Construct a DEMO observation (sample data). */
export function demoOf<T>(value: T, asOf: IsoTimestamp, note?: string): Observed<T> {
  const obs: Observed<T> = { value, freshness: "DEMO", asOf };
  if (note !== undefined) obs.note = note;
  return obs;
}

/** Construct a LIVE observation. Requires value, timestamp and source. */
export function liveOf<T>(value: T, asOf: IsoTimestamp, source: ObservedSource): Observed<T> {
  return { value, freshness: "LIVE", asOf, source };
}

/** Construct a STALE observation: real, but out of its freshness budget. */
export function staleOf<T>(value: T, asOf: IsoTimestamp, source?: ObservedSource): Observed<T> {
  const obs: Observed<T> = { value, freshness: "STALE", asOf };
  if (source !== undefined) obs.source = source;
  return obs;
}

/* ------------------------------------------------------------------------- *
 * 1. Record envelopes
 * ------------------------------------------------------------------------- */

/**
 * Fields every entity carries. `freshness`/`asOf` here are the record-level
 * rollup (worst freshness among the record's observed fields), which is what the
 * table row chip and the "as of" column render.
 */
export interface EntityBase {
  id: string;
  schemaVersion: ContractVersion;
  freshness: Freshness;
  asOf: IsoTimestamp;
  demo: boolean;
}

/**
 * Marker for any record that surfaces money. Extending it is what forces the
 * paper-only notice key to exist — the type system, not a code review, keeps the
 * notice from being forgotten on a new money panel.
 */
export interface MoneyBearing {
  paperNoticeKey: string;
  moneyUnit: MoneyUnit;
}

/** Header stamped on every file in `mock/`. */
export interface FileContract extends MoneyBearing {
  schemaVersion: ContractVersion;
  file: string;
  entity: string;
  mode: ExecutionMode;
  liveTrading: LiveTradingState;
  dataPrinciple: DataPrinciple;
  demo: boolean;
  freshness: Freshness;
  asOf: IsoTimestamp;
  generatedAt: IsoTimestamp;
  generator: string;
  seed: number;
  count: number;
  demoNotice: LocalizedText;
}

/** Shape of every `mock/*.json` collection file. */
export interface MockFile<T> {
  contract: FileContract;
  items: T[];
}

/** Shape of `mock/equity-curve.json` and `mock/risk-state.json` (single-record files). */
export interface MockRecord<T> {
  contract: FileContract;
  record: T;
}

/* ------------------------------------------------------------------------- *
 * 2. Markets & quotes
 * ------------------------------------------------------------------------- */

export const ASSET_CLASSES = ["CRYPTO", "FOREX", "INDEX", "METAL", "COMMODITY"] as const;
export type AssetClass = (typeof ASSET_CLASSES)[number];

export const VENUE_KINDS = ["CEX", "DEX", "OTC", "SYNTHETIC_FEED"] as const;
export type VenueKind = (typeof VENUE_KINDS)[number];

export const MARKET_STATES = ["OPEN", "CLOSED", "HALTED", "AUCTION", "UNKNOWN"] as const;
export type MarketState = (typeof MARKET_STATES)[number];

export const QUOTE_STATUSES = ["OK", "THIN", "NO_PRICE", "NO_LIQUIDITY", "HALTED", "UNKNOWN"] as const;
export type QuoteStatus = (typeof QUOTE_STATUSES)[number];

/** A single priced observation of a market. Every field is `Observed`. */
export interface Quote extends EntityBase {
  marketId: string;
  status: Observed<QuoteStatus>;
  bid: Observed<number>;
  ask: Observed<number>;
  last: Observed<number>;
  mid: Observed<number>;
  change24hPct: Observed<number>;
  high24h: Observed<number>;
  low24h: Observed<number>;
  volume24hQuote: Observed<number>;
  liquidityUsd: Observed<number>;
  spreadBps: Observed<number>;
  bestBidDepthUsd: Observed<number>;
  priceImpactBps: Observed<number>;
  tickSize: Observed<number>;
  observedAt: Observed<IsoTimestamp>;
}

/** A tradable (in paper) instrument plus its latest quote. */
export interface Market extends EntityBase, MoneyBearing {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  label: Observed<LocalizedText>;
  assetClass: Observed<AssetClass>;
  venue: Observed<VenueKind>;
  venueName: Observed<string>;
  marketState: Observed<MarketState>;
  tradableInPaper: Observed<boolean>;
  sessionTimezone: Observed<string>;
  minNotionalUsd: Observed<number>;
  demoGridStep: Observed<number>;
  quote: Quote;
}

/* ------------------------------------------------------------------------- *
 * 3. Signals
 * ------------------------------------------------------------------------- */

export const SIGNAL_SIDES = ["LONG", "SHORT", "FLAT"] as const;
export type SignalSide = (typeof SIGNAL_SIDES)[number];

export const SIGNAL_ACTIONS = ["ENTER", "ADD", "TRIM", "EXIT", "HOLD", "NO_TRADE", "ABSTAIN"] as const;
export type SignalAction = (typeof SIGNAL_ACTIONS)[number];

export const SIGNAL_STATES = ["NEW", "ACKNOWLEDGED", "ACTED_ON", "EXPIRED", "REJECTED", "INVALIDATED"] as const;
export type SignalState = (typeof SIGNAL_STATES)[number];

/** Mirrors the repo's `CONFIDENCE` union: UNKNOWN is a legal answer. */
export const CONVICTIONS = ["HIGH", "MED", "LOW", "UNKNOWN"] as const;
export type Conviction = (typeof CONVICTIONS)[number];

/** Mirrors the repo's `DECISIONS` union used by the expert council. */
export const COUNCIL_DECISIONS = [
  "WATCH",
  "REJECT",
  "ABSTAIN",
  "PAPER_CANDIDATE",
  "INSUFFICIENT_EVIDENCE",
  "UNKNOWN",
] as const;
export type CouncilDecision = (typeof COUNCIL_DECISIONS)[number];

export const SIGNAL_STRENGTHS = ["STRONG", "MODERATE", "WEAK", "UNKNOWN"] as const;
export type SignalStrength = (typeof SIGNAL_STRENGTHS)[number];

/** One analyst/council output. Prices are references, not orders. */
export interface Signal extends EntityBase, MoneyBearing {
  marketId: string;
  symbol: string;
  departmentId: string;
  agentId: string;
  side: Observed<SignalSide>;
  action: Observed<SignalAction>;
  state: Observed<SignalState>;
  conviction: Observed<Conviction>;
  strength: Observed<SignalStrength>;
  councilDecision: Observed<CouncilDecision>;
  score: Observed<number>;
  scoreBreakdown: Observed<Record<string, number>>;
  horizonMinutes: Observed<number>;
  entryRef: Observed<number>;
  stopRef: Observed<number>;
  targetRef: Observed<number>;
  invalidationRef: Observed<number>;
  suggestedNotionalUsd: Observed<number>;
  rationale: Observed<LocalizedText>;
  evidenceRefs: Observed<string[]>;
  riskFlags: Observed<string[]>;
  dissentCount: Observed<number>;
  emittedAt: Observed<IsoTimestamp>;
  expiresAt: Observed<IsoTimestamp>;
}

/* ------------------------------------------------------------------------- *
 * 4. Paper trading
 * ------------------------------------------------------------------------- */

export const POSITION_SIDES = ["LONG", "SHORT"] as const;
export type PositionSide = (typeof POSITION_SIDES)[number];

export const POSITION_STATES = ["OPEN", "CLOSED", "TRAPPED", "INVALIDATED"] as const;
export type PositionState = (typeof POSITION_STATES)[number];

/** From `paper_trading/schema_v3.sql` — honesty about whether an exit is possible. */
export const EXITABILITIES = [
  "EXECUTABLE_FULL",
  "EXECUTABLE_PARTIAL",
  "UNEXITABLE_HONEYPOT",
  "UNEXITABLE_NO_PRICE",
  "UNEXITABLE_NO_LIQUIDITY",
  "SECURITY_RECHECK_CRITICAL",
  "UNKNOWN",
] as const;
export type Exitability = (typeof EXITABILITIES)[number];

export const LIQUIDITY_RISKS = ["OK", "THIN", "COLLAPSED", "UNKNOWN"] as const;
export type LiquidityRisk = (typeof LIQUIDITY_RISKS)[number];

export const MOMENTUM_CLASSES = ["IMPROVING", "FLAT", "DETERIORATING", "UNKNOWN"] as const;
export type MomentumClass = (typeof MOMENTUM_CLASSES)[number];

/**
 * A paper position.
 *
 * `displayedValueUsd` (qty × mark) and `realizableValueUsd` (what could actually
 * be recovered after slippage, fee, tax and gas) are always both present, because
 * showing only the first one is how paper dashboards lie to their operator.
 */
export interface PaperPosition extends EntityBase, MoneyBearing {
  marketId: string;
  symbol: string;
  side: Observed<PositionSide>;
  state: Observed<PositionState>;
  qty: Observed<number>;
  entryPrice: Observed<number>;
  markPrice: Observed<number>;
  displayedValueUsd: Observed<number>;
  realizableValueUsd: Observed<number>;
  allocatedNotionalUsd: Observed<number>;
  unrealizedPnlUsd: Observed<number>;
  unrealizedPnlPct: Observed<number>;
  realizedPnlUsd: Observed<number>;
  exitCostUsd: Observed<number>;
  stopLoss: Observed<number>;
  takeProfit: Observed<number>;
  trailingStopPct: Observed<number>;
  leverage: Observed<number>;
  exitability: Observed<Exitability>;
  liquidityRisk: Observed<LiquidityRisk>;
  momentumClass: Observed<MomentumClass>;
  holdMinutes: Observed<number>;
  timeStopAt: Observed<IsoTimestamp>;
  openedAt: Observed<IsoTimestamp>;
  closedAt: Observed<IsoTimestamp>;
  signalId: Observed<string>;
  ruleVersion: Observed<string>;
}

export const ORDER_SIDES = ["BUY", "SELL"] as const;
export type OrderSide = (typeof ORDER_SIDES)[number];

export const ORDER_TYPES = ["MARKET", "LIMIT", "STOP_LOSS", "TAKE_PROFIT", "TRAILING_STOP"] as const;
export type OrderType = (typeof ORDER_TYPES)[number];

export const ORDER_STATES = [
  "PENDING",
  "FILLED",
  "PARTIALLY_FILLED",
  "CANCELLED",
  "REJECTED",
  "EXPIRED",
] as const;
export type OrderState = (typeof ORDER_STATES)[number];

/** There is exactly one venue: the simulator. No broker, no exchange, no key. */
export const ORDER_VENUES = ["PAPER_SIMULATOR"] as const;
export type OrderVenue = (typeof ORDER_VENUES)[number];

export const EXIT_REASONS = [
  "TAKE_PROFIT",
  "STOP_LOSS",
  "TIME_EXIT",
  "EXIT_RISK",
  "SECURITY_EVENT",
  "LIQUIDITY_COLLAPSE",
  "TRAPPED",
  "TOTAL_LOSS",
  "MANUAL",
  "NONE",
  "UNKNOWN",
] as const;
export type ExitReason = (typeof EXIT_REASONS)[number];

/** A paper order. `executionMode` is a single-member union on purpose. */
export interface PaperOrder extends EntityBase, MoneyBearing {
  positionId: string;
  marketId: string;
  symbol: string;
  executionMode: Observed<ExecutionMode>;
  venue: Observed<OrderVenue>;
  side: Observed<OrderSide>;
  type: Observed<OrderType>;
  state: Observed<OrderState>;
  qtyRequested: Observed<number>;
  qtyFilled: Observed<number>;
  limitPrice: Observed<number>;
  fillPrice: Observed<number>;
  requestedNotionalUsd: Observed<number>;
  executableNotionalUsd: Observed<number>;
  feeUsd: Observed<number>;
  slippageBps: Observed<number>;
  gasCostUsd: Observed<number>;
  netProceedsUsd: Observed<number>;
  realizedPnlUsd: Observed<number>;
  exitReason: Observed<ExitReason>;
  rejectReason: Observed<string>;
  ruleVersion: Observed<string>;
  submittedAt: Observed<IsoTimestamp>;
  filledAt: Observed<IsoTimestamp>;
}

/* ------------------------------------------------------------------------- *
 * 5. Organization: departments & agents
 * ------------------------------------------------------------------------- */

export const DEPARTMENT_HEALTHS = ["OK", "DEGRADED", "BLOCKED", "UNKNOWN"] as const;
export type DepartmentHealth = (typeof DEPARTMENT_HEALTHS)[number];

export const ESCALATION_LEVELS = [0, 1, 2, 3] as const;
export type EscalationLevel = (typeof ESCALATION_LEVELS)[number];

/** One of the 12 departments of the AHOS org chart. */
export interface Department extends EntityBase, MoneyBearing {
  code: string;
  order: number;
  name: Observed<LocalizedText>;
  mission: Observed<LocalizedText>;
  health: Observed<DepartmentHealth>;
  ownerAgentId: Observed<string>;
  agentIds: Observed<string[]>;
  agentCount: Observed<number>;
  activeAgentCount: Observed<number>;
  allocatedNotionalUsd: Observed<number>;
  throughputPerDay: Observed<number>;
  queueDepth: Observed<number>;
  openIssues: Observed<number>;
  escalationLevel: Observed<EscalationLevel>;
  lastOutputAt: Observed<IsoTimestamp>;
  cycleMinutes: Observed<number>;
}

export const AGENT_RUN_STATES = [
  "IDLE",
  "RUNNING",
  "WAITING_GATE",
  "BLOCKED",
  "DEGRADED",
  "STOPPED",
  "UNKNOWN",
] as const;
export type AgentRunState = (typeof AGENT_RUN_STATES)[number];

export const AGENT_RESULTS = ["OK", "WARN", "ERROR", "NO_DATA", "UNKNOWN"] as const;
export type AgentResult = (typeof AGENT_RESULTS)[number];

/** Runtime status of one logical agent. Agents are logical, not processes. */
export interface AgentStatus extends EntityBase {
  departmentId: string;
  role: Observed<LocalizedText>;
  runState: Observed<AgentRunState>;
  enabled: Observed<boolean>;
  lastResult: Observed<AgentResult>;
  lastRunAt: Observed<IsoTimestamp>;
  nextRunAt: Observed<IsoTimestamp>;
  cycleMs: Observed<number>;
  latencyMs: Observed<number>;
  consecutiveErrors: Observed<number>;
  queueDepth: Observed<number>;
  cyclesCompleted: Observed<number>;
  allowedCapabilities: Observed<string[]>;
  prohibitedCapabilities: Observed<string[]>;
  humanGateRequired: Observed<boolean>;
  canTouchRealMoney: Observed<boolean>;
  statusMessage: Observed<LocalizedText>;
}

/* ------------------------------------------------------------------------- *
 * 6. Risk, circuit breakers and the kill switch
 * ------------------------------------------------------------------------- */

export const RISK_LEVELS = ["GREEN", "AMBER", "RED", "HALTED", "UNKNOWN"] as const;
export type RiskLevel = (typeof RISK_LEVELS)[number];

export const BREAKER_STATES = ["ARMED", "TRIGGERED", "COOLDOWN", "DISABLED", "UNKNOWN"] as const;
export type BreakerState = (typeof BREAKER_STATES)[number];

/** One numeric limit and how much of it is currently used. */
export interface RiskLimit extends EntityBase {
  label: Observed<LocalizedText>;
  unit: Observed<MoneyUnit>;
  current: Observed<number>;
  limit: Observed<number>;
  utilizationPct: Observed<number>;
  breached: Observed<boolean>;
  warnAtPct: Observed<number>;
}

/** One circuit breaker (daily loss, drawdown, exposure, error rate, clock skew…). */
export interface CircuitBreaker extends EntityBase {
  label: Observed<LocalizedText>;
  state: Observed<BreakerState>;
  threshold: Observed<number>;
  observed: Observed<number>;
  unit: Observed<MoneyUnit>;
  triggeredAt: Observed<IsoTimestamp>;
  cooldownEndsAt: Observed<IsoTimestamp>;
  autoReset: Observed<boolean>;
}

/** Aggregate risk posture of the paper book. */
export interface RiskState extends EntityBase, MoneyBearing {
  level: Observed<RiskLevel>;
  mode: Observed<ExecutionMode>;
  liveTrading: Observed<LiveTradingState>;
  equityUsd: Observed<number>;
  cashUsd: Observed<number>;
  exposureUsd: Observed<number>;
  exposurePct: Observed<number>;
  dailyPnlUsd: Observed<number>;
  dailyPnlPct: Observed<number>;
  dailyLossUsd: Observed<number>;
  maxDrawdownPct: Observed<number>;
  openPositions: Observed<number>;
  maxOpenPositions: Observed<number>;
  largestPositionPct: Observed<number>;
  concentrationTop3Pct: Observed<number>;
  pendingOrders: Observed<number>;
  limits: Observed<RiskLimit[]>;
  breakers: Observed<CircuitBreaker[]>;
  haltReasons: Observed<string[]>;
  riskNotes: Observed<LocalizedText>;
  evaluatedAt: Observed<IsoTimestamp>;
  evaluationRuleVersion: Observed<string>;
}

export const KILL_SWITCH_PHASES = ["ARMED", "ENGAGED", "COOLDOWN", "LOCKED", "UNKNOWN"] as const;
export type KillSwitchPhase = (typeof KILL_SWITCH_PHASES)[number];

export const KILL_SWITCH_SCOPES = [
  "DATA_INGEST",
  "SIGNAL_INTAKE",
  "ORDER_SUBMISSION",
  "AUTO_EXIT",
  "ALERTS",
  "REPORTING",
] as const;
export type KillSwitchScope = (typeof KILL_SWITCH_SCOPES)[number];

/**
 * The kill switch. `confirmPhrase` is the exact string the operator must type in
 * the confirmation dialog; the dialog copy lives in `i18n/fa.json` under
 * `dialogs.killSwitchEngage`.
 */
export interface KillSwitchState extends EntityBase {
  engaged: Observed<boolean>;
  phase: Observed<KillSwitchPhase>;
  reasonCode: Observed<string>;
  reasonText: Observed<LocalizedText>;
  scope: Observed<KillSwitchScope[]>;
  engagedAt: Observed<IsoTimestamp>;
  engagedBy: Observed<string>;
  resetAt: Observed<IsoTimestamp>;
  resetBy: Observed<string>;
  requiresHumanReset: Observed<boolean>;
  cooldownEndsAt: Observed<IsoTimestamp>;
  confirmPhrase: Observed<string>;
  auditTrailRef: Observed<string>;
  lastDrillAt: Observed<IsoTimestamp>;
  drillResult: Observed<AgentResult>;
  openPositionsAtEngage: Observed<number>;
}

/* ------------------------------------------------------------------------- *
 * 7. Logs
 * ------------------------------------------------------------------------- */

export const LOG_LEVELS = ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL", "AUDIT"] as const;
export type LogLevel = (typeof LOG_LEVELS)[number];

/** One append-only log line. Secrets are redacted before they ever reach here. */
export interface LogEntry extends EntityBase {
  seq: number;
  at: IsoTimestamp;
  level: Observed<LogLevel>;
  departmentId: Observed<string>;
  agentId: Observed<string>;
  event: Observed<string>;
  message: Observed<LocalizedText>;
  marketId: Observed<string>;
  positionId: Observed<string>;
  durationMs: Observed<number>;
  traceId: Observed<string>;
  dataFreshness: Observed<Freshness>;
  redacted: Observed<boolean>;
}

/* ------------------------------------------------------------------------- *
 * 8. System health
 * ------------------------------------------------------------------------- */

export const HEALTH_STATES = ["UP", "DEGRADED", "DOWN", "UNKNOWN"] as const;
export type HealthState = (typeof HEALTH_STATES)[number];

/** Superset of the repo's `PROVIDER_HEALTH_STATUSES`: NO_KEY and COST_BLOCKED are honest answers. */
export const PROVIDER_STATUSES = [
  "LIVE",
  "DEGRADED",
  "TIMEOUT",
  "RATE_LIMITED",
  "NO_KEY",
  "AUTH_FAILED",
  "NETWORK_UNAVAILABLE",
  "SOURCE_UNAVAILABLE",
  "OUT_OF_POLICY",
  "COST_BLOCKED",
  "UNKNOWN",
] as const;
export type ProviderHealthStatus = (typeof PROVIDER_STATUSES)[number];

/** An internal component (cycle runner, store, projector, web API…). */
export interface ComponentHealth extends EntityBase {
  label: Observed<LocalizedText>;
  state: Observed<HealthState>;
  latencyMs: Observed<number>;
  uptimePct: Observed<number>;
  version: Observed<string>;
  lastCheckAt: Observed<IsoTimestamp>;
  restartCount: Observed<number>;
}

/** An external data source. Blocked sources stay visible with their real reason. */
export interface ProviderHealth extends EntityBase {
  label: Observed<LocalizedText>;
  status: Observed<ProviderHealthStatus>;
  latencyMs: Observed<number>;
  lastOkAt: Observed<IsoTimestamp>;
  itemCount: Observed<number>;
  costBlocked: Observed<boolean>;
  keyRequired: Observed<boolean>;
  statusMessage: Observed<LocalizedText>;
}

/** Whole-system health, shown in the header and on the Settings page. */
export interface SystemHealth extends EntityBase {
  overall: Observed<HealthState>;
  mode: Observed<ExecutionMode>;
  liveTrading: Observed<LiveTradingState>;
  dataPrinciple: Observed<DataPrinciple>;
  version: Observed<string>;
  commit: Observed<string>;
  startedAt: Observed<IsoTimestamp>;
  uptimeSeconds: Observed<number>;
  cycleMs: Observed<number>;
  cyclesCompleted: Observed<number>;
  cyclesFailed: Observed<number>;
  clockSkewMs: Observed<number>;
  queueDepth: Observed<number>;
  errorBudgetRemainingPct: Observed<number>;
  diskFreeMb: Observed<number>;
  components: Observed<ComponentHealth[]>;
  providers: Observed<ProviderHealth[]>;
}

/* ------------------------------------------------------------------------- *
 * 9. Equity curve (7 days)
 * ------------------------------------------------------------------------- */

/** One point of the paper equity curve. */
export interface EquityPoint extends EntityBase, MoneyBearing {
  bucketStart: IsoTimestamp;
  equityUsd: Observed<number>;
  cashUsd: Observed<number>;
  exposureUsd: Observed<number>;
  realizedPnlUsd: Observed<number>;
  unrealizedPnlUsd: Observed<number>;
  drawdownPct: Observed<number>;
  openPositions: Observed<number>;
  cyclesRun: Observed<number>;
  sampled: Observed<boolean>;
}

/** One calendar day (Jalali-aware in the UI, UTC in the data) of the curve. */
export interface DailyEquity extends EntityBase, MoneyBearing {
  day: string;
  jalaliDay: Observed<string>;
  openEquityUsd: Observed<number>;
  closeEquityUsd: Observed<number>;
  highEquityUsd: Observed<number>;
  lowEquityUsd: Observed<number>;
  pnlUsd: Observed<number>;
  pnlPct: Observed<number>;
  realizedPnlUsd: Observed<number>;
  volumeUsd: Observed<number>;
  tradesClosed: Observed<number>;
  hoursObserved: Observed<number>;
  complete: Observed<boolean>;
}

/** The curve itself. `intervalMinutes` is 60 for the 7-day view. */
export interface EquityCurve extends EntityBase, MoneyBearing {
  intervalMinutes: Observed<number>;
  rangeFrom: Observed<IsoTimestamp>;
  rangeTo: Observed<IsoTimestamp>;
  startEquityUsd: Observed<number>;
  endEquityUsd: Observed<number>;
  peakEquityUsd: Observed<number>;
  maxDrawdownPct: Observed<number>;
  points: Observed<EquityPoint[]>;
  daily: Observed<DailyEquity[]>;
  gaps: Observed<number>;
}

/* ------------------------------------------------------------------------- *
 * 10. Operator desk (human gate)
 * ------------------------------------------------------------------------- */

export const TASK_STATES = ["PENDING", "APPROVED", "REJECTED", "EXPIRED", "UNKNOWN"] as const;
export type TaskState = (typeof TASK_STATES)[number];

export const TASK_KINDS = [
  "KILL_SWITCH_RESET",
  "POSITION_CLOSE",
  "LIMIT_RAISE",
  "AGENT_ENABLE",
  "DEPLOY_APPROVAL",
  "DATA_SOURCE_ENABLE",
  "UNKNOWN",
] as const;
export type TaskKind = (typeof TASK_KINDS)[number];

/** One item waiting for the human operator. Nothing here can move real money. */
export interface OperatorTask extends EntityBase, MoneyBearing {
  kind: Observed<TaskKind>;
  state: Observed<TaskState>;
  title: Observed<LocalizedText>;
  detail: Observed<LocalizedText>;
  requestedBy: Observed<string>;
  departmentId: Observed<string>;
  amountUsd: Observed<number>;
  riskLevel: Observed<RiskLevel>;
  createdAt: Observed<IsoTimestamp>;
  expiresAt: Observed<IsoTimestamp>;
  decidedAt: Observed<IsoTimestamp>;
  decidedBy: Observed<string>;
  requiresPhrase: Observed<boolean>;
  confirmPhrase: Observed<string>;
  auditTrailRef: Observed<string>;
}

/** Operator desk: who is on shift, and what the desk is allowed to do. */
export interface OperatorSession extends EntityBase {
  operatorId: Observed<string>;
  displayName: Observed<string>;
  role: Observed<LocalizedText>;
  onShift: Observed<boolean>;
  shiftStartedAt: Observed<IsoTimestamp>;
  authorityLevel: Observed<EscalationLevel>;
  canEngageKillSwitch: Observed<boolean>;
  canResetKillSwitch: Observed<boolean>;
  canMoveRealMoney: Observed<boolean>;
  secondFactorVerified: Observed<boolean>;
  tasks: Observed<OperatorTask[]>;
  pendingCount: Observed<number>;
  lastActionAt: Observed<IsoTimestamp>;
  lastActionText: Observed<LocalizedText>;
}

/* ------------------------------------------------------------------------- *
 * 11. Convenience rollups used by the UI
 * ------------------------------------------------------------------------- */

/** Everything the Overview page needs in one payload. */
export interface OverviewSnapshot extends EntityBase, MoneyBearing {
  health: Observed<SystemHealth>;
  risk: Observed<RiskState>;
  killSwitch: Observed<KillSwitchState>;
  equity: Observed<EquityCurve>;
  departments: Observed<Department[]>;
  topSignals: Observed<Signal[]>;
  openPositions: Observed<PaperPosition[]>;
  watchlist: Observed<Market[]>;
  recentLogs: Observed<LogEntry[]>;
}
