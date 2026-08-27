/**
 * AHOS — Canonical Opportunity Authority (TypeScript adapter side).
 *
 * ONE BRAIN, MANY ADAPTERS.
 *
 * The authoritative production decision for security disposition, recommendation
 * cap, and positive-opportunity eligibility is owned by the Python canonical
 * brain (`architecture/security/gate.py` — SECURITY_VETO / PASS_WITH_UNKNOWN /
 * PASS). TypeScript (web, banner, Telegram) is a NON-AUTHORITATIVE ADAPTER: it
 * may format and display results, but it MUST NOT independently promote an
 * UNKNOWN or vetoed token into a positive opportunity.
 *
 * This module is the SINGLE eligibility gate every TS opportunity emitter must
 * consume. It re-uses the canonical disposition vocabulary and the ONE canonical
 * rule ("only an explicit security PASS may become a positive opportunity"); it
 * does NOT re-implement the security analysis (that is the Python brain's job).
 *
 * Canonical rule (identical to SecurityDisposition.allows_opportunity()):
 *   PASS               -> eligible for a positive opportunity
 *   PASS_WITH_UNKNOWN  -> recommendation cap WATCH  -> NOT a positive opportunity
 *   SECURITY_VETO      -> recommendation cap AVOID  -> NOT a positive opportunity
 */

export const SECURITY_VETO = "SECURITY_VETO";
export const PASS_WITH_UNKNOWN = "PASS_WITH_UNKNOWN";
export const PASS = "PASS";

export type SecurityDisposition =
  | typeof SECURITY_VETO
  | typeof PASS_WITH_UNKNOWN
  | typeof PASS;

export const CAP_AVOID = "AVOID";
export const CAP_WATCH = "WATCH";
export const CAP_PASS = "PASS";

// Statuses that represent an affirmed critical security failure (veto).
const VETO_STATUSES = new Set(["HONEYPOT", "REJECT", "FAIL", "DOWN"]);
// Statuses that represent an established, clean security check (pass).
const PASS_STATUSES = new Set(["OK", "SUCCESS", "PASS", "CLEAN"]);

/**
 * Map an adapter-side securityStatus string onto the canonical disposition.
 * Anything not affirmatively clean and not affirmatively bad is UNKNOWN — and
 * UNKNOWN is never a positive opportunity, regardless of score. There is no
 * score-based override (that override was the removed P0 bypass).
 */
export function securityStatusToDisposition(status: string | null | undefined): SecurityDisposition {
  const s = (status || "").toUpperCase().trim();
  if (VETO_STATUSES.has(s)) return SECURITY_VETO;
  if (PASS_STATUSES.has(s)) return PASS;
  return PASS_WITH_UNKNOWN;
}

export function recommendationCap(disposition: SecurityDisposition): string {
  if (disposition === SECURITY_VETO) return CAP_AVOID;
  if (disposition === PASS_WITH_UNKNOWN) return CAP_WATCH;
  return CAP_PASS;
}

/**
 * THE single canonical eligibility rule for a positive opportunity.
 * Mirrors Python SecurityDisposition.allows_opportunity(): PASS only.
 */
export function isPositiveOpportunityEligible(disposition: SecurityDisposition): boolean {
  return disposition === PASS;
}

/** Convenience: decide eligibility directly from a securityStatus string. */
export function securityStatusAllowsOpportunity(status: string | null | undefined): boolean {
  return isPositiveOpportunityEligible(securityStatusToDisposition(status));
}
