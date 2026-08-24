# AHOS CANONICAL — PROJECT STATE (always-current pointer)

> **W57 RECONCILED (documentation-only, per `docs/canonical/RECONCILIATION_R1.md`).** The Wave-7 snapshot
> below is retained as historical evidence; the head-of-repo reality is W57. Status legend:
> `CURRENT/IMPLEMENTED · PARTIAL · EXPERIMENTAL/OFF · MISSING · UNVERIFIED · CONTRADICTED`.
> Source: completed AHOS audit (authoritative observation set for this reconciliation). Uncertainty is
> preserved — `UNVERIFIED`/`LIKELY` are not promoted to `CONFIRMED`.

## W57 current state (verified reality)
| Subsystem | Status | Note (evidence) |
|---|---|---|
| Active directive | CURRENT | `MASTER_DIRECTIVE_v1.md` (registry-pinned, immutable); W43 = historical (R1) |
| Web Command Center (Next.js + PostgreSQL/Drizzle) | CURRENT/IMPLEMENTED | live cycling engine `engine.ts`; API `app/api/*`; Persian RTL UI |
| Python intelligence daemon (`architecture/`, Lane B) | CURRENT/IMPLEMENTED | `python -m architecture.runtime`; `OpportunityPipelineOrchestrator` |
| One Brain | PARTIAL | canonical conversation contract/gateway exists; Python + TypeScript scoring engines still separate (not one production brain) |
| Lane A (`discovery/`, `paper_trading/`) | CURRENT (frozen) | hash-frozen (`config/lane_a_freeze.sha256`); evidence-producing; human re-anchor only |
| Production providers (Python collector) | PARTIAL | CONNECTED: DexScreener, GeckoTerminal, GoPlus, RugCheck. Others registry-present but IMPLEMENTED_BUT_DISABLED/ABSTRACTED_ONLY (not LIVE) |
| Security VETO / WATCH-cap | CONTRADICTED (P0) | enforced in Lane-A `discovery/security_gate.py`; **Lane-B production pipeline does not fully enforce the WATCH cap** (UNKNOWN security can still yield a numeric score). Documented, NOT fixed here |
| Rank-first vs numeric score | CONTRADICTED | Lane-A is rank-first; Lane-B pipeline emits numeric `opportunity_score` and sorts on it |
| Scoring dimensions | PARTIAL | opportunity/risk/security/confidence implemented; narrative SCAFFOLD; catalyst/tokenomics/dev-activity MISSING |
| Telegram | PARTIAL | W57 gateway-only lockdown; `AHOS_GATEWAY_URL` required (else `EMERGENCY_FALLBACK_ONLY`) |
| Self-learning / self-evolution | PARTIAL / EXPERIMENTAL(OFF) | ledger + calibration measure, do not auto-tune; evolution engine gated behind human approval |
| GitHub intelligence | PARTIAL | `engine/oss_audit.py` CLI only; auto-issue MISSING |
| Test suite | UNVERIFIED (historical) | previous run observed 1387 passed / 30 failed (stale W57 Telegram expectations + a `.gitignore` expectation); NOT rerun during this reconciliation; tests NOT changed |
| PR-1 (`67eef26…`) | UNVERIFIED | absent from object store, not on origin, bundle/patch unavailable on this VM; not reconstructed |
| PR #17 (Cloud env) | CURRENT | audited independently; docs-only reconciliation does not touch it; remains unmerged |

Full detail: `reports/PHASE_STATE.md` and `AHOS_PROJECT_STATE_MAP.md`. Entry node = `docs/canonical/KNOWLEDGE_MAP.md`.
Next-step dependency order: `docs/canonical/ROADMAP.md`.

---

## Wave-7 historical snapshot (retained as evidence — NOT current)
**Status:** Wave-7 · 2026-08-11 · Full detail: `reports/PHASE_STATE.md` (live page) and
`AHOS_PROJECT_STATE_MAP.md` (forensic map, waves 1–7 addenda). This file = pointer only (compression law).
**Wave-7 delta:** hygiene engine + cleanup 11/11 manifested · pal_probe permanent (GoPlus↑, pollinations✗402) ·
H14–H20 registered (7 computable/3 blocked) + conjunction+materializer · telegram_ai core 25 tests ·
CI 80 tests green (stages 3d/3e added) · entry node = docs/canonical/KNOWLEDGE_MAP.md.

## One-line truth per subsystem
| Subsystem | Letter | Where proven |
|---|---|---|
| Backtest engine (frozen) + data audit + acquisition | D | reports/{BACKTEST_REPORT_EXACT,validation_results}.json etc. |
| Strategy lab (H1–H13 all REJECTED; H8 data-blocked) | D | strategy_lab/registry.json · research/experiments/* |
| CI gate (6-stage: audit/pytest×3/dry-run/telegram-SIM/n8n) | D | engine/run_all_checks.sh — unpiped exit 0 |
| n8n workflows ×6 | D import / C execution | reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt |
| Database schema v1.1 (+v1.2 additive twin) | C | psql boot pending user blocker ② |
| Telegram protocol layer | C (SIM 11/11) | REAL pending user blocker ① |
| Discovery Core (PAL/identity/obs/72h/features/security/outcomes/rank) | C Tested, RUNNING | tests/test_discovery.py 22/22; data/e01_discovery.sqlite |
| E-01 real collection | RUNNING (sandbox best-effort) | T0=2026-08-11 17:20Z; 72h report ≥2026-08-14 |
| Telegram contract (Persian) | A (frozen) → Wave-7 core C Tested | docs/mission_v1_1/I · telegram_ai/ (25 tests) |
| Document hygiene | D (engine + policy v2, manifested) | engine/doc_hygiene.py · reports/CLEANUP_MANIFEST_WAVE7.json |
| Research registry H14–H20 | C (registered, machinery tested, real scan gated) | research/SEARCH_SPACE_REGISTRY.json |
| Evolution layer | A (OFF by doctrine) | — |

## Binding constraints right now
- LIVE trading CLOSED: 0/13 strategies + 0 promoted features (E-01 < 8 weeks).
- User blockers: ① Telegram token rotation+chat-id ② Production VPS.
- Scores to users: NONE until research gate (ranks + evidence bullets only).
