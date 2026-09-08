import { NextResponse } from "next/server";
import { db } from "@/db";
import { tokens, councilOpinions } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;

    const tokenList = await db.select().from(tokens).where(eq(tokens.id, id)).limit(1);
    if (tokenList.length === 0) {
      return NextResponse.json({ success: false, error: "Token not found" }, { status: 404 });
    }

    const token = tokenList[0];
    const opinions = await db.select().from(councilOpinions).where(eq(councilOpinions.tokenId, id));

    return NextResponse.json({
      success: true,
      token,
      councilOpinions: opinions,
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
