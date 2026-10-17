import DashboardShell from "../../../src/components/layout/DashboardShell";
import { CapabilityLabPage } from "../../../src/features/missions-b5/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/capability-lab. Read-only, paper-only; real local files where they exist, otherwise DEMO. */
export default async function ArenaCapabilityLabPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="capability-lab">
      <CapabilityLabPage params={params} />
    </DashboardShell>
  );
}
