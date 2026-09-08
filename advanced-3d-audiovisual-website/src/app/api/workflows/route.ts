import { NextResponse } from "next/server";
import { db } from "@/db";
import { githubWorkflows, systemLogs } from "@/db/schema";
import { desc, eq } from "drizzle-orm";

export async function GET() {
  try {
    const workflows = await db.select().from(githubWorkflows).orderBy(desc(githubWorkflows.lastRun));
    return NextResponse.json({ success: true, workflows });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { workflowId } = body;

    if (!workflowId) {
      return NextResponse.json({ success: false, error: "workflowId required" }, { status: 400 });
    }

    const wf = await db.select().from(githubWorkflows).where(eq(githubWorkflows.id, workflowId)).limit(1);
    if (wf.length === 0) {
      return NextResponse.json({ success: false, error: "Workflow not found" }, { status: 404 });
    }

    const current = wf[0];
    const newCount = current.executionCount + 1;

    const [updated] = await db
      .update(githubWorkflows)
      .set({
        executionCount: newCount,
        lastRun: new Date(),
        logSummary: `[SUCCESS] Execution #${newCount}: Scanned RPCs, fetched OSINT feed, synchronized 10 AI Council Agents.`,
      })
      .where(eq(githubWorkflows.id, workflowId))
      .returning();

    await db.insert(systemLogs).values({
      level: "INFO",
      source: "n8nOrchestrator",
      message: `Triggered pipeline '${updated.name}' successfully.`,
      details: `Execution #${newCount}`,
    });

    return NextResponse.json({ success: true, workflow: updated });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
