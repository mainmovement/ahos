/**
 * AHOS Intelligence Command Deck — domain contracts.
 *
 * PAPER-ONLY display model: every value in this application is either
 * genuinely measured by the app itself, an explicitly labeled deterministic
 * sample, or an honest "not measured" absence. Nothing here may impersonate
 * live operational data.
 */

export type I18NText = Readonly<{ fa: string; en: string }>;

/* ------------------------------------------------------------------ */
/* Provenance                                                          */
/* ------------------------------------------------------------------ */

/** Central data provenance status model. */
export type DataStatus =
  | "MEASURED" // genuinely observed by a real, in-process source
  | "SAMPLE" // deterministic demo data — always visible-labeled
  | "NOT_MEASURED" // no measurement exists
  | "NOT_CONNECTED" // a real endpoint exists but is intentionally disconnected
  | "STALE" // measurement exists but is older than its freshness window
  | "QUARANTINED" // excluded from evidence by operator decision
  | "UNVERIFIED" // plausible but not independently verified
  | "UNAVAILABLE" // cannot be provided in this build
  | "EXCLUDED" // window removed from evidence (soak timeline)
  | "UNKNOWN"; // state genuinely unknown — never rendered as PASS/HEALTHY

export type ReasonCode =
  | "sampling_only"
  | "no_measurement"
  | "adapter_disabled"
  | "backend_not_connected"
  | "quarantined_by_operator"
  | "insufficient_evidence"
  | "not_available_in_demo"
  | "stale_beyond_window";

export interface DataProvenance {
  readonly status: DataStatus;
  /** Machine-readable source id, e.g. `sample://ahos-demo/gold/candles`. */
  readonly source: string;
  /** ISO-8601. Only present when the timestamp genuinely belongs to the dataset. */
  readonly observedAt: string | null;
  readonly reason: ReasonCode | null;
  /** 0..1 — only when a meaningful verification state exists. */
  readonly confidence: number | null;
  readonly note?: I18NText;
}

export interface DataEnvelope<T> {
  readonly value: T | null;
  readonly provenance: DataProvenance;
}

/* ------------------------------------------------------------------ */
/* Desks                                                               */
/* ------------------------------------------------------------------ */

export type DeskId =
  | "gold"
  | "oil"
  | "crypto"
  | "onchain"
  | "exchanges"
  | "tokens"
  | "stocks";

export type DeskPriority = "PRIORITY" | "STANDARD";
export type SignalState = "LONG" | "SHORT" | "HOLD" | "UNKNOWN";

/**
 * A raw model score. A score is NOT a probability unless it has been
 * calibrated — see `ProbabilityStatus`.
 */
export interface ModelScore {
  readonly value: number; // 0..1 raw score
  readonly calibrated: false; // this build ships no calibration evidence
}

export interface Desk {
  readonly id: DeskId;
  readonly name: I18NText;
  readonly instruments: readonly string[];
  readonly priority: DeskPriority;
  readonly signal: DataEnvelope<SignalState>;
  readonly score: DataEnvelope<ModelScore>;
  readonly sparkline: DataEnvelope<readonly number[]>;
  readonly lastObservation: DataEnvelope<string>;
  readonly alertCount: DataEnvelope<number>;
}

/* ------------------------------------------------------------------ */
/* Positions & trades                                                  */
/* ------------------------------------------------------------------ */

export type Side = "LONG" | "SHORT";
export type PositionState = "OPEN" | "CLOSED";

/**
 * Accounting identity preserved exactly:
 *   NET = GROSS − FEES + FUNDING
 * Missing fees/funding stay `null` — never silently zero.
 */
export interface PnLBreakdown {
  readonly gross: number;
  readonly fees: number | null;
  readonly funding: number | null;
  readonly net: number | null;
}

export interface Position {
  readonly id: string;
  readonly symbol: string;
  readonly deskId: DeskId;
  readonly side: Side;
  readonly leverage: number | null;
  readonly entry: number;
  readonly mark: number;
  readonly qty: number;
  readonly pnl: PnLBreakdown;
  readonly state: PositionState;
  readonly openedAt: string | null;
  readonly closedAt: string | null;
  readonly provenance: DataProvenance;
}

export interface Trade {
  readonly id: string;
  readonly positionId: string;
  readonly deskId: DeskId;
  readonly symbol: string;
  readonly kind: "ENTRY" | "EXIT" | "ADJUST";
  readonly side: Side;
  readonly price: number;
  readonly qty: number;
  readonly fee: number | null;
  readonly at: string | null;
  readonly provenance: DataProvenance;
}

export interface EquitySnapshot {
  readonly t: string; // ISO date
  readonly equity: number;
  readonly drawdown: number; // ≤ 0, fraction from running peak
}

export interface Signal {
  readonly id: string;
  readonly deskId: DeskId;
  readonly state: SignalState;
  readonly score: DataEnvelope<ModelScore>;
  readonly at: string | null;
  readonly basis: I18NText;
  readonly provenance: DataProvenance;
}

