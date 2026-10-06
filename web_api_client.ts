/**
 * Browser -> Lane-B API helper (Mission 9.5 security fix, REDTEAM-19 F1/F6).
 *
 * Dashboard auth is a server-issued httpOnly SameSite session cookie plus a
 * CSRF token echoed in the `X-AHOS-CSRF` header. The browser holds NO shared
 * secret (the old `NEXT_PUBLIC_AHOS_WEB_API_TOKEN` was compiled into the
 * bundle — review BLOCKER B1).
 *
 * Bootstrap (F1): the server mints a session only for a ONE-TIME token the
 * launcher put in the URL fragment it opened (`/#boot=<token>`). The fragment
 * is never sent to the server in the page request; this helper reads it once,
 * strips it from the address bar (history.replaceState) and POSTs it to
 * /api/auth/session. A browser opened by hand gets a fresh URL from
 * `python -m launcher bootstrap-url`.
 *
 * CSRF token storage (F6): the token comes back in the response BODY and is
 * kept in localStorage, which is scoped to this exact origin (host:port).
 * Cookies are not port-scoped, so a cookie-held token was sent to — and could
 * be planted by — any other 127.0.0.1 port. On a 401 the stored token is
 * dropped so a stale/foreign token never pins the dashboard to 401.
 */

export const CSRF_HEADER = "X-AHOS-CSRF";
const CSRF_STORAGE_KEY = "ahos.dashboard.csrf";
const BOOT_PARAM = "boot";

function storage(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null;
  }
}

function storedCsrf(): string | null {
  return storage()?.getItem(CSRF_STORAGE_KEY) || null;
}

/** Read `#boot=<token>` once and remove it from the address bar. */
export function takeBootTokenFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) return null;
  const params = new URLSearchParams(hash);
  const token = params.get(BOOT_PARAM);
  if (!token) return null;
  params.delete(BOOT_PARAM);
  const rest = params.toString();
  try {
    window.history.replaceState(
      null,
      "",
      window.location.pathname + window.location.search + (rest ? `#${rest}` : ""),
    );
  } catch {
    /* the token is single-use server-side even if the bar cannot be cleaned */
  }
  return token;
}

let bootstrap: Promise<boolean> | null = null;

/**
 * Make sure this tab has a session. Uses the URL's one-time token when there
 * is one (it always wins: a fresh launcher URL replaces an old session);
 * otherwise keeps the stored token. Returns false when there is no session
 * and no token — the caller shows the "open from the launcher" hint.
 */
export async function ensureDashboardSession(): Promise<boolean> {
  if (typeof window === "undefined") return false;
  if (!bootstrap) {
    bootstrap = (async () => {
      const boot = takeBootTokenFromUrl();
      if (!boot) return Boolean(storedCsrf());
      try {
        const res = await fetch("/api/auth/session", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ boot }),
        });
        const json = (await res.json().catch(() => ({}))) as { ok?: boolean; csrfToken?: string };
        if (res.ok && json.ok && typeof json.csrfToken === "string") {
          storage()?.setItem(CSRF_STORAGE_KEY, json.csrfToken);
          return true;
        }
      } catch {
        /* a 401 surfaces on the real call; never fabricate auth here */
      }
      return Boolean(storedCsrf());
    })();
  }
  return bootstrap;
}

/** True when this tab currently holds a CSRF token (UI hint only). */
export function hasDashboardSession(): boolean {
  return Boolean(storedCsrf());
}

export function webApiHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...(extra || {}) };
  const csrf = storedCsrf();
  if (csrf) headers[CSRF_HEADER] = csrf;
  return headers;
}

export async function webApiFetch(input: string, init?: RequestInit): Promise<Response> {
  if (typeof window !== "undefined") await ensureDashboardSession();
  const baseHeaders =
    init?.headers instanceof Headers
      ? Object.fromEntries(init.headers.entries())
      : ((init?.headers as Record<string, string> | undefined) ?? {});
  const res = await fetch(input, {
    ...init,
    headers: webApiHeaders(baseHeaders),
    credentials: "same-origin",
  });
  if (res.status === 401) {
    // A token from a previous server secret/instance can never recover; drop
    // it so the page shows the re-open hint instead of looping on 401.
    storage()?.removeItem(CSRF_STORAGE_KEY);
  }
  return res;
}
