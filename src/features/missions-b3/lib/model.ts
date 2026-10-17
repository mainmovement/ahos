/**
 * AHOS Arena - missions batch 11 (health-monitor, lessons, workroom, portable, oil-gold).
 * Pure logic only: no React, no fs, no net. Asserted by scripts/missions_b3_selftest.ts.
 * Truth rules: DEMO is never LIVE; no timestamp => UNKNOWN; missing numbers are "-" (never 0);
 * an unreachable/unknown probe is never LIVE; replay results are never presented as live.
 */
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { freshness, redact, type Highlight } from "@/src/features/missions-b2/lib/model";
import type { Mission } from "@/src/features/missions-b2/contract/types";
import type { HealthSnapshot, LessonRecord, MissionRecord, OilGoldSnapshot } from "../contract/types";

export type ProbeResult = "open" | "closed" | "unknown";
export const SOAK_MIN_STALE_MS = 30 * 60 * 1000;

type TS = HealthSnapshot["services"][number]["status"];
const ts = (s: ChipStatus): TS => (s === "SIMULATED" ? "DEMO" : s === "EMPTY" || s === "LOADING" ? "UNKNOWN" : (s as TS));

export function probeStatus(p: ProbeResult): ChipStatus {
  return p === "open" ? "LIVE" : p === "closed" ? "UNAVAILABLE" : "UNKNOWN";
}

export function resolveRamGuardState(s: HealthSnapshot): "ARMED" | "TRIPPED" | "UNKNOWN" {
  const r = s.ramGuard;
  if (r.usedGb === null || r.limitGb === null || r.headroomGb === null || r.limitGb <= 0) return "UNKNOWN";
  return r.state;
}

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown): string | null => (typeof v === "string" && v.length > 0 ? v : null);
const numOrNull = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

export interface SoakView {
  snapshot: HealthSnapshot;
  status: ChipStatus;
  highlights: Highlight[];
  breakerState: string | null;
  witnessState: string | null;
  mode: string;
  real: boolean;
}

/** REAL binding: reports/grok/M13_SOAK/soak_status.json (read-only). Returns null when the shape is not recognisable. */
export function healthFromSoak(raw: unknown, probes: { bridge: ProbeResult; arena: ProbeResult }, fileMtimeIso: string, nowMs: number): SoakView | null {
  if (!isObj(raw) || typeof raw.soak !== "string") return null;
  const last = isObj(raw.last_cycle) ? raw.last_cycle : null;
  const lastTs = last ? str(last.ts) : null;
  const interval = numOrNull(raw.cycle_interval_sec);
  const staleMs = Math.max(SOAK_MIN_STALE_MS, interval === null ? 0 : interval * 2000);
  const runner = freshness("file", lastTs, nowMs, staleMs);
  const paper = raw.paper_only === true;
  const ledger = isObj(raw.ledger_state) ? raw.ledger_state : null;
  const breaker = ledger && isObj(ledger.breaker) ? str(ledger.breaker.state) : last && isObj(last.breaker) ? str(last.breaker.state) : null;
  const witness = last ? str(last.witness_state) : null;
  const started = str(raw.started_hint);
  const startedMs = started ? Date.parse(started) : NaN;
  const planned = numOrNull(raw.planned_days);
  const failed = numOrNull(raw.cycles_failed);
  const gate = isObj(raw.last_tier_gate) ? raw.last_tier_gate : null;
  const recon = isObj(raw.last_m42_reconcile) ? raw.last_m42_reconcile : null;
  const ledgerError = last ? str(last.ledger_error) : null;
  const snapshot: HealthSnapshot = {
    executionMode: paper ? "PAPER_ONLY" : null,
    realTrading: paper ? false : null,
    source: "reports/grok/M13_SOAK/soak_status.json",
    generatedAt: lastTs ?? fileMtimeIso,
    demo: false,
    availability: "AVAILABLE",
    services: [
      { demo: false, name: `soak runner (${raw.soak})`, status: ts(runner), lastHeartbeat: lastTs, version: null, uptimeSeconds: null },
      { demo: false, name: "bridge :8787", status: ts(probeStatus(probes.bridge)), lastHeartbeat: null, version: null, uptimeSeconds: null },
      { demo: false, name: "arena :3200", status: ts(probeStatus(probes.arena)), lastHeartbeat: null, version: null, uptimeSeconds: null },
    ],
    soak: {
      currentRun: str(raw.soak),
      elapsedHours: Number.isFinite(startedMs) ? Math.max(0, Math.round(((nowMs - startedMs) / 3_600_000) * 10) / 10) : null,
      targetHours: planned === null ? null : Math.round(planned * 24 * 10) / 10,
      restarts: null,
      lastError: ledgerError ?? (failed !== null && failed > 0 ? `cycles_failed=${failed}` : null),
    },
    ramGuard: { usedGb: null, limitGb: null, headroomGb: null, state: "UNKNOWN" },
    faults: [],
  };
  const hl: Highlight[] = [
    { id: "runner", title: `soak ${raw.soak}`, detail: lastTs ? `cycle ${last && numOrNull(last.cycle) !== null ? last.cycle : "-"} | ok ${numOrNull(raw.cycles_ok) ?? "-"} / failed ${failed ?? "-"}` : null, status: runner, tag: paper ? "PAPER_ONLY" : null },
    { id: "bridge", title: "bridge :8787", detail: probes.bridge, status: probeStatus(probes.bridge) },
    { id: "arena", title: "arena :3200", detail: probes.arena, status: probeStatus(probes.arena) },
    { id: "breaker", title: "circuit breaker", detail: breaker, status: breaker === null ? "UNKNOWN" : breaker === "ARMED" ? runner : "ERROR" },
    { id: "witness", title: "price witness", detail: witness === null ? null : redact(`${witness}${last && str(last.witness_reason) ? ` - ${str(last.witness_reason)}` : ""}`), status: witness === "RESOLVED" ? runner : witness === null ? "UNKNOWN" : "PARTIAL" },
  ];
  if (gate) hl.push({ id: "tier-gate", title: "tier gate", detail: `tier ${str(gate.tier) ?? "-"} | owner review: ${gate.ready_for_owner_review === true ? "ready" : "not ready"}`, status: gate.ready_for_owner_review === true ? "PARTIAL" : "PARTIAL", tag: str(gate.day) });
  hl.push({ id: "ram", title: "RAM guard", detail: null, status: "UNKNOWN" });
  if (recon && str(recon.verdict) && recon.verdict !== "OK") hl.push({ id: "reconcile", title: "M42 reconcile", detail: String(recon.verdict), status: "UNKNOWN" });
  return { snapshot, status: runner, highlights: hl, breakerState: breaker, witnessState: witness, mode: snapshot.executionMode ?? "UNKNOWN", real: snapshot.realTrading ?? true };
}

