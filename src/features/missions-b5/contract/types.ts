/**
 * AHOS Arena - missions batch 5 / delivery batch 15 contract (nightly-report M35.4, university M59,
 * capability-lab M58.4/M58.5, agent-center M57). Rule: unknown => null (rendered "-"), never fabricated.
 * Adapted from Mood Agent batch 14 (14_missions_batch4); every section carries its own demo flag.
 */
export type ExecMode = "PAPER_ONLY" | "SIMULATION" | "LIVE" | "UNKNOWN";
export interface SectionMeta {
  executionMode: string;
  realTrading: boolean;
  source: string | null;
  generatedAt: string | null;
  demo: boolean;
}
export interface Row { demo: boolean }

export interface Night extends Row {
  id: string;
  day: string | null;
  timestamp: string | null;
  entries: number | null;
  closed: number | null;
  wins: number | null;
  losses: number | null;
  pnl: number | null;
  /** raw verdict token from the judge/reconcile file (CLEAN, PASS, ...); null when absent/unparseable */
  judge: string | null;
  reconcile: string | null;
  tier: number | null;
  criteria: string | null;
  signed: boolean | null;
  ai: boolean;
}
export interface NightlyReportSnapshot extends SectionMeta { kind: "nightlyReport"; nights: Night[] }

export interface Source extends Row {
  id: string; name: string; domain: string; category: string; access: string | null; licence: string | null;
  tosOk: boolean | null; authority: number | null; recency: number | null; trackRecord: number | null; citations: number | null; score: number | null;
}
export interface Exam extends Row {
  agent: string; week: string | null; score: number | null; items: number | null; ci: [number, number] | null; hash: string | null; retests: number | null;
}
export interface Bank extends Row { domain: string; skill: string; count: number | null }
export interface UniversitySnapshot extends SectionMeta { kind: "university"; sources: Source[]; exams: Exam[]; bank: Bank[] }

export const STAGES = ["PROPOSED", "SHADOW_EVAL", "QA", "RED_TEAM", "HUMAN_GATE"] as const;
export type Stage = (typeof STAGES)[number] | "UNKNOWN";
export type Scope = "rule" | "money" | "tier" | "new-agent" | "other";
export interface Point extends Row { capability: string; unit: string | null; timestamp: string | null; value: number | null; seed: number | null; items: number | null }
export interface Proposal extends Row { id: string; stage: Stage; scope: Scope; title: string; requiresHuman: boolean | null; redteam: string | null; createdAt: string | null }
export interface CapabilityLabSnapshot extends SectionMeta { kind: "capabilityLab"; points: Point[]; proposals: Proposal[] }

export interface Agent extends Row {
  id: string; name: string; role: string | null; regStatus: string | null; lane: string | null; criticality: string | null;
  liveFlag: boolean | null; heartbeat: string | null;
}
export interface AgentCenterSnapshot extends SectionMeta { kind: "agentCenter"; agents: Agent[] }

export interface AhosArenaContract {
  executionMode: string;
  realTrading: boolean;
  source: string;
  generatedAt: string | null;
  nightlyReport: NightlyReportSnapshot;
  university: UniversitySnapshot;
  capabilityLab: CapabilityLabSnapshot;
  agentCenter: AgentCenterSnapshot;
}
