import {
  boolean,
  index,
  integer,
  jsonb,
  pgTable,
  real,
  serial,
  text,
  timestamp,
  varchar,
} from "drizzle-orm/pg-core";

export const tokens = pgTable(
  "tokens",
  {
    id: serial("id").primaryKey(),
    slug: varchar("slug", { length: 80 }).notNull().unique(),
    name: varchar("name", { length: 120 }).notNull(),
    symbol: varchar("symbol", { length: 24 }).notNull(),
    chain: varchar("chain", { length: 48 }).notNull(),
    contract: varchar("contract", { length: 128 }).notNull(),
    tokenGroup: varchar("token_group", { length: 32 }).notNull(),
    launchDate: timestamp("launch_date", { withTimezone: true }),
    liquidityUsd: real("liquidity_usd").notNull().default(0),
    marketCapUsd: real("market_cap_usd").notNull().default(0),
    volumeUsd: real("volume_usd").notNull().default(0),
    priceUsd: real("price_usd").notNull().default(0),
    holders: integer("holders").notNull().default(0),
    status: varchar("status", { length: 24 }).notNull().default("watch"),
    narrative: varchar("narrative", { length: 64 }).notNull().default("Unknown"),
    summary: text("summary").notNull(),
    accent: varchar("accent", { length: 16 }).notNull().default("#c9a36a"),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("tokens_status_idx").on(t.status), index("tokens_chain_idx").on(t.chain)],
);

export const tokenScores = pgTable(
  "token_scores",
  {
    id: serial("id").primaryKey(),
    tokenId: integer("token_id")
      .notNull()
      .references(() => tokens.id, { onDelete: "cascade" }),
    opportunity: integer("opportunity").notNull(),
    security: integer("security").notNull(),
    liquidity: integer("liquidity").notNull(),
    social: integer("social").notNull(),
    whale: integer("whale").notNull(),
    narrative: integer("narrative").notNull(),
    evidence: integer("evidence").notNull(),
    confidence: integer("confidence").notNull(),
    decision: varchar("decision", { length: 24 }).notNull(),
    thesis: text("thesis").notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("token_scores_token_idx").on(t.tokenId)],
);

export const evidence = pgTable(
  "evidence",
  {
    id: serial("id").primaryKey(),
    tokenId: integer("token_id")
      .notNull()
      .references(() => tokens.id, { onDelete: "cascade" }),
    source: varchar("source", { length: 80 }).notNull(),
    kind: varchar("kind", { length: 40 }).notNull(),
    label: varchar("label", { length: 160 }).notNull(),
    detail: text("detail").notNull(),
    verification: varchar("verification", { length: 24 }).notNull(),
    weight: integer("weight").notNull().default(50),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("evidence_token_idx").on(t.tokenId)],
);

export const councilVotes = pgTable(
  "council_votes",
  {
    id: serial("id").primaryKey(),
    tokenId: integer("token_id")
      .notNull()
      .references(() => tokens.id, { onDelete: "cascade" }),
    teamNo: integer("team_no").notNull(),
    teamName: varchar("team_name", { length: 80 }).notNull(),
    stance: varchar("stance", { length: 24 }).notNull(),
    confidence: integer("confidence").notNull(),
    rationale: text("rationale").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("council_token_idx").on(t.tokenId)],
);

export const paperTrades = pgTable(
  "paper_trades",
  {
    id: serial("id").primaryKey(),
    tokenId: integer("token_id")
      .notNull()
      .references(() => tokens.id, { onDelete: "cascade" }),
    side: varchar("side", { length: 8 }).notNull().default("long"),
    entry: real("entry").notNull(),
    capital: real("capital").notNull(),
    size: real("size").notNull(),
    stop: real("stop").notNull(),
    target1: real("target1").notNull(),
    target2: real("target2").notNull(),
    target3: real("target3").notNull(),
    status: varchar("status", { length: 16 }).notNull().default("open"),
    pnlUsd: real("pnl_usd").notNull().default(0),
    pnlPct: real("pnl_pct").notNull().default(0),
    notes: text("notes").notNull().default(""),
    openedAt: timestamp("opened_at", { withTimezone: true }).notNull().defaultNow(),
    closedAt: timestamp("closed_at", { withTimezone: true }),
  },
  (t) => [index("paper_status_idx").on(t.status)],
);

export const alerts = pgTable(
  "alerts",
  {
    id: serial("id").primaryKey(),
    tokenId: integer("token_id").references(() => tokens.id, { onDelete: "set null" }),
    kind: varchar("kind", { length: 40 }).notNull(),
    severity: varchar("severity", { length: 16 }).notNull(),
    title: varchar("title", { length: 180 }).notNull(),
    body: text("body").notNull(),
    read: boolean("read").notNull().default(false),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("alerts_read_idx").on(t.read)],
);

