/**
 * Server-only, READ-ONLY data access. Nothing here writes; every failure degrades to null
 * (the page then shows UNAVAILABLE / UNKNOWN, never a guess).
 * - DEMO contract: contract/ahos-arena-contract.example.json (all five pages)
 * - REAL: self-debug from the M13 soak runlog (ok=false rows) + soak_status.json (paper_only flag)
 * - weekly-exam (no ahos_replay exam file exists) and skill-market (/workspace/ahos-asi not on this machine) stay DEMO.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import example from "../contract/ahos-arena-contract.example.json";
import { validateContract } from "../contract/validate";
import type { AhosArenaContract } from "../contract/types";
import { parseSoakRunlog } from "./model";

export function loadContract(): AhosArenaContract | null {
  return validateContract(example) ? (example as unknown as AhosArenaContract) : null;
}

const SOAK_DIR = process.env.AHOS_SOAK_DIR ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M13_SOAK");
export const SOAK_RUNLOG_PATH = join(SOAK_DIR, "soak_runlog.jsonl");
export const SOAK_STATUS_PATH = join(SOAK_DIR, "soak_status.json");

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
