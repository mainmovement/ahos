/** W56 One Brain — canonical health & opportunity contracts */
export const PROVIDER_HEALTH_STATUSES = [
  "LIVE",
  "DEGRADED",
  "TIMEOUT",
  "RATE_LIMITED",
  "NO_KEY",
  "AUTH_FAILED",
  "NETWORK_UNAVAILABLE",
  "SOURCE_UNAVAILABLE",
  "UNKNOWN",
] as const;
export type ProviderHealthStatus = (typeof PROVIDER_HEALTH_STATUSES)[number];

export const OPPORTUNITY_STATES = [
  "NORMAL",
  "WATCH",
  "EMERGING",
  "ACCELERATING",
  "HIGH_OPPORTUNITY",
  "REJECT",
  "INSUFFICIENT_EVIDENCE",
] as const;
export type OpportunityState = (typeof OPPORTUNITY_STATES)[number];

export const ALERT_TIERS = [
  "INFO",
  "WATCH",
  "HIGH_ATTENTION",
  "CRITICAL_OPPORTUNITY",
] as const;
export type AlertTier = (typeof ALERT_TIERS)[number];

export const PROVIDER_STATUSES = [
  "SUCCESS",
  "NO_DATA",
  "AUTH_REQUIRED",
  "COST_BLOCKED",
  "RATE_LIMIT",
  "DOWN",
  "OUT_OF_POLICY",
  "UNSUPPORTED",
  "NO_KEY",
  "UNKNOWN",
] as const;

export type ProviderStatus = (typeof PROVIDER_STATUSES)[number];

export const DECISIONS = [
  "WATCH",
  "REJECT",
  "ABSTAIN",
  "PAPER_CANDIDATE",
  "INSUFFICIENT_EVIDENCE",
  "UNKNOWN",
] as const;

export type Decision = (typeof DECISIONS)[number];

export const CONFIDENCE = ["HIGH", "MED", "LOW", "UNKNOWN"] as const;
export type Confidence = (typeof CONFIDENCE)[number];

export type ExpertVoteKind =
  | "WATCH"
  | "REJECT"
  | "ABSTAIN"
  | "PAPER_CANDIDATE"
  | "UNKNOWN";

export type Envelope<T> = {
  provider: string;
  category: string;
  status: ProviderStatus;
  latencyMs: number;
  fetchedAt: string;
  url?: string;
  itemCount: number;
  messageFa: string;
  messageEn: string;
  data: T | null;
};

export type MarketAsset = {
  id: string;
  symbol: string;
  name: string;
  priceUsd: number | null;
  change24h: number | null;
  marketCap: number | null;
  volume24h: number | null;
  source: string;
};

export type PairObservation = {
  tokenKey: string;
  symbol: string;
  name: string;
  chain: string;
  address: string | null;
  pairAddress: string | null;
  dexId: string | null;
  url: string | null;
  imageUrl: string | null;
  priceUsd: number | null;
  liquidityUsd: number | null;
  volume24h: number | null;
  fdv: number | null;
  marketCap: number | null;
  priceChange5m: number | null;
  priceChange1h: number | null;
  priceChange6h: number | null;
  priceChange24h: number | null;
  buys24h: number | null;
  sells24h: number | null;
  pairCreatedAt: string | null;
  boostActive: number | null;
  paidPromotion: boolean;
  source: string;
  labels: string[];
};

export type SecurityAssessment = {
  provider: string;
  status: ProviderStatus;
  honeypot: "YES" | "NO" | "UNKNOWN";
  sellable: "YES" | "NO" | "UNKNOWN";
  mintable: "YES" | "NO" | "UNKNOWN";
  freezeable: "YES" | "NO" | "UNKNOWN";
  ownership: "RENOUNCED" | "OPEN" | "UNKNOWN";
  flags: string[];
  summaryFa: string;
  raw: Record<string, unknown> | null;
};

export type NewsStory = {
  fingerprint: string;
  source: string;
  sourceUrl: string | null;
  titleOriginal: string;
  titleFa: string;
  summaryFa: string;
  publishedAt: string | null;
  importance: "HIGH" | "MED" | "LOW" | "UNKNOWN";
  category: string;
  sentiment: "POS" | "NEG" | "NEU" | "UNKNOWN";
  relatedTokens: string[];
  relatedChains: string[];
  impact: "HIGH" | "MED" | "LOW" | "UNKNOWN";
};

