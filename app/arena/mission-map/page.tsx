import DashboardShell from "../../../src/components/layout/DashboardShell";
import { MissionMapPage } from "../../../src/features/missions-b2/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/mission-map. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaMissionMapRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="mission-map">
      <MissionMapPage params={params} />
    </DashboardShell>
  );
}
