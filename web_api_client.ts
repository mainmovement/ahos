/**
 * Browser → Lane-B API helper.
 * Sends NEXT_PUBLIC_AHOS_WEB_API_TOKEN when configured (must match AHOS_WEB_API_TOKEN).
 */

export function webApiHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...(extra || {}) };
  const token = (process.env.NEXT_PUBLIC_AHOS_WEB_API_TOKEN || "").trim();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function webApiFetch(input: string, init?: RequestInit): Promise<Response> {
  const baseHeaders =
    init?.headers instanceof Headers
      ? Object.fromEntries(init.headers.entries())
      : ((init?.headers as Record<string, string> | undefined) ?? {});
  return fetch(input, {
    ...init,
    headers: webApiHeaders(baseHeaders),
  });
}
