/** Server-only, READ-ONLY data access. Every failure degrades to null/"unknown" (UNKNOWN/UNAVAILABLE, never a guess). */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { connect } from "node:net";
import example from "../contract/ahos-arena-contract.example.json";
import { validateArenaContract } from "../contract/validate";
import type { ArenaContract, LessonRecord, LessonsSnapshot } from "../contract/types";
import { healthFromSoak, parseReplayResults, type ProbeResult, type ReplayView, type SoakView } from "./model";

export function loadContract3(): ArenaContract | null {
  const r = validateArenaContract(example);
  return r.ok ? r.value : null;
}

export const SOAK_STATUS_PATH = process.env.AHOS_SOAK_STATUS_PATH ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M13_SOAK", "soak_status.json");
export const REPLAY_RESULTS_PATH = process.env.AHOS_REPLAY_RESULTS_PATH ?? join(process.cwd(), "..", "ahos_replay", "results.md");
export const LESSONS_SNAPSHOT_PATH =
  process.env.AHOS_LESSONS_SNAPSHOT_PATH ?? join(process.cwd(), "..", "ahos", "reports", "grok", "M49", "lessons_snapshot.json");

function lessonRow(raw: unknown): LessonRecord | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  if (typeof o.id !== "string") return null;
  return {
    demo: o.demo === true,
    id: o.id,
    market: typeof o.market === "string" ? o.market : "UNKNOWN",
    mistake: typeof o.mistake === "string" ? o.mistake : "-",
    lesson: typeof o.lesson === "string" ? o.lesson : "-",
    sourceReplayId: typeof o.sourceReplayId === "string" ? o.sourceReplayId : null,
    status: o.status === "ACCEPTED" || o.status === "REJECTED" ? o.status : "PROPOSED",
    reason: typeof o.reason === "string" ? o.reason : "-",
    unseenTest: null,
  };
}

export function readLessons(): LessonsSnapshot | null {
  let text: string;
  let mtimeIso: string;
  try {
    text = readFileSync(LESSONS_SNAPSHOT_PATH, "utf8");
    mtimeIso = new Date(statSync(LESSONS_SNAPSHOT_PATH).mtimeMs).toISOString();
  } catch {
    return null;
  }
  try {
    const j = JSON.parse(text) as { lessons?: unknown[]; generated_at?: string; source?: string };
    if (!Array.isArray(j.lessons)) return null;
    const lessons = j.lessons.map(lessonRow).filter((x): x is LessonRecord => x !== null);
    return {
      executionMode: "PAPER_ONLY",
      realTrading: false,
      source: j.source ?? "reports/grok/M49/lessons_snapshot.json",
      generatedAt: j.generated_at ?? mtimeIso,
      demo: false,
      availability: "AVAILABLE",
      lessons,
    };
  } catch {
    return null;
  }
}

function probe(port: number, timeoutMs = 800): Promise<ProbeResult> {
  return new Promise((resolve) => {
    const s = connect({ host: "127.0.0.1", port });
    const done = (r: ProbeResult) => { s.destroy(); resolve(r); };
    s.setTimeout(timeoutMs, () => done("unknown"));
    s.once("connect", () => done("open"));
    s.once("error", (e: NodeJS.ErrnoException) => done(e.code === "ECONNREFUSED" ? "closed" : "unknown"));
  });
}

export async function readHealth(nowMs: number): Promise<SoakView | null> {
  let text: string; let mtimeIso: string;
  try { text = readFileSync(SOAK_STATUS_PATH, "utf8"); mtimeIso = new Date(statSync(SOAK_STATUS_PATH).mtimeMs).toISOString(); } catch { return null; }
  let raw: unknown;
  try { raw = JSON.parse(text); } catch { return null; }
  const [bridge, arena] = await Promise.all([probe(8787), probe(3200)]);
  return healthFromSoak(raw, { bridge, arena }, mtimeIso, nowMs);
}

export function readReplay(): ReplayView | null {
  try { return parseReplayResults(readFileSync(REPLAY_RESULTS_PATH, "utf8")); } catch { return null; }
}
