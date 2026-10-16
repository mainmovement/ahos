import type { ChipStatus } from "../truth/status";
import type { WhiteHatsSnapshot } from "../types";

/**
 * Truth normalisation applied once, where data enters the screen:
 *  · a demo-backed snapshot never presents LIVE (green) → DEMO;
 *  · STALE without a timestamp is UNKNOWN (no timestamp ⇒ cannot be stale).
 * Pure; the adapter output is never mutated.
 */
export function displayStatus(status: ChipStatus, demo: boolean, timestamp: string | null): ChipStatus {
  let out = status;
  if (out === "STALE" && !timestamp) out = "UNKNOWN";
  if (out === "LIVE" && demo) out = "DEMO";
  return out;
}

export function normalizeSnapshot(snapshot: WhiteHatsSnapshot): WhiteHatsSnapshot {
  const demo = snapshot.demo;
  return {
    ...snapshot,
    freshness: displayStatus(snapshot.freshness, demo, snapshot.fetchedAt) as WhiteHatsSnapshot["freshness"],
    decisions: snapshot.decisions.map((d) => ({
      ...d,
      freshness: displayStatus(d.freshness, demo || !!d.demo, d.proposedAt) as typeof d.freshness,
    })),
    inspectors: snapshot.inspectors.map((i) => ({
      ...i,
      status: displayStatus(i.status, demo || !!i.demo, i.lastRunAt) as typeof i.status,
    })),
  };
}
