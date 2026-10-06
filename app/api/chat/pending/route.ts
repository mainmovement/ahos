/**
 * REDTEAM-19 F1: the dashboard's owner channel for a confirm code.
 *
 * /api/chat and /api/engine never return the one-time code. The dashboard asks
 * here, with the opaque `ref` of a pending action, when the human presses
 * «تایید». Only a verified dashboard session (cookie + X-AHOS-CSRF) whose
 * session id is the identity the action is bound to gets the code back; the
 * shared bearer, a Telegram HMAC, a foreign session, or a session-less caller
 * all get the same 404. A browser fetch from the dashboard always carries
 * `Sec-Fetch-Site: same-origin`; anything else is refused.
 */
import { verifyDashboardSession } from "@/chat_auth";
import { authorizeDashboardEndpoint } from "@/web_api_auth";
import { getPendingStore, revealPendingCode } from "@/chat_actions";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(req: Request) {
  const denied = authorizeDashboardEndpoint(req);
  if (denied) return denied;
  // Stricter than the shared gate: the bearer alone is not enough here.
  const sess = verifyDashboardSession(req.headers);
  const site = String(req.headers.get("sec-fetch-site") ?? "").toLowerCase();
  if (!sess.ok || site !== "same-origin") {
    return Response.json({ ok: false, error: "DASHBOARD_SESSION_REQUIRED" }, { status: 401 });
  }
  const body = (await req.json().catch(() => ({}))) as { ref?: unknown };
  const code = revealPendingCode(
    getPendingStore(),
    body.ref,
    { channel: "dashboard", userId: sess.sessionId, proven: true },
  );
  if (!code) return Response.json({ ok: false, error: "NO_SUCH_PENDING_ACTION" }, { status: 404 });
  return Response.json({ ok: true, code }, { headers: { "Cache-Control": "no-store" } });
}
