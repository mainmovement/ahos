import DashboardShell from "../../../src/components/layout/DashboardShell";
import { OilGoldPage } from "../../../src/features/missions-b3/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/oil-gold. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaOilGoldPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="oil-gold">
      <OilGoldPage params={params} />
    </DashboardShell>
  );
}
