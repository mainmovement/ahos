/**
 * Partial REAL binding: ahos_replay/results.md (REPLAY_NOT_LIVE, no proven edge).
 */
import type { Hypothesis, ResearchInstituteSnapshot } from "../contract/types";

function parseVerdictRows(text: string): Hypothesis[] {
  const out: Hypothesis[] = [];
  const lines = text.split(/\r?\n/);
  for (const line of lines) {
    if (!line.includes("|") || !/NO PROVEN EDGE/i.test(line)) continue;
    const cells = line.split("|").map((c) => c.trim()).filter(Boolean);
    if (cells.length < 2) continue;
    const marketCell = cells[0];
    if (!/gold|oil/i.test(marketCell)) continue;
    const id = `H-REPLAY-${marketCell.replace(/\s+/g, "-").replace(/[^\w-]/gi, "").toUpperCase()}`;
    out.push({
      id,
      statement: "Replay verdict: NO PROVEN EDGE (frozen test protocol; not live trading).",
      source: "paper",
      market: /oil/i.test(marketCell) ? "OIL" : "GOLD",
      status: "REJECTED",
      inSampleResult: { note: cells[1]?.slice(0, 120) ?? "in-sample metrics in results.md only" },
      unseenTest: {
        datasetId: "ahos_replay/results.md",
        period: null,
        sampleSize: null,
        costModelPresent: true,
        result: "FAIL",
      },
    });
  }
  return out;
}

export function buildResearchFromReplay(text: string, generatedAt: string): ResearchInstituteSnapshot | null {
  if (!text.trim()) return null;
  const hypotheses = parseVerdictRows(text);
  if (!hypotheses.length) return null;
  const examined = hypotheses.length;
  const passed = hypotheses.filter((h) => h.unseenTest?.result === "PASS").length;
  return {
    executionMode: "PAPER_ONLY",
    realTrading: false,
    source: "ahos_replay/results.md (REPLAY_NOT_LIVE)",
    generatedAt,
    demo: false,
    hypotheses,
    weeklyExam: {
      lastExamTime: generatedAt,
      itemsExamined: examined,
      itemsPassedUnseen: passed,
    },
  };
}
