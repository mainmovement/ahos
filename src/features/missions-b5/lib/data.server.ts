/**
 * Server-only, READ-ONLY data access. Nothing here writes; every failure degrades to null/empty
 * (the page then shows UNAVAILABLE / UNKNOWN, never a guess).
 * - nightly-report: REAL, <repo>/reports/grok/M13_SOAK/<day>_{digest.json,judge.md,reconcile.md,tier_gate.md}
 * - agent-center:   REAL, <repo>/config/agent_registry.yaml (REGISTERED; presence UNKNOWN without a fresh heartbeat)
 * - capability-lab: REAL when <repo>/proposals/prop_*.json or <repo>/reports/benchmark_run_*.json exist, else DEMO
 * - university:     REAL only if <repo>/config/university/sources.yaml exists (no parser yet => stays DEMO/PLANNED)
 */
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import example from "../contract/ahos-arena-contract.example.json";
import { validateContract } from "../contract/validate";
import type { AhosArenaContract, AgentCenterSnapshot, CapabilityLabSnapshot, Night, NightlyReportSnapshot } from "../contract/types";
import { parseAgentRegistry, parseBenchmark, parseCriteria, parseDigest, parseJudgeNumbers, parseProposal, parseTier, parseVerdict } from "./model";

export function loadContract(): AhosArenaContract | null {
  return validateContract(example) ? (example as unknown as AhosArenaContract) : null;
}

export const REPO_DIR = process.env.AHOS_REPO_DIR ?? join(process.cwd(), "..", "ahos");
export const SOAK_DIR = process.env.AHOS_SOAK_DIR ?? join(REPO_DIR, "reports", "grok", "M13_SOAK");
export const REGISTRY_PATH = join(REPO_DIR, "config", "agent_registry.yaml");
export const UNIVERSITY_SOURCES_PATH = join(REPO_DIR, "config", "university", "sources.yaml");
export const PROPOSALS_DIR = join(REPO_DIR, "proposals");
export const REPORTS_DIR = join(REPO_DIR, "reports");

const read = (p: string): string | null => { try { return readFileSync(p, "utf8"); } catch { return null; } };
const mtime = (p: string): number | null => { try { return statSync(p).mtimeMs; } catch { return null; } };
const iso = (ms: number | null): string | null => (ms === null ? null : new Date(ms).toISOString());
const NIGHT_FILE = /^(\d{4}-\d{2}-\d{2})_(digest\.json|judge\.md|reconcile\.md|tier_gate\.md)$/;

export function readNightly(): NightlyReportSnapshot | null {
  let names: string[];
  try { names = readdirSync(SOAK_DIR); } catch { return null; }
  const days = new Set<string>();
  for (const n of names) { const m = n.match(NIGHT_FILE); if (m) days.add(m[1]); }
  if (days.size === 0) return null;
  const nights: Night[] = [];
  let latest: number | null = null;
  for (const day of [...days].sort()) {
    const f = (suffix: string) => join(SOAK_DIR, `${day}_${suffix}`);
    const digest = parseDigest(read(f("digest.json")));
    const judgeText = read(f("judge.md"));
    const judge = parseVerdict(judgeText);
    const nums = parseJudgeNumbers(judgeText);
    const tierText = read(f("tier_gate.md"));
    const ms = ["digest.json", "judge.md", "reconcile.md", "tier_gate.md"].map((s) => mtime(f(s))).filter((x): x is number => x !== null);
    const ts = ms.length ? Math.max(...ms) : null;
    if (ts !== null && (latest === null || ts > latest)) latest = ts;
    nights.push({
      demo: false, id: `soak-${day}`, day: digest.day ?? day, timestamp: iso(ts), entries: digest.entries, closed: nums.closed, wins: nums.wins, losses: nums.losses, pnl: nums.pnl,
      judge, reconcile: parseVerdict(read(f("reconcile.md"))), tier: parseTier(tierText), criteria: parseCriteria(tierText), signed: digest.signed, ai: false,
    });
  }
  return { kind: "nightlyReport", executionMode: "PAPER_ONLY", realTrading: false, source: "M13_SOAK/*_digest.json|judge.md|reconcile.md|tier_gate.md", generatedAt: iso(latest), demo: false, nights };
}

export function readAgentRegistry(): AgentCenterSnapshot | null {
  const text = read(REGISTRY_PATH);
  if (!text) return null;
  const agents = parseAgentRegistry(text);
  if (agents.length === 0) return null;
  return { kind: "agentCenter", executionMode: "PAPER_ONLY", realTrading: false, source: "config/agent_registry.yaml", generatedAt: iso(mtime(REGISTRY_PATH)), demo: false, agents };
}

export function readCapabilityLab(): CapabilityLabSnapshot | null {
  const proposals: CapabilityLabSnapshot["proposals"] = [];
  const points: CapabilityLabSnapshot["points"] = [];
  const stamps: number[] = [];
  try {
    for (const n of readdirSync(PROPOSALS_DIR)) {
      if (!/^prop_[\w-]+\.json$/.test(n)) continue;
      const t = read(join(PROPOSALS_DIR, n));
      const p = t ? parseProposal(t) : null;
      if (p) { proposals.push(p); const ms = mtime(join(PROPOSALS_DIR, n)); if (ms !== null) stamps.push(ms); }
    }
  } catch { /* proposals dir optional */ }
  try {
    for (const n of readdirSync(REPORTS_DIR)) {
      if (!/^benchmark_run_[\w-]+\.json$/.test(n)) continue;
      const t = read(join(REPORTS_DIR, n));
      const ps = t ? parseBenchmark(t) : [];
      if (ps.length) { points.push(...ps); for (const p of ps) if (p.timestamp) stamps.push(Date.parse(p.timestamp)); }
    }
  } catch { /* reports dir optional */ }
  if (proposals.length === 0 && points.length === 0) return null;
  const gen = points.map((p) => p.timestamp).concat(proposals.map((p) => p.createdAt)).filter((x): x is string => !!x).sort().at(-1) ?? null;
  return { kind: "capabilityLab", executionMode: "PAPER_ONLY", realTrading: false, source: "proposals/prop_*.json + reports/benchmark_run_*.json", generatedAt: gen, demo: false, points, proposals };
}

export const universityRealSourceExists = (): boolean => existsSync(UNIVERSITY_SOURCES_PATH);
