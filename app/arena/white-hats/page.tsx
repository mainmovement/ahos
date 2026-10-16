import DashboardShell from "../../../src/components/layout/DashboardShell";
import { WhiteHatsScreen } from "../../../src/features/white-hats/WhiteHatsScreen";
import { parseOpenTarget, parseScenario, parseTier } from "../../../src/mock/white_hats/scenarios";

/** Arena route /arena/white-hats. Read-only audit screen; mock adapter (DEMO). Rendered inside the Arena shell. */
export default async function ArenaWhiteHatsRoute({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);
  const scenario = parseScenario(one(params.scenario));
  return (
    <DashboardShell activeId="white-hats">
      <WhiteHatsScreen
        key={scenario}
        scenario={scenario}
        tier={parseTier(one(params.tier))}
        openTarget={parseOpenTarget(one(params.open))}
      />
    </DashboardShell>
  );
}