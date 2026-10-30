/**
 * Read-only home numbers written by architecture/mission/mehrdad_status.py.
 * Presentation only. liveSwitch is forced off here even if the file says otherwise.
 */
import { readFile } from "fs/promises";
import path from "path";

export type HomeBriefModel = {
  equityUsd: number | null;
  openCount: number;
  openNames: string[];
  lessonsFa: string[];
  readinessPct: number | null;
  missingFa: string[];
  liveSwitch: false;
};

export async function loadHomeBrief(): Promise<HomeBriefModel | null> {
  try {
    const raw = await readFile(
      path.join(process.cwd(), "reports", "grok", "PAPER", "mehrdad_status.json"),
      "utf8",
    );
    const doc = JSON.parse(raw) as Record<string, unknown>;
    const names = Array.isArray(doc.open_names) ? doc.open_names.map(String) : [];
    const lessons = Array.isArray(doc.lessons_fa) ? doc.lessons_fa.map(String) : [];
    const missing = Array.isArray(doc.missing_fa) ? doc.missing_fa.map(String) : [];
    return {
      equityUsd: typeof doc.equity_usd === "number" ? doc.equity_usd : null,
      openCount: typeof doc.open_count === "number" ? doc.open_count : names.length,
      openNames: names,
      lessonsFa: lessons,
      readinessPct: typeof doc.readiness_pct === "number" ? doc.readiness_pct : null,
      missingFa: missing,
      liveSwitch: false,
    };
  } catch {
    return null;
  }
}
