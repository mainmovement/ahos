/**
 * The dashboard URL a capture script opens when the caller gives none.
 *
 * Hardcoding a port here kept biting the stage captures: the launcher resolves
 * the gateway from `AHOS_GATEWAY_URL` / `AHOS_GATEWAY_PORT` (see
 * `scripts/gateway_port.py`), and once the live server moved off the hardcoded
 * port every capture that omitted the URL silently photographed a dead page —
 * Chrome renders the connection-error page and a screenshot of it looks like a
 * dashboard that failed to mount. So the default comes from the same resolver
 * the launcher uses, never from this file.
 *
 * `gateway_port.py` imports only the stdlib, so the system interpreter runs it;
 * the venv is not required. Any failure falls back to the Next.js default of
 * 3000 and prints the reason, rather than inventing an address.
 *
 * Returns `{ url, source }` and never throws.
 */
export async function defaultDashboardUrl() {
  const { spawnSync } = await import("node:child_process");
  let lastError = null;
  // The system interpreter is enough: gateway_port.py is stdlib-only.
  for (const py of ["python", "python3", ".venv/Scripts/python.exe"]) {
    try {
      const res = spawnSync(py, ["scripts/gateway_port.py", "--url-only"], {
        cwd: process.cwd(),
        encoding: "utf-8",
        timeout: 8000,
        shell: false,
      });
      const url = (res.stdout || "").trim();
      if (/^http:\/\/127\.0\.0\.1:\d+\/api\/chat$/.test(url)) {
        return { url: url.replace("/api/chat", "/"), source: `${py} resolved` };
      }
    } catch (err) {
      lastError = err;
    }
  }
  return {
    url: "http://127.0.0.1:3000/",
    source: `gateway_port unavailable (${String(lastError?.message ?? lastError ?? "no interpreter")}), using the Next.js default`,
  };
}
