import { db } from "@/db";
import { auditLog, githubItems } from "@/db/schema";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = (await req.json()) as { title?: string; body?: string; kind?: string };
  if (!body.title || !body.body) return Response.json({ ok: false }, { status: 400 });
  await db.insert(githubItems).values({
    title: body.title,
    body: body.body,
    kind: body.kind ?? "issue",
    status: "open",
  });
  await db.insert(auditLog).values({ action: "GITHUB", detail: body.title });
  return Response.json({ ok: true });
}
