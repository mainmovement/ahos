import {
  pgTable,
  serial,
  text,
  varchar,
  integer,
  numeric,
  boolean,
  timestamp,
  jsonb,
  pgEnum,
} from "drizzle-orm/pg-core";

// ---------------------------------------------------------------------------
// AHOS — Artificial Hybrid Opportunity Scoring System
// Core data models. See /docs/DATA_MODEL.md for full contract documentation.
// ---------------------------------------------------------------------------

export const tokenStatusEnum = pgEnum("token_status", [
  "pre_launch",
  "new",
  "existing",
]);

export const councilDecisionEnum = pgEnum("council_decision", [
  "strong_buy",
  "watch",
  "insufficient_evidence",
  "reject",
  "skip",
]);

export const riskLevelEnum = pgEnum("risk_level", [
  "low",
  "medium",
  "high",
  "critical",
]);

export const stanceEnum = pgEnum("stance", [
  "bullish",
  "bearish",
  "neutral",
  "risk_flag",
  "insufficient_evidence",
]);

export const verificationEnum = pgEnum("verification_status", [
  "verified",
  "unverified",
  "rumor",
  "conflicted",
]);

export const impactEnum = pgEnum("impact", ["positive", "negative", "neutral"]);

export const sourceTypeEnum = pgEnum("source_type", [
  "market",
  "onchain",
  "social",
  "news",
  "development",
  "rumor",
  "security",
]);

export const tradeStatusEnum = pgEnum("trade_status", ["open", "closed"]);

export const tradeOutcomeEnum = pgEnum("trade_outcome", [
  "win",
  "loss",
  "breakeven",
  "pending",
  "skip",
]);

export const alertSeverityEnum = pgEnum("alert_severity", [
  "info",
  "warning",
  "critical",
]);

export const alertTypeEnum = pgEnum("alert_type", [
  "discovery",
  "opportunity",
  "security",
  "whale",
  "news",
  "exit",
  "system",
  "daily_report",
]);

export const componentStatusEnum = pgEnum("component_status", [
  "operational",
  "degraded",
  "down",
  "maintenance",
]);

export const chatRoleEnum = pgEnum("chat_role", ["user", "assistant"]);

export const patternTypeEnum = pgEnum("pattern_type", [
  "success",
  "failure",
  "skip",
]);

