import DashboardShell from "../../../src/components/layout/DashboardShell";
import { SkillMarketPage } from "../../../src/features/missions-b4/components/pages";

export const dynamic = "force-dynamic";

/** Arena route /arena/skill-market. Read-only, paper-only; DEMO unless a real local file is bound. */
export default async function ArenaSkillMarketPageRoute({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  return (
    <DashboardShell activeId="skill-market">
      <SkillMarketPage params={params} />
    </DashboardShell>
  );
}
