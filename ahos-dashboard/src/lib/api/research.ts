import type { DataEnvelope, ResearchOverview } from "./types";
import { fromMock, label } from "./_envelope";
import { mockResearch } from "@/mock/research";

/** Research institute. Real source: research_worker missions + epistemic core (tests2b). */
export async function getResearch(): Promise<DataEnvelope<ResearchOverview>> {
  return fromMock(mockResearch(), "research", label("پژوهشکده نمایشی", "Demo research institute"), 120, 900);
}
