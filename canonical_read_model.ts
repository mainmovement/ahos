/**
 * Command Center read-model for Python CanonicalDecisionAuthority.
 *
 * TypeScript may present these rows. It must not invent BUY/WATCH/ENTER
 * when the file is missing, corrupt, stale, or unmatched.
 */
import { readFile } from "fs/promises";
import path from "path";
import type { CanonicalBackendDecision } from "./scoring";

export const CANONICAL_READ_MODEL_VERSION = "canonical-decision-read-model-v1";
export const DEFAULT_STALE_SEC = 24 * 3600;

export type CanonicalReadStatus = "AVAILABLE" | "UNAVAILABLE" | "STALE";

export type CanonicalDecisionRow = {
  token_key?: string;
  chain?: string | null;
  address?: string | null;
  symbol?: string | null;
  outcome?: string | null;
  advisor_action?: string | null;
  identity_state?: string | null;
  security_state?: string | null;
  opportunity_score?: number | null;
  confidence_level?: string | null;
  risk_level?: string | null;
  is_positive?: boolean;
  alerts_allowed?: boolean;
  paper_allowed?: boolean;
  monitoring_only?: boolean;
  primary_reason?: string | null;
  reasons?: string[];
  risks?: string[];
  unknowns?: string[];
};

export type CanonicalReadModel = {
  version: string;
  status: CanonicalReadStatus;
  reason?: string | null;
  generated_ts: number | null;
  authority_version?: string | null;
  decision_count: number;
  decisions: CanonicalDecisionRow[];
  stale: boolean;
  no_invented_evidence: true;
};

function tokenKey(chain: string | null | undefined, address: string | null | undefined): string {
  const c = (chain || "unknown").trim().toLowerCase() || "unknown";
  const a = (address || "").trim();
  if (!a) return `${c}:unknown`;
  return `${c}:${a.toLowerCase()}`;
}

export function canonicalReadModelPath(): string {
  const env = (process.env.AHOS_CANONICAL_READ_MODEL || "").trim();
  if (env) return env;
  return path.join(process.cwd(), "reports", "canonical_decision_read_model.json");
}

export function unavailableModel(reason: string): CanonicalReadModel {
  return {
    version: CANONICAL_READ_MODEL_VERSION,
    status: "UNAVAILABLE",
    reason,
    generated_ts: null,
    authority_version: null,
    decision_count: 0,
    decisions: [],
    stale: false,
    no_invented_evidence: true,
  };
}

export function parseCanonicalReadModel(raw: unknown, now = Date.now() / 1000, staleAfterSec = DEFAULT_STALE_SEC): CanonicalReadModel {
  if (!raw || typeof raw !== "object") return unavailableModel("corrupt_read_model");
  const obj = raw as Record<string, unknown>;
  const generated = typeof obj.generated_ts === "number" ? obj.generated_ts : Number(obj.generated_ts);
  const stale = !Number.isFinite(generated) || now - generated > staleAfterSec;
  let status: CanonicalReadStatus = obj.status === "AVAILABLE" ? "AVAILABLE" : "UNAVAILABLE";
  if (stale && status === "AVAILABLE") status = "STALE";
  const rowsIn = Array.isArray(obj.decisions) ? obj.decisions : [];
  const decisions: CanonicalDecisionRow[] = [];
  for (const row of rowsIn) {
    if (!row || typeof row !== "object") continue;
    const item = { ...(row as CanonicalDecisionRow) };
    if (status !== "AVAILABLE") {
      item.is_positive = false;
      item.alerts_allowed = false;
      item.paper_allowed = false;
    }
    decisions.push(item);
  }
  return {
    version: String(obj.version || CANONICAL_READ_MODEL_VERSION),
    status,
    reason: typeof obj.reason === "string" ? obj.reason : null,
    generated_ts: Number.isFinite(generated) ? generated : null,
    authority_version: typeof obj.authority_version === "string" ? obj.authority_version : null,
    decision_count: decisions.length,
    decisions,
    stale,
    no_invented_evidence: true,
  };
}

export function lookupCanonicalRow(
  model: CanonicalReadModel,
  chain: string | null | undefined,
  address: string | null | undefined,
): CanonicalDecisionRow | null {
  const key = tokenKey(chain, address);
  const wantAddr = (address || "").trim().toLowerCase();
  const wantChain = (chain || "").trim().toLowerCase();
  for (const row of model.decisions) {
    if (row.token_key === key) return row;
    const rowAddr = (row.address || "").trim().toLowerCase();
    const rowChain = (row.chain || "").trim().toLowerCase();
    if (rowChain && wantChain && rowChain === wantChain && rowAddr && wantAddr && rowAddr === wantAddr) {
      return row;
    }
  }
  return null;
}

