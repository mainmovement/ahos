import type { Metadata } from "next";
import { getResearch } from "@/lib/api/research";
import { ResearchView } from "@/components/views/research-view";

export const metadata: Metadata = { title: "پژوهشکده · Research Institute" };

export default async function ResearchPage() {
  return <ResearchView research={await getResearch()} />;
}
