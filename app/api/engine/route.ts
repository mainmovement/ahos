import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { runCycle, startEngine, stopEngine } from "@/engine";
import { recordControlAudit } from "@/chat_control_gate";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  try {
    const body = (await req.json().catch(() => ({}))) as { action?: string };
    const action = body.action || "cycle";
    if (action === "start" || action === "stop") {
      // GM-04 audit: dashboard API control (bearer-authorized) is ALLOWED and recorded.
      recordControlAudit({
        surface: "engine_api",
        intent: action,
        capability: "ENGINE_CONTROL",
        decision: "ALLOWED",
        reason: "DASHBOARD_ENGINE_API_BEARER_AUTHORIZED",
        channelClaimed: "dashboard_engine_api",
      });
    }
    if (action === "start") {
      const state = await startEngine();
      return Response.json({ ok: true, action, state });
    }
    if (action === "stop") {
      const state = await stopEngine();
      return Response.json({ ok: true, action, state });
    }
    const result = await runCycle("manual");
    return Response.json({ ok: true, action: "cycle", result });
  } catch (error) {
    return Response.json(
      { ok: false, error: sanitizePublicError(error) },
      { status: 500 },
    );
  }
}
