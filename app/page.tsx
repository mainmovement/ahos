import { AhosShell } from '@/components/shell/AhosShell';
import { AhosOverview } from '@/components/ahos/overview';

export const dynamic = 'force-dynamic';

/**
 * The main screen: the AHOS command center (MASTER_SPEC "Layout to match").
 *
 * The shell is the ported template's layout primitives reskinned to AHOS; the
 * overview inside it is one read model from `/api/command`. The previous Dashi
 * shell remains importable and the old Command Center stays at `/command_center`.
 */
export default function HomePage() {
  return (
    <AhosShell>
      <AhosOverview />
    </AhosShell>
  );
}
