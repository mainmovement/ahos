import { desc } from "drizzle-orm";
import { db } from "@/db";
import {
  alerts,
  councilOpinions,
  decisions,
  evidence,
  learningPatterns,
  paperTrades,
  providers,
  teamStats,
  tokenScores,
  tokens,
  treeEvents,
  type GateSnapshot,
  type Scenario,
} from "@/db/schema";
import { seedIfEmpty } from "@/db/seed";

/* ------------------------------------------------------------------ */
/* View models — the ONLY thing the web layer is allowed to read        */
/* ------------------------------------------------------------------ */

export type IdentityStatus =
  | "VERIFIED" | "CONFLICT" | "UNRESOLVED" | "INVALID" | "STALE" | "UNSUPPORTED";
export type SecurityGate = "PASS" | "REJECT" | "INCOMPLETE" | "STALE";
export type DecisionKind =
  | "STRONG_CANDIDATE" | "CANDIDATE" | "MONITOR" | "SKIP" | "REJECT";
export type Stance = "BULLISH" | "BEARISH" | "NEUTRAL" | "ABSTAIN" | "ALARM";
export type ProviderStatus = "OK" | "DEGRADED" | "STALE" | "BLOCKED" | "FAILING";

export type ScoreSet = {
  opportunity: number; security: number; liquidity: number; whale: number;
  social: number; narrative: number; evidence: number; confidence: number;
};

export type TokenRow = typeof tokens.$inferSelect;
export type DecisionRow = typeof decisions.$inferSelect;
export type EvidenceRow = typeof evidence.$inferSelect;
export type AlertRow = typeof alerts.$inferSelect;
export type ProviderRow = typeof providers.$inferSelect;
export type TeamRow = typeof teamStats.$inferSelect;
export type OpinionRow = typeof councilOpinions.$inferSelect;
export type PatternRow = typeof learningPatterns.$inferSelect;
export type TreeEventRow = typeof treeEvents.$inferSelect;

export type PaperRow = typeof paperTrades.$inferSelect;

export type TokenCard = {
  token: TokenRow;
  scores: ScoreSet | null;
  decision: DecisionRow | null;
};

export type CouncilSession = {
  decision: DecisionRow;
  token: TokenRow;
  opinions: OpinionRow[];
  disagreement: number; // 0..1
};

export type PaperStats = {
  winRate: number | null;
  avgWin: number | null;
  avgLoss: number | null;
  maxDrawdown: number;
  expectancy: number | null;
  totalPnlUsd: number;
  wins: number;
  losses: number;
  timeouts: number;
};

export type TreeVitals = {
  roots: number;
  healthyRoots: number;
  rocks: number;
  branches: number;
  leaves: number;
  fruits: number;
  goldenFruits: number;
  water: number;
};

/* ------------------------------------------------------------------ */

function toScoreSet(row: typeof tokenScores.$inferSelect | undefined): ScoreSet | null {
  if (!row) return null;
  return {
    opportunity: row.opportunity, security: row.security, liquidity: row.liquidity,
    whale: row.whale, social: row.social, narrative: row.narrative,
    evidence: row.evidence, confidence: row.confidence,
  };
}

function latest<T extends { createdAt?: Date | null; computedAt?: Date | null }>(
  rows: T[],
  key: "createdAt" | "computedAt",
): T | undefined {
  let best: T | undefined;
  for (const r of rows) {
    const t = (r[key] ?? new Date(0)) as Date;
    const bt = best ? ((best[key] ?? new Date(0)) as Date) : new Date(0);
    if (!best || t > bt) best = r;
  }
  return best;
}

function disagreementIndex(opinions: OpinionRow[]): number {
  if (opinions.length === 0) return 0;
  const counts = new Map<string, number>();
  for (const o of opinions) counts.set(o.stance, (counts.get(o.stance) ?? 0) + 1);
  const max = Math.max(...counts.values());
  return Math.round((1 - max / opinions.length) * 100) / 100;
}

async function base() {
  await seedIfEmpty();
  const [t, s, d, e, a, p, ts, ops, lp, te, pt] = await Promise.all([
    db.select().from(tokens),
    db.select().from(tokenScores),
    db.select().from(decisions),
    db.select().from(evidence),
    db.select().from(alerts).orderBy(desc(alerts.createdAt)).limit(12),
    db.select().from(providers),
    db.select().from(teamStats),
    db.select().from(councilOpinions),
    db.select().from(learningPatterns).orderBy(desc(learningPatterns.createdAt)),
    db.select().from(treeEvents).orderBy(desc(treeEvents.createdAt)),
    db.select().from(paperTrades).orderBy(paperTrades.openedAt),
  ]);
  return { t, s, d, e, a, p, ts, ops, lp, te, pt };
}

function mapCards(ctx: Awaited<ReturnType<typeof base>>): TokenCard[] {
  return ctx.t.map((token) => ({
    token,
    scores: toScoreSet(latest(ctx.s.filter((x) => x.tokenId === token.id), "computedAt")),
    decision: latest(ctx.d.filter((x) => x.tokenId === token.id), "createdAt") ?? null,
  }));
}

