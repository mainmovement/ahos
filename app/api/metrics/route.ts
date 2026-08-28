import { authorizeWebApi } from "@/web_api_auth";
import { listRecentCycles, getCurrentCycle } from "@/engine_metrics";
import { listProviderHealth } from "@/provider_health";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  return Response.json({
    current_cycle: getCurrentCycle(),
    recent_cycles: listRecentCycles(15),
    provider_health: listProviderHealth(),
    timestamp: new Date().toISOString(),
  });
}
