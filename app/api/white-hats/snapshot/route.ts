import { NextResponse } from "next/server";
import { readWhiteHatsSoakSnapshot } from "@/src/features/white-hats/lib/data.server";

export const dynamic = "force-dynamic";

/** Read-only REAL white-hats snapshot from M13_SOAK (no secrets). */
export async function GET() {
  const snap = readWhiteHatsSoakSnapshot();
  if (!snap) {
    return NextResponse.json({ ok: false, error: "UNAVAILABLE" }, { status: 503 });
  }
  return NextResponse.json({ ok: true, snapshot: snap });
}
