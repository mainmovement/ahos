import {
  pgTable,
  pgEnum,
  uuid,
  varchar,
  text,
  integer,
  real,
  doublePrecision,
  boolean,
  timestamp,
  jsonb,
  index,
} from "drizzle-orm/pg-core";

/* ------------------------------------------------------------------ */
/* Enums — canonical vocabulary of the decision authority              */
/* ------------------------------------------------------------------ */

export const identityStatusEnum = pgEnum("identity_status", [
  "VERIFIED",
  "CONFLICT",
  "UNRESOLVED",
  "INVALID",
  "STALE",
  "UNSUPPORTED",
]);

export const securityGateEnum = pgEnum("security_gate", [
  "PASS",
  "REJECT",
  "INCOMPLETE",
  "STALE",
]);

export const decisionKindEnum = pgEnum("decision_kind", [
  "STRONG_CANDIDATE",
  "CANDIDATE",
  "MONITOR",
  "SKIP",
  "REJECT",
]);

export const councilStanceEnum = pgEnum("council_stance", [
  "BULLISH",
  "BEARISH",
  "NEUTRAL",
  "ABSTAIN",
  "ALARM",
]);

export const paperStatusEnum = pgEnum("paper_status", ["OPEN", "CLOSED"]);

export const paperResultEnum = pgEnum("paper_result", [
  "WIN",
  "LOSS",
  "TIMEOUT",
]);

export const alertSeverityEnum = pgEnum("alert_severity", [
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
  "INFO",
]);

export const providerStatusEnum = pgEnum("provider_status", [
  "OK",
  "DEGRADED",
  "STALE",
  "BLOCKED",
  "FAILING",
]);

export const patternKindEnum = pgEnum("pattern_kind", ["POSITIVE", "FAILURE"]);

export type GateSnapshot = {
  identity: "PASS" | "FAIL" | "INCOMPLETE";
  evidence: "PASS" | "FAIL" | "INCOMPLETE";
  security: "PASS" | "REJECT" | "INCOMPLETE";
  liquidity: "PASS" | "WARN" | "FAIL";
};

export type Scenario = {
  key: "bull" | "base" | "bear" | "extreme";
  prob: number;
  fa: string;
  en: string;
};

/* ------------------------------------------------------------------ */
/* Canonical token identity dossier                                    */
/* ------------------------------------------------------------------ */

export const tokens = pgTable(
  "ahos_tokens",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    slug: varchar("slug", { length: 64 }).notNull().unique(),
    chain: varchar("chain", { length: 32 }).notNull(),
    address: varchar("address", { length: 96 }).notNull(),
    name: varchar("name", { length: 128 }).notNull(),
    symbol: varchar("symbol", { length: 24 }).notNull(),
    nameFa: varchar("name_fa", { length: 128 }).notNull(),
    identityStatus: identityStatusEnum("identity_status").notNull(),
    securityGate: securityGateEnum("security_gate").notNull(),
    monitoringOnly: boolean("monitoring_only").notNull().default(false),
    launchAt: timestamp("launch_at", { withTimezone: true }),
    priceUsd: doublePrecision("price_usd").notNull().default(0),
    change24h: real("change_24h").notNull().default(0),
    marketCap: doublePrecision("market_cap").notNull().default(0),
    liquidityUsd: doublePrecision("liquidity_usd").notNull().default(0),
    volume24h: doublePrecision("volume_24h").notNull().default(0),
    sparkline: jsonb("sparkline").$type<number[]>().notNull().default([]),
    summaryFa: text("summary_fa").notNull().default(""),
    summaryEn: text("summary_en").notNull().default(""),
    provenance: varchar("provenance", { length: 256 }).notNull().default(""),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (t) => [index("ahos_tokens_identity_idx").on(t.identityStatus)],
);

export const tokenScores = pgTable(
  "ahos_token_scores",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    tokenId: uuid("token_id")
      .notNull()
      .references(() => tokens.id),
    opportunity: integer("opportunity").notNull(),
    security: integer("security").notNull(),
    liquidity: integer("liquidity").notNull(),
    whale: integer("whale").notNull(),
    social: integer("social").notNull(),
    narrative: integer("narrative").notNull(),
    evidence: integer("evidence").notNull(),
    confidence: integer("confidence").notNull(),
    computedAt: timestamp("computed_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (t) => [index("ahos_scores_token_idx").on(t.tokenId)],
);

export const decisions = pgTable(
  "ahos_decisions",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    tokenId: uuid("token_id")
      .notNull()
      .references(() => tokens.id),
    kind: decisionKindEnum("kind").notNull(),
    confidence: integer("confidence").notNull(),
    gateSnapshot: jsonb("gate_snapshot").$type<GateSnapshot>().notNull(),
    whyFa: jsonb("why_fa").$type<string[]>().notNull().default([]),
    whyEn: jsonb("why_en").$type<string[]>().notNull().default([]),
    risksFa: jsonb("risks_fa").$type<string[]>().notNull().default([]),
    risksEn: jsonb("risks_en").$type<string[]>().notNull().default([]),
    rejectFa: jsonb("reject_fa").$type<string[]>().notNull().default([]),
    rejectEn: jsonb("reject_en").$type<string[]>().notNull().default([]),
    scenarios: jsonb("scenarios").$type<Scenario[]>().notNull().default([]),
    policyVersion: varchar("policy_version", { length: 32 }).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (t) => [index("ahos_decisions_token_idx").on(t.tokenId)],
);

export const evidence = pgTable(
  "ahos_evidence",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    tokenId: uuid("token_id")
      .notNull()
      .references(() => tokens.id),
    kind: varchar("kind", { length: 24 }).notNull(), // MARKET SECURITY ONCHAIN SOCIAL IDENTITY NEWS
    source: varchar("source", { length: 128 }).notNull(),
    sourceUrl: varchar("source_url", { length: 256 }),
    status: varchar("status", { length: 16 }).notNull(), // VERIFIED UNVERIFIED CONFLICTED STALE
    confidence: integer("confidence").notNull(),
    contentFa: text("content_fa").notNull(),
    contentEn: text("content_en").notNull(),
    observedAt: timestamp("observed_at", { withTimezone: true }).notNull(),
  },
  (t) => [index("ahos_evidence_token_idx").on(t.tokenId)],
);

