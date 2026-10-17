import DashboardShell from "../../../src/components/layout/DashboardShell";
import { WeeklyExamPage } from "../../../src/features/missions-b4/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/weekly-exam. Read-only, paper-only; DEMO unless a real local file is bound. */
export default async function ArenaWeeklyExamPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="weekly-exam">
      <WeeklyExamPage params={params} />
    </DashboardShell>
  );
}
