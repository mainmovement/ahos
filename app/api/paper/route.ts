import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { addPaper, PaperSecurityDenied } from "@/engine";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  try {
    const body = (await req.json().catch(() => ({}))) as {
      tokenKey?: string;
      symbol?: string;
      chain?: string;
      address?: string;
      quantity?: number;
      entryPrice?: number;
      thesisFa?: string;
      targetPrice?: number;
      canonicalSecurityState?: unknown;
    };
    // Client-supplied canonicalSecurityState is ignored (not authority).
    void body.canonicalSecurityState;
    if (!body.tokenKey || !body.symbol || !body.chain) {
      return Response.json({ ok: false, error: "INSUFFICIENT_EVIDENCE" }, { status: 400 });
    }
    const row = await addPaper({
      tokenKey: body.tokenKey,
      symbol: body.symbol,
      chain: body.chain,
      address: body.address,
      quantity: body.quantity,
      entryPrice: body.entryPrice,
      thesisFa: body.thesisFa,
      targetPrice: body.targetPrice,
    });
    return Response.json({ ok: true, mode: "PAPER_ONLY", id: row.id });
  } catch (error) {
    if (error instanceof PaperSecurityDenied) {
      return Response.json(
        {
          ok: false,
          error: "SECURITY_GATE",
          canonicalSecurityState: error.canonicalSecurityState,
        },
        { status: 403 },
      );
    }
    return Response.json(
      { ok: false, error: sanitizePublicError(error) },
      { status: 500 },
    );
  }
}
