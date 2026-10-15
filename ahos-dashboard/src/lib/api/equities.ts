import type { DataEnvelope, EquitiesBoard, EquityRegion } from "./types";
import { fromMock, label } from "./_envelope";
import { mockEquities } from "@/mock/equities";

export const EQUITY_REGIONS: EquityRegion[] = ["us", "eu", "asia"];

export function isEquityRegion(value: string): value is EquityRegion {
  return (EQUITY_REGIONS as string[]).includes(value);
}

/** Regional equities board. Real source: licensed index/quote vendor (TBD). */
export async function getEquities(region: EquityRegion): Promise<DataEnvelope<EquitiesBoard>> {
  return fromMock(mockEquities(region), `equities/${region}`, label("سهام نمایشی", "Demo equities"), 40, 300);
}
