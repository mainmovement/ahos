import { db } from "@/db";
import {
  tokens,
  opportunityScores,
  securityChecks,
  councilOpinions,
  councilTeams,
  evidenceItems,
  newsItems,
  socialSignals,
  onchainEvents,
  paperTrades,
  tradeEvents,
  alerts,
  systemComponents,
  systemLogs,
  learningLogs,
  settings,
} from "@/db/schema";
import { desc, eq, sql } from "drizzle-orm";

export async function getGlobalStats() {
  const [tokenCount] = await db.select({ count: sql<number>`count(*)::int` }).from(tokens);
  const [rejectedCount] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(opportunityScores)
    .where(eq(opportunityScores.councilDecision, "reject"));
  const [watchCount] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(opportunityScores)
    .where(eq(opportunityScores.councilDecision, "watch"));
  const [openTrades] = await db.select({ count: sql<number>`count(*)::int` }).from(paperTrades).where(eq(paperTrades.status, "open"));
  const [closedTrades] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(paperTrades)
    .where(eq(paperTrades.status, "closed"));
  const [wins] = await db.select({ count: sql<number>`count(*)::int` }).from(paperTrades).where(eq(paperTrades.outcome, "win"));
  const [totalPnl] = await db.select({ sum: sql<string>`coalesce(sum(pnl_usd), 0)` }).from(paperTrades);

  return {
    tokensTracked: tokenCount?.count ?? 0,
    rejected: rejectedCount?.count ?? 0,
    watching: watchCount?.count ?? 0,
    openTrades: openTrades?.count ?? 0,
    closedTrades: closedTrades?.count ?? 0,
    wins: wins?.count ?? 0,
    totalPnl: Number(totalPnl?.sum ?? 0),
  };
}

export async function listTokensWithScores() {
  return db
    .select({
      token: tokens,
      score: opportunityScores,
    })
    .from(tokens)
    .leftJoin(opportunityScores, eq(opportunityScores.tokenId, tokens.id))
    .orderBy(desc(opportunityScores.opportunityScore));
}

export async function getTokenDossier(tokenId: number) {
  const [token] = await db.select().from(tokens).where(eq(tokens.id, tokenId));
  if (!token) return null;
  const [score] = await db.select().from(opportunityScores).where(eq(opportunityScores.tokenId, tokenId));
  const [security] = await db.select().from(securityChecks).where(eq(securityChecks.tokenId, tokenId));
  const opinions = await db
    .select({ opinion: councilOpinions, team: councilTeams })
    .from(councilOpinions)
    .innerJoin(councilTeams, eq(councilTeams.id, councilOpinions.teamId))
    .where(eq(councilOpinions.tokenId, tokenId))
    .orderBy(councilTeams.sortOrder);
  const evidence = await db.select().from(evidenceItems).where(eq(evidenceItems.tokenId, tokenId)).orderBy(desc(evidenceItems.createdAt));
  const social = await db.select().from(socialSignals).where(eq(socialSignals.tokenId, tokenId)).orderBy(desc(socialSignals.capturedAt));
  const onchain = await db.select().from(onchainEvents).where(eq(onchainEvents.tokenId, tokenId)).orderBy(desc(onchainEvents.occurredAt));
  const news = await db.select().from(newsItems).where(eq(newsItems.tokenId, tokenId)).orderBy(desc(newsItems.publishedAt));
  const trades = await db.select().from(paperTrades).where(eq(paperTrades.tokenId, tokenId)).orderBy(desc(paperTrades.openedAt));

  return { token, score, security, opinions, evidence, social, onchain, news, trades };
}

export async function listCouncilTeams() {
  return db.select().from(councilTeams).orderBy(councilTeams.sortOrder);
}

export async function listAlerts(limit = 50) {
  return db
    .select({ alert: alerts, token: tokens })
    .from(alerts)
    .leftJoin(tokens, eq(tokens.id, alerts.tokenId))
    .orderBy(desc(alerts.createdAt))
    .limit(limit);
}

export async function listNews(limit = 30) {
  return db
    .select({ news: newsItems, token: tokens })
    .from(newsItems)
    .leftJoin(tokens, eq(tokens.id, newsItems.tokenId))
    .orderBy(desc(newsItems.publishedAt))
    .limit(limit);
}

export async function listSocialAgg() {
  return db
    .select({
      tokenId: socialSignals.tokenId,
      token: tokens,
      mentions: sql<number>`sum(${socialSignals.mentions})::int`,
      engagement: sql<number>`avg(${socialSignals.engagementScore})::int`,
      sentiment: sql<number>`avg(${socialSignals.sentiment})::int`,
      velocity: sql<number>`avg(${socialSignals.narrativeVelocity})::int`,
      influencer: sql<number>`avg(${socialSignals.influencerActivity})::int`,
    })
    .from(socialSignals)
    .innerJoin(tokens, eq(tokens.id, socialSignals.tokenId))
    .groupBy(socialSignals.tokenId, tokens.id)
    .orderBy(desc(sql`sum(${socialSignals.mentions})`));
}

export async function listOnchainEvents(limit = 40) {
  return db
    .select({ event: onchainEvents, token: tokens })
    .from(onchainEvents)
    .innerJoin(tokens, eq(tokens.id, onchainEvents.tokenId))
    .orderBy(desc(onchainEvents.occurredAt))
    .limit(limit);
}

export async function listPaperTrades() {
  const trades = await db
    .select({ trade: paperTrades, token: tokens })
    .from(paperTrades)
    .innerJoin(tokens, eq(tokens.id, paperTrades.tokenId))
    .orderBy(desc(paperTrades.openedAt));

  const events = await db.select().from(tradeEvents).orderBy(desc(tradeEvents.createdAt));
  return { trades, events };
}

export async function listSystemStatus() {
  const components = await db.select().from(systemComponents).orderBy(systemComponents.category);
  const logs = await db.select().from(systemLogs).orderBy(desc(systemLogs.createdAt)).limit(30);
  return { components, logs };
}

export async function listLearningLogs() {
  return db
    .select({ log: learningLogs, token: tokens })
    .from(learningLogs)
    .leftJoin(tokens, eq(tokens.id, learningLogs.tokenId))
    .orderBy(desc(learningLogs.createdAt));
}

export async function getAllSettings() {
  const rows = await db.select().from(settings);
  return Object.fromEntries(rows.map((r) => [r.key, r.value]));
}

export async function listSecurityChecks() {
  return db
    .select({ security: securityChecks, token: tokens })
    .from(securityChecks)
    .innerJoin(tokens, eq(tokens.id, securityChecks.tokenId))
    .orderBy(desc(securityChecks.checkedAt));
}
