import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { SOAK_DIR } from "../../missions-b5/lib/data.server";
import type { WhiteHatsSnapshot } from "../types";
import { buildSoakWhiteHatsSnapshot } from "./soak-snapshot";

const read = (p: string): string | null => {
  try {
    return readFileSync(p, "utf8");
  } catch {
    return null;
  }
};

const iso = (p: string): string | null => {
  try {
    return new Date(statSync(p).mtimeMs).toISOString();
  } catch {
    return null;
  }
};

/** REAL binding: soak_status.json + latest *_judge.md / *_reconcile.md */
export function readWhiteHatsSoakSnapshot(): WhiteHatsSnapshot | null {
  const statusPath = join(SOAK_DIR, "soak_status.json");
  const raw = read(statusPath);
  if (!raw) return null;
  let soak: Record<string, unknown>;
  try {
    soak = JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
  let names: string[] = [];
  try {
    names = readdirSync(SOAK_DIR);
  } catch {
    return null;
  }
  const days = names
    .map((n) => n.match(/^(\d{4}-\d{2}-\d{2})_judge\.md$/)?.[1])
    .filter((d): d is string => !!d)
    .sort();
  const day = days.at(-1);
  if (!day) return null;
  const judgePath = join(SOAK_DIR, `${day}_judge.md`);
  const reconPath = join(SOAK_DIR, `${day}_reconcile.md`);
  const stamps = [statusPath, judgePath, reconPath].map(iso).filter((x): x is string => !!x);
  const generatedAt = stamps.length ? stamps.sort().at(-1)! : iso(statusPath);
  return buildSoakWhiteHatsSnapshot({
    soak,
    judgeText: read(judgePath),
    reconcileText: read(reconPath),
    generatedAt,
    sourceLabel: "reports/grok/M13_SOAK/soak_status.json + *_judge.md + *_reconcile.md",
  });
}
