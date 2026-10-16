/**
 * AHOS Newsroom — data contract (`NewsroomSnapshot`).
 *
 * This module is the single source of truth for the shape of the data the
 * Newsroom screen renders. The mock adapters in `src/mock/newsroom/**` produce
 * exactly this shape; see `README_MERGE.md` for the future mapping onto real
 * endpoints (the mapping must stay loss-free: no field here may be invented by
 * the UI layer).
 */

/* -------------------------------------------------------------------------- */
/* Truth vocabulary                                                            */
/* -------------------------------------------------------------------------- */

/**
 * The six statuses that may be attached to *data* (a source, a story, a feed).
 * Nothing outside this union is ever allowed to describe real-world truth.
 */
export type TruthStatus = 'LIVE' | 'STALE' | 'UNKNOWN' | 'DEMO' | 'CONFLICT' | 'REJECTED';

/**
 * Presentation-only states. These describe a *component* (or a pipeline stage),
 * never the world. They may never be used to upgrade a data status.
 */
export type ComponentState =
  | 'LOADING'
  | 'EMPTY'
  | 'ERROR'
  | 'UNKNOWN'
  | 'UNAVAILABLE'
  | 'STALE'
  | 'PARTIAL'
  | 'LIVE'
  | 'SIMULATED'
  | 'PLANNED'
  | 'MISSING';

export type CredibilityTier = 'A' | 'B' | 'C' | 'UNKNOWN';

export type MarketId = 'OIL' | 'GOLD' | 'CRYPTO' | 'EQUITIES';

export type ClaimStrength = 'STRONG' | 'MODERATE' | 'WEAK' | 'UNKNOWN';

export type PipelineStageId =
  | 'INGEST'
  | 'TRIAGE'
  | 'TWO_SOURCE_CHECK'
  | 'CONFLICT_SCAN'
  | 'JUDGE_HANDOFF';

export type PipelineStageState = 'DONE' | 'CURRENT' | 'PLANNED' | 'UNKNOWN';

/* -------------------------------------------------------------------------- */
/* Markets                                                                     */
/* -------------------------------------------------------------------------- */

export interface MarketFocus {
  id: MarketId;
  labelFa: string;
  labelEn: string;
  /** `true` only for Oil & Gold in the paper-only build. */
  connected: boolean;
  /** When `connected` is false the UI must show «متصل نیست» / PLANNED. */
  status: Extract<TruthStatus, 'LIVE'> | Extract<ComponentState, 'PLANNED'>;
  /** Zero invented headlines for disconnected markets — always 0. */
  storyCount: number | null;
  noteFa: string | null;
}

/* -------------------------------------------------------------------------- */
/* Sources                                                                     */
/* -------------------------------------------------------------------------- */

export interface NewsSource {
  id: string;
  /** Human readable name, e.g. «خبرگزاری الف — وایر انرژی». */
  nameFa: string;
  /**
   * URL shown as *plain text*. The Newsroom never renders it as a link and
   * never fetches it: no outbound calls from this screen.
   */
  urlPlaceholder: string;
  credibility: CredibilityTier;
  status: TruthStatus;
  /** ISO-8601 or `null`. `null` ⇒ UNKNOWN (never a fabricated timestamp). */
  lastReadAt: string | null;
  /**
   * Independence group used by the two-source rule. Two sources in the same
   * group (same wire, syndicated copy, same owner) count as ONE source.
   */
  independenceGroup: string;
  /** Short note explaining the status, e.g. «آخرین خوانش موفق». */
  noteFa: string | null;
}

/* -------------------------------------------------------------------------- */
/* Stories                                                                     */
/* -------------------------------------------------------------------------- */

export interface Story {
  id: string;
  headlineFa: string;
  headlineEn: string | null;
  market: MarketId;
  /** ISO-8601 or `null` ⇒ freshness is UNKNOWN. */
  publishedAt: string | null;
  claimStrength: ClaimStrength;
  /** Ids into `NewsroomSnapshot.sources`. */
  sourceIds: string[];
  marketImpactNoteFa: string | null;
  /** `true` ⇒ the row is fixture data and is excluded from every aggregate. */
  demo: boolean;
  status: TruthStatus;
  /** Set when at least one conflict record references this story. */
  conflictId: string | null;
}

/* -------------------------------------------------------------------------- */
/* Conflicts                                                                   */
/* -------------------------------------------------------------------------- */

export interface ClaimSide {
  sourceId: string;
  claimFa: string;
  /** Free-text value as reported by the source. `null` ⇒ «ناموجود». */
  value: string | null;
  reportedAt: string | null;
}

export interface Conflict {
  id: string;
  storyId: string;
  topicFa: string;
  claimA: ClaimSide;
  claimB: ClaimSide;
  /** Conflicts never auto-clear; the status is a constant. */
  status: Extract<TruthStatus, 'CONFLICT'>;
  detectedAt: string | null;
  noteFa: string | null;
}

/* -------------------------------------------------------------------------- */
/* Reporters                                                                   */
/* -------------------------------------------------------------------------- */

export type ReporterRole = 'wire' | 'macro' | 'energy' | 'metals';

export interface ReporterAgent {
  id: string;
  nameFa: string;
  codeEn: string;
  role: ReporterRole;
  status: TruthStatus;
  lastRunAt: string | null;
  /** Fetch attempts are counters, never fabricated: `null` ⇒ not measured. */
  attempts: number | null;
  pass: number | null;
  fail: number | null;
  noteFa: string | null;
}

/* -------------------------------------------------------------------------- */
/* Pipeline                                                                    */
/* -------------------------------------------------------------------------- */

export interface PipelineStage {
  id: PipelineStageId;
  labelFa: string;
  labelEn: string;
  state: PipelineStageState;
  completedAt: string | null;
  detailFa: string | null;
}

/* -------------------------------------------------------------------------- */
/* Snapshot                                                                    */
/* -------------------------------------------------------------------------- */

export type ExecutionMode = 'PAPER_ONLY' | 'PAPER' | 'LIVE' | 'SHADOW' | 'UNKNOWN';

export interface NewsroomFreshness {
  storiesAt: string | null;
  sourcesAt: string | null;
  conflictsAt: string | null;
  reportersAt: string | null;
}

export interface NewsroomTelemetry {
  /** Id of the primary source read last — shown in the bottom strip. */
  lastSourceId: string | null;
  lastReadAt: string | null;
  storyCount: number;
  demoCount: number;
  conflictCount: number;
  adapter: string;
}

export interface NewsroomSnapshot {
  executionMode: ExecutionMode;
  realTrading: boolean;
  /** ISO-8601 or `null`. The UI treats `null` as UNKNOWN. */
  generatedAt: string | null;
  markets: MarketFocus[];
  stories: Story[];
  sources: NewsSource[];
  conflicts: Conflict[];
  reporters: ReporterAgent[];
  pipeline: PipelineStage[];
  freshness: NewsroomFreshness;
  telemetry: NewsroomTelemetry;
}

/** Component-level load state for the page. */
export type NewsroomLoadState =
  | Extract<ComponentState, 'LOADING'>
  | Extract<ComponentState, 'EMPTY'>
  | Extract<ComponentState, 'ERROR'>
  | Extract<ComponentState, 'UNAVAILABLE'>
  | 'READY';