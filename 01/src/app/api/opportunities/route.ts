import { getOpportunities } from "@/lib/engine";

export const dynamic = "force-dynamic";

/** Ranked opportunity cards — ranking computed server-side only. */
export async function GET() {
  const data = await getOpportunities();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
