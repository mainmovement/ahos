/**
 * AHOS — Canonical decision store reader (TypeScript adapter, READ-ONLY).
 *
 * The Python canonical brain is the SOLE writer of
 * `reports/canonical/decisions/latest.json`. This module only READS it. It
 * cannot create a decision, promote a token, compute a security disposition, or
 * compute an authoritative score. There is deliberately no write/promote API.
 *
 * Fail-closed law: a missing file, malformed JSON, invalid record, version
 * mismatch, or STALE record is never a positive opportunity.
 */
import { readFile } from "fs/promises";
import path from "path";
import {
  isPositiveOpportunityEligible,
  PASS,
  type SecurityDisposition,
} from "./opportunity_authority";

// Must match architecture/canonical/contract.py DECISION_VERSION.
export const CANONICAL_DECISION_VERSION = 1;
// Must match architecture/canonical/decision_store.py DECISION_FRESHNESS_BUDGET_SEC.
export const CANONICAL_FRESHNESS_SEC = Number(process.env.AHOS_CANONICAL_FRESHNESS_SEC || "900");

const LATEST_REL = path.join("reports", "canonical", "decisions", "latest.json");

export type CanonicalDecision = {
  canonical_token_id: string;
  chain: string;
  normalized_contract_address: string;
  security_disposition: string;
  recommendation_cap: string;
  opportunity_eligible: boolean;
  opportunity_score: number;
  evidence_reference: string;
  decision_timestamp: number;
  decision_version: number;
  brain_version?: string;
  canonical_source?: string;
  // Non-authoritative display payload (symbol/name/reasons/…) for adapters.
  presentation?: Record<string, unknown> | null;
};

export type CanonicalSnapshot = {
  decisions: Map<string, CanonicalDecision>;
};

const _VALID_DISPOSITIONS = new Set(["SECURITY_VETO", "PASS_WITH_UNKNOWN", "PASS"]);
const _VALID_CAPS = new Set(["AVOID", "WATCH", "PASS"]);

/** Fail-closed record validation. Mirrors the Python contract invariant. */
function validate(rec: unknown): rec is CanonicalDecision {
  if (!rec || typeof rec !== "object") return false;
  const r = rec as Record<string, unknown>;
  if (typeof r.canonical_token_id !== "string" || !r.canonical_token_id) return false;
  if (typeof r.chain !== "string" || !r.chain) return false;
  if (typeof r.normalized_contract_address !== "string" || !r.normalized_contract_address) return false;
  if (typeof r.security_disposition !== "string" || !_VALID_DISPOSITIONS.has(r.security_disposition)) return false;
  if (typeof r.recommendation_cap !== "string" || !_VALID_CAPS.has(r.recommendation_cap)) return false;
  if (typeof r.opportunity_eligible !== "boolean") return false;
  // Binding invariant: eligible ⇒ security PASS.
  if (r.opportunity_eligible && r.security_disposition !== PASS) return false;
  if (typeof r.opportunity_score !== "number" || !Number.isFinite(r.opportunity_score)) return false;
  if (typeof r.decision_version !== "number" || r.decision_version !== CANONICAL_DECISION_VERSION) return false;
  if (typeof r.decision_timestamp !== "number" || !(r.decision_timestamp > 0)) return false;
  return true;
}

/** Load the canonical snapshot map. Fail-closed to an empty map on any error. */
export async function loadCanonicalSnapshot(cwd: string = process.cwd()): Promise<CanonicalSnapshot> {
  const decisions = new Map<string, CanonicalDecision>();
  let raw: string;
  try {
    raw = await readFile(path.join(cwd, LATEST_REL), "utf8");
  } catch {
    return { decisions }; // missing file ⇒ empty (fail-closed)
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return { decisions }; // malformed JSON ⇒ empty (fail-closed)
  }
  if (!parsed || typeof parsed !== "object") return { decisions };
  for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
    if (validate(value)) decisions.set(key, value);
  }
  return { decisions };
}

function isFresh(rec: CanonicalDecision, nowSec: number): boolean {
  return nowSec - rec.decision_timestamp <= CANONICAL_FRESHNESS_SEC;
}

/** Return a valid, FRESH decision for the token id, else null (fail-closed). */
export function getDecision(
  snapshot: CanonicalSnapshot,
  canonicalTokenId: string | null,
  nowSec: number = Date.now() / 1000,
): CanonicalDecision | null {
  if (!canonicalTokenId) return null;
  const rec = snapshot.decisions.get(canonicalTokenId);
  if (!rec) return null;
  if (!isFresh(rec, nowSec)) return null;
  return rec;
}

/**
 * THE canonical gate every TS opportunity surface must consume. True only for a
 * valid, fresh, eligible (⇒ security PASS) canonical record. Everything else
 * (missing/malformed/stale/UNKNOWN/VETO) fails closed. Adapters cannot promote.
 */
export function isCanonicalPositiveOpportunity(
  snapshot: CanonicalSnapshot,
  canonicalTokenId: string | null,
  nowSec: number = Date.now() / 1000,
): boolean {
  const rec = getDecision(snapshot, canonicalTokenId, nowSec);
  if (!rec) return false;
  // Consistency defense: the authoritative flag must agree with the canonical
  // disposition (only an explicit PASS may be eligible).
  return rec.opportunity_eligible
    && isPositiveOpportunityEligible(rec.security_disposition as SecurityDisposition);
}

/**
 * The single canonical source of "opportunities" for any TS adapter (web
 * banner, "best opportunities", Telegram): valid, fresh, eligible records only,
 * highest score first. Fail-closed — excludes missing/malformed/stale/UNKNOWN/
 * VETO. Adapters may format/paginate this; they may NOT add to it.
 */
export function listCanonicalOpportunities(
  snapshot: CanonicalSnapshot,
  nowSec: number = Date.now() / 1000,
): CanonicalDecision[] {
  const out: CanonicalDecision[] = [];
  for (const [cid, rec] of snapshot.decisions) {
    if (isCanonicalPositiveOpportunity(snapshot, cid, nowSec)) out.push(rec);
  }
  out.sort((a, b) => b.opportunity_score - a.opportunity_score);
  return out;
}
