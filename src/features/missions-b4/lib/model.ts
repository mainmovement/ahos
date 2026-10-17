/**
 * AHOS Arena - missions batch 4 / delivery batch 13 (science-radar M44, self-debug M46,
 * weekly-exam M50, skill-market M52, news-center M18.N). Pure logic: no React, no fs.
 * Truth rules (asserted by scripts/missions_b4_selftest.ts):
 *  - DEMO rows never read LIVE and are excluded from every count/aggregate
 *  - missing numbers are "-" (never 0); counts are derived from rows, never typed in
 *  - no timestamp => UNKNOWN; STALE needs a timestamp
 *  - REVIEWED/REJECTED without a reason renders as UNREVIEWED (a plugin is never called "safe")
 *  - weekly-exam shows neutral numbers only (no pass/fail), and below minSampleSize no aggregate
 *  - calm view shows at most 7 highlights, the rest sits behind Details
 */
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { MISSING, capHighlights, demoize, redact, type Highlight } from "../../missions-b2/lib/model";
import type {
  InstallState, NewsCenterSnapshot, NewsItem, ReviewState, ScienceRadarItem, ScienceRadarSnapshot, SelfDebugIncident,
  SelfDebugSnapshot, SkillMarketEntry, SkillMarketSnapshot, WeeklyExamRun, WeeklyExamSnapshot,
} from "../contract/types";

export { MISSING, capHighlights, demoize, redact };
export type { Highlight };

export const CALM_MAX = 7;
const nonDemo = <T extends { demo: boolean }>(rows: T[]): T[] => rows.filter((r) => !r.demo);
const num = (n: number | null | undefined): string => (typeof n === "number" && Number.isFinite(n) ? String(n) : MISSING);

