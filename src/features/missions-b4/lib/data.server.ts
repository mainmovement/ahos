/**
 * Server-only, READ-ONLY data access. Nothing here writes; every failure degrades to null
 * (the page then shows UNAVAILABLE / UNKNOWN, never a guess).
 * - DEMO contract: contract/ahos-arena-contract.example.json (all five pages)
 * - REAL: self-debug from the M13 soak runlog (ok=false rows) + soak_status.json (paper_only flag)
 * - weekly-exam + science-radar + news-center: partial REAL from soak_status.json.
 * - skill-market: partial REAL from proposals/prop_*.json (not ahos-asi skill registry).
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import example from "../contract/ahos-arena-contract.example.json";
import { validateContract } from "../contract/validate";
import type { AhosArenaContract } from "../contract/types";
import { PROPOSALS_DIR } from "../../missions-b5/lib/data.server";
import { parseSoakRunlog } from "./model";
import { buildNewsCenterFromSoak } from "./news-center-soak";
import { buildScienceRadarFromSoak } from "./science-radar-soak";
import { buildSkillMarketFromProposals } from "./skill-market-proposals";
import { buildWeeklyExamFromSoak } from "./weekly-exam-soak";
import type { NewsCenterSnapshot, ScienceRadarSnapshot, SkillMarketSnapshot, WeeklyExamSnapshot } from "../contract/types";

export function loadContract(): AhosArenaContract | null {
  return validateContract(example) ? (example as unknown as AhosArenaContract) : null;
}

const SOAK_DIR = process.env.AHOS_SOAK_DIR ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M13_SOAK");
export const SOAK_RUNLOG_PATH = join(SOAK_DIR, "soak_runlog.jsonl");
export const SOAK_STATUS_PATH = join(SOAK_DIR, "soak_status.json");

function readSoakStatusFile(): { raw: Record<string, unknown>; mtimeIso: string } | null {
  try {
    const st = statSync(SOAK_STATUS_PATH);
    const raw = JSON.parse(readFileSync(SOAK_STATUS_PATH, "utf8")) as Record<string, unknown>;
    return { raw, mtimeIso: new Date(st.mtimeMs).toISOString() };
  } catch {
    return null;
  }
}

export function readWeeklyExamSoak(): WeeklyExamSnapshot | null {
  const f = readSoakStatusFile();
  if (!f) return null;
  return buildWeeklyExamFromSoak(f.raw, f.mtimeIso);
}

export function readScienceRadarSoak(): ScienceRadarSnapshot | null {
  const f = readSoakStatusFile();
  if (!f) return null;
  return buildScienceRadarFromSoak(f.raw, f.mtimeIso);
}

export function readNewsCenterSoak(): NewsCenterSnapshot | null {
  const f = readSoakStatusFile();
  if (!f) return null;
  return buildNewsCenterFromSoak(f.raw, f.mtimeIso);
}

export function readSkillMarketProposals(): SkillMarketSnapshot | null {
  return buildSkillMarketFromProposals(PROPOSALS_DIR);
}

export function readSoakDebug(): { incidents: ReturnType<typeof parseSoakRunlog>; paperOnly: boolean | null; mtimeIso: string } | null {
  try {
    const st = statSync(SOAK_RUNLOG_PATH);
    const parsed = parseSoakRunlog(readFileSync(SOAK_RUNLOG_PATH, "utf8"));
    if (parsed.rows === 0) return null;
    let paperOnly: boolean | null = null;
    try {
      const s = JSON.parse(readFileSync(SOAK_STATUS_PATH, "utf8")) as { paper_only?: unknown };
      paperOnly = typeof s.paper_only === "boolean" ? s.paper_only : null;
    } catch { /* status file optional */ }
    return { incidents: parsed, paperOnly, mtimeIso: new Date(st.mtimeMs).toISOString() };
  } catch {
    return null;
  }
}