/** ACCEPTED is only legal with a complete passed unseen test; otherwise it is shown as PROPOSED. */
export function normalizeLesson(l: LessonRecord): LessonRecord {
  const t = l.unseenTest;
  const ok = t?.result === "PASS" && !!t.datasetId && !!t.outOfSamplePeriod && t.sampleSize !== null && t.sampleSize > 0;
  return l.status === "ACCEPTED" && !ok ? { ...l, status: "PROPOSED" } : l;
}
export function lessonHighlights(ls: LessonRecord[], demo: boolean): Highlight[] {
  return ls.map(normalizeLesson).map((l) => ({
    id: l.id,
    title: redact(l.lesson),
    detail: redact(l.reason),
    status: (l.status === "REJECTED" ? "REJECTED" : l.status === "ACCEPTED" && !demo ? "LIVE" : demo ? "DEMO" : "PARTIAL") as ChipStatus,
    tag: `${l.market} | ${l.status}`,
  }));
}

export function toMission(r: MissionRecord): Mission {
  return { id: r.id, title: r.title, group: "M", state: r.status === "NOT STARTED" ? "NOT_STARTED" : r.status, blockedOwner: false, evidence: r.evidence, lastUpdate: r.lastUpdate, caveat: null };
}

export function portableHighlights(s: { checklist: Record<string, string>; hardware: { tier: string; ramGb: number | null; heavyFeaturesAllowed: boolean | null } }, demo: boolean): Highlight[] {
  const st = (v: string): ChipStatus => (demo ? "DEMO" : v === "DONE" ? "LIVE" : v === "PARTIAL" ? "PARTIAL" : v === "NOT STARTED" ? "PLANNED" : "UNKNOWN");
  const hl: Highlight[] = Object.entries(s.checklist).map(([k, v]) => ({ id: k, title: k, detail: v, status: st(v) }));
  hl.unshift({ id: "tier", title: `tier ${s.hardware.tier}`, detail: s.hardware.ramGb === null ? null : `${s.hardware.ramGb} GB`, status: demo ? "DEMO" : s.hardware.tier === "UNKNOWN" ? "UNKNOWN" : "LIVE" });
  return hl;
}

export interface ReplayView {
  title: string | null;
  lines: string[];
  edge: "NO_PROVEN_EDGE";
}
/** results.md is replay output only. It is never live and never proves an edge by itself. */
export function parseReplayResults(text: string | null): ReplayView | null {
  if (!text || text.trim().length === 0) return null;
  const rows = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const title = rows.find((l) => /^#\s/.test(l))?.replace(/^#\s+/, "") ?? null;
  return { title: title ? redact(title) : null, lines: rows.filter((l) => !/^#/.test(l)).slice(0, 8).map((l) => redact(l).slice(0, 200)), edge: "NO_PROVEN_EDGE" };
}

export function oilGoldHighlights(s: OilGoldSnapshot, replay: ReplayView | null, demo: boolean): Highlight[] {
  const live = s.live.timestamp !== null && s.live.source !== null && s.live.status === "LIVE" && !demo;
  return [
    { id: "edge", title: "no proven edge yet", detail: s.evidence.note, status: "PARTIAL", tag: "NO_PROVEN_EDGE" },
    { id: "live", title: "live price", detail: live ? `oil ${s.live.oil ?? "-"} | gold ${s.live.gold ?? "-"}` : null, status: live ? "LIVE" : demo ? "DEMO" : "UNKNOWN" },
    { id: "replay", title: "historical replay", detail: replay ? (replay.title ?? "results.md") : s.replay.summary, status: replay ? "PARTIAL" : demo ? "DEMO" : "MISSING", tag: replay ? "REPLAY_NOT_LIVE" : null },
    { id: "news", title: "oil / gold news", detail: null, status: demo ? "DEMO" : "UNKNOWN" },
    { id: "other", title: "other markets", detail: null, status: "PLANNED" },
  ];
}