export function cardRank(c: TokenCard): number {
  // Canonical ranking: hard gates first, then opportunity, then confidence.
  const kind = c.decision?.kind ?? "MONITOR";
  const gatePenalty =
    c.token.identityStatus !== "VERIFIED" ? -1000 :
    c.token.securityGate === "REJECT" ? -900 :
    c.token.securityGate === "INCOMPLETE" ? -80 : 0;
  const kindBoost =
    kind === "STRONG_CANDIDATE" ? 400 : kind === "CANDIDATE" ? 200 :
    kind === "MONITOR" ? 40 : kind === "SKIP" ? -140 : -600;
  return (c.scores?.opportunity ?? 0) * 3 + (c.scores?.confidence ?? 0) + kindBoost + gatePenalty;
}

/* ------------------------------------------------------------------ */

export async function getOpportunities(): Promise<TokenCard[]> {
  const ctx = await base();
  return mapCards(ctx).sort((a, b) => cardRank(b) - cardRank(a));
}

export type Overview = {
  cards: TokenCard[];
  golden: TokenCard | null;
  decisionsCount: number;
  stats: { tracked: number; paperPnl: number; winRate: number | null; openCount: number };
  funnel: { stages: number[]; exceptional: number };
  alerts: AlertRow[];
  providers: ProviderRow[];
  patterns: PatternRow[];
  events: TreeEventRow[];
  teams: TeamRow[];
  session: CouncilSession | null;
  vitals: TreeVitals;
  evidenceCount: number;
};

function computePaperStats(closed: PaperRow[], open: PaperRow[]): PaperStats & { equity: number[] } {
  const decisive = closed.filter((x) => x.result === "WIN" || x.result === "LOSS");
  const wins = decisive.filter((x) => x.result === "WIN");
  const losses = decisive.filter((x) => x.result === "LOSS");
  const timeouts = closed.filter((x) => x.result === "TIMEOUT").length;
  const eq: number[] = [];
  let cum = 0;
  let peak = 0;
  let mdd = 0;
  for (const x of [...closed].sort((a, b) => (a.closedAt?.getTime() ?? 0) - (b.closedAt?.getTime() ?? 0))) {
    cum += x.pnlPct ?? 0;
    eq.push(Math.round(cum * 10) / 10);
    peak = Math.max(peak, cum);
    mdd = Math.max(mdd, peak - cum);
  }
  const openPnlUsd = open.reduce((acc, x) => {
    if (!x.currentPrice || !x.entry) return acc;
    return acc + ((x.currentPrice - x.entry) / x.entry) * x.sizeUsd;
  }, 0);
  const closedPnlUsd = closed.reduce((acc, x) => acc + (x.pnlUsd ?? 0), 0);
  return {
    equity: eq,
    winRate: decisive.length ? Math.round((wins.length / decisive.length) * 100) : null,
    avgWin: wins.length ? wins.reduce((a, x) => a + (x.pnlPct ?? 0), 0) / wins.length : null,
    avgLoss: losses.length ? losses.reduce((a, x) => a + (x.pnlPct ?? 0), 0) / losses.length : null,
    maxDrawdown: Math.round(mdd * 10) / 10,
    expectancy: closed.length
      ? Math.round((closed.reduce((a, x) => a + (x.pnlPct ?? 0), 0) / closed.length) * 10) / 10
      : null,
    totalPnlUsd: Math.round((closedPnlUsd + openPnlUsd) * 10) / 10,
    wins: wins.length,
    losses: losses.length,
    timeouts,
  };
}

function buildVitals(ctx: Awaited<ReturnType<typeof base>>, cards: TokenCard[]): TreeVitals {
  const rocks = ctx.p.filter((x) => x.status === "BLOCKED" || x.status === "FAILING").length;
  const golden = cards.filter((c) => c.decision?.kind === "STRONG_CANDIDATE").length;
  const fruits = cards.filter((c) => c.decision?.kind === "CANDIDATE").length;
  return {
    roots: ctx.p.length,
    healthyRoots: ctx.p.length - rocks - ctx.p.filter((x) => x.status === "STALE").length,
    rocks,
    branches: ctx.ts.length,
    leaves: ctx.e.length * 4,
    fruits,
    goldenFruits: golden,
    water: ctx.e.filter((x) => x.status === "VERIFIED").length,
  };
}

