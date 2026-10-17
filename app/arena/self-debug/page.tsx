import DashboardShell from "../../../src/components/layout/DashboardShell";
import { SelfDebugPage } from "../../../src/features/missions-b4/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/self-debug. Read-only, paper-only; DEMO unless a real local file is bound. */
export default async function ArenaSelfDebugPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="self-debug">
      <SelfDebugPage params={params} />
    </DashboardShell>
  );
}
