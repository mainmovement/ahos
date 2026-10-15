import type { DataEnvelope, GoldBoard, OilBoard } from "./types";
import { fromMock, label } from "./_envelope";
import { mockGold, mockOil } from "@/mock/commodities";

/** Oil board. Real source: EIA open data (inventories), exchange settlement feeds. */
export async function getOil(): Promise<DataEnvelope<OilBoard>> {
  return fromMock(mockOil(), "oil", label("داده نمایشی انرژی", "Demo energy data"), 50, 300);
}

/** Gold board. Real source: LBMA/COMEX settlement + domestic Iranian quotes. */
export async function getGold(): Promise<DataEnvelope<GoldBoard>> {
  return fromMock(mockGold(), "gold", label("داده نمایشی فلزات", "Demo metals data"), 50, 300);
}
