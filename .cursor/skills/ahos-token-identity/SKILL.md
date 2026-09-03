---
name: ahos-token-identity
description: Canonical token identity — chain, contract, pool, DEX, symbol ambiguity, provenance, conflicts. Use for discovery/identity questions and any token lookup. Do not edit Lane A identity.py.
paths:
  - "architecture/identity/**"
  - "discovery/identity.py"
  - "architecture/providers/**"
  - "types.ts"
disable-model-invocation: true
---

# AHOS token identity

Lane A `discovery/identity.py` is FROZEN (`token_id` / `pair_id` hashes).
Do not edit it. New resolution states belong in Lane B composition.

Required model (implement in Lane B, do not fork TS `tokenKey`):

- ChainIdentity, TokenIdentity, DexDeployment, PoolIdentity, IdentityResolution
- States: VERIFIED, CONFLICT, UNRESOLVED, INVALID, STALE, UNSUPPORTED

Rules:

- Validate chain before address.
- EVM: length + checksum-aware validation; do not treat symbol as identity.
- Solana: preserve canonical representation; do not lowercase.
- Symbol/name are aliases.
- Pool must belong to the same canonical token.
- Preserve every pool, provenance, and conflict. No silent overwrite.
- INVALID / CONFLICT / UNRESOLVED ⇒ no positive recommendation, alert, or
  paper candidate.
- Verified token + unresolved pool ⇒ token monitoring only; no pool liquidity
  claims.

Known conflict: `types.ts` `tokenKey` lowercases Solana and can key by symbol.
Do not extend that. Bridge to Lane A `token_id` instead.
