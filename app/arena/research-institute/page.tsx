import DashboardShell from "../../../src/components/layout/DashboardShell";
import { ResearchInstitutePage } from "../../../src/features/missions-b2/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/research-institute. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaResearchInstituteRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="research-institute">
      <ResearchInstitutePage params={params} />
    </DashboardShell>
  );
}