export const newsItems = pgTable("news_items", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").references(() => tokens.id, { onDelete: "set null" }),
  title: varchar("title", { length: 220 }).notNull(),
  source: varchar("source", { length: 80 }).notNull(),
  summary: text("summary").notNull(),
  url: text("url").notNull().default("#"),
  sentiment: varchar("sentiment", { length: 16 }).notNull(),
  verification: varchar("verification", { length: 24 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const socialSignals = pgTable("social_signals", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").references(() => tokens.id, { onDelete: "set null" }),
  platform: varchar("platform", { length: 40 }).notNull(),
  metric: varchar("metric", { length: 64 }).notNull(),
  value: real("value").notNull(),
  velocity: real("velocity").notNull(),
  note: text("note").notNull(),
  authenticity: varchar("authenticity", { length: 24 }).notNull().default("unknown"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const onchainEvents = pgTable("onchain_events", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id")
    .notNull()
    .references(() => tokens.id, { onDelete: "cascade" }),
  kind: varchar("kind", { length: 40 }).notNull(),
  wallet: varchar("wallet", { length: 80 }).notNull(),
  amountUsd: real("amount_usd").notNull().default(0),
  note: text("note").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const securityFindings = pgTable("security_findings", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id")
    .notNull()
    .references(() => tokens.id, { onDelete: "cascade" }),
  severity: varchar("severity", { length: 16 }).notNull(),
  title: varchar("title", { length: 180 }).notNull(),
  detail: text("detail").notNull(),
  gate: varchar("gate", { length: 16 }).notNull().default("pass"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const whaleMoves = pgTable("whale_moves", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id")
    .notNull()
    .references(() => tokens.id, { onDelete: "cascade" }),
  wallet: varchar("wallet", { length: 80 }).notNull(),
  action: varchar("action", { length: 24 }).notNull(),
  amountUsd: real("amount_usd").notNull(),
  note: text("note").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const systemComponents = pgTable("system_components", {
  id: serial("id").primaryKey(),
  key: varchar("key", { length: 64 }).notNull().unique(),
  name: varchar("name", { length: 120 }).notNull(),
  layer: varchar("layer", { length: 40 }).notNull(),
  status: varchar("status", { length: 16 }).notNull(),
  provider: varchar("provider", { length: 80 }).notNull(),
  latencyMs: integer("latency_ms").notNull().default(0),
  note: text("note").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const settings = pgTable("settings", {
  id: serial("id").primaryKey(),
  key: varchar("key", { length: 64 }).notNull().unique(),
  value: jsonb("value").$type<Record<string, unknown>>().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const chatMessages = pgTable("chat_messages", {
  id: serial("id").primaryKey(),
  role: varchar("role", { length: 16 }).notNull(),
  content: text("content").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const telegramMessages = pgTable("telegram_messages", {
  id: serial("id").primaryKey(),
  direction: varchar("direction", { length: 8 }).notNull(),
  content: text("content").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const learningRecords = pgTable("learning_records", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").references(() => tokens.id, { onDelete: "set null" }),
  kind: varchar("kind", { length: 16 }).notNull(),
  title: varchar("title", { length: 180 }).notNull(),
  insight: text("insight").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const githubItems = pgTable("github_items", {
  id: serial("id").primaryKey(),
  kind: varchar("kind", { length: 16 }).notNull(),
  title: varchar("title", { length: 180 }).notNull(),
  body: text("body").notNull(),
  status: varchar("status", { length: 24 }).notNull().default("open"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const dailyReports = pgTable("daily_reports", {
  id: serial("id").primaryKey(),
  reportDate: varchar("report_date", { length: 16 }).notNull().unique(),
  headline: varchar("headline", { length: 220 }).notNull(),
  body: text("body").notNull(),
  metrics: jsonb("metrics").$type<Record<string, number>>().notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const auditLog = pgTable("audit_log", {
  id: serial("id").primaryKey(),
  action: varchar("action", { length: 80 }).notNull(),
  detail: text("detail").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export type Token = typeof tokens.$inferSelect;
export type TokenScore = typeof tokenScores.$inferSelect;
export type Evidence = typeof evidence.$inferSelect;
export type CouncilVote = typeof councilVotes.$inferSelect;
export type PaperTrade = typeof paperTrades.$inferSelect;
export type Alert = typeof alerts.$inferSelect;
export type NewsItem = typeof newsItems.$inferSelect;
export type SocialSignal = typeof socialSignals.$inferSelect;
export type OnchainEvent = typeof onchainEvents.$inferSelect;
export type SecurityFinding = typeof securityFindings.$inferSelect;
export type WhaleMove = typeof whaleMoves.$inferSelect;
export type SystemComponent = typeof systemComponents.$inferSelect;
export type ChatMessage = typeof chatMessages.$inferSelect;
export type TelegramMessage = typeof telegramMessages.$inferSelect;
export type LearningRecord = typeof learningRecords.$inferSelect;
export type GithubItem = typeof githubItems.$inferSelect;
export type DailyReport = typeof dailyReports.$inferSelect;
export type Setting = typeof settings.$inferSelect;
