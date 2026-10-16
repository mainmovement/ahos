import type { TruthStatus } from "@/src/features/white-hats/truth/status";

/* ─────────────────────────────────────────────────────────────────────────
   WhiteHatsSnapshot — the typed data contract for the White Hats & Judge
   screen. Mocked today; documented mapping to real endpoints lives in
   README_MERGE.md. Null semantics: null/[] ⇒ UNKNOWN / «—» / «ناموجود» —
   never a fake zero, never a fake timestamp.
   ───────────────────────────────────────────────────────────────────────── */

/** The only acceptable production value is "PAPER_ONLY". */
export type ExecutionMode = "PAPER_ONLY" | "LIVE" | "SIMULATION";

/** Judge verdict for a challenged decision. No result ⇒ "UNKNOWN" (grey). */
export type Verdict = "CLEAN" | "FINDING" | "BLOCKED" | "UNKNOWN";

export type BreakerState = "ARMED" | "TRIPPED" | "UNKNOWN";

export type FindingSeverity = "INFO" | "MINOR" | "MAJOR" | "CRITICAL";
export type FindingStatus = "OPEN" | "RESOLVED";

/** Canary result: the deliberate cheat MUST FAIL. "PASS" ⇒ canary is blind. */
export type CanaryResult = "FAIL" | "PASS" | "UNKNOWN";

export type InspectorKind =
  | "data-sanity"
  | "leak-canary"
  | "cost-model"
  | "two-source-price"
  | "risk-limit"
  | "paper-invariant";

export type TimelineKind =
  | "proposer"
  | "reporter"
  | "council"
  | "judge"
  | "verdict";

export interface Decision {
  id: string;
  market: string;
  proposerAgent: string;
  /** ISO-8601; null ⇒ UNKNOWN (no timestamp may ever be invented). */
  proposedAt: string | null;
  verdict: Verdict;
  reasons: string[];
  evidenceId: string | null;
  /** false ⇒ row shows «غیرمجاز» and is never paper-executable. */
  paperAllowed: boolean;
  freshness: TruthStatus;
  demo?: boolean;
}

export interface Inspector {
  id: string;
  kind: InspectorKind;
  title: string;
  status: TruthStatus;
  lastRunAt: string | null;
  passes: number;
  failures: number;
  note?: string;
  demo?: boolean;
}

export interface BreakerLimit {
  key: string;
  label: string;
  unit: string;
  current: number;
  limit: number;
}

export interface Breaker {
  state: BreakerState;
  updatedAt: string | null;
  /** Neutral numbers with a thin bar — deliberately no green/red. */
  limits: BreakerLimit[];
  demo?: boolean;
}

export interface Finding {
  id: string;
  severity: FindingSeverity;
  inspectorId: string;
  market: string | null;
  status: FindingStatus;
  openedAt: string | null;
  ruleText: string;
  evidenceId: string | null;
  /** What would change the verdict if this finding were resolved. */
  verdictImpact: string;
  decisionId: string | null;
  demo?: boolean;
}

export interface EvidenceDoc {
  id: string;
  kind: string;
  hash: string;
  capturedAt: string | null;
  sourceId: string;
  excerpt: string;
  demo?: boolean;
}

export interface TimelineEvent {
  id: string;
  kind: TimelineKind;
  at: string | null;
  actor: string;
  title: string;
  detail: string;
  reasons?: string[];
  evidenceId?: string | null;
  verdict?: Verdict;
  rejected?: boolean;
  demo?: boolean;
}

export interface CanaryRun {
  id: string;
  ranAt: string | null;
  /** The deliberate cheat attempt — it MUST be caught (result FAIL). */
  cheatAttempt: string;
  expected: "FAIL";
  result: CanaryResult;
  caught: string | null;
  note: string;
  demo?: boolean;
}

/** Body state a panel can be in (component states, per AHOS truth rules). */
export type PanelBodyState =
  | { kind: "content" }
  | { kind: "loading" }
  | { kind: "empty"; message: string }
  | { kind: "unknown"; message: string }
  | { kind: "unavailable"; message: string }
  | { kind: "error"; message: string };

export interface WhiteHatsSnapshot {
  schemaVersion: 1;
  sourceId: string;
  executionMode: ExecutionMode;
  realTrading: boolean;
  fetchedAt: string | null;
  freshness: TruthStatus;
  /** Whole snapshot is mock-backed ⇒ true ⇒ DEMO chips everywhere. */
  demo: boolean;
  decisions: Decision[];
  inspectors: Inspector[];
  findings: Finding[];
  breaker: Breaker;
  canary: CanaryRun | null;
  timelines: Record<string, TimelineEvent[]>;
  evidence: Record<string, EvidenceDoc>;
}
