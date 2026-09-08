import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { failClosedCommandSnapshot, commandSnapshot } from "@/snapshot";
import { restoreDaemonIfNeeded } from "@/engine";
import { loadCanonicalReadModel } from "@/canonical_read_model";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  try {
    try {
      await restoreDaemonIfNeeded();
    } catch {
      // Postgres may be down; snapshot still presents the Python read model.
    }
    const snap = await commandSnapshot();
    return Response.json(snap);
  } catch (error) {
    const canonicalModel = await loadCanonicalReadModel();
    const payload = failClosedCommandSnapshot(error, canonicalModel);
    payload.state.lastError = sanitizePublicError(error);
    return Response.json(payload, { status: 200 });
  }
}
