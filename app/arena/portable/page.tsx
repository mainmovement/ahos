import DashboardShell from "../../../src/components/layout/DashboardShell";
import { PortablePage } from "../../../src/features/missions-b3/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/portable. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaPortablePageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="portable">
      <PortablePage params={params} />
    </DashboardShell>
  );
}
