import { authorizeDashboardEndpoint, sanitizePublicError } from "@/web_api_auth";
import { runCycle, startEngine, stopEngine } from "@/engine";
import { recordControlAudit } from "@/chat_control_gate";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const denied = authorizeDashboardEndpoint(req);
  if (denied) return denied;
  try {
    const body = (await req.json().catch(() => ({}))) as { action?: string };
    const action = body.action || "cycle";
    if (action === "start" || action === "stop") {
      // Mission 9.5 MJ-2: write an EXECUTING record BEFORE touching the engine.
      // If the audit cannot be written, the action is refused — the chain may
      // never say ALLOWED for something that did not happen, and an action may
      // never happen un-audited.
      const ahead = recordControlAudit({
        surface: "engine_api",
        intent: action,
        capability: "ENGINE_CONTROL",
        decision: "EXECUTING",
        reason: "AUDIT_WRITE_AHEAD_DASHBOARD_ENGINE_API",
        channelClaimed: "dashboard_engine_api",
      });
      if (!ahead) {
        return Response.json(
          { ok: false, error: "AUDIT_WRITE_FAILED", hint: "control audit unavailable; action refused" },
          { status: 503 },
        );
      }
      try {
        if (action === "start") {
          const state = await startEngine();
          recordControlAudit({
            surface: "engine_api",
            intent: "start",
            capability: "ENGINE_CONTROL",
            decision: "CONFIRMED",
            reason: "EXECUTED_DASHBOARD_ENGINE_API",
            channelClaimed: "dashboard_engine_api",
          });
          return Response.json({ ok: true, action, state });
        }
        const state = await stopEngine();
        recordControlAudit({
          surface: "engine_api",
          intent: "stop",
          capability: "ENGINE_CONTROL",
          decision: "CONFIRMED",
          reason: "EXECUTED_DASHBOARD_ENGINE_API",
          channelClaimed: "dashboard_engine_api",
        });
        return Response.json({ ok: true, action, state });
      } catch (error) {
        recordControlAudit({
          surface: "engine_api",
          intent: action,
          capability: "ENGINE_CONTROL",
          decision: "FAILED",
          reason: "ENGINE_ACTION_ERROR",
          channelClaimed: "dashboard_engine_api",
        });
        return Response.json({ ok: false, error: sanitizePublicError(error) }, { status: 500 });
      }
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
