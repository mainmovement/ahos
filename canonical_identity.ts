/**
 * AHOS — Canonical token identity (TypeScript mirror, adapter side).
 *
 * This is NOT a second identity authority. It is a byte-for-byte deterministic
 * mirror of the single canonical authority `discovery/identity.py::token_id`
 * used ONLY to derive the lookup key for the canonical decision store. The
 * authoritative identity is defined by Python; this mirror is verified against
 * it in `tests/test_canonical_identity_ts_parity.py`.
 *
 * Fail-closed: unknown chain, empty/missing address ⇒ null (never a guess).
 * The legacy `tokenKey` is presentation/grouping only and is NOT an identity
 * authority.
 */
import { createHash } from "crypto";

// Mirror of discovery/identity.py CHAIN_REGISTRY (controlled vocabulary).
const CHAIN_REGISTRY: Record<string, string> = {
  solana: "solana",
  ethereum: "ethereum", eth: "ethereum",
  bsc: "bsc", bnb: "bsc", binance: "bsc",
  base: "base",
  arbitrum: "arbitrum", arb: "arbitrum",
  polygon: "polygon", matic: "polygon",
  ton: "ton", sui: "sui", avalanche: "avalanche", avax: "avalanche",
  optimism: "optimism", op: "optimism",
  pulsechain: "pulsechain", fantom: "fantom", cronos: "cronos",
  robinhood: "robinhood",
};

// Mirror of discovery/identity.py EVM_CHAINS.
const EVM_CHAINS = new Set<string>([
  "ethereum", "bsc", "base", "arbitrum", "polygon", "avalanche",
  "optimism", "pulsechain", "fantom", "cronos",
]);

export function normalizeChain(raw: string | null | undefined): string | null {
  if (!raw || typeof raw !== "string") return null;
  return CHAIN_REGISTRY[raw.trim().toLowerCase()] ?? null;
}

export function normalizeAddress(chainId: string, address: string): string {
  const a = address.trim();
  return EVM_CHAINS.has(chainId) ? a.toLowerCase() : a; // solana/ton/sui preserved
}

/** Canonical token id, or null (fail-closed). Mirrors sha256(chain:addr)[:32]. */
export function canonicalTokenId(
  chain: string | null | undefined,
  address: string | null | undefined,
): string | null {
  const c = normalizeChain(chain);
  if (c === null) return null;
  if (!address || typeof address !== "string" || !address.trim()) return null;
  const a = normalizeAddress(c, address);
  if (!a) return null;
  return createHash("sha256").update(`${c}:${a}`).digest("hex").slice(0, 32);
}
