import { db } from "@/db";
import { alerts } from "@/db/schema";
import { eq } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function PATCH(req: Request) {
  try {
    const { id, isRead } = await req.json();
    if (typeof id !== "number") {
      return Response.json({ ok: false, error: "id is required" }, { status: 400 });
    }
    await db.update(alerts).set({ isRead: Boolean(isRead) }).where(eq(alerts.id, id));
    return Response.json({ ok: true });
  } catch (err) {
    console.error(err);
    return Response.json({ ok: false }, { status: 500 });
  }
}
