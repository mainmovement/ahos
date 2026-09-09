import { getOverview } from "@/lib/engine";

export const dynamic = "force-dynamic";

/** Canonical overview read model — the dashboard consumes exactly this. */
export async function GET() {
  const data = await getOverview();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
