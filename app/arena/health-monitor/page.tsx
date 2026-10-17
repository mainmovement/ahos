import DashboardShell from "../../../src/components/layout/DashboardShell";
import { HealthMonitorPage } from "../../../src/features/missions-b3/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/health-monitor. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaHealthMonitorPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="health-monitor">
      <HealthMonitorPage params={params} />
    </DashboardShell>
  );
}
