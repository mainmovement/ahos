import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { runCycle, startEngine, stopEngine } from "@/engine";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  try {
    const body = (await req.json().catch(() => ({}))) as { action?: string };
    const action = body.action || "cycle";
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
