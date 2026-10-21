import { NextResponse } from "next/server";
import { readSoakNewsroomSnapshot } from "@/src/features/newsroom/lib/data.server";

export const dynamic = "force-dynamic";

export async function GET() {
  const snap = readSoakNewsroomSnapshot();
  if (!snap) {
    return NextResponse.json({ ok: false, error: "UNAVAILABLE" }, { status: 503 });
  }
  return NextResponse.json({ ok: true, snapshot: snap });
}
