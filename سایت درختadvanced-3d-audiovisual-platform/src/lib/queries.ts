import { db } from "@/db";
import {
  alerts,
  chatMessages,
  councilVotes,
  dailyReports,
  evidence,
  githubItems,
  learningRecords,
  newsItems,
  onchainEvents,
  paperTrades,
  securityFindings,
  settings,
  socialSignals,
  systemComponents,
  telegramMessages,
  tokenScores,
  tokens,
  whaleMoves,
} from "@/db/schema";
import { desc, eq, sql } from "drizzle-orm";
import { ensureSeeded } from "@/lib/bootstrap";

export async function loadBoard() {
  await ensureSeeded();
  const rows = await db
    .select()
    .from(tokens)
    .leftJoin(tokenScores, eq(tokenScores.tokenId, tokens.id))
    .orderBy(desc(tokenScores.opportunity));
  return rows.map((r) => ({ token: r.tokens, score: r.token_scores }));
}

export async function loadToken(slug: string) {
  await ensureSeeded();
  const [row] = await db
    .select()
    .from(tokens)
    .leftJoin(tokenScores, eq(tokenScores.tokenId, tokens.id))
    .where(eq(tokens.slug, slug))
    .limit(1);
  if (!row) return null;
  const tokenId = row.tokens.id;
  const [ev, votes, findings, whales, chain, social, news, trades] = await Promise.all([
    db.select().from(evidence).where(eq(evidence.tokenId, tokenId)).orderBy(desc(evidence.weight)),
    db.select().from(councilVotes).where(eq(councilVotes.tokenId, tokenId)).orderBy(councilVotes.teamNo),
    db.select().from(securityFindings).where(eq(securityFindings.tokenId, tokenId)),
    db.select().from(whaleMoves).where(eq(whaleMoves.tokenId, tokenId)),
    db.select().from(onchainEvents).where(eq(onchainEvents.tokenId, tokenId)),
    db.select().from(socialSignals).where(eq(socialSignals.tokenId, tokenId)),
    db.select().from(newsItems).where(eq(newsItems.tokenId, tokenId)),
    db.select().from(paperTrades).where(eq(paperTrades.tokenId, tokenId)),
  ]);
  return {
    token: row.tokens,
    score: row.token_scores,
    evidence: ev,
    votes,
    findings,
    whales,
    chain,
    social,
    news,
    trades,
  };
}

export async function loadDashboard() {
  await ensureSeeded();
  const [board, trades, alertRows, components, learn, report, github] = await Promise.all([
    loadBoard(),
    db.select().from(paperTrades).orderBy(desc(paperTrades.openedAt)),
    db.select().from(alerts).orderBy(desc(alerts.createdAt)).limit(8),
    db.select().from(systemComponents),
    db.select().from(learningRecords).orderBy(desc(learningRecords.createdAt)).limit(4),
    db.select().from(dailyReports).orderBy(desc(dailyReports.createdAt)).limit(1),
    db.select().from(githubItems).orderBy(desc(githubItems.createdAt)).limit(5),
  ]);
  const open = trades.filter((t) => t.status === "open");
  const closed = trades.filter((t) => t.status !== "open");
  const pnl = trades.reduce((a, t) => a + t.pnlUsd, 0);
  const wins = closed.filter((t) => t.pnlUsd > 0).length;
  const losses = closed.filter((t) => t.pnlUsd <= 0).length;
  return {
    board,
    trades,
    open,
    closed,
    pnl,
    wins,
    losses,
    alerts: alertRows,
    components,
    learn,
    report: report[0] ?? null,
    github,
  };
}

export async function loadAlerts() {
  await ensureSeeded();
  return db.select().from(alerts).orderBy(desc(alerts.createdAt));
}

export async function loadNews() {
  await ensureSeeded();
  return db
    .select()
    .from(newsItems)
    .leftJoin(tokens, eq(newsItems.tokenId, tokens.id))
    .orderBy(desc(newsItems.createdAt));
}

export async function loadSocial() {
  await ensureSeeded();
  return db
    .select()
    .from(socialSignals)
    .leftJoin(tokens, eq(socialSignals.tokenId, tokens.id))
    .orderBy(desc(socialSignals.velocity));
}

