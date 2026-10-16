import DashboardShell from "../../../src/components/layout/DashboardShell";
import { MessageHubPage } from "../../../src/features/missions-b2/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/message-hub. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaMessageHubRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="message-hub">
      <MessageHubPage params={params} />
    </DashboardShell>
  );
}
