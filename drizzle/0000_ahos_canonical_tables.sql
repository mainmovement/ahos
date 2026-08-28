CREATE TABLE "ahos_chat_messages" (
	"id" serial PRIMARY KEY NOT NULL,
	"role" text NOT NULL,
	"content" text NOT NULL,
	"intent" text,
	"evidence" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_council_reports" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle_id" integer,
	"token_key" text NOT NULL,
	"verdict" text NOT NULL,
	"advisory_only" boolean DEFAULT true NOT NULL,
	"agree_count" integer DEFAULT 0 NOT NULL,
	"reject_count" integer DEFAULT 0 NOT NULL,
	"abstain_count" integer DEFAULT 0 NOT NULL,
	"watch_count" integer DEFAULT 0 NOT NULL,
	"summary_fa" text NOT NULL,
	"disagreement_fa" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_cycles" (
	"id" serial PRIMARY KEY NOT NULL,
	"status" text NOT NULL,
	"started_at" timestamp with time zone DEFAULT now() NOT NULL,
	"finished_at" timestamp with time zone,
	"duration_ms" integer,
	"token_count" integer,
	"news_count" integer,
	"opportunity_count" integer,
	"unknown_share" double precision,
	"notes_fa" text,
	"details" jsonb
);
--> statement-breakpoint
CREATE TABLE "ahos_expert_votes" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle_id" integer,
	"token_key" text NOT NULL,
	"expert_id" text NOT NULL,
	"team_id" text NOT NULL,
	"expert_name_fa" text NOT NULL,
	"vote" text NOT NULL,
	"confidence" text NOT NULL,
	"reason_fa" text NOT NULL,
	"uncertainty_fa" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_findings" (
	"id" serial PRIMARY KEY NOT NULL,
	"finding_id" text NOT NULL,
	"severity" text NOT NULL,
	"title_fa" text NOT NULL,
	"evidence_fa" text NOT NULL,
	"confidence" text NOT NULL,
	"status" text DEFAULT 'OPEN' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_lessons" (
	"id" serial PRIMARY KEY NOT NULL,
	"title_fa" text NOT NULL,
	"body_fa" text NOT NULL,
	"error_class" text,
	"token_key" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_market_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle_id" integer,
	"regime" text DEFAULT 'UNKNOWN' NOT NULL,
	"fear_greed" integer,
	"fear_greed_label" text,
	"btc_price" double precision,
	"btc_change_24h" double precision,
	"eth_price" double precision,
	"eth_change_24h" double precision,
	"sol_price" double precision,
	"sol_change_24h" double precision,
	"total_mcap" double precision,
	"mcap_change_24h" double precision,
	"btc_dominance" double precision,
	"defi_tvl" double precision,
	"payload" jsonb,
	"provenance" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_news_items" (
	"id" serial PRIMARY KEY NOT NULL,
	"fingerprint" text NOT NULL,
	"source" text NOT NULL,
	"source_url" text,
	"title_original" text NOT NULL,
	"title_fa" text,
	"summary_fa" text,
	"published_at" timestamp with time zone,
	"importance" text DEFAULT 'UNKNOWN' NOT NULL,
	"category" text DEFAULT 'UNKNOWN' NOT NULL,
	"sentiment" text DEFAULT 'UNKNOWN' NOT NULL,
	"related_tokens" jsonb,
	"related_chains" jsonb,
	"impact" text DEFAULT 'UNKNOWN' NOT NULL,
	"provenance" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_observations" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle_id" integer,
	"token_key" text NOT NULL,
	"price_usd" double precision,
	"liquidity_usd" double precision,
	"volume_24h" double precision,
	"fdv" double precision,
	"market_cap" double precision,
	"price_change_5m" double precision,
	"price_change_1h" double precision,
	"price_change_6h" double precision,
	"price_change_24h" double precision,
	"buys_24h" integer,
	"sells_24h" integer,
	"pair_created_at" timestamp with time zone,
	"boost_active" integer,
	"paid_promotion" boolean,
	"source" text NOT NULL,
	"raw" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_opportunities" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle_id" integer,
	"token_key" text NOT NULL,
	"symbol" text NOT NULL,
	"name" text,
	"chain" text NOT NULL,
	"address" text,
	"decision" text NOT NULL,
	"rank_score" double precision,
	"confidence" text NOT NULL,
	"security_status" text NOT NULL,
	"evidence_coverage" double precision,
	"reasons_fa" jsonb,
	"risks_fa" jsonb,
	"unknowns_fa" jsonb,
	"invalidation_fa" text,
	"missing_fa" jsonb,
	"council_verdict" text,
	"disagreement" boolean DEFAULT false NOT NULL,
	"payload" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_outcomes" (
	"id" serial PRIMARY KEY NOT NULL,
	"prediction_id" integer NOT NULL,
	"token_key" text NOT NULL,
	"horizon_min" integer NOT NULL,
	"start_price" double precision,
	"end_price" double precision,
	"max_favorable" double precision,
	"max_adverse" double precision,
	"hit" text DEFAULT 'UNKNOWN' NOT NULL,
	"error_class" text DEFAULT 'INSUFFICIENT_EVIDENCE' NOT NULL,
	"lesson_fa" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_paper_positions" (
	"id" serial PRIMARY KEY NOT NULL,
	"token_key" text NOT NULL,
	"symbol" text NOT NULL,
	"chain" text NOT NULL,
	"address" text,
	"side" text DEFAULT 'LONG' NOT NULL,
	"quantity" double precision,
	"entry_price" double precision,
	"last_price" double precision,
	"max_favorable" double precision,
	"max_adverse" double precision,
	"thesis_fa" text,
	"invalidation_fa" text,
	"target_price" double precision,
	"status" text DEFAULT 'OPEN' NOT NULL,
	"closed_at" timestamp with time zone,
	"close_price" double precision,
	"close_reason_fa" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_predictions" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle_id" integer,
	"token_key" text NOT NULL,
	"symbol" text NOT NULL,
	"decision" text NOT NULL,
	"rank_score" double precision,
	"confidence" text NOT NULL,
	"horizon_min" integer DEFAULT 240 NOT NULL,
	"entry_price" double precision,
	"evidence" jsonb,
	"source" text DEFAULT 'local' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"resolved_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE "ahos_provider_snapshots" (
	"id" serial PRIMARY KEY NOT NULL,
	"cycle_id" integer,
	"provider" text NOT NULL,
	"category" text NOT NULL,
	"status" text NOT NULL,
	"latency_ms" integer,
	"item_count" integer,
	"message_fa" text,
	"message_en" text,
	"provenance" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_security_reports" (
	"id" serial PRIMARY KEY NOT NULL,
	"token_key" text NOT NULL,
	"provider" text NOT NULL,
	"status" text NOT NULL,
	"honeypot" text DEFAULT 'UNKNOWN' NOT NULL,
	"sellable" text DEFAULT 'UNKNOWN' NOT NULL,
	"mintable" text DEFAULT 'UNKNOWN' NOT NULL,
	"freezeable" text DEFAULT 'UNKNOWN' NOT NULL,
	"ownership" text DEFAULT 'UNKNOWN' NOT NULL,
	"summary_fa" text,
	"payload" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_system_state" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"running" boolean DEFAULT false NOT NULL,
	"started_at" timestamp with time zone,
	"stopped_at" timestamp with time zone,
	"last_cycle_at" timestamp with time zone,
	"last_cycle_status" text DEFAULT 'UNKNOWN' NOT NULL,
	"cycle_count" integer DEFAULT 0 NOT NULL,
	"last_error" text,
	"interval_sec" integer DEFAULT 75 NOT NULL,
	"execution_mode" text DEFAULT 'PAPER_ONLY' NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_tokens" (
	"id" serial PRIMARY KEY NOT NULL,
	"key" text NOT NULL,
	"symbol" text NOT NULL,
	"name" text,
	"chain" text NOT NULL,
	"address" text,
	"pair_address" text,
	"dex_id" text,
	"url" text,
	"image_url" text,
	"first_seen_at" timestamp with time zone DEFAULT now() NOT NULL,
	"last_seen_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_translation_cache" (
	"id" serial PRIMARY KEY NOT NULL,
	"source_hash" text NOT NULL,
	"source_text" text NOT NULL,
	"translated_fa" text NOT NULL,
	"engine" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ahos_watchlist" (
	"id" serial PRIMARY KEY NOT NULL,
	"token_key" text NOT NULL,
	"symbol" text NOT NULL,
	"chain" text NOT NULL,
	"address" text,
	"thesis_fa" text,
	"invalidation_fa" text,
	"active" boolean DEFAULT true NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE INDEX "ahos_vote_token_idx" ON "ahos_expert_votes" USING btree ("token_key");--> statement-breakpoint
CREATE INDEX "ahos_vote_cycle_idx" ON "ahos_expert_votes" USING btree ("cycle_id");--> statement-breakpoint
CREATE UNIQUE INDEX "ahos_news_fp_uidx" ON "ahos_news_items" USING btree ("fingerprint");--> statement-breakpoint
CREATE INDEX "ahos_news_pub_idx" ON "ahos_news_items" USING btree ("published_at");--> statement-breakpoint
CREATE INDEX "ahos_obs_token_idx" ON "ahos_observations" USING btree ("token_key");--> statement-breakpoint
CREATE INDEX "ahos_obs_cycle_idx" ON "ahos_observations" USING btree ("cycle_id");--> statement-breakpoint
CREATE INDEX "ahos_opp_cycle_idx" ON "ahos_opportunities" USING btree ("cycle_id");--> statement-breakpoint
CREATE INDEX "ahos_opp_token_idx" ON "ahos_opportunities" USING btree ("token_key");--> statement-breakpoint
CREATE INDEX "ahos_provider_name_idx" ON "ahos_provider_snapshots" USING btree ("provider");--> statement-breakpoint
CREATE INDEX "ahos_provider_cycle_idx" ON "ahos_provider_snapshots" USING btree ("cycle_id");--> statement-breakpoint
CREATE INDEX "ahos_sec_token_idx" ON "ahos_security_reports" USING btree ("token_key");--> statement-breakpoint
CREATE UNIQUE INDEX "ahos_tokens_key_uidx" ON "ahos_tokens" USING btree ("key");--> statement-breakpoint
CREATE UNIQUE INDEX "ahos_tr_hash_uidx" ON "ahos_translation_cache" USING btree ("source_hash");--> statement-breakpoint
CREATE UNIQUE INDEX "ahos_watch_key_uidx" ON "ahos_watchlist" USING btree ("token_key");