import { getPaperView } from "@/lib/engine";

export const dynamic = "force-dynamic";

/** Paper laboratory read model — positions, equity, statistics, patterns. */
export async function GET() {
  const data = await getPaperView();
  return Response.json({ ok: true, source: "canonical-read-model", data });
}
