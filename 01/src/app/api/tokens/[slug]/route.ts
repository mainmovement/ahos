import { getDossier } from "@/lib/engine";

export const dynamic = "force-dynamic";

/**
 * Uploaded `01/` presentation. `source: "canonical-read-model"` is a local
 * demo label, NOT Python CanonicalDecisionAuthority.
 */
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ slug: string }> },
) {
  const { slug } = await params;
  const data = await getDossier(slug);
  if (!data) {
    return Response.json({ ok: false, error: "DOSSIER_NOT_FOUND" }, { status: 404 });
  }
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
