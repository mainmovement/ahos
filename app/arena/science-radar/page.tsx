import DashboardShell from "../../../src/components/layout/DashboardShell";
import { ScienceRadarPage } from "../../../src/features/missions-b4/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/science-radar. Read-only, paper-only; DEMO unless a real local file is bound. */
export default async function ArenaScienceRadarPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="science-radar">
      <ScienceRadarPage params={params} />
    </DashboardShell>
  );
}
