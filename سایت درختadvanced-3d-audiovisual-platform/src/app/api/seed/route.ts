import { resetAndSeed } from "@/lib/seed";

export const dynamic = "force-dynamic";

export async function POST() {
  await resetAndSeed();
  return Response.json({ ok: true });
}
