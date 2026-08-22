import type { AlertEvent, AlertTier, OpportunityState } from "./types";
import type { OpportunityCanonicalV1 } from "./opportunity_canonical";
import { mayEmitCritical } from "./opportunity_canonical";

const recent = new Map<string, number>();
const COOLDOWN_MS = 15 * 60 * 1000;

export function buildDedupeKey(
  tokenKey: string,
  tier: AlertTier,
  state: OpportunityState,
): string {
  return `${tokenKey}|${tier}|${state}`;
}

export function createAlertEvent(
  opp: OpportunityCanonicalV1,
  preferredTier?: AlertTier,
): AlertEvent | null {
  let tier: AlertTier = preferredTier || "INFO";
  if (opp.state === "HIGH_OPPORTUNITY" || opp.state === "ACCELERATING") {
    tier = mayEmitCritical(opp) ? "CRITICAL_OPPORTUNITY" : "HIGH_ATTENTION";
  } else if (opp.state === "EMERGING" || opp.state === "WATCH") {
    tier = "WATCH";
  } else if (opp.state === "REJECT" || opp.state === "INSUFFICIENT_EVIDENCE") {
    if (!preferredTier || preferredTier === "INFO") return null;
    tier = "INFO";
  }
  if (tier === "CRITICAL_OPPORTUNITY" && !mayEmitCritical(opp)) {
    tier = "HIGH_ATTENTION";
  }
  const cooldownKey = buildDedupeKey(opp.tokenKey, tier, opp.state);
  const exp = recent.get(cooldownKey);
  if (exp !== undefined && exp > Date.now()) return null;
  recent.set(cooldownKey, Date.now() + COOLDOWN_MS);
  return {
    id: `alert:${opp.tokenKey}:${tier}:${Date.now()}`,
    tier,
    tokenKey: opp.tokenKey,
    symbol: opp.token,
    chain: opp.chain,
    state: opp.state,
    why: [`state=${opp.state}`],
    evidence: [...opp.reasons],
    risk: [...opp.risks],
    unknowns: [...opp.unknowns],
    invalidation: [...opp.invalidation_conditions],
    sources: [...opp.sources],
    timestamp: new Date().toISOString(),
    cooldownKey,
  };
}

export function clearAlertCooldowns(): void {
  recent.clear();
}
