import DashboardShell from "../../../src/components/layout/DashboardShell";
import { WhiteHatsScreen } from "../../../src/features/white-hats/WhiteHatsScreen";
import { parseOpenTarget, parseScenario, parseTier } from "../../../src/mock/white_hats/scenarios";

/** Arena route /arena/white-hats. REAL: M13_SOAK via /api/white-hats/snapshot; ?demo=1 for fixtures. */
export default async function ArenaWhiteHatsRoute({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);
  const scenario = parseScenario(one(params.scenario));
  const dataMode = one(params.demo) === "1" ? "mock" : "soak";
  return (
    <DashboardShell activeId="white-hats">
      <WhiteHatsScreen
        key={`${scenario}-${dataMode}`}
        scenario={scenario}
        tier={parseTier(one(params.tier))}
        openTarget={parseOpenTarget(one(params.open))}
        dataMode={dataMode}
      />
    </DashboardShell>
  );
}