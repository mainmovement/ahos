import type { DataEnvelope, UniversityOverview } from "./types";
import { fromMock, label } from "./_envelope";
import { mockUniversity } from "@/mock/university";

/** University. Real source: evaluation harness results + verification records (INDEPENDENT vs SELF_CHECK). */
export async function getUniversity(): Promise<DataEnvelope<UniversityOverview>> {
  return fromMock(mockUniversity(), "university", label("دانشگاه نمایشی", "Demo university"), 120, 900);
}
