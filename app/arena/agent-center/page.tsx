import DashboardShell from "../../../src/components/layout/DashboardShell";
import { AgentCenterPage } from "../../../src/features/missions-b5/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/agent-center. Read-only, paper-only; real local files where they exist, otherwise DEMO. */
export default async function ArenaAgentCenterPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="agent-center">
      <AgentCenterPage params={params} />
    </DashboardShell>
  );
}