export async function loadOnchain() {
  await ensureSeeded();
  const [events, whales] = await Promise.all([
    db
      .select()
      .from(onchainEvents)
      .leftJoin(tokens, eq(onchainEvents.tokenId, tokens.id))
      .orderBy(desc(onchainEvents.createdAt)),
    db
      .select()
      .from(whaleMoves)
      .leftJoin(tokens, eq(whaleMoves.tokenId, tokens.id))
      .orderBy(desc(whaleMoves.amountUsd)),
  ]);
  return { events, whales };
}

export async function loadSecurity() {
  await ensureSeeded();
  return db
    .select()
    .from(securityFindings)
    .leftJoin(tokens, eq(securityFindings.tokenId, tokens.id))
    .leftJoin(tokenScores, eq(tokenScores.tokenId, tokens.id))
    .orderBy(desc(securityFindings.createdAt));
}

export async function loadCouncil() {
  await ensureSeeded();
  const votes = await db
    .select()
    .from(councilVotes)
    .leftJoin(tokens, eq(councilVotes.tokenId, tokens.id))
    .leftJoin(tokenScores, eq(tokenScores.tokenId, tokens.id))
    .orderBy(councilVotes.teamNo);
  return votes;
}

export async function loadPaper() {
  await ensureSeeded();
  return db
    .select()
    .from(paperTrades)
    .leftJoin(tokens, eq(paperTrades.tokenId, tokens.id))
    .leftJoin(tokenScores, eq(tokenScores.tokenId, tokens.id))
    .orderBy(desc(paperTrades.openedAt));
}

export async function loadSystem() {
  await ensureSeeded();
  const [components, logs] = await Promise.all([
    db.select().from(systemComponents),
    db.select().from(alerts).where(eq(alerts.kind, "system")).orderBy(desc(alerts.createdAt)),
  ]);
  return { components, logs };
}

export async function loadSettings() {
  await ensureSeeded();
  const rows = await db.select().from(settings);
  return rows;
}

export async function loadChat() {
  await ensureSeeded();
  return db.select().from(chatMessages).orderBy(chatMessages.createdAt);
}

export async function loadTelegram() {
  await ensureSeeded();
  return db.select().from(telegramMessages).orderBy(telegramMessages.createdAt);
}

export async function loadLearning() {
  await ensureSeeded();
  return db
    .select()
    .from(learningRecords)
    .leftJoin(tokens, eq(learningRecords.tokenId, tokens.id))
    .orderBy(desc(learningRecords.createdAt));
}

export async function loadGithub() {
  await ensureSeeded();
  return db.select().from(githubItems).orderBy(desc(githubItems.createdAt));
}

export async function loadReports() {
  await ensureSeeded();
  return db.select().from(dailyReports).orderBy(desc(dailyReports.createdAt));
}

export async function loadIntelligence() {
  const board = await loadBoard();
  const totals = board.reduce(
    (acc, row) => {
      acc.n += 1;
      if (row.score) {
        acc.opp += row.score.opportunity;
        acc.sec += row.score.security;
        acc.conf += row.score.confidence;
      }
      acc.vol += row.token.volumeUsd;
      acc.liq += row.token.liquidityUsd;
      acc.byGroup[row.token.tokenGroup] = (acc.byGroup[row.token.tokenGroup] ?? 0) + 1;
      acc.byStatus[row.token.status] = (acc.byStatus[row.token.status] ?? 0) + 1;
      acc.byChain[row.token.chain] = (acc.byChain[row.token.chain] ?? 0) + 1;
      return acc;
    },
    {
      n: 0,
      opp: 0,
      sec: 0,
      conf: 0,
      vol: 0,
      liq: 0,
      byGroup: {} as Record<string, number>,
      byStatus: {} as Record<string, number>,
      byChain: {} as Record<string, number>,
    },
  );
  return { board, totals };
}

export async function statsCount() {
  await ensureSeeded();
  const [row] = await db.select({ c: sql<number>`count(*)` }).from(tokens);
  return Number(row?.c ?? 0);
}
