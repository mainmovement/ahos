import { NextResponse } from "next/server";
import { readMessageHub } from "@/src/features/missions-b2/lib/data.server";

export const dynamic = "force-dynamic";

/** Read-only M35 message hub snapshot (local JSON file). */
export async function GET() {
  const hub = readMessageHub();
  if (!hub) {
    return NextResponse.json({ ok: false, error: "UNAVAILABLE" }, { status: 503 });
  }
  return NextResponse.json({
    ok: true,
    messageHub: hub,
    demo: false,
    telegramBridge: hub.telegram?.bridgeState ?? "UNKNOWN",
  });
}
