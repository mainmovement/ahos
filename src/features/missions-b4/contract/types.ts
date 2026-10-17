/**
 * AHOS Arena — shared data contract (batch 3).
 * One snapshot type per page. Rule: unknown ⇒ null (rendered «—»), never fabricated.
 */

/** Execution mode. Anything other than PAPER_ONLY triggers the VIOLATION bar. */
export type ExecutionMode = "PAPER_ONLY" | "SIMULATION" | "LIVE" | "UNKNOWN";

/** Truth status enum (page / chip level). */
export type TruthStatus =
  | "LIVE"
  | "STALE"
  | "UNKNOWN"
  | "DEMO"
  | "CONFLICT"
  | "REJECTED";

/** Component-level display states (every page must support these). */
export type ComponentState =
  | "LOADING"
  | "EMPTY"
  | "ERROR"
  | "UNKNOWN"
  | "UNAVAILABLE"
  | "PARTIAL"
  | "LIVE"
  | "SIMULATED";

/** Anything a status chip may render (truth + component states + planned/missing). */
export type ChipStatus = TruthStatus | ComponentState | "PLANNED" | "MISSING";

/** Fields every snapshot carries. */
export interface SnapshotMeta {
  executionMode: ExecutionMode;
  realTrading: boolean;
  /** Source id, e.g. "DEMO_FIXTURE" or an AHOS endpoint id. unknown ⇒ null. */
  source: string | null;
  /** ISO-8601 timestamp of the snapshot. unknown ⇒ null ⇒ status UNKNOWN. */
  generatedAt: string | null;
  /** True when the whole snapshot is demo data (DEMO chip + ribbon, excluded from counts). */
  demo?: boolean;
}

/* ------------------------------------------------------------------ */
/* (1) science-radar — «رادار علم» (M44)                                */
/* ------------------------------------------------------------------ */

export type RadarSourceType = "paper" | "repo" | "blog" | "university" | "agent";
export type RadarItemStatus = "NEW" | "REVIEWED" | "DISMISSED" | "UNKNOWN";

export interface ScienceRadarItem {
  id: string;
  title: string;
  sourceType: RadarSourceType;
  topic: string;
  /** Date the item was found (ISO-8601). unknown ⇒ null. */
  foundAt: string | null;
  /** Neutral relevance note. Never a claim of correctness. */
  relevanceNote: string | null;
  status: RadarItemStatus;
  /** Plain-text reference to the source. Never rendered as a live link. */
  sourceText: string | null;
  demo: boolean;
}

export interface ScienceRadarSnapshot extends SnapshotMeta {
  kind: "scienceRadar";
  items: ScienceRadarItem[];
}

/* ------------------------------------------------------------------ */
/* (2) self-debug — «خطایابی خودکار» (M46)                             */
/* ------------------------------------------------------------------ */

export type DebugStatus = "OPEN" | "DIAGNOSED" | "CLOSED" | "UNKNOWN";

export interface DebugTimelineEvent {
  time: string | null;
  event: string;
  /** Where this timeline entry came from. unknown ⇒ null. */
  source: string | null;
}

export interface SelfDebugIncident {
  id: string;
  /** ISO-8601. unknown ⇒ null. */
  time: string | null;
  component: string;
  /** Redacted error signature, ≤120 chars, never secrets/usernames. */
  errorSignature: string;
  diagnosisNote: string | null;
  status: DebugStatus;
  /** Evidence path as plain text. Absent ⇒ «بدون شواهد». */
  evidencePath: string | null;
  timeline: DebugTimelineEvent[];
  /** Redacted log excerpt lines, each ≤200 chars. */
  logExcerpt: string[];
  demo: boolean;
}

export interface SelfDebugSnapshot extends SnapshotMeta {
  kind: "selfDebug";
  incidents: SelfDebugIncident[];
}

/* ------------------------------------------------------------------ */
/* (3) weekly-exam — «آزمون هفتگی هوش» (M50)                           */
/* ------------------------------------------------------------------ */

