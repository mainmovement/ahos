import DashboardShell from "../../../src/components/layout/DashboardShell";
import { WorkroomPage } from "../../../src/features/missions-b3/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/workroom. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaWorkroomPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="workroom">
      <WorkroomPage params={params} />
    </DashboardShell>
  );
}
