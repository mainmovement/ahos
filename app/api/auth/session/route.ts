/**
 * Mission 9.5: dashboard session bootstrap.
 *
 * The browser dashboard holds no shared secret. A page load (or the first
 * `webApiFetch`) POSTs here; the server answers with an httpOnly + SameSite
 * session cookie plus a CSRF token cookie that the browser may read and must
 * echo back in the `X-AHOS-CSRF` header on every later call. Both are
 * HMAC-signed with the server-only AHOS_DASHBOARD_SESSION_SECRET.
 *
 * This replaces the NEXT_PUBLIC_AHOS_WEB_API_TOKEN, which was compiled into
 * the client bundle and therefore readable by anyone who could load the page
 * (review BLOCKER B1).
 *
 * Issuance is loopback-only: the gateway dev server binds 127.0.0.1, and the
 * owner's physical control of the machine is the trust boundary. A session
 * makes the caller eligible for owner proposals; it is not itself a grant of
 * execution — every action still needs the one-time confirm code.
 */
import { issueDashboardSession, isLoopbackRequest } from "@/chat_auth";
import { sanitizePublicError } from "@/web_api_auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(req: Request) {
  try {
    if (!isLoopbackRequest(req)) {
      return Response.json(
        { ok: false, error: "SESSION_ISSUANCE_NON_LOOPBACK" },
        { status: 403 },
      );
    }
    const issued = issueDashboardSession();
    if (!issued) {
      // The server secret is unset or too short: fail closed, and say so
      // without printing the secret or hinting at its value.
      return Response.json(
        {
          ok: false,
          error: "SESSION_SECRET_UNAVAILABLE",
          hint: "AHOS_DASHBOARD_SESSION_SECRET must be set server-side (>= 16 chars).",
        },
        { status: 503 },
      );
    }
    const headers = new Headers();
    for (const c of issued.cookies) headers.append("Set-Cookie", c);
    return Response.json({ ok: true, sessionId: issued.sessionId }, { headers });
  } catch (error) {
    return Response.json({ ok: false, error: sanitizePublicError(error) }, { status: 500 });
  }
}
