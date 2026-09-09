import { getTreeView } from "@/lib/engine";

export const dynamic = "force-dynamic";

/**
 * Uploaded `01/` Wise Tree vitals. Presentation only — not a decision, not
 * Phase 4. `source: "canonical-read-model"` is a local demo label, NOT
 * Python CanonicalDecisionAuthority.
 */
export async function GET() {
  const data = await getTreeView();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
