/** Server-only READ-ONLY file access for batch 14 (soak ledger + replay). Every failure => missing/malformed, never a guess. */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { parseJudgeMd, parseLessons, parseReplaySummary, parseSoakStatus, parseTradesCsv, type JudgeView, type LessonsSummary, type Loaded, type PaperLedgerView, type ReplaySummary, type TradesSummary } from "./model";

export const SOAK_STATUS_FILE = process.env.AHOS_SOAK_STATUS_PATH ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M13_SOAK", "soak_status.json");
export const REPLAY_DIR = process.env.AHOS_REPLAY_DIR ?? (process.env.AHOS_REPLAY_RESULTS_PATH ? dirname(process.env.AHOS_REPLAY_RESULTS_PATH) : join(process.cwd(), "..", "ahos_replay"));
export const REPLAY_MARKETS = ["gold", "oil", "gold_hourly", "oil_hourly"] as const;
export type ReplayMarket = (typeof REPLAY_MARKETS)[number];

function readText(path: string): { text: string; mtimeIso: string } | null {
  try { return { text: readFileSync(path, "utf8"), mtimeIso: new Date(statSync(path).mtimeMs).toISOString() }; } catch { return null; }
}
function load<T>(path: string, parse: (t: string) => T | null): Loaded<T> {
  const f = readText(path);
  if (!f) return { state: "missing" };
  let v: T | null = null;
  try { v = parse(f.text); } catch { v = null; }
  return v === null ? { state: "malformed" } : { state: "ok", value: v, mtimeIso: f.mtimeIso };
}

export function loadSoakLedger(nowMs: number, path = SOAK_STATUS_FILE): Loaded<PaperLedgerView> {
  return load(path, (t) => parseSoakStatus(JSON.parse(t), nowMs));
}
/** Newest *_judge.md next to soak_status.json (file names start with the ISO day). */
export function loadLatestJudge(path = SOAK_STATUS_FILE): Loaded<JudgeView> & { file?: string } {
  let names: string[] = [];
  try { names = readdirSync(dirname(path)).filter((n) => /^\d{4}-\d{2}-\d{2}_judge\.md$/.test(n)).sort(); } catch { return { state: "missing" }; }
  const name = names[names.length - 1];
  if (!name) return { state: "missing" };
  return { ...load(join(dirname(path), name), parseJudgeMd), file: name };
}
export function loadReplaySummary(dir = REPLAY_DIR): Loaded<ReplaySummary> { return load(join(dir, "results.md"), parseReplaySummary); }
export function loadReplayLessons(dir = REPLAY_DIR): Loaded<LessonsSummary> { return load(join(dir, "lessons.md"), parseLessons); }
export function loadReplayTrades(market: ReplayMarket, dir = REPLAY_DIR): Loaded<TradesSummary> { return load(join(dir, "out", market, "trades.csv"), parseTradesCsv); }
export function equityImagePath(market: string, dir = REPLAY_DIR): string | null {
  return (REPLAY_MARKETS as readonly string[]).includes(market) ? join(dir, "out", `equity_${market}.png`) : null;
}
