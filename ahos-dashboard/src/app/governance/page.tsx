import type { Metadata } from "next";
import { getGovernance } from "@/lib/api/org";
import { GovernanceView } from "@/components/views/governance-view";

export const metadata: Metadata = { title: "حاکمیت · Governance" };

export default async function GovernancePage() {
  return <GovernanceView gov={await getGovernance()} />;
}
