import { handleChat } from "@/chat";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const body = (await req.json().catch(() => ({}))) as {
      message?: string;
      focusToken?: string | null;
      history?: Array<{ role?: string; content?: string }>;
    };
    const message = (body.message || "").trim();
    if (!message) {
      return Response.json({ reply: "پیام خالی بود.", intent: "empty" }, { status: 400 });
    }
    const history = Array.isArray(body.history)
      ? body.history
          .filter((h) => h && (h.role === "user" || h.role === "assistant") && typeof h.content === "string")
          .map((h) => ({ role: h.role as "user" | "assistant", content: String(h.content) }))
          .slice(-12)
      : [];
    const result = await handleChat(message, {
      focusToken: body.focusToken ?? null,
      history,
    });
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
