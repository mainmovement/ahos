import { db } from "@/db";
import { alerts } from "@/db/schema";
import { eq } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request) {
  const body = (await req.json()) as { id?: number };
  if (!body.id) return Response.json({ ok: false }, { status: 400 });
  await db.update(alerts).set({ read: true }).where(eq(alerts.id, body.id));
  return Response.json({ ok: true });
}
