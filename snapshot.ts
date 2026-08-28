import { db } from "@/db";
import {
  councilReports,
  cycles,
  expertVotes,
  findings,
  lessons,
  marketSnapshots,
  newsItems,
  opportunities,
  outcomes,
  paperPositions,
  providerSnapshots,
  systemState,
  watchlist,
} from "@/db/schema";
import { desc, eq } from "drizzle-orm";
import { TEAM_META } from "./council";
import { ensureState } from "./engine";

function deepestErrorMessage(error: unknown): string {
  let cur: unknown = error;
  let last = error instanceof Error ? error.message : String(error);
  // Walk Error.cause and drizzle's nested [cause] without leaking secrets.
  for (let i = 0; i < 6; i++) {
    if (!cur || typeof cur !== "object") break;
    const c = cur as { cause?: unknown; message?: unknown };
    if (c.cause) {
      cur = c.cause;
      if (cur instanceof Error && cur.message) last = cur.message;
      else if (typeof cur === "object" && cur && "message" in cur) {
        last = String((cur as { message: unknown }).message);
      }
      continue;
    }
    break;
  }
  return last;
}

export async function commandSnapshot() {
  try {
    await ensureState();
  } catch (error) {
    const root = deepestErrorMessage(error);
    const msg = error instanceof Error ? error.message : String(error);
    throw new Error(
      `commandSnapshot.ensureState failed: ${root}` +
        (root !== msg ? ` (drizzle: ${msg.slice(0, 120)})` : ""),
      { cause: error },
    );
  }
  const [state] = await db.select().from(systemState).limit(1);
  if (!state) {
    throw new Error(
      "commandSnapshot: ahos_system_state empty after ensureState — " +
        "DATABASE_URL may point at the wrong database (STATE B: no migrate).",
    );
  }
  const [cycle] = await db.select().from(cycles).orderBy(desc(cycles.id)).limit(1);
  const [market] = await db.select().from(marketSnapshots).orderBy(desc(marketSnapshots.id)).limit(1);
  const opps = await db.select().from(opportunities).orderBy(desc(opportunities.id)).limit(30);
  const news = await db.select().from(newsItems).orderBy(desc(newsItems.id)).limit(24);
  const providers = cycle
    ? await db.select().from(providerSnapshots).where(eq(providerSnapshots.cycleId, cycle.id))
    : [];
  const watches = await db.select().from(watchlist).where(eq(watchlist.active, true));
  const papers = await db.select().from(paperPositions).orderBy(desc(paperPositions.id)).limit(20);
  const lastLessons = await db.select().from(lessons).orderBy(desc(lessons.id)).limit(8);
  const lastFindings = await db.select().from(findings).orderBy(desc(findings.id)).limit(8);
  const lastOutcomes = await db.select().from(outcomes).orderBy(desc(outcomes.id)).limit(8);
  const lastCouncil = await db.select().from(councilReports).orderBy(desc(councilReports.id)).limit(8);
  const lastVotes = await db.select().from(expertVotes).orderBy(desc(expertVotes.id)).limit(40);

  const successProviders = providers.filter((p) => p.status === "SUCCESS").length;
  const downProviders = providers.filter((p) => ["DOWN", "RATE_LIMIT", "AUTH_REQUIRED", "NO_KEY", "COST_BLOCKED", "OUT_OF_POLICY"].includes(p.status));

  const health = {
    dimensions: [
      dim("امنیت داده", state.lastCycleStatus === "SUCCESS" ? "OK" : "UNKNOWN", "UNKNOWN هرگز با داده جعلی پر نشد."),
      dim("سلامت پروایدر", providers.length ? (successProviders > 0 ? "OK" : "DEGRADED") : "UNKNOWN", `${successProviders} موفق از ${providers.length || 0}`),
      dim("تازگی شواهد", cycle?.finishedAt ? "OK" : "UNKNOWN", cycle?.finishedAt ? cycle.finishedAt.toISOString() : "NO_DATA"),
      dim("کیفیت شواهد", typeof cycle?.unknownShare === "number" ? "OK" : "UNKNOWN", `سهم UNKNOWN/ناکافی=${cycle?.unknownShare ?? "UNKNOWN"}`),
      dim("کالیبراسیون", lastOutcomes.length ? "OK" : "INSUFFICIENT_EVIDENCE", lastOutcomes.length ? `${lastOutcomes.length} نتیجه ثبت‌شده` : "هنوز outcome محلی کافی نیست"),
      dim("یادگیری", lastLessons.length ? "OK" : "INSUFFICIENT_EVIDENCE", lastLessons.length ? `${lastLessons.length} درس` : "درس جدیدی نیست"),
      dim("تکامل", lastFindings.length ? "OK" : "UNKNOWN", lastFindings.length ? `${lastFindings.length} یافته` : "یافته‌ای نیست"),
      dim("رژیم بازار", market?.regime && market.regime !== "UNKNOWN" ? "OK" : "UNKNOWN", market?.regime ?? "UNKNOWN"),
      dim("شورای کارشناسان", lastCouncil.length ? "OK" : "UNKNOWN", "۱۰۰ نقش در ۱۰ تیم — مشورتی"),
      dim("پورتفوی کاغذی", "OK", `${papers.filter((p) => p.status === "OPEN").length} موقعیت باز — اجرای واقعی DISABLED`),
      dim("خبر فارسی", news.length ? "OK" : "UNKNOWN", `${news.length} خبر با بازنویسی فارسی`),
      dim("صفرپولی", "OK", "NO REAL TRADING / PAPER_ONLY"),
    ],
  };

  return {
    generatedAt: new Date().toISOString(),
    executionMode: "PAPER_ONLY",
    realTrading: false,
    state: {
      running: state.running,
      startedAt: state.startedAt,
      stoppedAt: state.stoppedAt,
      lastCycleAt: state.lastCycleAt,
      lastCycleStatus: state.lastCycleStatus,
      cycleCount: state.cycleCount,
      lastError: state.lastError,
      intervalSec: state.intervalSec,
    },
    cycle: cycle
      ? {
          id: cycle.id,
          status: cycle.status,
          durationMs: cycle.durationMs,
          tokenCount: cycle.tokenCount,
          newsCount: cycle.newsCount,
          opportunityCount: cycle.opportunityCount,
          unknownShare: cycle.unknownShare,
          notesFa: cycle.notesFa,
        }
      : null,
    market: market
      ? {
          regime: market.regime,
          fearGreed: market.fearGreed,
          fearGreedLabel: market.fearGreedLabel,
          btcPrice: market.btcPrice,
          btcChange24h: market.btcChange24h,
          ethPrice: market.ethPrice,
          ethChange24h: market.ethChange24h,
          solPrice: market.solPrice,
          solChange24h: market.solChange24h,
          totalMcap: market.totalMcap,
          mcapChange24h: market.mcapChange24h,
          btcDominance: market.btcDominance,
          defiTvl: market.defiTvl,
          payload: market.payload,
          createdAt: market.createdAt,
        }
      : null,
    opportunities: opps.map((o) => ({
      id: o.id,
      tokenKey: o.tokenKey,
      symbol: o.symbol,
      name: o.name,
      chain: o.chain,
      address: o.address,
      decision: o.decision,
      rankScore: o.rankScore,
      confidence: o.confidence,
      securityStatus: o.securityStatus,
      evidenceCoverage: o.evidenceCoverage,
      reasonsFa: o.reasonsFa,
      risksFa: o.risksFa,
      unknownsFa: o.unknownsFa,
      invalidationFa: o.invalidationFa,
      missingFa: o.missingFa,
      councilVerdict: o.councilVerdict,
      disagreement: o.disagreement,
      payload: o.payload,
      createdAt: o.createdAt,
    })),
    news: news.map((n) => ({
      id: n.id,
      source: n.source,
      sourceUrl: n.sourceUrl,
      titleOriginal: n.titleOriginal,
      titleFa: n.titleFa,
      summaryFa: n.summaryFa,
      publishedAt: n.publishedAt,
      importance: n.importance,
      category: n.category,
      sentiment: n.sentiment,
      relatedTokens: n.relatedTokens,
      relatedChains: n.relatedChains,
      impact: n.impact,
    })),
    providers: providers.map((p) => ({
      provider: p.provider,
      category: p.category,
      status: p.status,
      latencyMs: p.latencyMs,
      itemCount: p.itemCount,
      messageFa: p.messageFa,
    })),
    providerCensus: {
      total: providers.length,
      success: successProviders,
      degraded: downProviders.length,
    },
    watchlist: watches,
    paper: papers,
    lessons: lastLessons,
    findings: lastFindings,
    outcomes: lastOutcomes,
    council: lastCouncil,
    votes: lastVotes,
    teams: TEAM_META,
    health,
    blocked: [
      { item: "معامله واقعی", status: "DISABLED" },
      { item: "امضای کیف پول", status: "DISABLED" },
      { item: "DEXTools", status: "NO_KEY" },
      { item: "X/Twitter API", status: "COST_BLOCKED" },
      { item: "Instagram/TikTok scrape", status: "OUT_OF_POLICY" },
      { item: "Telegram scrape", status: "OUT_OF_POLICY" },
      { item: "مدل‌های پولی AI", status: process.env.OPENAI_API_KEY || process.env.GROQ_API_KEY || process.env.GEMINI_API_KEY ? "OPTIONAL_KEY_PRESENT" : "NO_KEY" },
    ],
  };
}

function dim(nameFa: string, status: string, evidenceFa: string) {
  return { nameFa, status, evidenceFa };
}
