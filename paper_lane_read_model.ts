/**
 * Read-only projection of Python Lane B paper trader (reports/grok/PAPER/*).
 * Presentation for Kian/chat — not a second decision authority.
 */
import { readFile } from "fs/promises";
import path from "path";

export type PaperDeskFeedRow = {
  paperDesk: string;
  pipelineDesk: string;
  notionalMult: number;
  notionalMultSource: string;
  researchOverlayScore: number | null;
  strategySwitchKeys: string[];
  overlaySources?: string[];
  registryHypotheses?: string[];
  shadowForwardHypotheses?: string[];
  shadowOutcomeScorecard?: Array<{
    hypothesisId: string;
    hitRate: number | null;
    scoredCloses: number;
    hits: number;
    misses: number;
    skipped: number;
  }>;
};

export type PaperLaneReadModel = {
  status: "AVAILABLE" | "UNAVAILABLE";
  reason?: string | null;
  generatedAt?: string | null;
  edgeStatus?: string | null;
  edgeStatusFa?: string | null;
  closedTrades?: number | null;
  markToMarketEquityUsd?: number | null;
  tradeQuality?: {
    entryThreshold: number;
    feeMinProfitToFeeRatio: number;
    deskShadowBlockOpens?: boolean;
  } | null;
  deskPolicy?: {
    generatedAt: string | null;
    shrinkAdvisoryCount: number;
  } | null;
  deskSignalFeed?: {
    generatedAt: string | null;
    strategySwitchVersion: number | null;
    desks: PaperDeskFeedRow[];
  } | null;
  openExplainsFa: Record<string, string>;
  lastCloseExplainFa?: string | null;
  lastSkipReason?: string | null;
  paperOnly: true;
};

function paperDir(): string {
  const env = (process.env.AHOS_PAPER_DIR || "").trim();
  if (env) return env;
  return path.join(/* turbopackIgnore: true */ process.cwd(), "reports", "grok", "PAPER");
}