// ---------------------------------------------------------------------------
// Tokens
// ---------------------------------------------------------------------------
export const tokens = pgTable("tokens", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 128 }).notNull(),
  symbol: varchar("symbol", { length: 32 }).notNull(),
  chain: varchar("chain", { length: 64 }).notNull(),
  contractAddress: varchar("contract_address", { length: 128 }),
  status: tokenStatusEnum("status").notNull().default("new"),
  narrative: varchar("narrative", { length: 64 }),
  logoEmoji: varchar("logo_emoji", { length: 8 }).default("🪙"),
  launchDate: timestamp("launch_date", { withTimezone: true }),
  priceUsd: numeric("price_usd", { precision: 24, scale: 10 }).default("0"),
  priceChange24h: numeric("price_change_24h", { precision: 10, scale: 4 }).default("0"),
  marketCapUsd: numeric("market_cap_usd", { precision: 24, scale: 2 }).default("0"),
  liquidityUsd: numeric("liquidity_usd", { precision: 24, scale: 2 }).default("0"),
  volume24hUsd: numeric("volume_24h_usd", { precision: 24, scale: 2 }).default("0"),
  holders: integer("holders").default(0),
  summary: text("summary"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Opportunity Scores (multi-dimensional, per section 14)
// ---------------------------------------------------------------------------
export const opportunityScores = pgTable("opportunity_scores", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").notNull().references(() => tokens.id, { onDelete: "cascade" }),
  opportunityScore: integer("opportunity_score").notNull().default(0),
  securityScore: integer("security_score").notNull().default(0),
  liquidityScore: integer("liquidity_score").notNull().default(0),
  socialMomentum: integer("social_momentum").notNull().default(0),
  whaleScore: integer("whale_score").notNull().default(0),
  narrativeScore: integer("narrative_score").notNull().default(0),
  evidenceScore: integer("evidence_score").notNull().default(0),
  confidence: integer("confidence").notNull().default(0),
  councilDecision: councilDecisionEnum("council_decision").notNull().default("insufficient_evidence"),
  bullScenario: text("bull_scenario"),
  baseScenario: text("base_scenario"),
  bearScenario: text("bear_scenario"),
  extremeRiskScenario: text("extreme_risk_scenario"),
  whyPoints: jsonb("why_points").$type<string[]>().default([]),
  riskPoints: jsonb("risk_points").$type<string[]>().default([]),
  rejectConditions: jsonb("reject_conditions").$type<string[]>().default([]),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Security Analysis (section 9)
// ---------------------------------------------------------------------------
export const securityChecks = pgTable("security_checks", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").notNull().references(() => tokens.id, { onDelete: "cascade" }),
  riskLevel: riskLevelEnum("risk_level").notNull().default("medium"),
  honeypot: boolean("honeypot").notNull().default(false),
  buyTaxPercent: numeric("buy_tax_percent", { precision: 6, scale: 2 }).default("0"),
  sellTaxPercent: numeric("sell_tax_percent", { precision: 6, scale: 2 }).default("0"),
  mintAuthority: boolean("mint_authority").notNull().default(false),
  freezeAuthority: boolean("freeze_authority").notNull().default(false),
  ownershipRenounced: boolean("ownership_renounced").notNull().default(false),
  liquidityLocked: boolean("liquidity_locked").notNull().default(false),
  lpLockPercent: numeric("lp_lock_percent", { precision: 6, scale: 2 }).default("0"),
  topHolderConcentration: numeric("top_holder_concentration", { precision: 6, scale: 2 }).default("0"),
  deployerRugHistory: boolean("deployer_rug_history").notNull().default(false),
  hiddenAdminFunctions: boolean("hidden_admin_functions").notNull().default(false),
  flags: jsonb("flags").$type<string[]>().default([]),
  notes: text("notes"),
  checkedAt: timestamp("checked_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Council Teams & Opinions (sections 11-13)
// ---------------------------------------------------------------------------
export const councilTeams = pgTable("council_teams", {
  id: serial("id").primaryKey(),
  code: varchar("code", { length: 16 }).notNull().unique(),
  name: varchar("name", { length: 128 }).notNull(),
  focus: text("focus").notNull(),
  icon: varchar("icon", { length: 32 }).default("brain"),
  sortOrder: integer("sort_order").notNull().default(0),
});

export const councilOpinions = pgTable("council_opinions", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").notNull().references(() => tokens.id, { onDelete: "cascade" }),
  teamId: integer("team_id").notNull().references(() => councilTeams.id, { onDelete: "cascade" }),
  stance: stanceEnum("stance").notNull().default("neutral"),
  summary: text("summary").notNull(),
  confidence: integer("confidence").notNull().default(50),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Evidence Ledger (section 3, 57)
// ---------------------------------------------------------------------------
export const evidenceItems = pgTable("evidence_items", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").notNull().references(() => tokens.id, { onDelete: "cascade" }),
  sourceType: sourceTypeEnum("source_type").notNull(),
  sourceName: varchar("source_name", { length: 128 }).notNull(),
  title: text("title").notNull(),
  url: text("url"),
  verification: verificationEnum("verification").notNull().default("unverified"),
  impact: impactEnum("impact").notNull().default("neutral"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// News
// ---------------------------------------------------------------------------
export const newsItems = pgTable("news_items", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").references(() => tokens.id, { onDelete: "set null" }),
  title: text("title").notNull(),
  summary: text("summary").notNull(),
  source: varchar("source", { length: 128 }).notNull(),
  url: text("url"),
  sentiment: impactEnum("sentiment").notNull().default("neutral"),
  credibility: integer("credibility").notNull().default(50),
  tags: jsonb("tags").$type<string[]>().default([]),
  publishedAt: timestamp("published_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Social Intelligence
// ---------------------------------------------------------------------------
export const socialSignals = pgTable("social_signals", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").notNull().references(() => tokens.id, { onDelete: "cascade" }),
  platform: varchar("platform", { length: 32 }).notNull(),
  mentions: integer("mentions").notNull().default(0),
  engagementScore: integer("engagement_score").notNull().default(0),
  sentiment: integer("sentiment").notNull().default(0),
  narrativeVelocity: integer("narrative_velocity").notNull().default(0),
  influencerActivity: integer("influencer_activity").notNull().default(0),
  isSynthetic: boolean("is_synthetic").notNull().default(false),
  capturedAt: timestamp("captured_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// On-chain events
// ---------------------------------------------------------------------------
export const onchainEvents = pgTable("onchain_events", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").notNull().references(() => tokens.id, { onDelete: "cascade" }),
  eventType: varchar("event_type", { length: 64 }).notNull(),
  walletAddress: varchar("wallet_address", { length: 128 }),
  amountUsd: numeric("amount_usd", { precision: 24, scale: 2 }).default("0"),
  description: text("description").notNull(),
  occurredAt: timestamp("occurred_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Paper Trading (sections 16-20)
// ---------------------------------------------------------------------------
export const paperTrades = pgTable("paper_trades", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").notNull().references(() => tokens.id, { onDelete: "cascade" }),
  status: tradeStatusEnum("status").notNull().default("open"),
  outcome: tradeOutcomeEnum("outcome").notNull().default("pending"),
  entryPrice: numeric("entry_price", { precision: 24, scale: 10 }).notNull(),
  exitPrice: numeric("exit_price", { precision: 24, scale: 10 }),
  virtualCapitalUsd: numeric("virtual_capital_usd", { precision: 18, scale: 2 }).notNull().default("1000"),
  positionSizeUsd: numeric("position_size_usd", { precision: 18, scale: 2 }).notNull().default("100"),
  stopLoss: numeric("stop_loss", { precision: 24, scale: 10 }),
  target1: numeric("target1", { precision: 24, scale: 10 }),
  target2: numeric("target2", { precision: 24, scale: 10 }),
  target3: numeric("target3", { precision: 24, scale: 10 }),
  maxHoldingHours: integer("max_holding_hours").notNull().default(72),
  pnlUsd: numeric("pnl_usd", { precision: 18, scale: 2 }).default("0"),
  pnlPercent: numeric("pnl_percent", { precision: 10, scale: 2 }).default("0"),
  reason: text("reason"),
  postMortem: text("post_mortem"),
  openedAt: timestamp("opened_at", { withTimezone: true }).notNull().defaultNow(),
  closedAt: timestamp("closed_at", { withTimezone: true }),
});

export const tradeEvents = pgTable("trade_events", {
  id: serial("id").primaryKey(),
  paperTradeId: integer("paper_trade_id").notNull().references(() => paperTrades.id, { onDelete: "cascade" }),
  eventType: varchar("event_type", { length: 64 }).notNull(),
  note: text("note").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Alerts (sections 38, telegram)
// ---------------------------------------------------------------------------
export const alerts = pgTable("alerts", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").references(() => tokens.id, { onDelete: "set null" }),
  type: alertTypeEnum("type").notNull(),
  severity: alertSeverityEnum("severity").notNull().default("info"),
  title: varchar("title", { length: 200 }).notNull(),
  message: text("message").notNull(),
  isRead: boolean("is_read").notNull().default(false),
  sentToTelegram: boolean("sent_to_telegram").notNull().default(false),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// System status / self-debug (sections 44-46)
// ---------------------------------------------------------------------------
export const systemComponents = pgTable("system_components", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 128 }).notNull(),
  category: varchar("category", { length: 64 }).notNull(),
  status: componentStatusEnum("status").notNull().default("operational"),
  latencyMs: integer("latency_ms").default(0),
  uptimePercent: numeric("uptime_percent", { precision: 5, scale: 2 }).default("100"),
  message: text("message"),
  lastChecked: timestamp("last_checked", { withTimezone: true }).notNull().defaultNow(),
});

export const systemLogs = pgTable("system_logs", {
  id: serial("id").primaryKey(),
  level: varchar("level", { length: 16 }).notNull().default("info"),
  component: varchar("component", { length: 128 }).notNull(),
  message: text("message").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Learning logs (sections 18-21)
// ---------------------------------------------------------------------------
export const learningLogs = pgTable("learning_logs", {
  id: serial("id").primaryKey(),
  tokenId: integer("token_id").references(() => tokens.id, { onDelete: "set null" }),
  paperTradeId: integer("paper_trade_id").references(() => paperTrades.id, { onDelete: "set null" }),
  patternType: patternTypeEnum("pattern_type").notNull(),
  title: varchar("title", { length: 200 }).notNull(),
  description: text("description").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// AI Chat
// ---------------------------------------------------------------------------
export const chatMessages = pgTable("chat_messages", {
  id: serial("id").primaryKey(),
  role: chatRoleEnum("role").notNull(),
  content: text("content").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// ---------------------------------------------------------------------------
// Settings (key/value, single-user system per section 30)
// ---------------------------------------------------------------------------
export const settings = pgTable("settings", {
  key: varchar("key", { length: 128 }).primaryKey(),
  value: jsonb("value").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});
