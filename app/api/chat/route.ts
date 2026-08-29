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

function isTransientPgError(error: unknown): boolean {
  const msg = error instanceof Error ? error.message : String(error || "");
  return /ECONNREFUSED|ETIMEDOUT|ENOTFOUND|Connection terminated|timeout expired|the database system is starting up|remaining connection slots|Too many connections|ECONNRESET/i.test(
    msg,
  );
}

async function sleep(ms: number): Promise<void> {
  await new Promise((r) => setTimeout(r, ms));
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
    const payload = {
      message: String(body.message || ""),
      conversation_id: (body.conversation_id as string) ?? null,
      user_id: (body.user_id as string) ?? null,
      channel: (body.channel as "web" | "telegram" | "api") ?? "web",
      history,
      focus_token:
        (body.focus_token as string) ?? (body.focusToken as string) ?? null,
      referenced_token: (body.referenced_token as string) ?? null,
    };
    // One transient retry for Postgres just-started / Next pool race (Windows G2).
    // Permanent errors (auth, missing relation) still fail honestly — no invented PASS.
    let gw;
    try {
      gw = await conversationGateway(payload);
    } catch (first) {
      if (!isTransientPgError(first)) throw first;
      console.warn(
        "[api/chat] transient DB error; one retry in 750ms:",
        first instanceof Error ? first.message : first,
      );
      await sleep(750);
      gw = await conversationGateway(payload);
    }
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
            "Windows G2: run scripts\\windows_recover_g2_warm.ps1 " +
            "(forensics + DATABASE_URL + restart; STATE B: no migrate).",
        },
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}
