import DashboardShell from "../../../src/components/layout/DashboardShell";
import { WhiteHatsScreen } from "../../../src/features/white-hats/WhiteHatsScreen";

/** Arena route /arena/white-hats. Read-only audit screen; mock adapter (DEMO). Rendered inside the Arena shell. */
export default function ArenaWhiteHatsRoute() {
  return (
    <DashboardShell activeId="white-hats">
      <WhiteHatsScreen />
    </DashboardShell>
  );
}
