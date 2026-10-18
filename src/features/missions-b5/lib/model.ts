/**
 * AHOS Arena - missions batch 5 / delivery batch 15 (nightly-report M35.4, university M59,
 * capability-lab M58.4/M58.5, agent-center M57). Pure logic: no React, no fs.
 * Truth rules (asserted by scripts/missions_b5_selftest.ts):
 *  - DEMO rows never read LIVE and are excluded from every count/aggregate
 *  - missing numbers are "-" (never 0); counts are derived from rows, never typed in
 *  - no timestamp => UNKNOWN; STALE (>26h for nightly files) needs a timestamp
 *  - an unparseable verdict is UNKNOWN, never green; only a recognised clean token is LIVE (and only while fresh)
 *  - agent presence is ONLINE only with a heartbeat <= 2 minutes old, otherwise UNKNOWN; every row is REGISTERED
 *  - exam scores are neutral numbers (no invented pass/fail bands); below the sample floor the score is "insufficient"
 *  - calm view shows at most 7 highlights, the rest sits behind Details
 */
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { MISSING, capHighlights, demoize, redact, type Highlight } from "../../missions-b2/lib/model";
import type { Agent, Exam, Night, Point, Proposal, Stage } from "../contract/types";
import { STAGES } from "../contract/types";

export { MISSING, capHighlights, demoize, redact };
export type { Highlight };

export const CALM_MAX = 7;
export const NIGHT_STALE_HOURS = 26;
export const HEARTBEAT_MAX_MIN = 2;
export const EXAM_MIN_ITEMS = 30;
export const EXAM_MAX_RETESTS = 3;
export const REGISTERED = "REGISTERED";
export const EXAM_SCHEDULE = "Asia/Tehran - 09:00 (شنبه)";

const nonDemo = <T extends { demo: boolean }>(rows: T[]): T[] => rows.filter((r) => !r.demo);
export const num = (n: number | null | undefined): string => (typeof n === "number" && Number.isFinite(n) ? String(n) : MISSING);

