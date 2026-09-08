import { db } from "@/db";
import { chatMessages } from "@/db/schema";
import { loadBoard } from "@/lib/queries";
import { councilReply } from "@/lib/reply";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = (await req.json()) as { content?: string };
  const content = (body.content ?? "").trim();
  if (!content) return Response.json({ ok: false, error: "Empty" }, { status: 400 });
  await db.insert(chatMessages).values({ role: "user", content });
  const board = await loadBoard();
  const reply = councilReply(content, board);
  await db.insert(chatMessages).values({ role: "assistant", content: reply });
  return Response.json({ ok: true, reply });
}
