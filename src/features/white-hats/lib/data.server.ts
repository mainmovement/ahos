import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { REPO_DIR, SOAK_DIR } from "../../missions-b5/lib/data.server";

import type { WhiteHatsSnapshot } from "../types";
import { buildSoakWhiteHatsSnapshot } from "./soak-snapshot";

const M42_DIR = join(REPO_DIR, "reports", "grok", "M42");

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

function latestReconcileMd(dir: string): { day: string; path: string } | null {
  let names: string[] = [];
  try {
    names = readdirSync(dir);
  } catch {
    return null;
  }
  const days = names
    .map((n) => n.match(/^(\d{4}-\d{2}-\d{2})_reconcile\.md$/)?.[1])
    .filter((d): d is string => !!d)
    .sort();
  const day = days.at(-1);
  return day ? { day, path: join(dir, `${day}_reconcile.md`) } : null;
}

function readReconcileForJudgeDay(judgeDay: string): { text: string | null; label: string } {
  const soakPath = join(SOAK_DIR, `${judgeDay}_reconcile.md`);
  const soakText = read(soakPath);
  if (soakText) return { text: soakText, label: `M13_SOAK/${judgeDay}_reconcile.md` };
  const m42 = latestReconcileMd(M42_DIR);
  if (m42) {
    return { text: read(m42.path), label: `M42/${m42.day}_reconcile.md` };
  }
  return { text: null, label: "reconcile.md (missing)" };
}

/** REAL binding: soak_status.json + latest *_judge.md / *_reconcile.md (M13 or M42) */
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
  const recon = readReconcileForJudgeDay(day);
  const stampPaths = [statusPath, judgePath];
  if (recon.text) {
    if (recon.label.startsWith("M42/")) {
      const m42 = latestReconcileMd(M42_DIR);
      if (m42) stampPaths.push(m42.path);
    } else {
      stampPaths.push(join(SOAK_DIR, `${day}_reconcile.md`));
    }
  }
  const stamps = stampPaths.map(iso).filter((x): x is string => !!x);
  const generatedAt = stamps.length ? stamps.sort().at(-1)! : iso(statusPath);
  return buildSoakWhiteHatsSnapshot({
    soak,
    judgeText: read(judgePath),
    reconcileText: recon.text,
    generatedAt,
    sourceLabel: `M13_SOAK soak_status + ${day}_judge.md + ${recon.label}`,
  });
}
