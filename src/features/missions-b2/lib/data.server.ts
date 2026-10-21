/**
 * Server-only, READ-ONLY data access. Nothing here writes, and every failure
 * degrades to null (the page then shows UNKNOWN / UNAVAILABLE, never a guess).
 * Single contract file: contract/ahos-arena-contract.example.json (DEMO).
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import example from "../contract/ahos-arena-contract.example.json";
import { validateContract } from "../contract/validate";
import type { AHOSArenaContract, MessageHubSnapshot, ResearchInstituteSnapshot, SelfEvaluationSnapshot } from "../contract/types";
import { buildResearchFromReplay } from "./research-replay";
import { headerConflicts, parseMissionsStatus, type ParsedMissions } from "./missions-status";
import { parseMissionsFromSoakTierGate } from "./missions-soak-fallback";

const SOAK_STATUS_FOR_MISSIONS =
  process.env.AHOS_SOAK_DIR ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M13_SOAK");
const SOAK_STATUS_MISSIONS_PATH = join(SOAK_STATUS_FOR_MISSIONS, "soak_status.json");

export function loadContract(): AHOSArenaContract | null {
  return validateContract(example) ? (example as unknown as AHOSArenaContract) : null;
}

function readFileInfo(path: string): { text: string; mtimeIso: string } | null {
  try {
    const st = statSync(path);
    return { text: readFileSync(path, "utf8"), mtimeIso: new Date(st.mtimeMs).toISOString() };
  } catch {
    return null;
  }
}

export const MISSIONS_STATUS_PATH = process.env.AHOS_MISSIONS_STATUS_PATH ?? join(process.cwd(), "..", "ahos_assets", "MISSIONS_STATUS.md");
export const IDEA_SHELF_PATH = join(process.cwd(), "config", "idea_shelf.json");
export const MESSAGE_HUB_SNAPSHOT_PATH =
  process.env.AHOS_MESSAGE_HUB_SNAPSHOT_PATH ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M35", "message_hub_snapshot.json");

export const SELF_EVAL_SNAPSHOT_PATH =
  process.env.AHOS_SELF_EVAL_SNAPSHOT_PATH ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M58", "self_eval_snapshot.json");
export const RESEARCH_REPLAY_PATH =
  process.env.AHOS_RESEARCH_REPLAY_PATH ?? join(process.cwd(), "..", "ahos_replay", "results.md");

export function readResearchReplay(): ResearchInstituteSnapshot | null {
  const f = readFileInfo(RESEARCH_REPLAY_PATH);
  if (!f) return null;
  return buildResearchFromReplay(f.text, f.mtimeIso);
}

export function readSelfEvaluation(): SelfEvaluationSnapshot | null {
  const f = readFileInfo(SELF_EVAL_SNAPSHOT_PATH);
  if (!f) return null;
  try {
    const j = JSON.parse(f.text) as { selfEvaluation?: SelfEvaluationSnapshot };
    const se = j.selfEvaluation;
    if (!se || !Array.isArray(se.scorecards)) return null;
    return { ...se, demo: false, generatedAt: se.generatedAt ?? f.mtimeIso };
  } catch {
    return null;
  }
}

export function readMessageHub(): MessageHubSnapshot | null {
  const f = readFileInfo(MESSAGE_HUB_SNAPSHOT_PATH);
  if (!f) return null;
  try {
    const j = JSON.parse(f.text) as { messageHub?: MessageHubSnapshot };
    const hub = j.messageHub;
    if (!hub || typeof hub !== "object" || !Array.isArray(hub.channels)) return null;
    return { ...hub, demo: false, generatedAt: hub.generatedAt ?? f.mtimeIso };
  } catch {
    return null;
  }
}

export function readMissionsStatus(): { parsed: ParsedMissions; generatedAt: string; conflict: boolean; soakFallback?: boolean } | null {
  const f = readFileInfo(MISSIONS_STATUS_PATH);
  if (f) {
    const parsed = parseMissionsStatus(f.text);
    if (!parsed) return null;
    return { parsed, generatedAt: parsed.generatedAt ?? f.mtimeIso, conflict: headerConflicts(parsed) };
  }
  const soakFile = readFileInfo(SOAK_STATUS_MISSIONS_PATH);
  if (!soakFile) return null;
  try {
    const raw = JSON.parse(soakFile.text) as Record<string, unknown>;
    const parsed = parseMissionsFromSoakTierGate(raw);
    if (!parsed) return null;
    return {
      parsed,
      generatedAt: parsed.generatedAt ?? soakFile.mtimeIso,
      conflict: false,
      soakFallback: true,
    };
  } catch {
    return null;
  }
}

export function readIdeaShelf(): { raw: unknown; mtimeIso: string } | null {
  const f = readFileInfo(IDEA_SHELF_PATH);
  if (!f) return null;
  try {
    return { raw: JSON.parse(f.text), mtimeIso: f.mtimeIso };
  } catch {
    return null;
  }
}
