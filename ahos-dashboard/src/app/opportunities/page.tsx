import type { Metadata } from "next";
import { getOpportunities } from "@/lib/api/tokens";
import { OpportunitiesView } from "@/components/views/opportunities-view";

export const metadata: Metadata = { title: "فرصت‌ها · Opportunities" };

export default async function OpportunitiesPage() {
  return <OpportunitiesView data={await getOpportunities()} />;
}
