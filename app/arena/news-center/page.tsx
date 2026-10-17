import DashboardShell from "../../../src/components/layout/DashboardShell";
import { NewsCenterPage } from "../../../src/features/missions-b4/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/news-center. Read-only, paper-only; DEMO unless a real local file is bound. */
export default async function ArenaNewsCenterPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="news-center">
      <NewsCenterPage params={params} />
    </DashboardShell>
  );
}
