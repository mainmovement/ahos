/**
 * AHOS Arena - missions batch 2 (message-hub, self-evaluation, idea-shelf,
 * research-institute, mission-map). Pure logic only: no React, no fs.
 * Truth rules enforced here and asserted by scripts/missions_b2_selftest.ts:
 *  - DEMO data is never LIVE; UNKNOWN/STALE need honest inputs (no timestamp => UNKNOWN)
 *  - missing numbers are "-" (never 0); counts are derived from rows, never typed in
 *  - calm view shows at most MAX_HIGHLIGHTS items; everything else sits behind Details
 *  - free text is redacted (tokens / secrets are never displayed)
 */
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { detectViolation, type ViolationReport } from "@/src/features/trade-venue/logic/truth";
import type {
  BridgeState,
  DeliveryState,
  Hypothesis,
  Idea,
  MessageHubSnapshot,
  MessageState,
  Mission,
  MissionMapSnapshot,
  ResearchInstituteSnapshot,
  ReviewState,
  SelfEvaluationSnapshot,
  Status,
  IdeaShelfSnapshot,
} from "../contract/types";

export const MAX_HIGHLIGHTS = 7;
/** A file-backed snapshot older than this is STALE (a timestamp is always required). */
export const STALE_AFTER_MS = 12 * 60 * 60 * 1000;
export const MISSING = "-";

export type PageState = "ready" | "empty" | "error" | "unavailable" | "loading" | "stale";
const PAGE_STATES: readonly PageState[] = ["ready", "empty", "error", "unavailable", "loading", "stale"];

export function one(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}
export function parseFlag(v: string | string[] | undefined): boolean {
  return one(v) === "1";
}
export function parsePageState(v: string | string[] | undefined): PageState {
  const s = one(v);
  return PAGE_STATES.includes(s as PageState) ? (s as PageState) : "ready";
}
export function parsePeriod(v: string | string[] | undefined): "week" | "month" {
  return one(v) === "month" ? "month" : "week";
}

/* ------------------------------------------------------------- freshness -- */

export type SourceKind = "demo" | "file" | "none";

export function freshness(kind: SourceKind, generatedAt: string | null, nowMs: number, staleAfterMs = STALE_AFTER_MS): ChipStatus {
  if (kind === "demo") return "DEMO"; // DEMO is never promoted to LIVE
  if (kind === "none") return "UNAVAILABLE";
  if (!generatedAt) return "UNKNOWN"; // STALE needs a timestamp; none => UNKNOWN
  const t = Date.parse(generatedAt);
  if (!Number.isFinite(t)) return "UNKNOWN";
  return nowMs - t > staleAfterMs ? "STALE" : "LIVE";
}

/** Rows inside a DEMO snapshot may never read LIVE. */
export function demoize(status: ChipStatus, demo: boolean): ChipStatus {
  return demo && status === "LIVE" ? "DEMO" : status;
}

/** Attention order for the calm view: problems first, calm last. */
const RANK: Partial<Record<ChipStatus, number>> = {
  CONFLICT: 0, REJECTED: 1, ERROR: 2, UNAVAILABLE: 3, STALE: 4, UNKNOWN: 5, MISSING: 5, PARTIAL: 6, PLANNED: 7, DEMO: 8, LIVE: 9,
};
export function attentionRank(s: ChipStatus): number {
  return RANK[s] ?? 8;
}

export interface Highlight {
  id: string;
  title: string;
  detail: string | null;
  status: ChipStatus;
  tag?: string | null;
}

/** Stable sort by attention then cap to 7. Never invents rows. */
export function capHighlights(items: Highlight[]): { shown: Highlight[]; hidden: number } {
  const sorted = items
    .map((h, i) => ({ h, i }))
    .sort((a, b) => attentionRank(a.h.status) - attentionRank(b.h.status) || a.i - b.i)
    .map((x) => x.h);
  return { shown: sorted.slice(0, MAX_HIGHLIGHTS), hidden: Math.max(0, sorted.length - MAX_HIGHLIGHTS) };
}

/* ------------------------------------------------------------- hygiene ----- */

export function formatNum(n: number | null | undefined): string {
  return typeof n === "number" && Number.isFinite(n) ? String(n) : MISSING;
}

