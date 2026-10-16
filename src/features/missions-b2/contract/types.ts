// AHOS Arena Contract Types
// All snapshot types for the 5 pages

// ============================================================================
// Common Types
// ============================================================================

export type ExecutionMode = "PAPER_ONLY" | "SIMULATED" | "LIVE" | string;
export type Source = string;
export type GeneratedAt = string | null; // ISO 8601 timestamp or null
export type RealTrading = boolean;

// Base snapshot with common fields
export interface BaseSnapshot {
  executionMode: ExecutionMode;
  realTrading: RealTrading;
  source: Source;
  generatedAt: GeneratedAt;
}

// ============================================================================
// Status Enums
// ============================================================================

export type Status = 
  | "LIVE"
  | "STALE" 
  | "UNKNOWN"
  | "DEMO"
  | "CONFLICT"
  | "REJECTED"
  | "UNAVAILABLE"
  | "PARTIAL"
  | "PLANNED"
  | "MISSING"
  | "ERROR";

export type DeliveryState = "SENT" | "NOT_SENT" | "UNKNOWN";
export type BridgeState = "CONNECTED" | "DISCONNECTED" | "UNKNOWN" | "BLOCKED_OWNER";
export type ChannelType = "Kian chat" | "Telegram" | "nightly report" | "command router";
export type Direction = "in" | "out";
export type MessageState = "DELIVERED" | "FAILED" | "PENDING" | "UNKNOWN";

// ============================================================================
// Message Hub Types (M35)
// ============================================================================

export interface ChannelStatus {
  channel: ChannelType;
  status: Status;
  lastMessageTime: string | null;
  queueDepth: number | null;
  lastError: string | null;
}

export interface TelegramStatus {
  bridgeState: BridgeState;
  needsTokenRotation: boolean; // true when BLOCKED_OWNER
  // NEVER include token, chatId, or any secret
}

export interface NightlyReportStatus {
  lastReportTime: string | null;
  language: string; // "فارسی"
  deliveryState: DeliveryState;
  evidenceLink: string | null; // plain text path/URL
}

export interface HumanGateItem {
  id: string;
  title: string;
  requestedByAgent: string;
  age: string; // duration like "2h", "3d"
  state: Status;
}

export interface MessageLogItem {
  time: string;
  direction: Direction;
  channel: ChannelType;
  summary: string; // redacted, <= 120 chars
  deliveryState: MessageState;
}

export interface MessageHubSnapshot extends BaseSnapshot {
  channels: ChannelStatus[];
  telegram: TelegramStatus;
  nightlyReport: NightlyReportStatus;
  humanGateInbox: HumanGateItem[];
  messageLog: MessageLogItem[];
  demo?: boolean;
}

// ============================================================================
// Self Evaluation Types (M58)
// ============================================================================

export type Period = "week" | "month";

export type ReviewState = "REVIEWED" | "PENDING" | "UNKNOWN";
export type OutcomeKnown = "yes" | "no" | "UNKNOWN";

export interface Scorecard {
  period: Period;
  decisionsReviewed: number | null; // null if sample insufficient
  decisionsWithEvidence: number | null;
  decisionsWithUnseenCheck: number | null;
  calibrationNote: string | null; // neutral text
  unresolvedItems: number | null;
  highlights: DecisionHighlight[];
  allDecisions: DecisionDetail[];
}

export interface DecisionHighlight {
  id: string;
  market: string;
  rationaleSummary: string;
  outcomeKnown: OutcomeKnown;
  reviewState: ReviewState;
}

export interface DecisionDetail extends DecisionHighlight {
  // Additional fields for full details
}

export interface SelfEvaluationSnapshot extends BaseSnapshot {
  scorecards: Scorecard[];
  demo?: boolean;
}

// ============================================================================
// Idea Shelf Types (M59)
// ============================================================================

export type IdeaStatus = "PROPOSED" | "ACCEPTED" | "REJECTED";
export type IdeaOrigin = "agent" | "university" | "owner";
export type UnseenTestResult = "PASS" | "FAIL" | "NOT_RUN";

export interface Idea {
  id: string;
  title: string;
  origin: IdeaOrigin;
  status: IdeaStatus;
  reason: string | null; // mandatory for ACCEPTED/REJECTED
  hardwareRequirement: {
    minRAM: string; // e.g., "8 GB"
  } | null;
  flags: string[];
  unseenTest: {
    datasetId: string | null;
    outOfSamplePeriod: string | null;
    sampleSize: number | null;
    result: UnseenTestResult;
  } | null;
}

export interface IdeaShelfSnapshot extends BaseSnapshot {
  ideas: Idea[];
  demo?: boolean;
}

// ============================================================================
// Research Institute Types (M16/M59)
// ============================================================================

export type HypothesisStatus = "UNTESTED" | "TESTED_UNSEEN" | "REJECTED" | "INCONCLUSIVE";
export type HypothesisSource = "university" | "paper" | "agent";

export interface Hypothesis {
  id: string;
  statement: string;
  source: HypothesisSource;
  market: string;
  status: HypothesisStatus;
  inSampleResult: {
    // In-sample results are shown but marked as invalid
    note: string;
  } | null;
  unseenTest: {
    datasetId: string | null;
    period: string | null;
    sampleSize: number | null;
    costModelPresent: boolean | null;
    result: UnseenTestResult;
  } | null;
}

export interface ResearchInstituteSnapshot extends BaseSnapshot {
  hypotheses: Hypothesis[];
  weeklyExam: {
    lastExamTime: string | null;
    itemsExamined: number | null;
    itemsPassedUnseen: number | null; // computed from non-DEMO rows
  } | null;
  demo?: boolean;
}

// ============================================================================
// Mission Map Types
// ============================================================================

export type MissionState = "DONE" | "PARTIAL" | "NOT_STARTED";
export type MissionGroup = "M" | "M-D" | "M-PORT";

export interface Mission {
  id: string;
  title: string;
  group: MissionGroup;
  state: MissionState;
  blockedOwner: boolean; // BLOCKED_OWNER flag
  evidence: string | null; // commit/report path as plain text
  lastUpdate: string | null;
  caveat: string | null; // e.g., "DONE یعنی ماشین‌آلات، نه پذیرش"
  demo?: boolean;
}

export interface MissionMapSnapshot extends BaseSnapshot {
  missions: Mission[];
  summary: {
    doneCount: number;
    partialCount: number;
    notStartedCount: number;
  } | null;
  highlightedMissions: Mission[]; // at most 7
  demo?: boolean;
}

// ============================================================================
// Full Contract Type
// ============================================================================

export interface AHOSArenaContract {
  messageHub: MessageHubSnapshot;
  selfEvaluation: SelfEvaluationSnapshot;
  ideaShelf: IdeaShelfSnapshot;
  researchInstitute: ResearchInstituteSnapshot;
  missionMap: MissionMapSnapshot;
  executionMode: ExecutionMode;
  realTrading: RealTrading;
  source: Source;
  generatedAt: GeneratedAt;
}

// ============================================================================
// Component States (for UI rendering)
// ============================================================================

export type ComponentState = 
  | "LOADING"
  | "EMPTY"
  | "ERROR"
  | "UNKNOWN"
  | "UNAVAILABLE"
  | "STALE"
  | "PARTIAL"
  | "LIVE"
  | "SIMULATED";

// ============================================================================
// Utility Types
// ============================================================================

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
