/**
 * Browser -> Lane-B API helper (Mission 9.5 security fix).
 *
 * Dashboard auth is a server-issued httpOnly + SameSite session cookie plus a
 * CSRF token echoed back in the `X-AHOS-CSRF` header. The browser holds NO
 * shared secret: the previous `NEXT_PUBLIC_AHOS_WEB_API_TOKEN` was compiled
 * into the client bundle and therefore readable by anyone who could load the
 * dashboard page, which made every /api/chat caller indistinguishable from
 * the owner (review BLOCKER B1).
 *
 * The session is bootstrapped lazily from POST /api/auth/session on the first
 * call, then carried by the cookie jar. Server-side callers (scripts, the
 * Telegram bot) bypass this helper and use their own bearer.
 */

const CSRF_COOKIE = "AHOS_CSRF";
export const CSRF_HEADER = "X-AHOS-CSRF";

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  for (const part of document.cookie.split(/;+/)) {
    const idx = part.indexOf("=");
    if (idx <= 0) continue;
    if (part.slice(0, idx).trim() === name) return part.slice(idx + 1).trim();
  }
  return null;
}

let bootstrap: Promise<void> | null = null;

/** Ask the server for a session cookie once; no-op afterwards. */
export async function ensureDashboardSession(): Promise<void> {
  if (typeof document === "undefined") return;
  if (readCookie(CSRF_COOKIE)) return;
  if (!bootstrap) {
    bootstrap = (async () => {
      try {
        await fetch("/api/auth/session", { method: "POST", credentials: "include" });
      } catch {
        /* a 401 surfaces on the real call; never fabricate auth here */
      }
    })();
  }
  await bootstrap;
}

export function webApiHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...(extra || {}) };
  const csrf = readCookie(CSRF_COOKIE);
  if (csrf) headers[CSRF_HEADER] = csrf;
  return headers;
}

export async function webApiFetch(input: string, init?: RequestInit): Promise<Response> {
  if (typeof document !== "undefined") await ensureDashboardSession();
  const baseHeaders =
    init?.headers instanceof Headers
      ? Object.fromEntries(init.headers.entries())
      : ((init?.headers as Record<string, string> | undefined) ?? {});
  return fetch(input, {
    ...init,
    headers: webApiHeaders(baseHeaders),
    credentials: "include",
  });
}