/** Strip Windows user-profile paths and secrets from free text; clamp length. */
export function clean(text: string | null | undefined, max = 160): string {
  if (!text) return "";
  const t = redact(text).replace(/[A-Za-z]:\\Users\\[^\\\s"']+/gi, "<user>").replace(/\/(?:home|Users)\/[^/\s"']+/g, "/<user>");
  return t.length > max ? `${t.slice(0, max - 1)}…` : t;
}

export function ageHoursOf(iso: string | null | undefined, nowMs: number): number | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return null;
  const d = nowMs - t;
  return d < 0 ? null : d / 3_600_000; // future timestamps cannot be trusted
}
export function freshOf(iso: string | null | undefined, nowMs: number, hours = NIGHT_STALE_HOURS): "LIVE" | "STALE" | "UNKNOWN" {
  const a = ageHoursOf(iso, nowMs);
  return a === null ? "UNKNOWN" : a > hours ? "STALE" : "LIVE";
}

/* ------------------------------------------------------------ nightly-report */
const OK_TOKENS = ["CLEAN", "PASS", "PASSED", "OK"];
const BAD_TOKENS = ["DISCREPANCY", "DISCREPANCIES", "FAIL", "FAILED", "HALT", "HALTED", "CONFLICT", "TAMPERED", "BROKEN"];

/** Tolerant: `**Verdict: CLEAN**`, `# Verdict - PASS`, `Verdict: fail`. No match => null (UNKNOWN). */
export function parseVerdict(text: string | null | undefined): string | null {
  if (!text) return null;
  const m = text.match(/verdict\s*\**\s*[:：=\-–]\s*\**\s*([A-Za-z_]{2,24})/i);
  return m ? m[1].toUpperCase() : null;
}
export function verdictStatus(token: string | null, fresh: "LIVE" | "STALE" | "UNKNOWN", demo: boolean): ChipStatus {
  let base: ChipStatus;
  if (token === null) base = "UNKNOWN";
  else if (BAD_TOKENS.includes(token)) base = "CONFLICT";
  else if (OK_TOKENS.includes(token)) base = fresh === "LIVE" ? "LIVE" : fresh === "STALE" ? "STALE" : "UNKNOWN";
  else base = "UNKNOWN";
  return demoize(base, demo);
}
export function parseTier(text: string | null | undefined): number | null {
  if (!text) return null;
  const m = text.match(/tier\s+today\s*:\s*\**\s*T([0-4])\b/i) ?? text.match(/^\s*#{0,6}\s*tier\s*[:=]\s*\**\s*T([0-4])\b/im);
  return m ? Number(m[1]) : null;
}
export function parseCriteria(text: string | null | undefined): string | null {
  const m = text?.match(/(\d+)\s*\/\s*(\d+)\s+measurable\s+criteria\s+passed(?:;\s*(\d+)\s+unmeasurable)?/i);
  return m ? `${m[1]}/${m[2]}${m[3] ? ` (+${m[3]} unmeasurable)` : ""}` : null;
}
const intAfter = (text: string | null | undefined, re: RegExp): number | null => {
  const m = text?.match(re);
  return m ? Number(m[1]) : null;
};
export function parseJudgeNumbers(text: string | null | undefined) {
  const wl = text?.match(/wins\s*\/\s*losses\s*:\s*(\d+)\s*\/\s*(\d+)/i);
  const pnl = text?.match(/gross\s+realized\s+pnl\s*:\s*(-?\d+(?:\.\d+)?)/i);
  return {
    closed: intAfter(text, /closed\s+trades\s*:\s*(\d+)/i),
    wins: wl ? Number(wl[1]) : null,
    losses: wl ? Number(wl[2]) : null,
    pnl: pnl ? Number(pnl[1]) : null,
  };
}
export function parseDigest(text: string | null | undefined): { day: string | null; entries: number | null; signed: boolean | null } {
  if (!text) return { day: null, entries: null, signed: null };
  try {
    const j = JSON.parse(text) as Record<string, unknown>;
    if (!j || typeof j !== "object" || Array.isArray(j)) return { day: null, entries: null, signed: null };
    return {
      day: typeof j.day === "string" && /^\d{4}-\d{2}-\d{2}$/.test(j.day) ? j.day : null,
      entries: typeof j.entries === "number" && Number.isInteger(j.entries) && j.entries >= 0 ? j.entries : null,
      signed: typeof j.signed === "boolean" ? j.signed : null,
    };
  } catch {
    return { day: null, entries: null, signed: null };
  }
}

export function buildNightly(nights: Night[], nowMs: number, demo: boolean) {
  const rows = [...nights].sort((a, b) => (b.day ?? "").localeCompare(a.day ?? "") || (b.timestamp ?? "").localeCompare(a.timestamp ?? ""));
  const latest = rows[0] ?? null;
  const fresh = (n: Night) => freshOf(n.timestamp, nowMs);
  const highlights: Highlight[] = rows.map((n) => {
    const f = fresh(n);
    const status: ChipStatus = demo || n.demo ? "DEMO" : n.judge === null && n.reconcile === null ? "UNKNOWN" : verdictStatus(n.judge, f, false);
    return {
      id: n.id, title: `${n.day ?? n.id}`, status,
      detail: `judge ${n.judge ?? MISSING} | reconcile ${n.reconcile ?? MISSING} | T${n.tier ?? MISSING}`,
      tag: `${num(n.closed)} closed`,
    };
  });
  const counted = nonDemo(nights);
  const counts = demo || counted.length === 0 ? null : {
    nights: counted.length,
    closed: counted.reduce((a, n) => a + (n.closed ?? 0), 0),
    fresh: counted.filter((n) => fresh(n) === "LIVE").length,
    unknownVerdicts: counted.filter((n) => n.judge === null).length,
  };
  return { rows, latest, highlights, counts, latestFresh: latest ? fresh(latest) : ("UNKNOWN" as const), latestAge: latest ? ageHoursOf(latest.timestamp, nowMs) : null };
}

/* ---------------------------------------------------------------- university */
export function examResult(e: Exam): { label: string; sufficient: boolean } {
  const ok = e.score !== null && !!e.items && e.items >= EXAM_MIN_ITEMS && !!e.ci && !!e.hash?.trim();
  return { label: ok ? String(e.score) : "insufficient", sufficient: ok };
}
export function buildUniversity(s: { sources: { demo: boolean; id: string; name: string; domain: string; score: number | null }[]; exams: Exam[]; bank: { demo: boolean; count: number | null }[] }, demo: boolean) {
  const highlights: Highlight[] = [
    ...s.exams.map((e, i): Highlight => {
      const r = examResult(e);
      return { id: `exam-${i}-${e.agent}`, title: `${e.agent} ${e.week ?? MISSING}`, detail: `${r.label} | n=${num(e.items)} | ${e.ci ? `CI ${e.ci[0]}-${e.ci[1]}` : "CI -"}`, status: demo || e.demo ? "DEMO" : r.sufficient ? "PARTIAL" : "UNKNOWN", tag: "exam" };
    }),
    ...s.sources.map((r): Highlight => ({
      id: r.id, title: clean(r.name, 80), detail: `${r.domain} | ${r.access ?? "source"} | score ${num(r.score)}`,
      status: demo || r.demo ? "DEMO" : r.access === "registry" ? "PARTIAL" : "UNKNOWN", tag: "source",
    })),
  ];
  const cs = nonDemo(s.sources), ce = nonDemo(s.exams), cb = nonDemo(s.bank);
  const counts = demo || cs.length + ce.length + cb.length === 0 ? null : { sources: cs.length, exams: ce.length, bankItems: cb.reduce((a, b) => a + (b.count ?? 0), 0) };
  return { highlights, counts };
}

/* ------------------------------------------------------------- capability-lab */
export function trend(points: Point[]) {
  const groups = new Map<string, Point[]>();
  for (const p of points) groups.set(p.capability, [...(groups.get(p.capability) ?? []), p]);
  return [...groups].map(([name, rows]) => {
    rows.sort((a, b) => (Date.parse(a.timestamp ?? "") || 0) - (Date.parse(b.timestamp ?? "") || 0));
    const last = rows.at(-1), prev = rows.at(-2);
    const measured = !!last && !!prev && last.value !== null && prev.value !== null && !!last.items && !!prev.items && !!last.timestamp && !!prev.timestamp;
    return { name, rows, unit: last?.unit ?? null, delta: measured ? Math.round((last!.value! - prev!.value!) * 1000) / 1000 : null };
  });
}
export const needsOwner = (p: Proposal): boolean => p.scope !== "other" || p.requiresHuman === true;
export function stageOf(raw: unknown): Stage {
  const t = typeof raw === "string" ? raw.toUpperCase() : "";
  return (STAGES as readonly string[]).includes(t) ? (t as Stage) : "UNKNOWN";
}
export function proposalStatus(p: Proposal, demo: boolean): ChipStatus {
  return demoize(p.stage === "UNKNOWN" ? "UNKNOWN" : "PARTIAL", demo);
}
export function buildCapability(s: { points: Point[]; proposals: Proposal[] }, demo: boolean) {
  const lines = trend(s.points);
  const highlights: Highlight[] = [
    ...s.proposals.map((p): Highlight => ({
      id: p.id, title: clean(p.title, 120), detail: `${p.stage}${needsOwner(p) ? " | owner" : ""}${p.redteam ? ` | ${p.redteam}` : ""}`,
      status: demo || p.demo ? "DEMO" : proposalStatus(p, false), tag: "proposal",
    })),
    ...lines.map((l): Highlight => ({
      id: `m-${l.name}`, title: l.name, detail: `Δ ${l.delta === null ? MISSING : l.delta} | n=${l.rows.length}`,
      status: demo || l.rows.every((r) => r.demo) ? "DEMO" : "PARTIAL", tag: "measurement",
    })),
  ];
  const cp = nonDemo(s.points), cr = nonDemo(s.proposals);
  const counts = demo || cp.length + cr.length === 0 ? null : {
    measurements: cp.length, proposals: cr.length, ownerGate: cr.filter(needsOwner).length,
  };
  return { lines, highlights, counts };
}

/* -------------------------------------------------------------- agent-center */
export type Presence = "ONLINE" | "UNKNOWN";
export function presenceOf(a: Pick<Agent, "heartbeat">, nowMs: number): Presence {
  if (!a.heartbeat) return "UNKNOWN";
  const t = Date.parse(a.heartbeat);
  if (!Number.isFinite(t)) return "UNKNOWN";
  const ageMin = (nowMs - t) / 60_000;
  return ageMin >= 0 && ageMin <= HEARTBEAT_MAX_MIN ? "ONLINE" : "UNKNOWN"; // future or old heartbeat proves nothing
}
export function presenceChip(p: Presence, demo: boolean): ChipStatus {
  return demo ? "DEMO" : p === "ONLINE" ? "LIVE" : "UNKNOWN";
}
const CRIT_RANK: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
const REG_RANK: Record<string, number> = { EXISTS: 0, PARTIAL: 1, PLANNED: 2, MISSING: 3 };
export function buildAgents(agents: Agent[], nowMs: number, demo: boolean) {
  const rows = agents.map((a) => ({ a, presence: presenceOf(a, nowMs) }));
  const sorted = [...rows].sort((x, y) =>
    (CRIT_RANK[x.a.criticality ?? ""] ?? 4) - (CRIT_RANK[y.a.criticality ?? ""] ?? 4) ||
    (REG_RANK[x.a.regStatus ?? ""] ?? 4) - (REG_RANK[y.a.regStatus ?? ""] ?? 4) || x.a.id.localeCompare(y.a.id));
  const highlights: Highlight[] = sorted.map(({ a, presence }) => ({
    id: a.id, title: `${a.id} ${clean(a.name, 60)}`, detail: `${REGISTERED} | ${a.regStatus ?? MISSING} | lane ${a.lane ?? MISSING}`,
    status: presenceChip(presence, demo || a.demo), tag: `${a.criticality ?? MISSING}`,
  }));
  const counted = rows.filter((r) => !r.a.demo);
  const by = (st: string) => counted.filter((r) => r.a.regStatus === st).length;
  const counts = demo || counted.length === 0 ? null : {
    registered: counted.length, online: counted.filter((r) => r.presence === "ONLINE").length,
    unknown: counted.filter((r) => r.presence === "UNKNOWN").length,
    exists: by("EXISTS"), partial: by("PARTIAL"), planned: by("PLANNED"), missing: by("MISSING"),
  };
  return { rows: sorted, highlights, counts };
}

/** Tolerant parser for config/university/sources.yaml (sources block only). */
export function parseUniversitySources(text: string): import("../contract/types").Source[] {
  const sources: import("../contract/types").Source[] = [];
  let cur: Record<string, string> | null = null;
  const flush = () => {
    if (!cur?.url) { cur = null; return; }
    let domain = cur.url;
    try { domain = new URL(cur.url).hostname; } catch { domain = cur.url; }
    const id = `src-${sources.length + 1}`;
    sources.push({
      demo: false,
      id,
      name: cur.url,
      domain,
      category: cur.faculty ?? "research",
      access: "registry",
      licence: cur.license ?? null,
      tosOk: null,
      authority: null,
      recency: null,
      trackRecord: null,
      citations: null,
      score: null,
    });
    cur = null;
  };
  const unq = (v: string) => v.trim().replace(/^["']|["']$/g, "");
  for (const line of text.split(/\r?\n/)) {
    const start = line.match(/^ {2}- url:\s*(.+?)\s*$/);
    if (start) { flush(); cur = { url: unq(start[1]) }; continue; }
    if (!cur) continue;
    if (/^\S/.test(line)) { flush(); continue; }
    const f = line.match(/^ {4}(license|faculty):\s*(.*?)\s*$/);
    if (f) cur[f[1]] = unq(f[2]);
  }
  flush();
  return sources;
}

/** Tolerant line parser for config/agent_registry.yaml (no YAML dependency). Unparseable => empty list. */
export function parseAgentRegistry(text: string): Agent[] {
  const agents: Agent[] = [];
  let cur: Record<string, string> | null = null;
  const flush = () => {
    if (cur && cur.agent_id) {
      const hb = cur.heartbeat ?? cur.last_heartbeat ?? cur.heartbeat_utc ?? null;
      agents.push({
        demo: false, id: cur.agent_id, name: cur.name ?? cur.agent_id, role: cur.form ?? null, regStatus: cur.status ?? null, lane: cur.lane ?? null,
        criticality: cur.criticality ?? null, liveFlag: cur.live === "true" ? true : cur.live === "false" ? false : null,
        heartbeat: hb && Number.isFinite(Date.parse(hb)) ? new Date(hb).toISOString() : null,
      });
    }
    cur = null;
  };
  const unq = (v: string) => v.trim().replace(/^["']|["']$/g, "");
  for (const line of text.split(/\r?\n/)) {
    const start = line.match(/^ {2}- agent_id:\s*(.+?)\s*$/);
    if (start) { flush(); cur = { agent_id: unq(start[1]) }; continue; }
    if (!cur) continue;
    if (/^\S/.test(line)) { flush(); continue; } // left the agents block
    const f = line.match(/^ {4}(name|status|lane|form|criticality|heartbeat|last_heartbeat|heartbeat_utc):\s*(.*?)\s*$/);
    if (f) { cur[f[1]] = unq(f[2]); continue; }
    const op = line.match(/^ {6}operability:\s*\{.*\blive:\s*(true|false)/);
    if (op) cur.live = op[1];
  }
  flush();
  return agents;
}

/* ------------------------------------------------------------------- real I/O */
export function parseBenchmark(text: string): Point[] {
  try {
    const j = JSON.parse(text) as { timestamp_utc?: unknown; results?: Record<string, Record<string, unknown>> };
    const ts = typeof j.timestamp_utc === "string" && Number.isFinite(Date.parse(j.timestamp_utc)) ? new Date(j.timestamp_utc).toISOString() : null;
    if (!j.results || typeof j.results !== "object") return [];
    const spec: Record<string, [string, string, string]> = {
      vectorized_backtest: ["evaluations_per_sec", "combinations_evaluated", "/s"],
      quantstats_tearsheet: ["latency_per_tearsheet_ms", "runs", "ms"],
      olap_analytics_bridge: ["latency_per_aggregation_ms", "runs", "ms"],
      streaming_drift_throughput: ["samples_per_sec", "samples", "/s"],
      event_driven_backtest: ["events_per_sec", "events_processed", "/s"],
    };
    const out: Point[] = [];
    for (const [name, [vk, ik, unit]] of Object.entries(spec)) {
      const r = j.results[name];
      if (!r || typeof r !== "object") continue;
      const v = r[vk], it = r[ik];
      out.push({ demo: false, capability: name, unit, timestamp: ts, value: typeof v === "number" && Number.isFinite(v) ? v : null, seed: null, items: typeof it === "number" && Number.isInteger(it) && it >= 0 ? it : null });
    }
    return out;
  } catch {
    return [];
  }
}
export function parseProposal(text: string): Proposal | null {
  try {
    const j = JSON.parse(text) as Record<string, unknown>;
    if (!j || typeof j !== "object" || typeof j.proposal_id !== "string") return null;
    const created = typeof j.created_ts === "number" && Number.isFinite(j.created_ts) ? new Date(j.created_ts * 1000).toISOString() : null;
    return {
      demo: false, id: j.proposal_id, stage: stageOf(j.current_stage),
      scope: j.governance_touching === true ? "rule" : "other",
      title: clean(typeof j.diagnosis === "string" ? j.diagnosis : typeof j.detected_by === "string" ? j.detected_by : "-", 200),
      requiresHuman: typeof j.requires_human === "boolean" ? j.requires_human : null,
      redteam: typeof j.redteam_verdict === "string" ? clean(j.redteam_verdict, 40) : null, createdAt: created,
    };
  } catch {
    return null;
  }
}
