/**
 * Mission 9.5 + REDTEAM-19 F1: dashboard session bootstrap.
 *
 * The browser dashboard holds no shared secret. It POSTs here once with the
 * ONE-TIME bootstrap token the launcher put in the URL fragment it opened
 * (`/#boot=<token>`; `python -m launcher bootstrap-url` prints a fresh URL for
 * a browser opened by hand). The server answers with an httpOnly SameSite
 * session cookie and, in the body, a CSRF token the client keeps in
 * origin-scoped storage and echoes in `X-AHOS-CSRF` on every later call.
 *
 * Reaching 127.0.0.1 is not proof of ownership (any local process can), so
 * issuance requires, in this order:
 *   1. exact loopback Host, `Sec-Fetch-Site: same-origin|none`, and an Origin
 *      equal to `http://<Host>` when present (`checkSessionIssuance`);
 *   2. a valid, unexpired, unused bootstrap token (`consumeBootstrapToken`).
 * x-forwarded-for is not consulted (client-controlled under Next).
 *
 * A session makes the caller eligible for owner proposals; every action still
 * needs the one-time confirm code.
 */
import { handleSessionIssuance } from "@/chat_auth";
import { sanitizePublicError } from "@/web_api_auth";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(req: Request) {
  try {
    // The full decision (shape checks, secret, one-time token) lives in
    // chat_auth.handleSessionIssuance so the selftests run the same code.
    return await handleSessionIssuance(req);
  } catch (error) {
    return Response.json({ ok: false, error: sanitizePublicError(error) }, { status: 500 });
  }
}
