# J. IMPLEMENTATION PLAN v1.1 — Mission v1.1 §20 — 2026-08-11
# Order per directive STEP 1..10. "Do not skip steps" — each STEP has exit evidence.

## Wave-5 execution ledger
| STEP | Item | Exit evidence | Status |
|---|---|---|---|
| 1 | Audit current PAL | docs mission_v1_1/A (audit table, live probes) | ✅ DONE |
| 2 | Gap report | docs mission_v1_1/B (G1–G10 ranked) | ✅ DONE |
| 3 | Canonical token identity | discovery/identity.py + unit tests (chain-aware, dedupe, cross-provider) | 🔨 this wave |
| 4 | Timestamped discovery observations | discovery/observations.py + schema_v1_2.sql + dual-time + raw_payloads + tests | 🔨 this wave |
| 5 | 72h observation lifecycle | discovery/lifecycle.py (clock-injected; MOCK fixtures prove transitions; first REAL T0 cohort starts) | 🔨 this wave |
| 6 | Feature store | discovery/feature_store.py (D-registry fs_v0.1 subset, leakage tests L1–L4) | 🔨 this wave |
| 7 | Security gate | discovery/security_gate.py + veto registry + fixtures (veto 100% on fixture set, labeled FIXTURE) | 🔨 this wave |
| 8 | Research dataset integration | discovery/outcomes.py labeler + joins read-only into research/ (labels only via availability law) | 🔨 this wave (labeler; data accrues 72h+) |
| 9 | Paper opportunity ranking | discovery/ranker.py — RANK-first (documented feature-ranking, NO numeric probability); "NO OPPORTUNITY" first-class | 🔨 this wave |
| 10 | Telegram Persian integration | contract I is frozen; implementation = Phase-6 (needs user blocker #1 for REAL). Harness-level fa renderer tests added where possible | ⏭ NEXT wave |

## Hard sequencing rules
- STEPs 3–5 code-merged only with tests green (CI 6-stage + new tests/test_discovery.py).
- STEP 9 ranking never shows score to user surfaces yet (research gate law); ranks+bullets only.
- STEP 10 REAL run waits user blocker ①; everything ships as fixtures+harness until then.

## Wave-6+ queue (unchanged, ranked)
1. USER #1 token rotation / #2 VPS (n8n live + 24/7 continuity + Iran probes)
2. Phase-3 on-chain depth: RPC holder snapshots (budget: ≤N tokens/day), GoPlus re-probe, holder features DEFINED→IMPL
3. Phase-7 narrative: re-probe CryptoPanic; RSS velocity MVP; unique-authors heuristics
4. 72h exit report (first cohort): AUTO-generated on 2026-08-14+ from collected data (survival/liquidity-stability/outcomes)
5. Workflow 20 (discovery) n8n build after PAL stabilizes (Phase-5)

## Effort/cost envelope
All wave-5 work: $0; providers free tier; sandbox runs; no paid API touched (policy G unchanged).