/** Strip Windows user-profile paths and secrets from free text; clamp length. */
export function clean(text: string | null | undefined, max = 160): string {
  if (!text) return "";
  const t = redact(text).replace(/[A-Za-z]:\\Users\\[^\\\s"']+/gi, "<user>").replace(/\/(?:home|Users)\/[^/\s"']+/g, "/<user>");
  return t.length > max ? `${t.slice(0, max - 1)}…` : t;
}

/* ------------------------------------------------------------ science-radar */
const RADAR_RANK: Record<ScienceRadarItem["status"], number> = { NEW: 0, UNKNOWN: 1, REVIEWED: 2, DISMISSED: 3 };
export function radarStatus(s: ScienceRadarItem["status"], demo: boolean): ChipStatus {
  const base: ChipStatus = s === "REVIEWED" ? "LIVE" : s === "NEW" ? "PARTIAL" : s === "DISMISSED" ? "MISSING" : "UNKNOWN";
  return demoize(base, demo);
}
export function buildScienceRadar(s: ScienceRadarSnapshot, demo: boolean) {
  const rows = [...s.items].sort((a, b) => RADAR_RANK[a.status] - RADAR_RANK[b.status] || (b.foundAt ?? "").localeCompare(a.foundAt ?? ""));
  const highlights: Highlight[] = rows.map((r) => ({
    id: r.id, title: clean(r.title), detail: r.relevanceNote ? clean(r.relevanceNote) : null,
    status: demo || r.demo ? "DEMO" : radarStatus(r.status, false), tag: `${r.sourceType} / ${r.status}`,
  }));
  const counted = nonDemo(s.items);
  const counts = demo || counted.length === 0 ? null : {
    total: counted.length, fresh: counted.filter((r) => r.status === "NEW").length, reviewed: counted.filter((r) => r.status === "REVIEWED").length,
  };
  return { rows, highlights, counts };
}

/* --------------------------------------------------------------- self-debug */
export function debugStatus(s: SelfDebugIncident["status"], demo: boolean): ChipStatus {
  const base: ChipStatus = s === "CLOSED" ? "LIVE" : s === "DIAGNOSED" ? "PARTIAL" : s === "OPEN" ? "ERROR" : "UNKNOWN";
  return demoize(base, demo);
}
export function buildSelfDebug(s: SelfDebugSnapshot, demo: boolean) {
  const rows = [...s.incidents].sort((a, b) => (b.time ?? "").localeCompare(a.time ?? ""));
  const highlights: Highlight[] = rows.map((r) => ({
    id: r.id, title: `${r.component} - ${clean(r.errorSignature, 120)}`,
    detail: r.diagnosisNote ? clean(r.diagnosisNote) : null, status: demo || r.demo ? "DEMO" : debugStatus(r.status, false), tag: r.status,
  }));
  const counted = nonDemo(s.incidents);
  const counts = demo || counted.length === 0 ? null : {
    total: counted.length, open: counted.filter((r) => r.status === "OPEN").length, diagnosed: counted.filter((r) => r.status === "DIAGNOSED").length,
    unknown: counted.filter((r) => r.status === "UNKNOWN").length,
  };
  return { rows, highlights, counts };
}

/** REAL binding: soak_runlog.jsonl rows with ok=false / ledger_error become incidents. Nothing is invented. */
export function parseSoakRunlog(text: string): { incidents: SelfDebugIncident[]; lastTs: string | null; rows: number; skipped: number } {
  const incidents: SelfDebugIncident[] = [];
  let lastTs: string | null = null;
  let rows = 0;
  let skipped = 0;
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue;
    let r: Record<string, unknown>;
    try {
      const p = JSON.parse(line);
      if (!p || typeof p !== "object" || Array.isArray(p)) { skipped++; continue; }
      r = p as Record<string, unknown>;
    } catch {
      skipped++;
      continue;
    }
    rows++;
    const ts = typeof r.ts === "string" && Number.isFinite(Date.parse(r.ts)) ? r.ts : null;
    if (ts && (!lastTs || Date.parse(ts) > Date.parse(lastTs))) lastTs = ts;
    const err = typeof r.error === "string" ? r.error : typeof r.ledger_error === "string" ? r.ledger_error : null;
    if (r.ok !== false && !err) continue;
    const kind = typeof r.kind === "string" ? r.kind : "runlog";
    const tb = typeof r.traceback === "string" ? r.traceback.split(/\r?\n/).filter(Boolean).slice(-4).map((l) => clean(l.trim(), 200)) : [];
    incidents.push({
      id: `soak-${kind}-${ts ?? `row${rows}`}`, time: ts, component: kind,
      errorSignature: clean(err ?? "ok=false (no error text)", 120), diagnosisNote: null, status: "UNKNOWN", evidencePath: "soak_runlog.jsonl",
      timeline: [{ time: ts, event: "runlog ok=false", source: "soak_runlog.jsonl" }], logExcerpt: tb, demo: false,
    });
  }
  return { incidents, lastTs, rows, skipped };
}

/* -------------------------------------------------------------- weekly-exam */
export function examStatus(s: WeeklyExamRun["state"], demo: boolean): ChipStatus {
  const base: ChipStatus = s === "RAN" ? "LIVE" : s === "PARTIAL" ? "PARTIAL" : s === "SCHEDULED" ? "PLANNED" : s === "NOT_RUN" ? "MISSING" : "UNKNOWN";
  return demoize(base, demo);
}
export function buildWeeklyExam(s: WeeklyExamSnapshot, demo: boolean) {
  const runs = s.runs;
  const counted = nonDemo(runs);
  const adequate = !demo && counted.length >= s.minSampleSize;
  const highlights: Highlight[] = runs.map((r) => ({
    id: r.id, title: r.week ?? MISSING,
    detail: `${num(r.answeredCount)} / ${num(r.itemsCount)} | ${num(r.withEvidenceCount)}`,
    status: demo || r.demo ? "DEMO" : examStatus(r.state, false), tag: r.state,
  }));
  return { runs, highlights, adequate, countedRuns: demo ? null : counted.length, minSampleSize: s.minSampleSize };
}

/* ------------------------------------------------------------- skill-market */
export function effectiveReview(e: Pick<SkillMarketEntry, "reviewState" | "reason">): { state: ReviewState; missingReason: boolean } {
  const has = typeof e.reason === "string" && e.reason.trim() !== "";
  if ((e.reviewState === "REVIEWED" || e.reviewState === "REJECTED") && !has) return { state: "UNREVIEWED", missingReason: true };
  return { state: e.reviewState, missingReason: false };
}
export function installChip(s: InstallState, demo: boolean): ChipStatus {
  const base: ChipStatus = s === "INSTALLED" ? "LIVE" : s === "BLOCKED" ? "REJECTED" : s === "AVAILABLE" ? "PARTIAL" : "UNKNOWN";
  return demoize(base, demo);
}
export function buildSkillMarket(s: SkillMarketSnapshot, demo: boolean) {
  const rows = s.entries.map((e) => ({ e, review: effectiveReview(e) }));
  const rank = (x: { e: SkillMarketEntry; review: { state: ReviewState } }) => (x.e.installState === "BLOCKED" ? 0 : x.review.state === "UNREVIEWED" ? 1 : x.review.state === "REJECTED" ? 2 : 3);
  const sorted = [...rows].sort((a, b) => rank(a) - rank(b));
  const highlights: Highlight[] = sorted.map(({ e, review }) => ({
    id: e.id, title: clean(e.name, 80), detail: `${e.kind} ${e.version ?? MISSING} | ${review.state}${review.missingReason ? " *" : ""}`,
    status: demo || e.demo ? "DEMO" : installChip(e.installState, false), tag: e.installState,
  }));
  const counted = rows.filter((r) => !r.e.demo);
  const counts = demo || counted.length === 0 ? null : {
    total: counted.length, installed: counted.filter((r) => r.e.installState === "INSTALLED").length,
    unreviewed: counted.filter((r) => r.review.state === "UNREVIEWED").length,
  };
  return { rows: sorted, highlights, counts };
}

/* -------------------------------------------------------------- news-center */
export type NewsFresh = "LIVE" | "STALE" | "UNKNOWN";
export function newsFreshness(item: Pick<NewsItem, "time">, generatedAt: string | null, staleAfterMinutes: number): NewsFresh {
  if (!item.time || !generatedAt) return "UNKNOWN";
  const a = Date.parse(item.time);
  const g = Date.parse(generatedAt);
  if (!Number.isFinite(a) || !Number.isFinite(g)) return "UNKNOWN";
  const age = (g - a) / 60000;
  if (age < 0) return "UNKNOWN"; // item newer than the snapshot clock: cannot be trusted
  return age <= staleAfterMinutes ? "LIVE" : "STALE";
}
export function buildNewsCenter(s: NewsCenterSnapshot, demo: boolean) {
  const rows = [...s.items].sort((a, b) => (b.time ?? "").localeCompare(a.time ?? "")).map((n) => ({ n, fresh: newsFreshness(n, s.generatedAt, s.staleAfterMinutes) }));
  const highlights: Highlight[] = rows.map(({ n, fresh }) => ({
    id: n.id, title: clean(n.summary, 120), detail: `${n.sourceName ?? MISSING} | ${n.reliability ?? MISSING}`,
    status: demo || n.demo ? "DEMO" : (fresh as ChipStatus), tag: `${n.topic} / ${fresh}`,
  }));
  const counted = rows.filter((r) => !r.n.demo);
  const counts = demo || counted.length === 0 ? null : { total: counted.length, live: counted.filter((r) => r.fresh === "LIVE").length, stale: counted.filter((r) => r.fresh === "STALE").length };
  return { rows, highlights, counts };
}
