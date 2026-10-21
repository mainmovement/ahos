import { NextResponse } from "next/server";
import { readSelfEvaluation } from "@/src/features/missions-b2/lib/data.server";

export const dynamic = "force-dynamic";

/** Read-only M58 self-evaluation snapshot (local JSON file). */
export async function GET() {
  const se = readSelfEvaluation();
  if (!se) {
    return NextResponse.json({ ok: false, error: "UNAVAILABLE" }, { status: 503 });
  }
  return NextResponse.json({ ok: true, selfEvaluation: se, demo: false });
}
