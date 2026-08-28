import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { addWatch } from "@/engine";

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
      thesisFa?: string;
    };
    if (!body.tokenKey || !body.symbol || !body.chain) {
      return Response.json({ ok: false, error: "INSUFFICIENT_EVIDENCE" }, { status: 400 });
    }
    await addWatch({
      tokenKey: body.tokenKey,
      symbol: body.symbol,
      chain: body.chain,
      address: body.address,
      thesisFa: body.thesisFa,
    });
    return Response.json({ ok: true, mode: "PAPER_ONLY" });
  } catch (error) {
    return Response.json(
      { ok: false, error: sanitizePublicError(error) },
      { status: 500 },
    );
  }
}
