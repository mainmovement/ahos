import { NextResponse } from "next/server";
import { readPortable } from "@/src/features/missions-b3/lib/data.server";

export const dynamic = "force-dynamic";

/** Read-only M62 portable evidence (file or launcher state). */
export async function GET() {
  const portable = readPortable();
  if (!portable) {
    return NextResponse.json({ ok: false, error: "UNAVAILABLE" }, { status: 503 });
  }
  return NextResponse.json({ ok: true, portable, demo: false });
}
