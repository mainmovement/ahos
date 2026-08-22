import type {
  Confidence,
  Decision,
  OpportunityCanonicalV1,
  OpportunityState,
  ProviderEvidence,
  ScoredOpportunity,
} from "./types";

export type { OpportunityCanonicalV1 };

export function decisionToState(
  d: Decision | string | null | undefined,
): OpportunityState {
  switch (d) {
    case "WATCH":
      return "WATCH";
    case "REJECT":
      return "REJECT";
    case "INSUFFICIENT_EVIDENCE":
      return "INSUFFICIENT_EVIDENCE";
    case "PAPER_CANDIDATE":
      return "HIGH_OPPORTUNITY";
    case "ABSTAIN":
      return "NORMAL";
    default:
      return "INSUFFICIENT_EVIDENCE";
  }
}

export function fromScored(
  scored: ScoredOpportunity,
  extra?: { provider_evidence?: ProviderEvidence[]; holders?: number | null },
): OpportunityCanonicalV1 {
  const token = (scored as { token?: Record<string, unknown> }).token || {};
  const state = decisionToState(scored.decision);
  const reasons = ((scored as { reasonsFa?: string[] }).reasonsFa || []).map(String);
  const risks = ((scored as { risksFa?: string[] }).risksFa || []).map(String);
  const unknowns = (
    (scored as { unknownsFa?: string[]; missingFa?: string[] }).unknownsFa ||
    (scored as { missingFa?: string[] }).missingFa ||
    []
  ).map(String);

  let security_status = "UNKNOWN";
  const sec = (
    scored as {
      security?: { honeypot?: string; sellable?: string; status?: string };
    }
  ).security;
  if (sec) {
    security_status =
      sec.honeypot === "YES"
        ? "HONEYPOT"
        : sec.status === "SUCCESS" &&
            sec.honeypot === "NO" &&
            sec.sellable !== "NO"
          ? "PASSED"
          : sec.status === "SUCCESS"
            ? "PARTIAL"
            : String(sec.status || "UNKNOWN");
    if (sec.honeypot === "YES") risks.push("honeypot=YES");
    if (sec.sellable === "NO") risks.push("sellable=NO");
  } else {
    unknowns.push("security assessment missing");
  }
  if ((scored as { paidPromotion?: boolean }).paidPromotion) {
    risks.push("paid_promotion_or_boost");
  }

  const provider_evidence = extra?.provider_evidence || [];
  const sources = [
    ...new Set(
      [
        ...((scored as { sources?: string[] }).sources || []),
        (token as { source?: string }).source,
        ...provider_evidence.map((x) => x.provider),
      ].filter(Boolean) as string[],
    ),
  ];
  const inv = (scored as { invalidationFa?: string | string[] }).invalidationFa;
  const invalidation_conditions = Array.isArray(inv)
    ? inv.map(String)
    : inv
      ? [String(inv)]
      : [];
  const scoreRaw =
    (scored as { score?: number | null; rankScore?: number | null }).score ??
    (scored as { rankScore?: number | null }).rankScore;
  let age_hours: number | null = null;
  const pca = (token as { pairCreatedAt?: string | null }).pairCreatedAt;
  if (pca) {
    const ts = new Date(pca).getTime();
    if (Number.isFinite(ts)) age_hours = Math.max(0, (Date.now() - ts) / 3_600_000);
  }

  return {
    id: `opp:${scored.tokenKey}:${Date.now()}`,
    token:
      (scored as { symbol?: string }).symbol ||
      (token as { symbol?: string }).symbol ||
      scored.tokenKey,
    chain:
      (scored as { chain?: string }).chain ||
      (token as { chain?: string }).chain ||
      "unknown",
    contract: (token as { address?: string | null }).address ?? null,
    liquidity:
      typeof (token as { liquidityUsd?: number }).liquidityUsd === "number"
        ? (token as { liquidityUsd: number }).liquidityUsd
        : null,
    volume:
      typeof (token as { volume24h?: number }).volume24h === "number"
        ? (token as { volume24h: number }).volume24h
        : null,
    age_hours,
    holders: extra?.holders ?? null,
    security_status,
    provider_evidence,
    score:
      typeof scoreRaw === "number" && Number.isFinite(scoreRaw) ? scoreRaw : null,
    state,
    confidence: ((scored as { confidence?: Confidence }).confidence ||
      "UNKNOWN") as Confidence,
    reasons,
    risks,
    unknowns,
    invalidation_conditions,
    timestamp:
      (scored as { updatedAt?: string }).updatedAt || new Date().toISOString(),
    tokenKey: scored.tokenKey,
    sources,
  };
}

/** CRITICAL requires multi-source evidence, security passed, anti-hype. */
export function mayEmitCritical(opp: OpportunityCanonicalV1): boolean {
  if (opp.state === "REJECT" || opp.state === "INSUFFICIENT_EVIDENCE") return false;
  if (opp.security_status === "HONEYPOT" || opp.security_status === "UNKNOWN")
    return false;
  if (opp.security_status !== "PASSED" && opp.security_status !== "PARTIAL")
    return false;
  if (opp.risks.some((r) => /honeypot|sellable=NO|paid_promotion/i.test(r)))
    return false;
  if (opp.unknowns.some((u) => /security/i.test(u))) return false;
  if (new Set(opp.sources.filter(Boolean)).size < 2) return false;
  if (opp.score === null || opp.score < 70) return false;
  return true;
}