async function readJsonFile(base: string, name: string): Promise<Record<string, unknown> | null> {
  try {
    const raw = await readFile(path.join(base, name), "utf8");
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function unavailablePaperLane(reason: string): PaperLaneReadModel {
  return { status: "UNAVAILABLE", reason, openExplainsFa: {}, paperOnly: true };
}

function mapDeskFeed(doc: Record<string, unknown>): PaperLaneReadModel["deskSignalFeed"] {
  const desksRaw = doc.desks;
  if (!Array.isArray(desksRaw)) return null;
  const desks: PaperDeskFeedRow[] = desksRaw
    .filter((d): d is Record<string, unknown> => !!d && typeof d === "object")
    .map((d) => ({
      paperDesk: String(d.paper_desk ?? ""),
      pipelineDesk: String(d.pipeline_desk ?? ""),
      notionalMult: Number(d.notional_mult ?? 1),
      notionalMultSource: String(d.notional_mult_source ?? "unknown"),
      researchOverlayScore:
        typeof d.research_overlay_score === "number" && Number.isFinite(d.research_overlay_score)
          ? d.research_overlay_score
          : null,
      strategySwitchKeys: Array.isArray(d.strategy_switch_active_keys)
        ? d.strategy_switch_active_keys.map(String)
        : [],
      overlaySources: Array.isArray(d.weighted_sources) ? d.weighted_sources.map(String) : [],
      registryHypotheses: Array.isArray(d.shadow_forward_hypotheses)
        ? d.shadow_forward_hypotheses.map(String)
        : [],
      shadowForwardHypotheses: Array.isArray(d.shadow_forward_hypotheses)
        ? d.shadow_forward_hypotheses.map(String)
        : [],
      shadowOutcomeScorecard: Array.isArray(d.shadow_outcome_scorecard)
        ? d.shadow_outcome_scorecard
            .filter((x): x is Record<string, unknown> => !!x && typeof x === "object")
            .map((x) => ({
              hypothesisId: String(x.hypothesis_id ?? ""),
              hitRate: typeof x.hit_rate === "number" ? x.hit_rate : null,
              scoredCloses: Number(x.scored_closes ?? 0),
              hits: Number(x.hits ?? 0),
              misses: Number(x.misses ?? 0),
              skipped: Number(x.skipped ?? 0),
            }))
        : [],
    }));
  return {
    generatedAt: typeof doc.generated_at === "string" ? doc.generated_at : null,
    strategySwitchVersion: typeof doc.strategy_switch_version === "number" ? doc.strategy_switch_version : null,
    desks,
  };
}

function mapDeskPolicy(doc: Record<string, unknown>): PaperLaneReadModel["deskPolicy"] {
  const rows = doc.desks;
  if (!Array.isArray(rows)) return null;
  const shrink = rows.filter(
    (d) => typeof d === "object" && d && (d as { shadow_only_advisory?: boolean }).shadow_only_advisory,
  ).length;
  return {
    generatedAt: typeof doc.generated_at === "string" ? doc.generated_at : null,
    shrinkAdvisoryCount: shrink,
  };
}

export async function loadPaperLaneReadModel(): Promise<PaperLaneReadModel> {
  const base = paperDir();
  try {
    const [st, policyDoc, feedDoc] = await Promise.all([
      readJsonFile(base, "paper_trader_status.json"),
      readJsonFile(base, "desk_policy.json"),
      readJsonFile(base, "desk_signal_feed.json"),
    ]);
    if (!st) throw new Error("paper_trader_status.json missing");
    const tq = st.trade_quality as Record<string, unknown> | undefined;
    const explains = (st.open_explains_fa as Record<string, string>) || {};
    return {
      status: "AVAILABLE",
      generatedAt: typeof st.updated_at === "string" ? st.updated_at : null,
      edgeStatus: typeof st.edge_status === "string" ? st.edge_status : null,
      edgeStatusFa: typeof st.edge_status_fa === "string" ? st.edge_status_fa : null,
      closedTrades: typeof st.closed_trades === "number" ? st.closed_trades : null,
      markToMarketEquityUsd: typeof st.mark_to_market_equity_usd === "number" ? st.mark_to_market_equity_usd : null,
      tradeQuality: tq
        ? {
            entryThreshold: Number(tq.entry_threshold ?? 0.32),
            feeMinProfitToFeeRatio: Number(tq.fee_min_profit_to_fee_ratio ?? 2),
            deskShadowBlockOpens: Boolean(tq.desk_shadow_block_opens),
          }
        : null,
      deskPolicy: policyDoc ? mapDeskPolicy(policyDoc) : null,
      deskSignalFeed: feedDoc ? mapDeskFeed(feedDoc) : null,
      openExplainsFa: explains,
      lastCloseExplainFa: typeof st.last_close_explain_fa === "string" ? st.last_close_explain_fa : null,
      lastSkipReason: typeof st.last_no_trade_reason === "string" ? st.last_no_trade_reason : null,
      paperOnly: true,
    };
  } catch (e) {
    return {
      status: "UNAVAILABLE",
      reason: e instanceof Error ? e.message : String(e),
      openExplainsFa: {},
      paperOnly: true,
    };
  }
}

export function pickPaperExplainForSymbol(lane: PaperLaneReadModel, text: string): string | null {
  const up = text.toUpperCase();
  for (const [sym, fa] of Object.entries(lane.openExplainsFa || {})) {
    if (up.includes(sym.toUpperCase())) return fa;
  }
  return lane.lastCloseExplainFa || Object.values(lane.openExplainsFa || {})[0] || null;
}

export function pickDeskFeedRow(lane: PaperLaneReadModel, text: string): PaperDeskFeedRow | null {
  const feed = lane.deskSignalFeed?.desks;
  if (!feed?.length) return null;
  const up = text.toUpperCase();
  return (
    feed.find((d) => up.includes(d.paperDesk.toUpperCase())) ||
    feed.find((d) => /CRYPTO|BTC|ETH|SOL/.test(up) && d.paperDesk === "CRYPTO") ||
    null
  );
}
