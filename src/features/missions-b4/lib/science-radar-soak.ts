import type { ScienceRadarItem, ScienceRadarSnapshot } from "../contract/types";

/** Witness labels from M13 soak cycle (price feeds only — not headline crawl). */
export function buildScienceRadarFromSoak(
  status: Record<string, unknown>,
  generatedAt: string,
): ScienceRadarSnapshot | null {
  const lc = status.last_cycle;
  if (!lc || typeof lc !== "object") return null;
  const cycle = lc as Record<string, unknown>;
  const ts = typeof cycle.ts === "string" ? cycle.ts : generatedAt;
  const reason = typeof cycle.witness_reason === "string" ? cycle.witness_reason : "";
  const verified = cycle.witness_state === "VERIFIED";
  const items: ScienceRadarItem[] = [];
  const add = (id: string, title: string, sourceText: string) => {
    items.push({
      id,
      title,
      sourceType: "repo",
      topic: "GOLD",
      foundAt: ts,
      relevanceNote: "M13 two-source price witness (not headline crawl)",
      status: verified ? "REVIEWED" : "UNKNOWN",
      sourceText,
      demo: false,
    });
  };
  if (/goldapi_spot/.test(reason)) add("RADAR-GOLDAPI", "goldapi_spot witness", "M13_SOAK witness ledger");
  if (/yahoo_gc_futures/.test(reason)) add("RADAR-YAHOO-GC", "yahoo_gc_futures witness", "M13_SOAK witness ledger");
  if (!items.length) {
    add("RADAR-SOAK", `witness ${String(cycle.witness_state ?? "UNKNOWN")}`, reason || "soak_status.json");
  }
  return {
    kind: "scienceRadar",
    executionMode: "PAPER_ONLY",
    realTrading: false,
    source: "M13_SOAK soak_status.json · last_cycle",
    generatedAt,
    demo: false,
    items,
  };
}
