import { db } from "@/db";
import { auditLog, settings } from "@/db/schema";
import { eq } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = (await req.json()) as Record<string, unknown>;
  const [row] = await db.select().from(settings).where(eq(settings.key, "workspace")).limit(1);
  const next = { ...(row?.value ?? {}), ...body };
  if (row) {
    await db.update(settings).set({ value: next, updatedAt: new Date() }).where(eq(settings.key, "workspace"));
  } else {
    await db.insert(settings).values({ key: "workspace", value: next });
  }
  await db.insert(auditLog).values({ action: "SETTINGS", detail: JSON.stringify(body) });
  return Response.json({ ok: true });
}