export function toBackendDecision(row: CanonicalDecisionRow | null, modelStatus: CanonicalReadStatus): CanonicalBackendDecision | null {
  if (!row || modelStatus !== "AVAILABLE") return null;
  return {
    outcome: row.outcome,
    action: row.advisor_action,
    identityState: row.identity_state,
    securityState: row.security_state,
  };
}

export function displayDecision(row: CanonicalDecisionRow | null, modelStatus: CanonicalReadStatus): string {
  if (modelStatus === "UNAVAILABLE") return "UNAVAILABLE";
  if (modelStatus === "STALE") return "STALE";
  if (!row || !row.outcome) return "UNAVAILABLE";
  return String(row.outcome);
}

export type OverlayOpportunity = {
  chain: string;
  address: string | null;
  decision: string;
  confidence?: string;
  [key: string]: unknown;
};

export function overlayOpportunity<T extends OverlayOpportunity>(opp: T, model: CanonicalReadModel): T & {
  canonicalStatus: CanonicalReadStatus;
  canonicalOutcome: string | null;
  identityState: string | null;
  securityState: string | null;
  paperAllowed: boolean;
  canonicalUnavailable: boolean;
} {
  const row = lookupCanonicalRow(model, opp.chain, opp.address);
  const decision = displayDecision(row, model.status);
  const paperAllowed = Boolean(row?.paper_allowed) && model.status === "AVAILABLE";
  return {
    ...opp,
    decision,
    canonicalStatus: model.status,
    canonicalOutcome: row?.outcome ? String(row.outcome) : null,
    identityState: row?.identity_state ? String(row.identity_state) : null,
    securityState: row?.security_state ? String(row.security_state) : null,
    paperAllowed,
    canonicalUnavailable: model.status !== "AVAILABLE" || !row,
    confidence: row?.confidence_level || opp.confidence,
  };
}

export function paperAllowedFromCanonical(
  model: CanonicalReadModel,
  chain: string | null | undefined,
  address: string | null | undefined,
): boolean {
  if (model.status !== "AVAILABLE") return false;
  const row = lookupCanonicalRow(model, chain, address);
  return Boolean(row?.paper_allowed);
}

export function alertsAllowedFromCanonical(
  model: CanonicalReadModel,
  chain: string | null | undefined,
  address: string | null | undefined,
): boolean {
  if (model.status !== "AVAILABLE") return false;
  const row = lookupCanonicalRow(model, chain, address);
  return Boolean(row?.alerts_allowed);
}

export type CanonicalReadModelSummary = {
  status: CanonicalReadStatus;
  reason: string | null;
  generatedTs: number | null;
  decisionCount: number;
  stale: boolean;
  authorityVersion: string | null;
};

export function canonicalReadModelSummary(model: CanonicalReadModel): CanonicalReadModelSummary {
  return {
    status: model.status,
    reason: model.reason || null,
    generatedTs: model.generated_ts,
    decisionCount: model.decision_count,
    stale: model.stale,
    authorityVersion: model.authority_version || null,
  };
}

/** Presentation-only view of Python rows. Never invents BUY/WATCH. */
export type CanonicalDecisionView = {
  tokenKey: string;
  symbol: string | null;
  chain: string | null;
  address: string | null;
  outcome: string;
  identityState: string | null;
  securityState: string | null;
  confidence: string | null;
  opportunityScore: number | null;
  paperAllowed: boolean;
  isPositive: boolean;
  monitoringOnly: boolean;
  primaryReason: string | null;
};

export function presentCanonicalDecisions(model: CanonicalReadModel): CanonicalDecisionView[] {
  const live = model.status === "AVAILABLE";
  return model.decisions.map((row) => {
    const outcome = displayDecision(row, model.status);
    return {
      tokenKey: row.token_key || tokenKey(row.chain, row.address),
      symbol: row.symbol ? String(row.symbol) : null,
      chain: row.chain ? String(row.chain) : null,
      address: row.address ? String(row.address) : null,
      outcome,
      identityState: row.identity_state ? String(row.identity_state) : null,
      securityState: row.security_state ? String(row.security_state) : null,
      confidence: row.confidence_level ? String(row.confidence_level) : null,
      opportunityScore: typeof row.opportunity_score === "number" ? row.opportunity_score : null,
      paperAllowed: live && Boolean(row.paper_allowed),
      isPositive: live && Boolean(row.is_positive) && outcome === "BUY",
      monitoringOnly: Boolean(row.monitoring_only) || outcome === "MONITOR_ONLY",
      primaryReason: row.primary_reason ? String(row.primary_reason) : null,
    };
  });
}

export async function loadCanonicalReadModel(now = Date.now() / 1000): Promise<CanonicalReadModel> {
  try {
    const raw = await readFile(canonicalReadModelPath(), "utf8");
    return parseCanonicalReadModel(JSON.parse(raw), now);
  } catch {
    return unavailableModel("missing_read_model");
  }
}
