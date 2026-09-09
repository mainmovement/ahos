import { getOpportunities } from "@/lib/engine";

export const dynamic = "force-dynamic";

/**
 * Ranked opportunity cards — ranking computed server-side only.
 *
 * `source: "canonical-read-model"` is a local presentation label for this
 * uploaded `01/` tree. It is NOT Python CanonicalDecisionAuthority and NOT
 * reports/canonical_decision_read_model.json. Do not treat this API as the
 * Command Center brain.
 */
export async function GET() {
  const data = await getOpportunities();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
