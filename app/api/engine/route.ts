import { runCycle, startEngine, stopEngine } from "@/engine";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
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
    const message = error instanceof Error ? error.message : "UNKNOWN";
    return Response.json({ ok: false, error: message }, { status: 500 });
  }
}
