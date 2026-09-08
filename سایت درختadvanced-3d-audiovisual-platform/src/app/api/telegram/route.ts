import { db } from "@/db";
import { telegramMessages } from "@/db/schema";
import { loadBoard } from "@/lib/queries";
import { councilReply } from "@/lib/reply";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = (await req.json()) as { content?: string };
  const content = (body.content ?? "").trim();
  if (!content) return Response.json({ ok: false }, { status: 400 });
  await db.insert(telegramMessages).values({ direction: "in", content });
  const board = await loadBoard();
  const reply = councilReply(content, board);
  await db.insert(telegramMessages).values({ direction: "out", content: reply });
  return Response.json({ ok: true, reply });
}
