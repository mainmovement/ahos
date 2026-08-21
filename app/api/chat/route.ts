import { handleChat } from "@/chat";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const body = (await req.json().catch(() => ({}))) as { message?: string };
    const message = (body.message || "").trim();
    if (!message) {
      return Response.json({ reply: "پیام خالی بود.", intent: "empty" }, { status: 400 });
    }
    const result = await handleChat(message);
    return Response.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "UNKNOWN";
    return Response.json(
      {
        reply: `خطای داخلی: ${message}. چیزی جعل نشد.`,
        intent: "error",
        evidence: { error: message },
      },
      { status: 500 },
    );
  }
}
