/**
 * Read-only parser for G:\robat\ahos_assets\MISSIONS_STATUS.md (the real mission checklist).
 * Counts are derived from the parsed rows and cross-checked against the file's own
 * header totals; a disagreement is surfaced as CONFLICT, never silently picked.
 */
import type { Mission, MissionGroup, MissionState } from "../contract/types";

export interface ParsedMissions {
  missions: Mission[];
  generatedAt: string | null;
  header: { units: number | null; done: number | null; partial: number | null; notStarted: number | null };
}

function num(text: string, re: RegExp): number | null {
  const m = re.exec(text);
  return m ? Number(m[1]) : null;
}

export function parseMissionsStatus(text: string): ParsedMissions | null {
  if (!text || !/Claude missions/i.test(text)) return null;
  const gen = /Generated\s+(\d{4}-\d{2}-\d{2})\s*~?\s*(\d{2}):(\d{2})\s*Tehran/i.exec(text);
  const generatedAt = gen ? `${gen[1]}T${gen[2]}:${gen[3]}:00+03:30` : null;
  const header = {
    units: num(text, /Units tracked:\s*\*\*(\d+)\*\*/),
    done: num(text, /- DONE:\s*\*\*(\d+)\*\*/),
    partial: num(text, /- PARTIAL:\s*\*\*(\d+)\*\*/),
    notStarted: num(text, /- NOT STARTED:\s*\*\*(\d+)\*\*/),
  };
  const missions: Mission[] = [];
  let state: MissionState | null = null;
  for (const line of text.split(/\r?\n/)) {
    const h = /^###\s+(DONE|PARTIAL|NOT STARTED)\s*$/.exec(line);
    if (h) {
      state = h[1] === "DONE" ? "DONE" : h[1] === "PARTIAL" ? "PARTIAL" : "NOT_STARTED";
      continue;
    }
    if (/^##\s/.test(line) && !/^###/.test(line) && !/Checklist/i.test(line)) state = null;
    if (!state) continue;
    const m = /^- \[[ x~]\]\s+\*\*(.+?)\*\*:\s*(.*)$/.exec(line);
    if (!m) continue;
    const id = m[1].trim();
    const rest = m[2].trim();
    const cav = /CAVEAT:\s*(.*)$/i.exec(rest);
    const body = cav ? rest.slice(0, cav.index).trim() : rest;
    const dot = body.search(/\.\s|\.$/);
    const title = (dot > 0 ? body.slice(0, dot) : body).trim();
    const evidence = dot > 0 ? body.slice(dot + 1).trim() || null : null;
    const group: MissionGroup = id.startsWith("M-D") ? "M-D" : id.startsWith("M-PORT") ? "M-PORT" : "M";
    missions.push({
      id,
      title,
      group,
      state,
      blockedOwner: /BLOCKED_OWNER/.test(rest),
      evidence,
      lastUpdate: null, // the file carries no per-mission timestamp
      caveat: cav ? cav[1].trim() : null,
    });
  }
  if (missions.length === 0) return null;
  return { missions, generatedAt, header };
}

/** true when the header's own totals disagree with the parsed rows. */
export function headerConflicts(p: ParsedMissions): boolean {
  const c = (s: MissionState) => p.missions.filter((m) => m.state === s).length;
  const pairs: Array<[number | null, number]> = [
    [p.header.done, c("DONE")],
    [p.header.partial, c("PARTIAL")],
    [p.header.notStarted, c("NOT_STARTED")],
  ];
  return pairs.some(([h, n]) => h !== null && h !== n);
}
