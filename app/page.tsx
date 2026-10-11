import DashiShell from "@/components/shell/DashiShell";

export const dynamic = "force-dynamic";

/**
 * The main screen: the Dashi shell (M-D5.2). Built from scratch to
 * DASHBOARD_DESIGN_SPEC §4 and OWNER_DECISIONS; the previous Command Center
 * surface remains at `/command_center`.
 */
export default function HomePage() {
  return <DashiShell />;
}
