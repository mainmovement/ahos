import { getDossier } from "@/lib/engine";

export const dynamic = "force-dynamic";

/** Full canonical dossier for one token. */
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