export type ExamState = "SCHEDULED" | "RAN" | "PARTIAL" | "NOT_RUN" | "UNKNOWN";
/** Tri-state answer/evidence flag. */
export type TriState = "yes" | "no" | "UNKNOWN";

export interface WeeklyExamItem {
  id: string;
  topic: string;
  answered: TriState;
  evidence: TriState;
  reviewState: string | null;
  demo: boolean;
}

export interface WeeklyExamRun {
  id: string;
  /** Tehran (Jalali) week label, e.g. "1405-W29". unknown ⇒ null. */
  week: string | null;
  itemsCount: number | null;
  answeredCount: number | null;
  withEvidenceCount: number | null;
  /** Neutral numbers only — never a pass/fail verdict. */
  resultSummary: string | null;
  state: ExamState;
  items: WeeklyExamItem[];
  demo: boolean;
}

export interface WeeklyExamSnapshot extends SnapshotMeta {
  kind: "weeklyExam";
  /** Below this many non-DEMO items a run is rendered as «نمونه ناکافی». */
  minSampleSize: number;
  runs: WeeklyExamRun[];
}

/* ------------------------------------------------------------------ */
/* (4) skill-market — «بازار مهارت و افزونه» (M52)                     */
/* ------------------------------------------------------------------ */

export type SkillKind = "skill" | "plugin";
export type InstallState = "AVAILABLE" | "INSTALLED" | "BLOCKED" | "UNKNOWN";
export type ReviewState = "UNREVIEWED" | "REVIEWED" | "REJECTED";

export interface SkillMarketEntry {
  id: string;
  name: string;
  kind: SkillKind;
  version: string | null;
  source: string | null;
  /** Display only. This page can never install/enable/update/remove anything. */
  installState: InstallState;
  /** Requested permissions as plain text. Neutral list — never "safe". */
  permissions: string[];
  reviewState: ReviewState;
  /** Mandatory for REVIEWED/REJECTED. Missing ⇒ render UNREVIEWED + «دلیل ثبت نشده». */
  reason: string | null;
  demo: boolean;
}

export interface SkillMarketSnapshot extends SnapshotMeta {
  kind: "skillMarket";
  entries: SkillMarketEntry[];
}

/* ------------------------------------------------------------------ */
/* (5) news-center — «مرکز اخبار آرام» (M18.N)                         */
/* ------------------------------------------------------------------ */

export type NewsTopic = "Oil" | "Gold" | "Macro" | "Other";
export type Freshness = "LIVE" | "STALE" | "UNKNOWN";

export interface NewsItem {
  id: string;
  /** ISO-8601. No timestamp ⇒ freshness UNKNOWN. */
  time: string | null;
  sourceName: string | null;
  topic: NewsTopic;
  /** One-line neutral summary, ≤120 chars. */
  summary: string;
  /** Source reliability. null ⇒ «نامشخص». */
  reliability: string | null;
  demo: boolean;
}

export interface NewsCenterSnapshot extends SnapshotMeta {
  kind: "newsCenter";
  /** Minutes after generatedAt at which an item turns STALE. */
  staleAfterMinutes: number;
  items: NewsItem[];
}

/* ------------------------------------------------------------------ */
/* Top-level contract document                                        */
/* ------------------------------------------------------------------ */

export interface AhosArenaContract {
  contractVersion: string;
  executionMode: ExecutionMode;
  realTrading: boolean;
  source: string | null;
  generatedAt: string | null;
  scienceRadar: ScienceRadarSnapshot;
  selfDebug: SelfDebugSnapshot;
  weeklyExam: WeeklyExamSnapshot;
  skillMarket: SkillMarketSnapshot;
  newsCenter: NewsCenterSnapshot;
}

export type AnySnapshot =
  | ScienceRadarSnapshot
  | SelfDebugSnapshot
  | WeeklyExamSnapshot
  | SkillMarketSnapshot
  | NewsCenterSnapshot;
