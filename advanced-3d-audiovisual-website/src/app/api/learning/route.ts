import { NextResponse } from "next/server";
import { db } from "@/db";
import { learningLogs } from "@/db/schema";
import { desc } from "drizzle-orm";

export async function GET() {
  try {
    const logs = await db.select().from(learningLogs).orderBy(desc(learningLogs.createdAt));
    return NextResponse.json({ success: true, learningLogs: logs });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
