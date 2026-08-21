import {
  boolean,
  doublePrecision,
  index,
  integer,
  jsonb,
  pgTable,
  serial,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

export const systemState = pgTable("ahos_system_state", {
  id: integer("id").primaryKey().default(1),
  running: boolean("running").notNull().default(false),
  startedAt: timestamp("started_at", { withTimezone: true }),
  stoppedAt: timestamp("stopped_at", { withTimezone: true }),
  lastCycleAt: timestamp("last_cycle_at", { withTimezone: true }),
  lastCycleStatus: text("last_cycle_status").notNull().default("UNKNOWN"),
  cycleCount: integer("cycle_count").notNull().default(0),
  lastError: text("last_error"),
  intervalSec: integer("interval_sec").notNull().default(75),
  executionMode: text("execution_mode").notNull().default("PAPER_ONLY"),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export const providerSnapshots = pgTable(
  "ahos_provider_snapshots",
  {
    id: serial("id").primaryKey(),
    cycleId: integer("cycle_id"),
    provider: text("provider").notNull(),
    category: text("category").notNull(),
    status: text("status").notNull(),
    latencyMs: integer("latency_ms"),
    itemCount: integer("item_count"),
    messageFa: text("message_fa"),
    messageEn: text("message_en"),
    provenance: jsonb("provenance").$type<Record<string, unknown>>(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [index("ahos_provider_name_idx").on(t.provider), index("ahos_provider_cycle_idx").on(t.cycleId)],
);

export const cycles = pgTable("ahos_cycles", {
  id: serial("id").primaryKey(),
  status: text("status").notNull(),
  startedAt: timestamp("started_at", { withTimezone: true }).defaultNow().notNull(),
  finishedAt: timestamp("finished_at", { withTimezone: true }),
  durationMs: integer("duration_ms"),
  tokenCount: integer("token_count"),
  newsCount: integer("news_count"),
  opportunityCount: integer("opportunity_count"),
  unknownShare: doublePrecision("unknown_share"),
  notesFa: text("notes_fa"),
  details: jsonb("details").$type<Record<string, unknown>>(),
});

export const marketSnapshots = pgTable("ahos_market_snapshots", {
  id: serial("id").primaryKey(),
  cycleId: integer("cycle_id"),
  regime: text("regime").notNull().default("UNKNOWN"),
  fearGreed: integer("fear_greed"),
  fearGreedLabel: text("fear_greed_label"),
  btcPrice: doublePrecision("btc_price"),
  btcChange24h: doublePrecision("btc_change_24h"),
  ethPrice: doublePrecision("eth_price"),
  ethChange24h: doublePrecision("eth_change_24h"),
  solPrice: doublePrecision("sol_price"),
  solChange24h: doublePrecision("sol_change_24h"),
  totalMcap: doublePrecision("total_mcap"),
  mcapChange24h: doublePrecision("mcap_change_24h"),
  btcDominance: doublePrecision("btc_dominance"),
  defiTvl: doublePrecision("defi_tvl"),
  payload: jsonb("payload").$type<Record<string, unknown>>(),
  provenance: jsonb("provenance").$type<Record<string, unknown>>(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const tokens = pgTable(
  "ahos_tokens",
  {
    id: serial("id").primaryKey(),
    key: text("key").notNull(),
    symbol: text("symbol").notNull(),
    name: text("name"),
    chain: text("chain").notNull(),
    address: text("address"),
    pairAddress: text("pair_address"),
    dexId: text("dex_id"),
    url: text("url"),
    imageUrl: text("image_url"),
    firstSeenAt: timestamp("first_seen_at", { withTimezone: true }).defaultNow().notNull(),
    lastSeenAt: timestamp("last_seen_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [uniqueIndex("ahos_tokens_key_uidx").on(t.key)],
);

export const observations = pgTable(
  "ahos_observations",
  {
    id: serial("id").primaryKey(),
    cycleId: integer("cycle_id"),
    tokenKey: text("token_key").notNull(),
    priceUsd: doublePrecision("price_usd"),
    liquidityUsd: doublePrecision("liquidity_usd"),
    volume24h: doublePrecision("volume_24h"),
    fdv: doublePrecision("fdv"),
    marketCap: doublePrecision("market_cap"),
    priceChange5m: doublePrecision("price_change_5m"),
    priceChange1h: doublePrecision("price_change_1h"),
    priceChange6h: doublePrecision("price_change_6h"),
    priceChange24h: doublePrecision("price_change_24h"),
    buys24h: integer("buys_24h"),
    sells24h: integer("sells_24h"),
    pairCreatedAt: timestamp("pair_created_at", { withTimezone: true }),
    boostActive: integer("boost_active"),
    paidPromotion: boolean("paid_promotion"),
    source: text("source").notNull(),
    raw: jsonb("raw").$type<Record<string, unknown>>(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [index("ahos_obs_token_idx").on(t.tokenKey), index("ahos_obs_cycle_idx").on(t.cycleId)],
);

export const opportunities = pgTable(
  "ahos_opportunities",
  {
    id: serial("id").primaryKey(),
    cycleId: integer("cycle_id"),
    tokenKey: text("token_key").notNull(),
    symbol: text("symbol").notNull(),
    name: text("name"),
    chain: text("chain").notNull(),
    address: text("address"),
    decision: text("decision").notNull(),
    rankScore: doublePrecision("rank_score"),
    confidence: text("confidence").notNull(),
    securityStatus: text("security_status").notNull(),
    evidenceCoverage: doublePrecision("evidence_coverage"),
    reasonsFa: jsonb("reasons_fa").$type<string[]>(),
    risksFa: jsonb("risks_fa").$type<string[]>(),
    unknownsFa: jsonb("unknowns_fa").$type<string[]>(),
    invalidationFa: text("invalidation_fa"),
    missingFa: jsonb("missing_fa").$type<string[]>(),
    councilVerdict: text("council_verdict"),
    disagreement: boolean("disagreement").notNull().default(false),
    payload: jsonb("payload").$type<Record<string, unknown>>(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [index("ahos_opp_cycle_idx").on(t.cycleId), index("ahos_opp_token_idx").on(t.tokenKey)],
);

export const securityReports = pgTable(
  "ahos_security_reports",
  {
    id: serial("id").primaryKey(),
    tokenKey: text("token_key").notNull(),
    provider: text("provider").notNull(),
    status: text("status").notNull(),
    honeypot: text("honeypot").notNull().default("UNKNOWN"),
    sellable: text("sellable").notNull().default("UNKNOWN"),
    mintable: text("mintable").notNull().default("UNKNOWN"),
    freezeable: text("freezeable").notNull().default("UNKNOWN"),
    ownership: text("ownership").notNull().default("UNKNOWN"),
    summaryFa: text("summary_fa"),
    payload: jsonb("payload").$type<Record<string, unknown>>(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [index("ahos_sec_token_idx").on(t.tokenKey)],
);

export const newsItems = pgTable(
  "ahos_news_items",
  {
    id: serial("id").primaryKey(),
    fingerprint: text("fingerprint").notNull(),
    source: text("source").notNull(),
    sourceUrl: text("source_url"),
    titleOriginal: text("title_original").notNull(),
    titleFa: text("title_fa"),
    summaryFa: text("summary_fa"),
    publishedAt: timestamp("published_at", { withTimezone: true }),
    importance: text("importance").notNull().default("UNKNOWN"),
    category: text("category").notNull().default("UNKNOWN"),
    sentiment: text("sentiment").notNull().default("UNKNOWN"),
    relatedTokens: jsonb("related_tokens").$type<string[]>(),
    relatedChains: jsonb("related_chains").$type<string[]>(),
    impact: text("impact").notNull().default("UNKNOWN"),
    provenance: jsonb("provenance").$type<Record<string, unknown>>(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [uniqueIndex("ahos_news_fp_uidx").on(t.fingerprint), index("ahos_news_pub_idx").on(t.publishedAt)],
);

export const expertVotes = pgTable(
  "ahos_expert_votes",
  {
    id: serial("id").primaryKey(),
    cycleId: integer("cycle_id"),
    tokenKey: text("token_key").notNull(),
    expertId: text("expert_id").notNull(),
    teamId: text("team_id").notNull(),
    expertNameFa: text("expert_name_fa").notNull(),
    vote: text("vote").notNull(),
    confidence: text("confidence").notNull(),
    reasonFa: text("reason_fa").notNull(),
    uncertaintyFa: text("uncertainty_fa"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [index("ahos_vote_token_idx").on(t.tokenKey), index("ahos_vote_cycle_idx").on(t.cycleId)],
);

export const councilReports = pgTable("ahos_council_reports", {
  id: serial("id").primaryKey(),
  cycleId: integer("cycle_id"),
  tokenKey: text("token_key").notNull(),
  verdict: text("verdict").notNull(),
  advisoryOnly: boolean("advisory_only").notNull().default(true),
  agreeCount: integer("agree_count").notNull().default(0),
  rejectCount: integer("reject_count").notNull().default(0),
  abstainCount: integer("abstain_count").notNull().default(0),
  watchCount: integer("watch_count").notNull().default(0),
  summaryFa: text("summary_fa").notNull(),
  disagreementFa: jsonb("disagreement_fa").$type<string[]>(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const watchlist = pgTable(
  "ahos_watchlist",
  {
    id: serial("id").primaryKey(),
    tokenKey: text("token_key").notNull(),
    symbol: text("symbol").notNull(),
    chain: text("chain").notNull(),
    address: text("address"),
    thesisFa: text("thesis_fa"),
    invalidationFa: text("invalidation_fa"),
    active: boolean("active").notNull().default(true),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [uniqueIndex("ahos_watch_key_uidx").on(t.tokenKey)],
);

export const paperPositions = pgTable("ahos_paper_positions", {
  id: serial("id").primaryKey(),
  tokenKey: text("token_key").notNull(),
  symbol: text("symbol").notNull(),
  chain: text("chain").notNull(),
  address: text("address"),
  side: text("side").notNull().default("LONG"),
  quantity: doublePrecision("quantity"),
  entryPrice: doublePrecision("entry_price"),
  lastPrice: doublePrecision("last_price"),
  maxFavorable: doublePrecision("max_favorable"),
  maxAdverse: doublePrecision("max_adverse"),
  thesisFa: text("thesis_fa"),
  invalidationFa: text("invalidation_fa"),
  targetPrice: doublePrecision("target_price"),
  status: text("status").notNull().default("OPEN"),
  closedAt: timestamp("closed_at", { withTimezone: true }),
  closePrice: doublePrecision("close_price"),
  closeReasonFa: text("close_reason_fa"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const predictions = pgTable("ahos_predictions", {
  id: serial("id").primaryKey(),
  cycleId: integer("cycle_id"),
  tokenKey: text("token_key").notNull(),
  symbol: text("symbol").notNull(),
  decision: text("decision").notNull(),
  rankScore: doublePrecision("rank_score"),
  confidence: text("confidence").notNull(),
  horizonMin: integer("horizon_min").notNull().default(240),
  entryPrice: doublePrecision("entry_price"),
  evidence: jsonb("evidence").$type<Record<string, unknown>>(),
  source: text("source").notNull().default("local"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  resolvedAt: timestamp("resolved_at", { withTimezone: true }),
});

export const outcomes = pgTable("ahos_outcomes", {
  id: serial("id").primaryKey(),
  predictionId: integer("prediction_id").notNull(),
  tokenKey: text("token_key").notNull(),
  horizonMin: integer("horizon_min").notNull(),
  startPrice: doublePrecision("start_price"),
  endPrice: doublePrecision("end_price"),
  maxFavorable: doublePrecision("max_favorable"),
  maxAdverse: doublePrecision("max_adverse"),
  hit: text("hit").notNull().default("UNKNOWN"),
  errorClass: text("error_class").notNull().default("INSUFFICIENT_EVIDENCE"),
  lessonFa: text("lesson_fa"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const lessons = pgTable("ahos_lessons", {
  id: serial("id").primaryKey(),
  titleFa: text("title_fa").notNull(),
  bodyFa: text("body_fa").notNull(),
  errorClass: text("error_class"),
  tokenKey: text("token_key"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const findings = pgTable("ahos_findings", {
  id: serial("id").primaryKey(),
  findingId: text("finding_id").notNull(),
  severity: text("severity").notNull(),
  titleFa: text("title_fa").notNull(),
  evidenceFa: text("evidence_fa").notNull(),
  confidence: text("confidence").notNull(),
  status: text("status").notNull().default("OPEN"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const chatMessages = pgTable("ahos_chat_messages", {
  id: serial("id").primaryKey(),
  role: text("role").notNull(),
  content: text("content").notNull(),
  intent: text("intent"),
  evidence: jsonb("evidence").$type<Record<string, unknown>>(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const translationCache = pgTable(
  "ahos_translation_cache",
  {
    id: serial("id").primaryKey(),
    sourceHash: text("source_hash").notNull(),
    sourceText: text("source_text").notNull(),
    translatedFa: text("translated_fa").notNull(),
    engine: text("engine").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [uniqueIndex("ahos_tr_hash_uidx").on(t.sourceHash)],
);