const SECRET_PATTERNS: RegExp[] = [
  /\b\d{6,}:[A-Za-z0-9_-]{20,}\b/g, // telegram bot token
  /\bsk-[A-Za-z0-9_-]{12,}\b/g,
  /\bghp_[A-Za-z0-9]{20,}\b/g,
  /\bBearer\s+[A-Za-z0-9._~+/=-]{12,}/gi,
  /\b[A-Fa-f0-9]{40,}\b/g,
  /\b(?:token|secret|password|passwd|api[_-]?key|chat[_-]?id)\s*[:=]\s*\S+/gi,
];
export const REDACTED = "[redacted]";
export function redact(text: string | null | undefined): string {
  if (!text) return "";
  let out = text;
  for (const re of SECRET_PATTERNS) out = out.replace(re, REDACTED);
  return out;
}

export function tehranStamp(iso: string | null | undefined): string {
  if (!iso) return MISSING;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return MISSING;
  const p = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Tehran", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(new Date(t));
  const g = (k: string) => p.find((x) => x.type === k)?.value ?? "";
  return `${g("year")}-${g("month")}-${g("day")} ${g("hour")}:${g("minute")}`;
}

export function ageHours(iso: string | null | undefined, nowMs: number): number | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  return Number.isFinite(t) ? Math.max(0, Math.round(((nowMs - t) / 3_600_000) * 10) / 10) : null;
}

/* ------------------------------------------------------------- violation --- */

const KNOWN_MODES = ["PAPER_ONLY", "SIMULATION", "SHADOW", "LIVE", "UNKNOWN"] as const;
export function violationOf(executionMode: string, realTrading: boolean): ViolationReport | null {
  const mode = (KNOWN_MODES as readonly string[]).includes(executionMode) ? (executionMode as (typeof KNOWN_MODES)[number]) : "UNKNOWN";
  return detectViolation({ executionMode: mode, realTrading });
}

/* ------------------------------------------------------------- mappings ---- */

export function bridgeStatus(s: BridgeState): ChipStatus {
  return s === "CONNECTED" ? "LIVE" : s === "DISCONNECTED" ? "UNAVAILABLE" : s === "BLOCKED_OWNER" ? "UNAVAILABLE" : "UNKNOWN";
}
export function deliveryStatus(s: DeliveryState | MessageState): ChipStatus {
  switch (s) {
    case "SENT":
    case "DELIVERED":
      return "LIVE";
    case "FAILED":
      return "ERROR";
    case "PENDING":
      return "PARTIAL";
    case "NOT_SENT":
      return "MISSING";
    default:
      return "UNKNOWN";
  }
}
export function reviewStatus(s: ReviewState): ChipStatus {
  return s === "REVIEWED" ? "LIVE" : s === "PENDING" ? "PARTIAL" : "UNKNOWN";
}
export function contractStatus(s: Status): ChipStatus {
  return s;
}

/* ------------------------------------------------------------- view models - */

export interface MessageHubView {
  highlights: Highlight[];
  telegramBlockedOwner: boolean;
  snapshot: MessageHubSnapshot;
}
export function buildMessageHub(s: MessageHubSnapshot, demo: boolean): MessageHubView {
  const items: Highlight[] = [
    {
      id: "telegram",
      title: "Telegram",
      detail: s.telegram.bridgeState,
      status: demoize(bridgeStatus(s.telegram.bridgeState), demo),
    },
    { id: "nightly", title: "nightly report", detail: s.nightlyReport.language, status: demoize(deliveryStatus(s.nightlyReport.deliveryState), demo) },
    ...s.channels.map((c) => ({
      id: `ch-${c.channel}`,
      title: c.channel,
      detail: c.lastError ? redact(c.lastError) : null,
      status: demoize(c.status, demo),
    })),
    ...s.humanGateInbox.map((g) => ({
      id: `gate-${g.id}`,
      title: redact(g.title),
      detail: `${g.requestedByAgent} - ${g.age}`,
      status: demoize(g.state, demo),
    })),
  ];
  return { highlights: items, telegramBlockedOwner: s.telegram.bridgeState === "BLOCKED_OWNER" || s.telegram.needsTokenRotation, snapshot: s };
}

export interface SelfEvalView {
  period: "week" | "month";
  highlights: Highlight[];
  scorecard: SelfEvaluationSnapshot["scorecards"][number] | null;
}
export function buildSelfEval(s: SelfEvaluationSnapshot, period: "week" | "month", demo: boolean): SelfEvalView {
  const sc = s.scorecards.find((x) => x.period === period) ?? null;
  const highlights: Highlight[] = (sc?.highlights ?? []).map((h) => ({
    id: h.id,
    title: redact(h.market),
    detail: redact(h.rationaleSummary),
    status: demoize(reviewStatus(h.reviewState), demo),
    tag: h.outcomeKnown,
  }));
  return { period, highlights, scorecard: sc };
}

