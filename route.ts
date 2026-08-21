import { addWatch } from "@/lib/ahos/engine";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
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
}
