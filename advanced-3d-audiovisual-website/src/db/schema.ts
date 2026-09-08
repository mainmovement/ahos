import { pgTable, uuid, text, integer, numeric, timestamp, jsonb } from "drizzle-orm/pg-core";

export const tokens = pgTable("tokens", {
  id: uuid("id").primaryKey().defaultRandom(),
  symbol: text("symbol").notNull(),
  name: text("name").notNull(),
  chain: text("chain").notNull(), // Solana, Ethereum, Base, BNB
  contractAddress: text("contract_address").notNull(),
  category: text("category").notNull(), // 'pre-launch', 'newly-launched', 'hidden-opportunity'
  opportunityScore: integer("opportunity_score").notNull().default(0),
  securityScore: integer("security_score").notNull().default(0),
  confidenceScore: integer("confidence_score").notNull().default(0),
  liquidityScore: integer("liquidity_score").notNull().default(0),
  whaleScore: integer("whale_score").notNull().default(0),
  socialScore: integer("social_score").notNull().default(0),
  narrativeScore: integer("narrative_score").notNull().default(0),
  evidenceScore: integer("evidence_score").notNull().default(0),
  price: numeric("price").notNull().default("0"),
  priceChange24h: numeric("price_change_24h").notNull().default("0"),
  liquidityUsd: numeric("liquidity_usd").notNull().default("0"),
  marketCapUsd: numeric("market_cap_usd").notNull().default("0"),
  volume24h: numeric("volume_24h").notNull().default("0"),
  holdersCount: integer("holders_count").notNull().default(0),
  status: text("status").notNull().default("screened"), // 'screened', 'investigating', 'approved', 'rejected'
  narrative: text("narrative").notNull().default("General"),
  evidenceSummary: text("evidence_summary"),
  risksSummary: text("risks_summary"),
  bullScenario: text("bull_scenario"),
  baseScenario: text("base_scenario"),
  bearScenario: text("bear_scenario"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const councilOpinions = pgTable("council_opinions", {
  id: uuid("id").primaryKey().defaultRandom(),
  tokenId: uuid("token_id").references(() => tokens.id, { onDelete: "cascade" }),
  teamCode: text("team_code").notNull(), // team_01 .. team_10
  teamName: text("team_name").notNull(),
  verdict: text("verdict").notNull(), // 'bullish', 'bearish', 'caution', 'reject', 'insufficient_data'
  confidence: integer("confidence").notNull().default(50),
  argument: text("argument").notNull(),
  keyEvidence: text("key_evidence"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const paperTrades = pgTable("paper_trades", {
  id: uuid("id").primaryKey().defaultRandom(),
  tokenId: uuid("token_id").references(() => tokens.id, { onDelete: "cascade" }),
  symbol: text("symbol").notNull(),
  type: text("type").notNull().default("BUY"),
  entryPrice: numeric("entry_price").notNull(),
  currentPrice: numeric("current_price").notNull(),
  exitPrice: numeric("exit_price"),
  stopLoss: numeric("stop_loss").notNull(),
  targetPrice: numeric("target_price").notNull(),
  virtualCapital: numeric("virtual_capital").notNull().default("100"),
  positionSize: numeric("position_size").notNull(),
  pnlUsd: numeric("pnl_usd").notNull().default("0"),
  pnlPercent: numeric("pnl_percent").notNull().default("0"),
  status: text("status").notNull().default("OPEN"), // 'OPEN', 'CLOSED_WIN', 'CLOSED_LOSS', 'CANCELLED'
  postMortem: text("post_mortem"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  closedAt: timestamp("closed_at"),
});

export const learningLogs = pgTable("learning_logs", {
  id: uuid("id").primaryKey().defaultRandom(),
  eventType: text("event_type").notNull(), // WIN_PATTERN, FAILURE_PATTERN, SECURITY_EXPLOIT, FALSE_POSITIVE
  title: text("title").notNull(),
  description: text("description").notNull(),
  impact: text("impact").notNull(),
  treeLayer: text("tree_layer").notNull().default("ROOTS"), // ROOTS, TRUNK, BRANCHES, LEAVES, OCEAN
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const githubWorkflows = pgTable("github_workflows", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: text("name").notNull(),
  type: text("type").notNull(), // github_action, n8n_agent, python_scanner
  status: text("status").notNull().default("active"),
  lastRun: timestamp("last_run").defaultNow().notNull(),
  executionCount: integer("execution_count").notNull().default(0),
  logSummary: text("log_summary"),
});

export const systemLogs = pgTable("system_logs", {
  id: uuid("id").primaryKey().defaultRandom(),
  level: text("level").notNull(), // INFO, WARN, SECURITY_ALERT, WHALE_ALERT
  source: text("source").notNull(),
  message: text("message").notNull(),
  details: text("details"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});