/* ------------------------------------------------------------------ */
/* Intelligence                                                        */
/* ------------------------------------------------------------------ */

export type ImpactLevel = "HIGH" | "MEDIUM" | "LOW";

export type NewsCategory =
  | "geopolitics"
  | "central_banks"
  | "macroeconomics"
  | "whale_activity"
  | "onchain"
  | "exchanges"
  | "regulatory"
  | "commodity_supply";

export interface NewsEvent {
  readonly id: string;
  readonly category: NewsCategory;
  readonly title: I18NText;
  readonly summary: I18NText;
  readonly at: string | null;
  readonly desks: readonly DeskId[];
  readonly impact: ImpactLevel;
  /** Always a fictional sample source label — never a real outlet. */
  readonly sourceLabel: string;
  readonly provenance: DataProvenance;
}

export interface MarketDriver {
  readonly id: string;
  readonly deskId: DeskId;
  readonly name: I18NText;
  readonly direction: "UP" | "DOWN" | "FLAT" | "UNKNOWN";
  readonly weight: DataEnvelope<number>; // −1..1 influence weight
  readonly reading: DataEnvelope<number | null>; // latest reading, if any
  readonly unit: string | null;
  readonly explanation: I18NText;
}

/* ------------------------------------------------------------------ */
/* Health & soak                                                       */
/* ------------------------------------------------------------------ */

export type SoakSegmentKind = "MEASURED" | "GAP" | "EXCLUDED" | "QUARANTINED";

export interface SoakSegment {
  readonly id: string;
  readonly start: string;
  readonly end: string;
  readonly kind: SoakSegmentKind;
  readonly note?: I18NText;
}

export interface SoakStatus {
  readonly windowId: string;
  readonly scope: DeskId | "system";
  readonly start: string;
  readonly end: string | null;
  readonly coverage: DataEnvelope<number>; // percent 0..100
  readonly segments: readonly SoakSegment[];
  readonly provenance: DataProvenance;
}

export interface HealthCheck {
  readonly id: string;
  readonly serviceId: string;
  readonly name: I18NText;
  readonly status: DataStatus;
  readonly latencyMs: DataEnvelope<number>;
  readonly lastRunAt: string | null;
  readonly detail: I18NText;
  readonly provenance: DataProvenance;
}

export interface ServiceRecord {
  readonly id: string;
  readonly name: I18NText;
  readonly role: I18NText;
  readonly endpoint: string | null;
  readonly status: DataStatus;
  readonly pid: DataEnvelope<number>;
  readonly provenance: DataProvenance;
}

/* ------------------------------------------------------------------ */
/* Security & readiness                                                */
/* ------------------------------------------------------------------ */

export interface SecurityCheck {
  readonly id: string;
  readonly name: I18NText;
  readonly status: DataStatus;
}

/** Unknown security state must never render as PASS/SECURE. */
export interface SecurityStatus {
  readonly deskId: DeskId;
  readonly state: "SECURE" | "AT_RISK" | "UNKNOWN" | "NOT_MEASURED";
  readonly checks: readonly SecurityCheck[];
  readonly provenance: DataProvenance;
}

export type ReadinessItemState = "PASS" | "FAIL" | "NOT_MEASURED" | "NOT_VERIFIED";

export interface ReadinessItem {
  readonly id: string;
  readonly title: I18NText;
  readonly requirement: I18NText;
  readonly state: ReadinessItemState;
  /** Evidence only in demonstration mode (sample-labeled). */
  readonly demonstrationState: ReadinessItemState;
  readonly evidence: I18NText | null;
  /** Cannot pass while the backend adapter is disconnected, even in demonstration. */
  readonly hardBlocked: boolean;
}

export type ReadinessVerdict = "NOT_READY" | "NOT_AUTHORIZED";

/* ------------------------------------------------------------------ */
/* System                                                              */
/* ------------------------------------------------------------------ */

export interface SystemSnapshot {
  readonly datasetId: string;
  /** Fixed, clearly-labeled dataset timestamp — never "now". */
  readonly asOf: string;
  readonly services: readonly ServiceRecord[];
  readonly healthChecks: readonly HealthCheck[];
  readonly soak: readonly SoakStatus[];
  readonly notes: readonly I18NText[];
}

export interface AlertItem {
  readonly id: string;
  readonly severity: "INFO" | "WARN" | "CRITICAL";
  readonly title: I18NText;
  readonly body: I18NText;
  readonly at: string | null;
  readonly provenance: DataProvenance;
}

/* ------------------------------------------------------------------ */
/* UI preferences (harmless, local-only)                               */
/* ------------------------------------------------------------------ */

export type ThemeMode = "dark" | "light" | "system";
export type Density = "comfortable" | "compact";
export type MotionPreference = "system" | "reduce" | "no_preference";
export type RefreshInterval = "off" | 30 | 60 | 300;
export type AmbiencePreset = "night" | "dawn" | "day" | "dusk";
export type SeasonPreset = "spring" | "summer" | "autumn" | "winter";
export type SceneView = "room" | "space" | "fpv";
