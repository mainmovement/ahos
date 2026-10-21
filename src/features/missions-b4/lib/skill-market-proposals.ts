import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { parseProposal } from "../../missions-b5/lib/model";
import type { ReviewState, SkillMarketEntry, SkillMarketSnapshot } from "../contract/types";

function reviewOf(redteam: string | null, requiresHuman: boolean | null): { reviewState: ReviewState; reason: string | null } {
  const token = (redteam ?? "").toUpperCase();
  if (token.includes("REJECT") || token === "FAIL" || token === "FAILED") {
    return { reviewState: "REJECTED", reason: redteam };
  }
  if (token.includes("PASS") || token === "APPROVED" || token === "CLEAN") {
    return { reviewState: "REVIEWED", reason: redteam };
  }
  const pending = requiresHuman ? "requires_human approval" : null;
  return { reviewState: "UNREVIEWED", reason: redteam ?? pending };
}

/** Lane B proposal queue on disk — not the ahos-asi skill registry (M52 display-only). */
export function buildSkillMarketFromProposals(proposalsDir: string): SkillMarketSnapshot | null {
  let names: string[];
  try {
    names = readdirSync(proposalsDir);
  } catch {
    return null;
  }
  const entries: SkillMarketEntry[] = [];
  const stamps: number[] = [];
  for (const n of names) {
    if (!/^prop_[\w-]+\.json$/.test(n)) continue;
    const path = join(proposalsDir, n);
    const text = readFileSync(path, "utf8");
    const p = parseProposal(text);
    if (!p) continue;
    const { reviewState, reason } = reviewOf(p.redteam, p.requiresHuman);
    entries.push({
      id: p.id,
      name: p.title,
      kind: "skill",
      version: p.stage,
      source: `proposals/${n}`,
      installState: p.requiresHuman ? "BLOCKED" : "AVAILABLE",
      permissions: ["Lane B change proposal (read-only)"],
      reviewState,
      reason,
      demo: false,
    });
    const ms = statSync(path).mtimeMs;
    if (Number.isFinite(ms)) stamps.push(ms);
  }
  if (entries.length === 0) return null;
  const generatedAt = stamps.length ? new Date(Math.max(...stamps)).toISOString() : null;
  return {
    kind: "skillMarket",
    executionMode: "PAPER_ONLY",
    realTrading: false,
    source: "proposals/prop_*.json (not ahos-asi registry)",
    generatedAt,
    demo: false,
    entries,
  };
}