export async function getOverview(): Promise<Overview> {
  const ctx = await base();
  const cards = mapCards(ctx);
  const closed = ctx.pt.filter((x) => x.status === "CLOSED");
  const open = ctx.pt.filter((x) => x.status === "OPEN");
  const pstats = computePaperStats(closed, open);
  const golden = cards
    .filter((c) => c.decision?.kind === "STRONG_CANDIDATE")
    .sort((a, b) => cardRank(b) - cardRank(a))[0] ?? null;

  let session: CouncilSession | null = null;
  if (golden?.decision) {
    const ops = ctx.ops.filter((o) => o.decisionId === golden.decision!.id);
    session = { decision: golden.decision, token: golden.token, opinions: ops, disagreement: disagreementIndex(ops) };
  }

  const investigated = new Set(ctx.e.map((x) => x.tokenId)).size;
  const strong = cards.filter((c) => c.decision?.kind === "STRONG_CANDIDATE" || c.decision?.kind === "CANDIDATE").length;
  const exceptional = cards.filter((c) => c.decision?.kind === "STRONG_CANDIDATE").length;

  return {
    cards,
    golden,
    decisionsCount: ctx.d.length,
    stats: {
      tracked: ctx.t.length,
      paperPnl: pstats.totalPnlUsd,
      winRate: pstats.winRate,
      openCount: open.length,
    },
    funnel: { stages: [1240, 480, 96, investigated, strong, exceptional], exceptional },
    alerts: ctx.a,
    providers: ctx.p,
    patterns: ctx.lp,
    events: ctx.te,
    teams: ctx.ts,
    session,
    vitals: buildVitals(ctx, cards),
    evidenceCount: ctx.e.length,
  };
}

export type Dossier = {
  token: TokenRow;
  scores: ScoreSet | null;
  decision: DecisionRow | null;
  opinions: OpinionRow[];
  evidence: EvidenceRow[];
  trades: PaperRow[];
  teams: TeamRow[];
  disagreement: number;
} | null;

export async function getDossier(slug: string): Promise<Dossier> {
  const ctx = await base();
  const token = ctx.t.find((x) => x.slug === slug);
  if (!token) return null;
  const decision = latest(ctx.d.filter((x) => x.tokenId === token.id), "createdAt") ?? null;
  const opinions = decision ? ctx.ops.filter((o) => o.decisionId === decision.id) : [];
  return {
    token,
    scores: toScoreSet(latest(ctx.s.filter((x) => x.tokenId === token.id), "computedAt")),
    decision,
    opinions,
    evidence: ctx.e.filter((x) => x.tokenId === token.id).sort((a, b) => b.observedAt.getTime() - a.observedAt.getTime()),
    trades: ctx.pt.filter((x) => x.tokenId === token.id).sort((a, b) => b.openedAt.getTime() - a.openedAt.getTime()),
    teams: ctx.ts,
    disagreement: disagreementIndex(opinions),
  };
}

export type CouncilView = {
  teams: TeamRow[];
  sessions: CouncilSession[];
};

export async function getCouncilView(): Promise<CouncilView> {
  const ctx = await base();
  const sorted = [...ctx.d].sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  const sessions: CouncilSession[] = sorted.slice(0, 3).map((decision) => {
    const token = ctx.t.find((x) => x.id === decision.tokenId)!;
    const opinions = ctx.ops.filter((o) => o.decisionId === decision.id);
    return { decision, token, opinions, disagreement: disagreementIndex(opinions) };
  }).filter((s) => s.token);
  return { teams: ctx.ts, sessions };
}

export type PaperView = {
  open: { trade: PaperRow; token: TokenRow; runningPct: number; progress: number }[];
  closed: { trade: PaperRow; token: TokenRow }[];
  stats: PaperStats;
  equity: number[];
  patterns: PatternRow[];
};

export async function getPaperView(): Promise<PaperView> {
  const ctx = await base();
  const tokenOf = (id: string) => ctx.t.find((x) => x.id === id)!;
  const closed = ctx.pt.filter((x) => x.status === "CLOSED");
  const openRows = ctx.pt.filter((x) => x.status === "OPEN");
  const pstats = computePaperStats(closed, openRows);
  const open = openRows.map((trade) => {
    const runningPct =
      trade.currentPrice && trade.entry ? ((trade.currentPrice - trade.entry) / trade.entry) * 100 : 0;
    const span = trade.target1 - trade.entry;
    const progress =
      span !== 0 && trade.currentPrice
        ? Math.min(100, Math.max(-100, ((trade.currentPrice - trade.entry) / span) * 100))
        : 0;
    return { trade, token: tokenOf(trade.tokenId), runningPct, progress };
  });
  return {
    open,
    closed: [...closed]
      .sort((a, b) => (b.closedAt?.getTime() ?? 0) - (a.closedAt?.getTime() ?? 0))
      .map((trade) => ({ trade, token: tokenOf(trade.tokenId) })),
    stats: pstats,
    equity: pstats.equity,
    patterns: ctx.lp,
  };
}

export async function getTreeView() {
  const ctx = await base();
  const cards = mapCards(ctx);
  return {
    events: ctx.te,
    providers: ctx.p,
    vitals: buildVitals(ctx, cards),
    patterns: ctx.lp,
  };
}

/* Re-export schema helper types for pages */
export type { GateSnapshot, Scenario };

/** Latest alert top item (used by ticker). */
export async function getTickerItems() {
  const ctx = await base();
  return ctx.t.map((token) => ({
    slug: token.slug,
    symbol: token.symbol,
    priceUsd: token.priceUsd,
    change24h: token.change24h,
    decision: latest(ctx.d.filter((x) => x.tokenId === token.id), "createdAt")?.kind ?? null,
  }));
}
