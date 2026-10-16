/**
 * AHOS · Trade Venue — per-row display status (pure, no UI strings).
 *
 * Rules enforced here (and covered by scripts/trade_venue_selftest.ts):
 *  · STALE requires a timestamp; STALE without one is UNKNOWN.
 *  · A row backed by a demo source can never present as LIVE (green); it
 *    presents as DEMO and carries a per-row DEMO marker.
 */
import type { ChipStatus } from "./model";
import { MOCK_SOURCES } from "../../../mock/trade_venue/sources";

const DEMO_SOURCE_IDS: ReadonlySet<string> = new Set(
  Object.values(MOCK_SOURCES)
    .filter((source) => source.demo)
    .map((source) => source.id),
);

/** Unknown sources are treated as demo: the page never claims a real feed it cannot prove. */
export function isDemoSource(sourceId: string | null | undefined): boolean {
  if (!sourceId) return true;
  const known = Object.values(MOCK_SOURCES).some((source) => source.id === sourceId);
  return !known || DEMO_SOURCE_IDS.has(sourceId);
}

export interface RowStatusInput {
  status: ChipStatus;
  updatedAt: string | null;
  sourceId: string | null | undefined;
  /** True when the whole bundle is a fixture (always true for the mock adapter). */
  bundleDemo?: boolean;
}

export interface RowDisplay {
  status: ChipStatus;
  /** True ⇒ render the per-row DEMO label + striped marker. */
  demo: boolean;
}

export function rowDisplay({ status, updatedAt, sourceId, bundleDemo = false }: RowStatusInput): RowDisplay {
  const demo = bundleDemo || isDemoSource(sourceId);
  let out: ChipStatus = status;
  if (out === "STALE" && !updatedAt) out = "UNKNOWN";
  if (out === "LIVE" && demo) out = "DEMO";
  return { status: out, demo };
}
