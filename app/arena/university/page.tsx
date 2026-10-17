import DashboardShell from "../../../src/components/layout/DashboardShell";
import { UniversityPage } from "../../../src/features/missions-b5/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/university. Read-only, paper-only; real local files where they exist, otherwise DEMO. */
export default async function ArenaUniversityPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="arena-university">
      <UniversityPage params={params} />
    </DashboardShell>
  );
}
