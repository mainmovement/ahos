import DashboardShell from "../../../src/components/layout/DashboardShell";
import { KianArenaChat } from "../../../src/features/kian/KianArenaChat";

export const dynamic = "force-dynamic";

/** Arena route /arena/kian — canonical /api/chat (M35.2), PAPER_ONLY. */
export default function ArenaKianPage() {
  return (
    <DashboardShell activeId="kian">
      <KianArenaChat fa />
    </DashboardShell>
  );
}
