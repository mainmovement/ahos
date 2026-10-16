import type { WhiteHatsSnapshot } from "./types";

/**
 * The one and only violation predicate (tested in tests/violation.test.tsx):
 * a VIOLATION bar must render when the snapshot claims real trading, or when
 * the execution mode is anything other than PAPER_ONLY.
 */
export function isViolation(snapshot: WhiteHatsSnapshot): boolean {
  return snapshot.executionMode !== "PAPER_ONLY" || snapshot.realTrading === true;
}

/** Totals never include DEMO rows. */
export function countNonDemo<T extends { demo?: boolean }>(items: readonly T[]): number {
  return items.filter((item) => !item.demo).length;
}

/** Decisions with no judge result are UNKNOWN — they must never read CLEAN. */
export function isUnjudged(snapshot: WhiteHatsSnapshot): string[] {
  return snapshot.decisions
    .filter((d) => d.verdict === "UNKNOWN")
    .map((d) => d.id);
}

export interface TelemetryRows {
  total: number;
  nonDemo: number;
}

export function telemetryRowCount(snapshot: WhiteHatsSnapshot): TelemetryRows {
  const total =
    snapshot.decisions.length +
    snapshot.findings.length +
    snapshot.inspectors.length;
  const nonDemo =
    countNonDemo(snapshot.decisions) +
    countNonDemo(snapshot.findings) +
    countNonDemo(snapshot.inspectors);
  return { total, nonDemo };
}
