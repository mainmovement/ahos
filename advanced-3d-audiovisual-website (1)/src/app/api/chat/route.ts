import { db } from "@/db";
import { chatMessages } from "@/db/schema";
import { answerQuestion } from "@/lib/reasoningEngine";
import { z } from "zod";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rows = await db.select().from(chatMessages).orderBy(chatMessages.createdAt).limit(200);
    return Response.json({ ok: true, messages: rows });
  } catch {
    return Response.json({ ok: false, messages: [] }, { status: 500 });
  }
}

const bodySchema = z.object({ message: z.string().min(1).max(2000) });

export async function POST(req: Request) {
  try {
    const json = await req.json();
    const parsed = bodySchema.safeParse(json);
    if (!parsed.success) {
      return Response.json({ ok: false, error: "Message is required." }, { status: 400 });
    }

    const { message } = parsed.data;
    await db.insert(chatMessages).values({ role: "user", content: message });

    const reply = await answerQuestion(message);
    const [saved] = await db.insert(chatMessages).values({ role: "assistant", content: reply }).returning();

    return Response.json({ ok: true, reply: saved });
  } catch (err) {
    console.error(err);
    return Response.json({ ok: false, error: "AHOS could not process this message." }, { status: 500 });
  }
}

export async function DELETE() {
  try {
    await db.delete(chatMessages);
    return Response.json({ ok: true });
  } catch {
    return Response.json({ ok: false }, { status: 500 });
  }
}
