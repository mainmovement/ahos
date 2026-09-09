import { getOverview } from "@/lib/engine";

export const dynamic = "force-dynamic";

/**
 * Uploaded `01/` presentation. `source: "canonical-read-model"` is a local
 * demo label, NOT Python CanonicalDecisionAuthority.
 */
export async function GET() {
  const data = await getOverview();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
