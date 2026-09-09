import { getTreeView } from "@/lib/engine";

export const dynamic = "force-dynamic";

/** Wise Tree vitals + growth events — provenance visualization, not a decision. */
export async function GET() {
  const data = await getTreeView();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
