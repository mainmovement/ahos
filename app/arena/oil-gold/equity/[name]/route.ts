import { readFileSync } from "node:fs";
import { equityImagePath } from "../../../../../src/features/real-paper/lib/data.server";

export const dynamic = "force-dynamic";

/** Read-only whitelisted replay equity PNG (REPLAY_NOT_LIVE). Unknown names 404. */
export async function GET(_req: Request, ctx: { params: Promise<{ name: string }> }) {
  const { name } = await ctx.params;
  const path = equityImagePath(name);
  if (!path) return new Response("not found", { status: 404 });
  try {
    return new Response(new Uint8Array(readFileSync(path)), { headers: { "content-type": "image/png", "cache-control": "no-store", "x-ahos-label": "REPLAY_NOT_LIVE" } });
  } catch {
    return new Response("not found", { status: 404 });
  }
}
