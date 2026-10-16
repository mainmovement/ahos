import DashboardShell from "../../../src/components/layout/DashboardShell";
import { IdeaShelfPage } from "../../../src/features/missions-b2/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/idea-shelf. Read-only, paper-only; real data where a local file exists, otherwise DEMO. */
export default async function ArenaIdeaShelfRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="idea-shelf">
      <IdeaShelfPage params={params} />
    </DashboardShell>
  );
}
