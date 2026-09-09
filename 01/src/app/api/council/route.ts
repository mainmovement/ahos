import { getCouncilView } from "@/lib/engine";

export const dynamic = "force-dynamic";

/** AI Expert Council view — teams, sessions, disagreement indices. */
export async function GET() {
  const data = await getCouncilView();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
