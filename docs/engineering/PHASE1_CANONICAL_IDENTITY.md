# AHOS Phase 1 — Canonical Identity (Lane B overlay)

**Baseline (main):** `f67eb483396eb0808d6fcc8b1b0b322c856b2167`  
**Phase 0 commit:** `2bb458e1e51c0b28d3471e0370b8beb6a1f237c1`  
**Branch:** `cursor/phase0-engineering-foundation-9500`  
**Date:** 2026-09-03  
**Classification:** `INTEGRATION_READY` (agent-host). Unchanged.  
**Lane A freeze:** 36 files pinned — verified before and after this phase.

This phase adds a Lane B identity overlay. It does **not** edit frozen
`discovery/identity.py`. Canonical `token_id` / `pair_id` hashes still come
from that module when the chain is in the Lane A registry.

---

## Scope

Implemented:

- `ChainIdentity`, `TokenIdentity`, `DexDeployment`, `PoolIdentity`,
  `IdentityResolution`, `IdentitySource`
- States: `VERIFIED`, `CONFLICT`, `UNRESOLVED`, `INVALID`, `STALE`,
  `UNSUPPORTED`
- EVM 20-byte hex + mixed-case EIP-55 (Keccak-256, empty digest pinned)
- Solana 32-byte base58 with canonical string preserved (not lowercased)
- Chain validated before address
- Symbol/name treated as aliases; symbol-only queries return choices and
  never guess
- Minimum verification: two distinct providers, including the
  on-chain + market pattern
- Provenance and conflicts retained; frozen dataclasses prevent silent
  overwrite
- Versioned DEX registry `config/dex_registry.yaml` (`dex-registry-v1`);
  ambiguous uniswap v2/v3 without a version does not silently pick one
- Every supplied pool is preserved on `IdentityResolution.pools`
- Gates: no positive decision / alert / paper candidate / identity mutation
  unless token `VERIFIED`; verified token + unresolved pool ⇒ monitoring
  only, no pool liquidity claims
- `DecisionAdvisor` GATE 0 is fail-closed: missing or non-VERIFIED identity
  cannot `ENTER`

Not in this phase (explicit):

- Binding TypeScript `tokenKey` / `scoring.ts` (Phase 3)
- Wiring `DecisionAdvisor` into `orchestrator.py` (Phase 3)
- Security overlay PASS/REJECT/INCOMPLETE/STALE and GoPlus UNKNOWN (Phase 2)
- Telegram live identity gateway (Phase 9)

---

## Changed-file classification

| Path | Class |
|------|--------|
| `architecture/identity/**` | Lane B new (identity authority overlay) |
| `config/dex_registry.yaml` | Lane B config (DEX versions) |
| `architecture/decision/advisor.py` | Lane B GATE 0 (fail-closed identity) |
| `tests/test_canonical_identity.py` | tests |
| `tests/helpers_identity.py` | tests (VERIFIED fixture for fake `Tok111`) |
| `tests/test_decision_advisor.py` | tests (pass VERIFIED fixture) |
| `tests/test_cognitive_panel.py` | tests (pass VERIFIED fixture) |
| `AGENTS.md` | governance pointer |
| `.cursor/skills/ahos-token-identity/SKILL.md` | skill path |
| `docs/DOC_TRUTH_MAP.md` | truth map |
| `docs/engineering/PHASE1_CANONICAL_IDENTITY.md` | this evidence |

Lane A (`discovery/**`, `paper_trading/**`, `config/lane_a_freeze.sha256`):
**untouched**. `reports/**`: **not committed** (import side-effects restored).

---

## PHASE_STATUS (Phase 1)

```
PHASE_STATUS: COMPLETE
PASS_GATES:
  - ChainIdentity / TokenIdentity / PoolIdentity / DexDeployment / IdentityResolution
  - EVM length + EIP-55 mixed-case; Solana canonical preservation
  - symbol-only ambiguity returns choices; no guess
  - provenance + conflicts retained; frozen types block overwrite
  - duplicate EVM identity => same discovery.identity.token_id
  - INVALID/CONFLICT/UNRESOLVED/STALE/UNSUPPORTED cannot pass identity gates
  - unresolved pool cannot produce pool liquidity claims
  - DecisionAdvisor GATE 0 fail-closed (missing identity => AVOID)
  - Lane A freeze CLI OK (36 files)
  - targeted pytest passed
  - validate_imports PASSED (178 imports, freeze, secrets)
  - no Lane A paths in diff
  - no secrets committed
FAILED_GATES: none for Phase 1 identity-overlay scope
BLOCKERS:
  - TypeScript tokenKey / scoring.ts remain a documented second identity/score
    surface (Phase 3 must not widen; must bind or isolate)
  - orchestrator.py still does not call DecisionAdvisor (Phase 3)
EVIDENCE:
  - docs/engineering/PHASE1_CANONICAL_IDENTITY.md
  - pytest tests/test_canonical_identity.py tests/test_decision_advisor.py
    tests/test_cognitive_panel.py tests/test_discovery.py
    tests/test_cursor_engineering_foundation.py tests/test_cursor_hook_guard.py
    tests/test_one_brain_architecture.py
  - python3 -B scripts/freeze_lane_a.py
  - python3 -B scripts/validate_imports.py
TEST_RESULTS:
  - test_canonical_identity + advisor + cognitive_panel + discovery: 131 passed
  - foundation + one-brain: 15 passed
  - validate_imports VALIDATION PASSED (178 modules)
REGRESSIONS: none. validate_imports import probes can rewrite reports/*.json;
  those files were restored and are not in this commit.
KNOWN_LIMITATIONS:
  - Provider independence is by provider name, not a shared-upstream graph
  - Lane A token_id remains checksum-insensitive lowercase for EVM (frozen)
  - Advisor tests use a VERIFIED fixture because historical Tok111 is not a
    valid Solana pubkey; GATE 0 on production paths requires a real resolution
  - Other recommendation edges (TS, Telegram, unused IntelligenceEngine
    advisor wiring) are Phase 3/9, not claimed closed here
NEXT_UNLOCKED_PHASE: Phase 2 Security Gate overlay (compose Lane A verdicts;
  do not rename frozen discovery/security_gate.py enums; GoPlus missing
  fields must become INCOMPLETE/UNKNOWN, not fail-open False)
```

Do not read this COMPLETE as production-readiness. Product classification
remains `INTEGRATION_READY`.
