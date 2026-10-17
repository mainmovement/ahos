// FILE: 13_missions_batch3/src/contract/validate.ts
/**
 * Runtime contract validator — zero external dependencies.
 * Every entry point returns `null` on invalid input. Callers render UNAVAILABLE.
 * It never throws to the UI.
 */
import type {
  AhosArenaContract,
  DebugTimelineEvent,
  ExecutionMode,
  NewsCenterSnapshot,
  NewsItem,
  NewsTopic,
  ScienceRadarItem,
  ScienceRadarSnapshot,
  SelfDebugIncident,
  SelfDebugSnapshot,
  SkillMarketEntry,
  SkillMarketSnapshot,
  WeeklyExamItem,
  WeeklyExamRun,
  WeeklyExamSnapshot,
  ExamState,
  InstallState,
  RadarItemStatus,
  RadarSourceType,
  ReviewState,
  SkillKind,
  TriState,
  DebugStatus,
} from "./types";

/* ---------- primitives ---------- */

function isObj(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function str(v: unknown): string | null {
  return typeof v === "string" ? v : null;
}

function reqStr(v: unknown): string | null {
  return typeof v === "string" && v.length > 0 ? v : null;
}

function nullableStr(v: unknown): string | null {
  if (v === null || v === undefined) return null;
  return typeof v === "string" ? v : null;
}

function bool(v: unknown): boolean | null {
  return typeof v === "boolean" ? v : null;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function nullableNum(v: unknown): number | null {
  if (v === null || v === undefined) return null;
  return num(v);
}

function enumOf<T extends string>(v: unknown, allowed: readonly T[]): T | null {
  return typeof v === "string" && (allowed as readonly string[]).includes(v)
    ? (v as T)
    : null;
}

function strArray(v: unknown): string[] | null {
  if (!Array.isArray(v)) return null;
  const out: string[] = [];
  for (const item of v) {
    const s = str(item);
    if (s === null) return null;
    out.push(s);
  }
  return out;
}

/* ---------- meta ---------- */

const EXEC_MODES = [
  "PAPER_ONLY",
  "SIMULATION",
  "LIVE",
  "UNKNOWN",
] as const satisfies readonly ExecutionMode[];

interface MetaIn {
  executionMode: ExecutionMode;
  realTrading: boolean;
  source: string | null;
  generatedAt: string | null;
  demo?: boolean;
}

/**
 * Section meta may be self-contained or inherited from the document root.
 * Returns null when executionMode or realTrading are missing/invalid anywhere.
 */
function readMeta(
  section: Record<string, unknown>,
  root: Record<string, unknown>,
): MetaIn | null {
  const executionMode =
    enumOf(section.executionMode, EXEC_MODES) ??
    enumOf(root.executionMode, EXEC_MODES);
  const realTrading = bool(section.realTrading) ?? bool(root.realTrading);
  if (executionMode === null || realTrading === null) return null;
  const source =
    section.source !== undefined
      ? nullableStr(section.source)
      : nullableStr(root.source);
  const generatedAt =
    section.generatedAt !== undefined
      ? nullableStr(section.generatedAt)
      : nullableStr(root.generatedAt);
  const demo = bool(section.demo);
  return { executionMode, realTrading, source, generatedAt, ...(demo !== null ? { demo } : {}) };
}

/* ---------- science-radar ---------- */

const RADAR_SOURCES = [
  "paper",
  "repo",
  "blog",
  "university",
  "agent",
] as const satisfies readonly RadarSourceType[];
const RADAR_STATUSES = [
  "NEW",
  "REVIEWED",
  "DISMISSED",
  "UNKNOWN",
] as const satisfies readonly RadarItemStatus[];

function readRadarItem(v: unknown): ScienceRadarItem | null {
  if (!isObj(v)) return null;
  const id = reqStr(v.id);
  const title = reqStr(v.title);
  const sourceType = enumOf(v.sourceType, RADAR_SOURCES);
  const topic = reqStr(v.topic);
  const status = enumOf(v.status, RADAR_STATUSES);
  const demo = bool(v.demo);
  if (!id || !title || !sourceType || !topic || !status || demo === null) return null;
  return {
    id,
    title,
    sourceType,
    topic,
    foundAt: nullableStr(v.foundAt),
    relevanceNote: nullableStr(v.relevanceNote),
    status,
    sourceText: nullableStr(v.sourceText),
    demo,
  };
}

export function validateScienceRadar(
  raw: unknown,
  root: Record<string, unknown> = {},
): ScienceRadarSnapshot | null {
  if (!isObj(raw)) return null;
  const meta = readMeta(raw, root);
  if (!meta) return null;
  if (!Array.isArray(raw.items)) return null;
  const items: ScienceRadarItem[] = [];
  for (const it of raw.items) {
    const item = readRadarItem(it);
    if (!item) return null;
    items.push(item);
  }
  return { ...meta, kind: "scienceRadar", items };
}

/* ---------- self-debug ---------- */

const DEBUG_STATUSES = [
  "OPEN",
  "DIAGNOSED",
  "CLOSED",
  "UNKNOWN",
] as const satisfies readonly DebugStatus[];

function readTimeline(v: unknown): DebugTimelineEvent[] | null {
  if (!Array.isArray(v)) return null;
  const out: DebugTimelineEvent[] = [];
  for (const e of v) {
    if (!isObj(e)) return null;
    const event = reqStr(e.event);
    if (!event) return null;
    out.push({ time: nullableStr(e.time), event, source: nullableStr(e.source) });
  }
  return out;
}

function readIncident(v: unknown): SelfDebugIncident | null {
  if (!isObj(v)) return null;
  const id = reqStr(v.id);
  const component = reqStr(v.component);
  const errorSignature = reqStr(v.errorSignature);
  const status = enumOf(v.status, DEBUG_STATUSES);
  const demo = bool(v.demo);
  const timeline = readTimeline(v.timeline);
  const logExcerpt = strArray(v.logExcerpt);
  if (!id || !component || !errorSignature || !status || demo === null) return null;
  if (!timeline || !logExcerpt) return null;
  if (errorSignature.length > 120) return null;
  if (logExcerpt.some((line) => line.length > 200)) return null;
  return {
    id,
    time: nullableStr(v.time),
    component,
    errorSignature,
    diagnosisNote: nullableStr(v.diagnosisNote),
    status,
    evidencePath: nullableStr(v.evidencePath),
    timeline,
    logExcerpt,
    demo,
  };
}

export function validateSelfDebug(
  raw: unknown,
  root: Record<string, unknown> = {},
): SelfDebugSnapshot | null {
  if (!isObj(raw)) return null;
  const meta = readMeta(raw, root);
  if (!meta) return null;
  if (!Array.isArray(raw.incidents)) return null;
  const incidents: SelfDebugIncident[] = [];
  for (const it of raw.incidents) {
    const incident = readIncident(it);
    if (!incident) return null;
    incidents.push(incident);
  }
  return { ...meta, kind: "selfDebug", incidents };
}

/* ---------- weekly-exam ---------- */

const EXAM_STATES = [
  "SCHEDULED",
  "RAN",
  "PARTIAL",
  "NOT_RUN",
  "UNKNOWN",
] as const satisfies readonly ExamState[];
const TRI = ["yes", "no", "UNKNOWN"] as const satisfies readonly TriState[];

function readExamItem(v: unknown): WeeklyExamItem | null {
  if (!isObj(v)) return null;
  const id = reqStr(v.id);
  const topic = reqStr(v.topic);
  const answered = enumOf(v.answered, TRI);
  const evidence = enumOf(v.evidence, TRI);
  const demo = bool(v.demo);
  if (!id || !topic || !answered || !evidence || demo === null) return null;
  return { id, topic, answered, evidence, reviewState: nullableStr(v.reviewState), demo };
}

function readExamRun(v: unknown): WeeklyExamRun | null {
  if (!isObj(v)) return null;
  const id = reqStr(v.id);
  const state = enumOf(v.state, EXAM_STATES);
  const demo = bool(v.demo);
  if (!id || !state || demo === null) return null;
  if (!Array.isArray(v.items)) return null;
  const items: WeeklyExamItem[] = [];
  for (const it of v.items) {
    const item = readExamItem(it);
    if (!item) return null;
    items.push(item);
  }
  return {
    id,
    week: nullableStr(v.week),
    itemsCount: nullableNum(v.itemsCount),
    answeredCount: nullableNum(v.answeredCount),
    withEvidenceCount: nullableNum(v.withEvidenceCount),
    resultSummary: nullableStr(v.resultSummary),
    state,
    items,
    demo,
  };
}

export function validateWeeklyExam(
  raw: unknown,
  root: Record<string, unknown> = {},
): WeeklyExamSnapshot | null {
  if (!isObj(raw)) return null;
  const meta = readMeta(raw, root);
  if (!meta) return null;
  const minSampleSize = nullableNum(raw.minSampleSize);
  if (minSampleSize === null || minSampleSize < 1) return null;
  if (!Array.isArray(raw.runs)) return null;
  const runs: WeeklyExamRun[] = [];
  for (const it of raw.runs) {
    const run = readExamRun(it);
    if (!run) return null;
    runs.push(run);
  }
  return { ...meta, kind: "weeklyExam", minSampleSize, runs };
}

/* ---------- skill-market ---------- */

const SKILL_KINDS = ["skill", "plugin"] as const satisfies readonly SkillKind[];
const INSTALL_STATES = [
  "AVAILABLE",
  "INSTALLED",
  "BLOCKED",
  "UNKNOWN",
] as const satisfies readonly InstallState[];
const REVIEW_STATES = [
  "UNREVIEWED",
  "REVIEWED",
  "REJECTED",
] as const satisfies readonly ReviewState[];

function readEntry(v: unknown): SkillMarketEntry | null {
  if (!isObj(v)) return null;
  const id = reqStr(v.id);
  const name = reqStr(v.name);
  const kind = enumOf(v.kind, SKILL_KINDS);
  const installState = enumOf(v.installState, INSTALL_STATES);
  const reviewState = enumOf(v.reviewState, REVIEW_STATES);
  const permissions = strArray(v.permissions);
  const demo = bool(v.demo);
  if (!id || !name || !kind || !installState || !reviewState) return null;
  if (!permissions || demo === null) return null;
  return {
    id,
    name,
    kind,
    version: nullableStr(v.version),
    source: nullableStr(v.source),
    installState,
    permissions,
    reviewState,
    reason: nullableStr(v.reason),
    demo,
  };
}

export function validateSkillMarket(
  raw: unknown,
  root: Record<string, unknown> = {},
): SkillMarketSnapshot | null {
  if (!isObj(raw)) return null;
  const meta = readMeta(raw, root);
  if (!meta) return null;
  if (!Array.isArray(raw.entries)) return null;
  const entries: SkillMarketEntry[] = [];
  for (const it of raw.entries) {
    const entry = readEntry(it);
    if (!entry) return null;
    entries.push(entry);
  }
  return { ...meta, kind: "skillMarket", entries };
}

/* ---------- news-center ---------- */

const NEWS_TOPICS = [
  "Oil",
  "Gold",
  "Macro",
  "Other",
] as const satisfies readonly NewsTopic[];

function readNewsItem(v: unknown): NewsItem | null {
  if (!isObj(v)) return null;
  const id = reqStr(v.id);
  const topic = enumOf(v.topic, NEWS_TOPICS);
  const summary = reqStr(v.summary);
  const demo = bool(v.demo);
  if (!id || !topic || !summary || demo === null) return null;
  if (summary.length > 120) return null;
  return {
    id,
    time: nullableStr(v.time),
    sourceName: nullableStr(v.sourceName),
    topic,
    summary,
    reliability: nullableStr(v.reliability),
    demo,
  };
}

export function validateNewsCenter(
  raw: unknown,
  root: Record<string, unknown> = {},
): NewsCenterSnapshot | null {
  if (!isObj(raw)) return null;
  const meta = readMeta(raw, root);
  if (!meta) return null;
  const staleAfterMinutes = nullableNum(raw.staleAfterMinutes);
  if (staleAfterMinutes === null || staleAfterMinutes < 1) return null;
  if (!Array.isArray(raw.items)) return null;
  const items: NewsItem[] = [];
  for (const it of raw.items) {
    const item = readNewsItem(it);
    if (!item) return null;
    items.push(item);
  }
  return { ...meta, kind: "newsCenter", staleAfterMinutes, items };
}

/* ---------- full document ---------- */

/**
 * Validates the whole contract document. Returns null (⇒ UNAVAILABLE) for any
 * malformed section; partial documents are never "partially accepted".
 */
export function validateContract(raw: unknown): AhosArenaContract | null {
  if (!isObj(raw)) return null;
  const root = raw;
  const contractVersion = reqStr(raw.contractVersion);
  if (!contractVersion) return null;
  const scienceRadar = validateScienceRadar(raw.scienceRadar, root);
  const selfDebug = validateSelfDebug(raw.selfDebug, root);
  const weeklyExam = validateWeeklyExam(raw.weeklyExam, root);
  const skillMarket = validateSkillMarket(raw.skillMarket, root);
  const newsCenter = validateNewsCenter(raw.newsCenter, root);
  if (!scienceRadar || !selfDebug || !weeklyExam || !skillMarket || !newsCenter) {
    return null;
  }
  const executionMode = enumOf(raw.executionMode, EXEC_MODES);
  const realTrading = bool(raw.realTrading);
  if (!executionMode || realTrading === null) return null;
  return {
    contractVersion,
    executionMode,
    realTrading,
    source: nullableStr(raw.source),
    generatedAt: nullableStr(raw.generatedAt),
    scienceRadar,
    selfDebug,
    weeklyExam,
    skillMarket,
    newsCenter,
  };
}