export const councilOpinions = pgTable(
  "ahos_council_opinions",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    decisionId: uuid("decision_id")
      .notNull()
      .references(() => decisions.id),
    teamId: varchar("team_id", { length: 4 }).notNull(),
    stance: councilStanceEnum("stance").notNull(),
    confidence: integer("confidence").notNull(),
    summaryFa: text("summary_fa").notNull(),
    summaryEn: text("summary_en").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (t) => [index("ahos_opinions_decision_idx").on(t.decisionId)],
);

export const teamStats = pgTable("ahos_team_stats", {
  teamId: varchar("team_id", { length: 4 }).primaryKey(),
  nameFa: varchar("name_fa", { length: 64 }).notNull(),
  nameEn: varchar("name_en", { length: 64 }).notNull(),
  personaFa: varchar("persona_fa", { length: 64 }).notNull(),
  personaEn: varchar("persona_en", { length: 64 }).notNull(),
  specialtyFa: text("specialty_fa").notNull(),
  specialtyEn: text("specialty_en").notNull(),
  icon: varchar("icon", { length: 48 }).notNull(),
  color: varchar("color", { length: 16 }).notNull(),
  calls: integer("calls").notNull().default(0),
  correct: integer("correct").notNull().default(0),
  abstains: integer("abstains").notNull().default(0),
  calibration: real("calibration").notNull().default(0),
});

export const paperTrades = pgTable(
  "ahos_paper_trades",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    tokenId: uuid("token_id")
      .notNull()
      .references(() => tokens.id),
    status: paperStatusEnum("status").notNull(),
    result: paperResultEnum("result"),
    entry: doublePrecision("entry").notNull(),
    sizeUsd: doublePrecision("size_usd").notNull(),
    stop: doublePrecision("stop").notNull(),
    target1: doublePrecision("t1").notNull(),
    target2: doublePrecision("t2"),
    target3: doublePrecision("t3"),
    currentPrice: doublePrecision("current_price"),
    exitPrice: doublePrecision("exit_price"),
    pnlPct: real("pnl_pct"),
    pnlUsd: doublePrecision("pnl_usd"),
    feesUsd: doublePrecision("fees_usd").notNull().default(0),
    maxHoldHours: integer("max_hold_hours").notNull().default(96),
    postmortemFa: text("postmortem_fa"),
    postmortemEn: text("postmortem_en"),
    lessonFa: text("lesson_fa"),
    lessonEn: text("lesson_en"),
    openedAt: timestamp("opened_at", { withTimezone: true }).notNull(),
    closedAt: timestamp("closed_at", { withTimezone: true }),
  },
  (t) => [index("ahos_paper_token_idx").on(t.tokenId)],
);

export const alerts = pgTable("ahos_alerts", {
  id: uuid("id").primaryKey().defaultRandom(),
  type: varchar("type", { length: 24 }).notNull(), // OPPORTUNITY SECURITY IDENTITY WHALE PAPER DAILY
  severity: alertSeverityEnum("severity").notNull(),
  tokenSlug: varchar("token_slug", { length: 64 }),
  titleFa: varchar("title_fa", { length: 180 }).notNull(),
  titleEn: varchar("title_en", { length: 180 }).notNull(),
  bodyFa: text("body_fa").notNull(),
  bodyEn: text("body_en").notNull(),
  source: varchar("source", { length: 64 }).notNull().default("CANONICAL_DECISION"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const providers = pgTable("ahos_providers", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: varchar("name", { length: 64 }).notNull(),
  kind: varchar("kind", { length: 32 }).notNull(),
  status: providerStatusEnum("status").notNull(),
  latencyMs: integer("latency_ms").notNull().default(0),
  reliability: real("reliability").notNull().default(0),
  lastSuccessAt: timestamp("last_success_at", { withTimezone: true }),
  failureFa: text("failure_fa"),
  failureEn: text("failure_en"),
});

export const learningPatterns = pgTable("ahos_learning_patterns", {
  id: uuid("id").primaryKey().defaultRandom(),
  kind: patternKindEnum("kind").notNull(),
  titleFa: varchar("title_fa", { length: 160 }).notNull(),
  titleEn: varchar("title_en", { length: 160 }).notNull(),
  descFa: text("desc_fa").notNull(),
  descEn: text("desc_en").notNull(),
  metricFa: varchar("metric_fa", { length: 120 }),
  metricEn: varchar("metric_en", { length: 120 }),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const treeEvents = pgTable("ahos_tree_events", {
  id: uuid("id").primaryKey().defaultRandom(),
  kind: varchar("kind", { length: 32 }).notNull(), // ROOT NEW_SOURCE ROCK GOLDEN_FRUIT FRUIT LESSON WATER BRANCH
  titleFa: varchar("title_fa", { length: 160 }).notNull(),
  titleEn: varchar("title_en", { length: 160 }).notNull(),
  detailFa: text("detail_fa").notNull(),
  detailEn: text("detail_en").notNull(),
  weight: integer("weight").notNull().default(1),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});
