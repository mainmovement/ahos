import DashboardShell from "../../../src/components/layout/DashboardShell";
import { NightlyReportPage } from "../../../src/features/missions-b5/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/nightly-report. Read-only, paper-only; real local files where they exist, otherwise DEMO. */
export default async function ArenaNightlyReportPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="nightly-report">
      <NightlyReportPage params={params} />
    </DashboardShell>
  );
}
