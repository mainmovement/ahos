/**
 * Server-only, READ-ONLY data access. Nothing here writes, and every failure
 * degrades to null (the page then shows UNKNOWN / UNAVAILABLE, never a guess).
 * Single contract file: contract/ahos-arena-contract.example.json (DEMO).
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import example from "../contract/ahos-arena-contract.example.json";
import { validateContract } from "../contract/validate";
import type { AHOSArenaContract } from "../contract/types";
import { headerConflicts, parseMissionsStatus, type ParsedMissions } from "./missions-status";

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

export function readMissionsStatus(): { parsed: ParsedMissions; generatedAt: string; conflict: boolean } | null {
  const f = readFileInfo(MISSIONS_STATUS_PATH);
  if (!f) return null;
  const parsed = parseMissionsStatus(f.text);
  if (!parsed) return null;
  return { parsed, generatedAt: parsed.generatedAt ?? f.mtimeIso, conflict: headerConflicts(parsed) };
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
