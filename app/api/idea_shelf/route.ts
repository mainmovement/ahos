/**
 * M-D5.5 — serve the idea shelf, honestly.
 *
 * The registry is `config/idea_shelf.json`, Aji's M59.S deliverable. It lives
 * under `config/`, not `public/`, so the browser cannot fetch it directly — and
 * it must not be copied into `public/`, because then the dashboard would serve a
 * second copy that could drift from the one M59.S reads as its single source.
 *
 * So this route is the one reader. It holds the file's path and reports an
 * explicit UNAVAILABLE shape when the file is absent or unreadable, which is the
 * case today: M59.S has not shipped yet. The panel renders grey UNKNOWN from that
 * shape instead of substituting idea names of its own.
 *
 * The UNAVAILABLE shape is returned with HTTP 200, matching `/api/command`'s
 * contract: a missing registry is not a server error, it is a fact about the
 * system the client should present as UNKNOWN rather than as a failure.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { authorizeDashboardEndpoint, sanitizePublicError } from "@/web_api_auth";
import { parseShelf } from "@/components/shelf/ideaShelf";

export const dynamic = "force-dynamic";

/** Resolved against the repo root, where `config/` actually lives. */
const SHELF_PATH = join(process.cwd(), "config", "idea_shelf.json");

export async function GET(req: Request) {
  const denied = authorizeDashboardEndpoint(req);
  if (denied) return denied;

  let raw: string | null;
  try {
    raw = readFileSync(SHELF_PATH, "utf8");
  } catch (e) {
    // ENOENT is the expected case until M59.S ships; anything else (EACCES,
    // EISDIR) is still a shelf we cannot read, not a shelf with no ideas.
    raw = null;
    void e;
  }

  const parsed = parseShelf(raw);
  if (parsed.status === "OK") {
    return Response.json({ status: "OK", ideas: parsed.ideas });
  }
  // `reason` is a filesystem fact about our own config path, not user input, but
  // it is routed through the same sanitizer so a hostile or enormous path error
  // can never be echoed into the browser.
  return Response.json({
    status: "UNAVAILABLE",
    reason: sanitizePublicError(parsed.reason, 120),
  });
}
