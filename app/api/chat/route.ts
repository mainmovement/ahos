import { conversationGateway } from "@/conversation_gateway";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
    const history = Array.isArray(body.history)
      ? (body.history as Array<{ role?: string; content?: string }>)
          .filter(
            (h) =>
              h &&
              (h.role === "user" || h.role === "assistant") &&
              typeof h.content === "string",
          )
          .map((h) => ({
            role: h.role as "user" | "assistant",
            content: String(h.content),
          }))
          .slice(-12)
      : [];
    const gw = await conversationGateway({
      message: String(body.message || ""),
      conversation_id: (body.conversation_id as string) ?? null,
      user_id: (body.user_id as string) ?? null,
      channel: (body.channel as "web" | "telegram" | "api") ?? "web",
      history,
      focus_token:
        (body.focus_token as string) ?? (body.focusToken as string) ?? null,
      referenced_token: (body.referenced_token as string) ?? null,
    });
    return Response.json({
      reply: gw.answer,
      intent: gw.intent,
      evidence: gw.evidence,
      focusToken: gw.focus_token,
      answer: gw.answer,
      focus_token: gw.focus_token,
      uncertainty: gw.uncertainty,
      timestamp: gw.timestamp,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "UNKNOWN";
    return Response.json(
      {
        reply: `خطای داخلی: ${message}`,
        intent: "error",
        evidence: { error: message },
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}