export interface IdeaRow {
  id: string;
  title: string;
  origin: string | null;
  lifecycle: "PROPOSED" | "ACCEPTED" | "REJECTED" | "UNKNOWN";
  reason: string | null;
  minRam: string | null;
  tier: string | null;
  flags: string[];
  unseen: Idea["unseenTest"];
}
export function ideaFromContract(i: Idea): IdeaRow {
  return {
    id: i.id, title: redact(i.title), origin: i.origin, lifecycle: i.status, reason: i.reason ? redact(i.reason) : null,
    minRam: i.hardwareRequirement?.minRAM ?? null, tier: null, flags: i.flags, unseen: i.unseenTest,
  };
}
/** REAL binding: config/idea_shelf.json entries carry id/title/tier only; nothing else is invented. */
export function ideasFromShelfFile(raw: unknown): IdeaRow[] | null {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const list = (raw as { ideas?: unknown }).ideas;
  if (!Array.isArray(list)) return null;
  const out: IdeaRow[] = [];
  for (const e of list) {
    if (!e || typeof e !== "object") continue;
    const r = e as Record<string, unknown>;
    if (typeof r.id !== "string" || typeof r.title !== "string") continue;
    out.push({
      id: r.id, title: redact(r.title), origin: null, lifecycle: "UNKNOWN", reason: null,
      minRam: typeof r.est_ram_mb === "number" ? `${r.est_ram_mb} MB` : null,
      tier: typeof r.tier === "string" ? r.tier : null,
      flags: typeof r.flag === "string" ? [r.flag] : [], unseen: null,
    });
  }
  return out;
}
export function ideaHighlights(rows: IdeaRow[], provenance: ChipStatus): Highlight[] {
  return rows.map((r) => ({
    id: r.id,
    title: r.title,
    detail: r.tier ? `tier ${r.tier}` : r.reason,
    status: r.lifecycle === "REJECTED" ? "REJECTED" : provenance,
    tag: r.lifecycle === "UNKNOWN" ? null : r.lifecycle,
  }));
}

export function buildResearch(s: ResearchInstituteSnapshot, demo: boolean) {
  const hs: Hypothesis[] = s.hypotheses;
  const highlights: Highlight[] = hs.map((h) => ({
    id: h.id,
    title: redact(h.statement),
    detail: h.market,
    status:
      h.status === "REJECTED" ? "REJECTED" : h.status === "TESTED_UNSEEN" ? demoize("LIVE", demo) : "UNKNOWN",
    tag: h.status,
  }));
  // passed-unseen is computed from non-DEMO rows only. Demo rows never count.
  const real = demo ? [] : hs;
  const passedUnseen = real.length === 0 ? null : real.filter((h) => h.unseenTest?.result === "PASS").length;
  return { highlights, passedUnseen, hypotheses: hs, exam: s.weeklyExam };
}

export function buildMissionMap(missions: Mission[], demo: boolean) {
  const rank = (m: Mission) => (m.blockedOwner ? 0 : m.state === "PARTIAL" ? 1 : m.caveat ? 2 : m.state === "NOT_STARTED" ? 3 : 4);
  const highlights: Highlight[] = missions
    .map((m, i) => ({ m, i }))
    .sort((a, b) => rank(a.m) - rank(b.m) || a.i - b.i)
    .map(({ m }) => ({
      id: m.id,
      title: `${m.id} - ${redact(m.title)}`,
      detail: m.blockedOwner ? "BLOCKED_OWNER" : m.caveat ? redact(m.caveat) : null,
      status: (demo ? "DEMO" : m.blockedOwner ? "UNAVAILABLE" : m.state === "PARTIAL" ? "PARTIAL" : m.state === "NOT_STARTED" ? "PLANNED" : "LIVE") as ChipStatus,
      tag: m.state,
    }));
  const counts = demo
    ? null
    : {
        done: missions.filter((m) => m.state === "DONE").length,
        partial: missions.filter((m) => m.state === "PARTIAL").length,
        notStarted: missions.filter((m) => m.state === "NOT_STARTED").length,
        blockedOwner: missions.filter((m) => m.blockedOwner).length,
      };
  return { highlights, counts };
}

export type { MissionMapSnapshot };
