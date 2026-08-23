import { listRecentCycles, getCurrentCycle } from "@/engine_metrics";
import { listProviderHealth } from "@/provider_health";

export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json({
    current_cycle: getCurrentCycle(),
    recent_cycles: listRecentCycles(15),
    provider_health: listProviderHealth(),
    timestamp: new Date().toISOString(),
  });
}
