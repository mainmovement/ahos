# AHOS — Canonical Implementation Matrix

**Date:** 2026-08-27  
**Branch:** `cursor/ahos-cleanup-alignment-4bde`  
**Authority inputs:** `docs/canonical/MASTER_DIRECTIVE_v1.md`, `MASTER_DIRECTIVE_W43.md`, `AHOS_GAP_REGISTER.md`, `docs/DOC_TRUTH_MAP.md`, source + tests  
**Law:** Statuses are repository reality, not aspiration.

Status alphabet: `COMPLETE` · `PARTIAL` · `MISSING` · `BROKEN` · `BLOCKED_EXTERNAL` · `DEFERRED_BY_DESIGN` · `CONTRADICTORY`

| Requirement | Canonical Source | Expected Capability | Current Implementation | Relevant Files | Relevant Tests | Evidence | Status | Gap | Priority | Blocking Reason | Required Action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Early multi-source discovery | Doctrine + DMS | Collect emerging pairs with provenance | Collector + discovery poller implemented | `architecture/collector/`, `discovery/`, `architecture/providers/` | `tests/test_discovery.py`, provider tests | Agent-host LIVE SUCCESS 2026-08-27 | COMPLETE | Laptop re-probe residual | Med | Operator egress may differ | OA-3 on Windows laptop |
| Narrative intel feed-through | R-69/R-80 | News atoms in scored reports | `attach_narrative` + orchestrator prefetch | `architecture/intel/news.py`, `scoring/engine.py`, `pipeline/orchestrator.py` | `test_narrative_and_intel_feed_through` | Live DERIVED atoms | COMPLETE | — | — | — | Keep AHOS_NARRATIVE_FETCH documented |
| Market structure / tokenomics / catalysts | Backlog P1 | Honest microstructure + tokenomics + catalysts | Lane B intel modules | `architecture/intel/market_structure.py`, `tokenomics.py`, `catalyst.py` | feed-through + contract tests | Live DERIVED | COMPLETE | Unlock schedules UNKNOWN by design | Low | Data scarcity | Do not fabricate vesting |
| Scoring semantic contract | P1-5 | Shared field dictionary Py↔TS | Contract JSON + tests | `docs/contracts/scoring_contract_v1.json` | `test_scoring_contract_v1` | Present | COMPLETE | Numeric parity deferred | Low | Dual engines | Optional parity harness |
| Multi-chain / DEX / launchpad | Provider registry | Replaceable providers + pump.fun | Router + CMC + pumpfun adapters | `architecture/providers/*` | `test_coinmarketcap_adapter`, `test_pumpfun_adapter`, `test_provider_yaml_sync` | Offline PASS | COMPLETE | Live probe | Med | Egress | M-GAP-007 |
| Evidence ≠ score ≠ decision ≠ outcome | DEB / learning | Traceable ledger | Score ledger + frozen outcomes materializer | `architecture/learning/score_ledger.py`, `discovery/materialize.py` | `test_score_ledger_calibration` | Infra closed M-GAP-013/014 | PARTIAL | Measurement empty | High | Needs local evidence accrual | M-GAP-008 |
| Deterministic scoring | SPS | Explainable multi-factor score | Python scoring + TS scoring | `architecture/scoring/`, `scoring.ts`, `opportunity_canonical.ts` | scoring / one-brain tests | Dual stacks | PARTIAL | Dual brain ownership | High | Doc/ops clarity | Documented in DOC_TRUTH_MAP; keep both |
| Security-first gate | RAS | Attractive score cannot ignore critical security | GoPlus/RugCheck + security_gate | `discovery/security_gate.py`, `architecture/security/`, adapters | security + discovery tests | Code COMPLETE | COMPLETE | Live probe | Med | Egress | M-GAP-007 |
| Opportunity explainability | Doctrine | WHY interesting / dangerous / missing | Reasons/risks/unknowns + council advisory | `opportunity_canonical.ts`, `council.ts`, `architecture/council.py` | one-brain / council tests | Present | COMPLETE | — | — | — | Keep advisory-only |
| Monitoring / lifecycle | RAS | Repeated observations + alerts | observe_active + web alerts | `discovery/observe_active.py`, `alerts.ts` | observation scheduler tests | Present | PARTIAL | 168h soak | High | User laptop | M-GAP-003 |
| Paper trading only | Doctrine | No real execution | paper_trading v3 + PAPER_ONLY UI | `paper_trading/`, `engine.ts` | `test_paper_trading*` | Present | COMPLETE | strategies.json not in freeze | Low | By design | Documented in `freeze_lane_a.py` |
| Learning loop | Evolution docs | Observation→outcome→calibration | Calibration harness, no weight mutation | `architecture/learning/` | calibration tests | Infra COMPLETE | PARTIAL | No local pairs | High | User data | M-GAP-008 |
| One-Brain chat | W56/W57 | Single conversation entry | `conversationGateway` + `/api/chat` | `conversation_gateway.ts`, `app/api/chat/route.ts` | `test_one_brain_architecture` | Present | COMPLETE | Telegram needs URL | Med | Config | Set `AHOS_GATEWAY_URL` |
| Lane A freeze | Governance | Drift veto | `config/lane_a_freeze.sha256` | `scripts/freeze_lane_a.py`, observation_loop | `test_lane_a_frozen_files_hash_integrity` | PASS | COMPLETE | — | — | — | — |
| Lane B research | Doctrine | Evolve without rewriting Lane A | strategy_lab + evolution packages | `strategy_lab/`, `architecture/evolution/` | strategy_lab / evolution tests | Present | COMPLETE | — | — | — | Human gate for promotions |
| AI council advisory-only | Council contract | Never DECIDE | advisory_only enforced | `architecture/council.py`, `architecture/ai/` | council tests | Present | COMPLETE | Paid AI keys optional | Low | Optional | Leave free-first |
| Telegram Persian UX | Telegram docs | Intent + honest replies | Intent parser COMPLETE; service gateway-only | `telegram_ai/` | `test_telegram_service`, updated conversational | W57 lockdown | PARTIAL | Live bot + gateway | High | Token + URL | M-GAP-009 + `AHOS_GATEWAY_URL` |
| n8n automation | Deployment docs | Meaningful workflows | 6 JSON workflows + validator | `n8n/workflows/`, `tests/validate_n8n.py` | validate_n8n | Structural PASS | PARTIAL | Runtime import/creds | Med | Docker + creds | Operator import |
| Windows-first local run | Operator docs | One-click start | install/start scripts | `install_windows.ps1`, `start_ahos.ps1`, `run_ahos.sh` | phase18 launcher tests | Present | COMPLETE | Soak evidence | High | User | M-GAP-003 |
| CI | Gap register | Green PR checks | Template only | `deployment/github-actions-ci.yml.template` | — | No `.github/workflows` | BLOCKED_EXTERNAL | Workflows permission | Med | GitHub App | M-GAP-004 |
| No READY overclaim | Gap register honesty | Docs match reality | Supersede banners + truth map | `AHOS_FINAL_STATUS.md`, `docs/DOC_TRUTH_MAP.md` | — | Hygiene PR | COMPLETE | — | — | — | Maintain |
| Telegram tests vs W57 | W57 commits | Tests match lockdown | Aligned 2026-08-27 | `tests/test_telegram_*` | conversational + service | Was CONTRADICTORY | COMPLETE | Was stale | High | — | Closed this pass |
| Env key documentation | Config validation | Every key in `.env.example` | Documented AHOS_GATEWAY_URL + alert keys | `.env.example` | `test_config_validation` | Fixed this pass | COMPLETE | — | — | — | — |
| GitHub / OSS capability intelligence (AG-25) | Agent registry | Live GitHub harvest agent | PLANNED only; offline oss_pipeline + optional `engine/oss_audit.py` | `config/agent_registry.yaml`, `architecture/knowledge/oss_pipeline.py` | control_plane / oss tests | Registry `implemented: false` | NOT_IMPLEMENTED | AG-25 | Low | Design + owner gate | Keep PLANNED; do not claim live |
| Live trading enablement | Doctrine | DISABLED | Flags veto + honest exchange-key isolation | `architecture/security/hygiene.py` | `test_security_hardening` | Fixed dead `== "1"` key check | COMPLETE | — | — | — | — |
| Owner action consolidator | Ops | One OWNER checklist | `docs/OWNER_ACTION_REQUIRED.md` | same | — | Added 2026-08-27 | COMPLETE | — | — | — | Owner executes OA-* |
| Real trading | Doctrine | DISABLED | No execution path in scanned runtime | multiple | month1 failure matrix | Present | DEFERRED_BY_DESIGN | Forever unless doctrine change | — | Safety | Keep DISABLED |
| Social scrape X/IG/TikTok | Policy | OUT_OF_POLICY | Honest BLOCKED in providers | `providers.ts`, README | — | Present | DEFERRED_BY_DESIGN | Cost/policy | — | Policy | Keep blocked |
| DEXTools full | Cost | Optional paid | NO_KEY / COST_BLOCKED | providers | — | Present | BLOCKED_EXTERNAL | Key/cost | Low | Operator | Optional |
| Calibration measurement | Learning | Score vs outcome | Framework COMPLETE | `architecture/learning/` | calibration tests | `CALIBRATION_READY_BUT_DATA_REQUIRED` | PARTIAL | Local pairs | High | Owner OA-4 | Accrue evidence |
| 168h soak execution | Ops | 7-day reliability | Protocol + scripts COMPLETE | `AHOS_LOCAL_SOAK_PROTOCOL.md`, `scripts/soak_*.py` | soak tests | `SOAK_INFRASTRUCTURE_READY` / `SOAK_NOT_YET_EXECUTED` | PARTIAL | Execution | High | Owner OA-5 | Run soak |

## Summary counts (rows above)

| Status | Count |
|--------|------:|
| COMPLETE | 16 |
| PARTIAL | 8 |
| BLOCKED_EXTERNAL | 2 (+ live legs of COMPLETE rows) |
| DEFERRED_BY_DESIGN | 2 |
| NOT_IMPLEMENTED | 1 (AG-25 live harvest) |
| MISSING / BROKEN / CONTRADICTORY | 0 in scanned core after acceptance pass |

## Closable now vs not

**Closed this pass / prior PR #19 commits:** stale Telegram tests; env-key docs; n8n wording; freeze exclusion docs; truth map dual-stack; security hygiene dead-check; historical doc banners; owner action consolidator; GitHub intelligence honesty.

**Not closable without owner/external:** M-GAP-003, 004, 008, 009, 010 residual; M-GAP-007 residual laptop re-probe (agent-host MITIGATED). See `docs/OWNER_ACTION_REQUIRED.md`.

**Classification:** `INTEGRATION_READY` (agent-host) — see `docs/FINAL_TRUTH_AUDIT.md`.
