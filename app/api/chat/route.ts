import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { conversationGateway } from "@/conversation_gateway";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function stackTop(error: unknown, maxFrames = 6): string | null {
  if (!(error instanceof Error) || !error.stack) return null;
  const frames = error.stack
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.startsWith("at "))
    .slice(0, maxFrames);
  return frames.length ? frames.join(" | ") : null;
}

export async function POST(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
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
    // Next access log only shows "POST /api/chat 500" — always print the real stack.
    console.error("[api/chat] POST failed:", error);
    if (error instanceof Error && error.stack) {
      console.error("[api/chat] stack:\n" + error.stack);
    }
    const message = sanitizePublicError(error);
    const top = stackTop(error);
    return Response.json(
      {
        reply: `خطای داخلی: ${message}`,
        intent: "error",
        evidence: {
          error: message,
          error_name: error instanceof Error ? error.name : "UNKNOWN",
          stack_top: top,
          hint:
            "Windows G2: run scripts\\windows_chat_500_forensics.ps1 and " +
            "scripts\\windows_ensure_database_url.ps1 (STATE B: no migrate).",
        },
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}