export type ExpertDefinition = {
  id: string;
  teamId: string;
  teamFa: string;
  nameFa: string;
  specialty: string;
};

export type ExpertVote = {
  expertId: string;
  teamId: string;
  expertNameFa: string;
  vote: ExpertVoteKind;
  confidence: Confidence;
  reasonFa: string;
  uncertaintyFa: string;
};

export type ScoredOpportunity = {
  token: PairObservation;
  decision: Decision;
  rankScore: number | null;
  confidence: Confidence;
  securityStatus: string;
  evidenceCoverage: number;
  reasonsFa: string[];
  risksFa: string[];
  unknownsFa: string[];
  invalidationFa: string;
  missingFa: string[];
  councilVerdict: string;
  disagreement: boolean;
  votes: ExpertVote[];
  security: SecurityAssessment | null;
};

export function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

export function asString(value: unknown): string | null {
  if (typeof value === "string" && value.trim() !== "") return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return null;
}

export function tokenKey(chain: string, address: string | null, symbol: string): string {
  const c = (chain || "unknown").toLowerCase();
  const a = (address || "").toLowerCase();
  if (a) return `${c}:${a}`;
  return `${c}:sym:${symbol.toUpperCase()}`;
}

export const FINAL_USER_LINE = "تصمیم نهایی با کاربر است.";

export function toProviderHealth(status: string): ProviderHealthStatus {
  switch (status) {
    case "SUCCESS":
      return "LIVE";
    case "RATE_LIMIT":
      return "RATE_LIMITED";
    case "AUTH_REQUIRED":
      return "AUTH_FAILED";
    case "NO_KEY":
      return "NO_KEY";
    case "DOWN":
      return "NETWORK_UNAVAILABLE";
    case "NO_DATA":
    case "UNSUPPORTED":
    case "OUT_OF_POLICY":
    case "COST_BLOCKED":
      return "SOURCE_UNAVAILABLE";
    default:
      return "UNKNOWN";
  }
}

export type ProviderHealthEntry = {
  name: string;
  status: ProviderHealthStatus;
  last_success: string | null;
  last_failure: string | null;
  latency_ms: number | null;
  error_count: number;
  request_count: number;
  availability: number | null;
  error_type?: string | null;
};

export type ProviderEvidence = {
  provider: string;
  status: ProviderHealthStatus;
  latency_ms?: number | null;
  summary?: string;
};

export type OpportunityCanonicalV1 = {
  id: string;
  token: string;
  chain: string;
  contract: string | null;
  liquidity: number | null;
  volume: number | null;
  age_hours: number | null;
  holders: number | null;
  security_status: string;
  provider_evidence: ProviderEvidence[];
  score: number | null;
  state: OpportunityState;
  confidence: Confidence;
  reasons: string[];
  risks: string[];
  unknowns: string[];
  invalidation_conditions: string[];
  timestamp: string;
  tokenKey: string;
  sources: string[];
};

export type AlertEvent = {
  id: string;
  tier: AlertTier;
  tokenKey: string;
  symbol: string;
  chain: string;
  state: OpportunityState;
  why: string[];
  evidence: string[];
  risk: string[];
  unknowns: string[];
  invalidation: string[];
  sources: string[];
  timestamp: string;
  cooldownKey: string;
};

export type ConversationRequest = {
  message: string;
  conversation_id?: string | null;
  user_id?: string | null;
  channel: "web" | "telegram" | "api";
  history?: Array<{ role: "user" | "assistant"; content: string }>;
  focus_token?: string | null;
  referenced_token?: string | null;
};

export type ConversationResponse = {
  answer: string;
  intent: string;
  entities: Record<string, unknown>;
  focus_token: string | null;
  referenced_token: string | null;
  evidence: Record<string, unknown>;
  uncertainty: string[];
  suggested_followups: string[];
  timestamp: string;
  conversation_id?: string | null;
};
