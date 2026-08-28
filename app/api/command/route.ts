import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { commandSnapshot } from "@/snapshot";
import { restoreDaemonIfNeeded } from "@/engine";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  try {
    await restoreDaemonIfNeeded();
    const snap = await commandSnapshot();
    return Response.json(snap);
  } catch (error) {
    const message = sanitizePublicError(error);
    return Response.json(
      {
        generatedAt: new Date().toISOString(),
        executionMode: "PAPER_ONLY",
        realTrading: false,
        state: {
          running: false,
          startedAt: null,
          stoppedAt: null,
          lastCycleAt: null,
          lastCycleStatus: "CODE_FAILURE",
          cycleCount: 0,
          lastError: message,
          intervalSec: 70,
        },
        cycle: null,
        market: null,
        opportunities: [],
        news: [],
        providers: [],
        providerCensus: { total: 0, success: 0, degraded: 0 },
        watchlist: [],
        paper: [],
        lessons: [],
        findings: [],
        outcomes: [],
        council: [],
        votes: [],
        teams: [],
        health: {
          dimensions: [
            {
              nameFa: "راه‌اندازی",
              status: "CODE_FAILURE",
              evidenceFa: message,
            },
          ],
        },
        blocked: [
          {
            item: "DATABASE_URL / Postgres",
            status: message.includes("DATABASE_URL") ? "NO_KEY" : "DOWN",
          },
        ],
      },
      { status: 200 },
    );
  }
}
