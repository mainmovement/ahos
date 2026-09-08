import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { addPaper } from "@/engine";
import { loadCanonicalReadModel, paperAllowedFromCanonical } from "@/canonical_read_model";

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
    const model = await loadCanonicalReadModel();
    if (!paperAllowedFromCanonical(model, body.chain, body.address || null)) {
      return Response.json(
        {
          ok: false,
          error: "CANONICAL_PAPER_DENIED",
          canonicalStatus: model.status,
          hintFa: "خرید کاغذی فقط با حکم کانونیکال BUY پایتون مجاز است — لایه وب تصمیم نمی‌سازد.",
        },
        { status: 403 },
      );
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
