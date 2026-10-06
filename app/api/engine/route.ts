import { authorizeDashboardEndpoint, sanitizePublicError } from "@/web_api_auth";
import { runCycle } from "@/engine";
import { verifyDashboardSession } from "@/chat_auth";
import { getPendingStore, propose, proposalTextFa, toPublic, type ActionKind } from "@/chat_actions";

export const dynamic = "force-dynamic";

/**
 * REDTEAM-19 F2: engine start/stop never execute from this route any more.
 *
 * They used to call startEngine()/stopEngine() directly for anyone holding a
 * session or the bearer, so one scripted request could stop the engine with no
 * human. Start/stop now go through the SAME propose -> confirm gate as chat
 * (chat_actions.propose / handleConfirmation): this route only creates a
 * proposal bound to the caller's verified dashboard session, and the action
 * runs when that session confirms the one-time code («تایید <code>» via
 * /api/chat; the code is revealed to the bound session only, never returned
 * here). handleConfirmation writes the EXECUTING audit record before it
 * touches the engine (MJ-1/MJ-2) and consumes the code first.
 *
 * The shared bearer is not an owner identity (isOwner requires a proven
 * session/HMAC), so a bearer-only caller is refused (403). `cycle` (one manual
 * paper analysis cycle; changes no engine state) is unchanged.
 */
export async function POST(req: Request) {
  const denied = authorizeDashboardEndpoint(req);
  if (denied) return denied;
  try {
    const body = (await req.json().catch(() => ({}))) as { action?: string };
    const action = body.action || "cycle";
    if (action === "start" || action === "stop") {
      const sess = verifyDashboardSession(req.headers);
      const identity = sess.ok
        ? { channel: "dashboard", userId: sess.sessionId, proven: true }
        : { channel: "engine_api_bearer", userId: null, proven: false };
      const kind: ActionKind = action === "start" ? "engine_start" : "engine_stop";
      const r = propose(getPendingStore(), kind, {}, identity, `engine_api:${action}`);
      if (!r.ok) {
        return Response.json(
          {
            ok: false,
            error: "OWNER_CONFIRMATION_REQUIRED",
            hint: "engine start/stop needs a dashboard owner session and a one-time confirmation",
          },
          { status: 403 },
        );
      }
      return Response.json({
        ok: true,
        action,
        proposed: true,
        executed: false,
        reply: proposalTextFa(r.action),
        pending_action: toPublic(r.action),
      });
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
