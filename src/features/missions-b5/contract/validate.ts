/** Runtime validator, zero dependencies. Returns null on invalid input; never throws into the UI. */
import { STAGES, type AhosArenaContract } from "./types";

type Guard = (v: unknown) => boolean;
const str: Guard = (v) => typeof v === "string";
const bool: Guard = (v) => typeof v === "boolean";
const num: Guard = (v) => typeof v === "number" && Number.isFinite(v);
const nat: Guard = (v) => num(v) && Number.isInteger(v) && (v as number) >= 0;
const nullable = (g: Guard): Guard => (v) => v === null || g(v);
const iso: Guard = (v) => typeof v === "string" && /^\d{4}-\d{2}-\d{2}T/.test(v) && Number.isFinite(Date.parse(v));
const oneOf = (vals: readonly unknown[]): Guard => (v) => vals.includes(v);
const obj = (shape: Record<string, Guard>): Guard => (v) => {
  if (!v || typeof v !== "object" || Array.isArray(v)) return false;
  const o = v as Record<string, unknown>;
  return Object.keys(o).every((k) => k in shape) && Object.entries(shape).every(([k, g]) => k in o && g(o[k]));
};
const arr = (g: Guard): Guard => (v) => Array.isArray(v) && v.length <= 10000 && v.every(g);
const ci: Guard = (v) => v === null || (Array.isArray(v) && v.length === 2 && v.every(num) && (v[0] as number) <= (v[1] as number));
const n = nullable(num), s = nullable(str), d = nullable(iso), c = nullable(nat), b = nullable(bool);

const meta = (kind: string) => ({ kind: oneOf([kind]), executionMode: str, realTrading: bool, source: s, generatedAt: d, demo: bool });
const row = (shape: Record<string, Guard>) => obj({ demo: bool, ...shape });

const schema = obj({
  executionMode: str, realTrading: bool, source: str, generatedAt: d,
  nightlyReport: obj({
    ...meta("nightlyReport"),
    nights: arr(row({ id: str, day: s, timestamp: d, entries: c, closed: c, wins: c, losses: c, pnl: n, judge: s, reconcile: s, tier: nullable((v) => nat(v) && (v as number) <= 4), criteria: s, signed: b, ai: bool })),
  }),
  university: obj({
    ...meta("university"),
    sources: arr(row({ id: str, name: str, domain: str, category: str, access: s, licence: s, tosOk: b, authority: n, recency: n, trackRecord: n, citations: n, score: n })),
    exams: arr(row({ agent: str, week: s, score: nullable((v) => num(v) && (v as number) >= 0 && (v as number) <= 100), items: c, ci, hash: s, retests: nullable((v) => nat(v) && (v as number) <= 3) })),
    bank: arr(row({ domain: str, skill: str, count: c })),
  }),
  capabilityLab: obj({
    ...meta("capabilityLab"),
    points: arr(row({ capability: str, unit: s, timestamp: d, value: n, seed: c, items: c })),
    proposals: arr(row({ id: str, stage: oneOf([...STAGES, "UNKNOWN"]), scope: oneOf(["rule", "money", "tier", "new-agent", "other"]), title: str, requiresHuman: b, redteam: s, createdAt: d })),
  }),
  agentCenter: obj({
    ...meta("agentCenter"),
    agents: arr(row({ id: str, name: str, role: s, regStatus: s, lane: s, criticality: s, liveFlag: b, heartbeat: d })),
  }),
});

export function validateContract(input: unknown): AhosArenaContract | null {
  try { return schema(input) ? (input as AhosArenaContract) : null; } catch { return null; }
}
