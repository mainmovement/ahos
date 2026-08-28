import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { addPaper } from "@/engine";

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
    };
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
    return Response.json(
      { ok: false, error: sanitizePublicError(error) },
      { status: 500 },
    );
  }
}
