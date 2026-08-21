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
