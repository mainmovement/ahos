import type { WhiteHatsSnapshot } from "@/src/features/white-hats/types";

/**
 * EMPTY demo fixture: an honest empty page. Empty means empty — no fake rows,
 * no fake zeros. Panels render their EMPTY state and the telemetry shows "—".
 */
export function buildEmptySnapshot(): WhiteHatsSnapshot {
  return {
    schemaVersion: 1,
    sourceId: "mock://white-hats/snapshot@v1",
    executionMode: "PAPER_ONLY",
    realTrading: false,
    fetchedAt: new Date().toISOString(),
    freshness: "LIVE",
    demo: true,
    decisions: [],
    inspectors: [],
    findings: [],
    breaker: {
      state: "UNKNOWN",
      updatedAt: null,
      limits: [],
    },
    canary: null,
    timelines: {},
    evidence: {},
  };
}
