import { db } from "@/db";
import { paperTrades } from "@/db/schema";
import { eq } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = (await req.json()) as { action?: string };
  if (body.action !== "mark") return Response.json({ ok: false }, { status: 400 });
  const open = await db.select().from(paperTrades).where(eq(paperTrades.status, "open"));
  for (const t of open) {
    const drift = (Math.random() - 0.42) * 1.8;
    const pnlPct = t.pnlPct + drift;
    const pnlUsd = (pnlPct / 100) * t.capital;
    await db.update(paperTrades).set({ pnlPct, pnlUsd }).where(eq(paperTrades.id, t.id));
  }
  return Response.json({ ok: true, updated: open.length });
}
