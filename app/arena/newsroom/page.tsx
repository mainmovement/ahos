import DashboardShell from "../../../src/components/layout/DashboardShell";
import { NewsroomPage } from "../../../src/features/newsroom/NewsroomPage";
import { parseFlag, parseScenario, parseTier } from "../../../src/mock/newsroom/scenarios";

/** Arena route /arena/newsroom. REAL witness feeds from M13_SOAK; ?mock=1 for fixtures. */
export default async function ArenaNewsroomRoute({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);
  const scenario = parseScenario(one(params.state) ?? one(params.scenario));
  const forceDemo = parseFlag(one(params.demo));
  const forceViolation = parseFlag(one(params.violation));
  const tier = parseTier(one(params.tier));
  const dataMode = parseFlag(one(params.mock)) ? "mock" : "soak";
  return (
    <DashboardShell activeId="newsroom">
      <NewsroomPage
        key={`${dataMode}|${scenario}|${forceDemo}|${forceViolation}`}
        scenario={scenario}
        forceDemo={forceDemo}
        forceViolation={forceViolation}
        dataMode={dataMode}
        tier={tier}
        story={one(params.story) ?? null}
        details={one(params.details) === "1"}
      />
    </DashboardShell>
  );
}
