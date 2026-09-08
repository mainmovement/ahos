import { db } from "@/db";
import { settings } from "@/db/schema";
import { eq } from "drizzle-orm";
import { z } from "zod";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rows = await db.select().from(settings);
    const map = Object.fromEntries(rows.map((r) => [r.key, r.value]));
    return Response.json({ ok: true, settings: map });
  } catch {
    return Response.json({ ok: false, settings: {} }, { status: 500 });
  }
}

const bodySchema = z.object({
  key: z.string().min(1),
  value: z.record(z.string(), z.unknown()),
});

export async function PUT(req: Request) {
  try {
    const json = await req.json();
    const parsed = bodySchema.safeParse(json);
    if (!parsed.success) {
      return Response.json({ ok: false, error: "Invalid settings payload." }, { status: 400 });
    }
    const { key, value } = parsed.data;

    const existing = await db.select().from(settings).where(eq(settings.key, key));
    if (existing.length > 0) {
      await db.update(settings).set({ value, updatedAt: new Date() }).where(eq(settings.key, key));
    } else {
      await db.insert(settings).values({ key, value });
    }

    return Response.json({ ok: true });
  } catch (err) {
    console.error(err);
    return Response.json({ ok: false, error: "Could not save settings." }, { status: 500 });
  }
}
