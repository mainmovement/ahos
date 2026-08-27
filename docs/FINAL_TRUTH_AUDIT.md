# AHOS — Final Truth Audit

**Date:** 2026-08-27 (UTC)  
**Repo:** `github.com/mainmovement/ahos`  
**Branch:** `cursor/ahos-cleanup-alignment-4bde`  
**PR:** https://github.com/mainmovement/ahos/pull/19  
**Companion:** `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` · `docs/OWNER_ACTION_REQUIRED.md`  
**Honesty law:** Truth > appearance. This document does **not** claim `PRODUCTION_READY`.

---

## 1. What AHOS IS

Artificial Hybrid Opportunity Scoring System — evidence-first crypto opportunity intelligence (discovery, multi-source evidence, deterministic scoring, security gating, paper trading, learning harness).  
**Not** a live trading bot. **Not** a wallet signer. Persian-first operator UX. **PAPER_ONLY** is non-negotiable.

## 2. What AHOS DOES

1. Discovers emerging market pairs via replaceable providers.  
2. Preserves UNKNOWN instead of fabricating prices/confidence.  
3. Runs security gates before attractive ranking.  
4. Scores deterministically (Python Lane-A + TS Command Center).  
5. Explains reasons / risks / unknowns; AI council is advisory-only.  
6. Tracks paper positions/outcomes; score ledger for future calibration.  
7. Serves Web Command Center; Telegram is gateway-only (W57).

## 3. Fully implemented (code evidence)

Discovery · provider registry · security adapters/gates · paper trading v3 · Lane-A freeze · advisory council · One-Brain Web gateway · Windows launchers · W57 Telegram lockdown · env/config validation · n8n structural workflows · document truth map · owner-action consolidator · live-trading flag veto (honest exchange-key isolation).

## 4. Partially implemented / ready-but-unexecuted

| Label | Meaning |
|-------|---------|
| `CALIBRATION_READY_BUT_DATA_REQUIRED` | Harness exists; needs `local` pairs (OA-4) |
| `SOAK_INFRASTRUCTURE_READY` / `SOAK_NOT_YET_EXECUTED` | Protocol+scripts exist; 168h not run (OA-5) |
| Live providers / Telegram E2E / n8n activation | Code present; owner/external required |

## 5. Externally blocked

OA-1…OA-7 in `docs/OWNER_ACTION_REQUIRED.md` (M-GAP-003/004/007/008/009/010).

## 6. Intentionally deferred / not implemented

- Real-money trading — DISABLED  
- X/IG/TikTok scrape — OUT_OF_POLICY  
- AG-25 live GitHub harvest — **NOT_IMPLEMENTED** (registry PLANNED)  
- Freezing `strategies.json` into Lane-A hash — intentional exclusion  

## 7. Production blockers

AHOS is **not** production-complete until OA-3…OA-5 (and preferably OA-1/2/6) produce real artifacts.

## 8. Verification commands (re-run independently 2026-08-27)

```bash
npm run typecheck
.venv/bin/python -m pytest tests/ -q --tb=line
.venv/bin/python scripts/freeze_lane_a.py
.venv/bin/python tests/validate_n8n.py
```

## 9. Final test results (independent re-verification)

| Gate | Result |
|------|--------|
| `npm run typecheck` | **PASS** |
| `pytest tests/ -q` | **1385 passed, 0 failed** (pre-acceptance-pass baseline; security tests added → re-run in this commit) |
| Lane-A freeze | **OK (36 files)** |
| n8n validate | **6/6 PASS** |

## 10. Repository classification

**`DEVELOPMENT_READY`**

Meaning: core engineering, architecture coherence, tests, and documentation are synchronized enough to enter the next development phase. Remaining gaps are **owner/external operational validation**, not missing core product engineering.

**Not** `PRODUCTION_READY`.

## 11. Final acceptance matrix

| DOMAIN | REQUIRED | IMPLEMENTED | TESTED | LIVE VERIFIED | STATUS | EVIDENCE | REMAINING ACTION |
|--------|----------|-------------|--------|---------------|--------|----------|------------------|
| Architecture | Coherent lanes + One-Brain | Yes | Arch tests | N/A | PASS | matrix + one-brain tests | — |
| Governance | Doctrine + registers | Yes | master directive tests | N/A | PASS | DOC_TRUTH_MAP | — |
| Lane A | Freeze + evidence integrity | Yes | freeze test | N/A | PASS | lane_a_freeze.sha256 | — |
| Lane B | Research without rewriting A | Yes | strategy/evolution tests | N/A | PASS | strategy_lab | — |
| Discovery | Multi-source candidates | Yes | discovery tests | No | PARTIAL | adapters | OA-3 |
| Providers | Registry + fallbacks | Yes | provider tests | No | PARTIAL | registry | OA-3 |
| Security | Fail-safe gates | Yes | security tests | No | PARTIAL | hygiene+gates | OA-3 |
| Risk | Risk dimensions | Yes | scoring/risk tests | N/A | PASS | architecture/risk | — |
| Scoring | Deterministic + explainable | Yes | scoring tests | N/A | PASS | dual stacks documented | — |
| Opportunity Intelligence | WHY/MISSING/DANGEROUS | Yes | canonical TS + Python | N/A | PASS | opportunity_canonical | — |
| One Brain | Single chat path | Yes | one-brain tests | Partial (Web) | PASS | conversation_gateway | OA-2 for Telegram |
| Telegram | Persian UX + gateway | Gateway-only | W57 tests | No | PARTIAL | service.py | OA-1/OA-2 |
| Web/UI | Honest Command Center | Yes | typecheck + routes | Not in this env | PARTIAL | app/ | Owner laptop UI |
| n8n | Meaningful workflows | JSON+validator | 6/6 | No | PARTIAL | validate_n8n | Docker+creds |
| Paper Trading | PAPER_ONLY lifecycle | Yes | paper tests | N/A | PASS | paper_trading/ | — |
| Learning | Loop infra | Yes | calibration tests | No data | PARTIAL | learning/ | OA-4 |
| AI Council | Advisory only | Yes | council tests | Optional keys | PASS | advisory_only | — |
| GitHub Intelligence | AG-25 harvest | No (PLANNED) | N/A | No | NOT_IMPLEMENTED | agent_registry | Keep PLANNED |
| Persistence | SQLite stores | Yes | backup tests | Soak residual | PARTIAL | backup script | OA-6 |
| Scheduler | Daemon cycles | Yes | runtime tests | Soak | PARTIAL | architecture.runtime | OA-5 |
| Observability | Snapshots/health | Yes | observability tests | N/A | PASS | health snapshot | — |
| Configuration | .env.example + validation | Yes | config tests | N/A | PASS | .env.example | — |
| Windows Runtime | Launchers | Yes | phase18 tests | Not Windows VM | PARTIAL | start_ahos.ps1 | Owner Windows |
| Calibration | Framework + data | Framework | yes | No | PARTIAL | CALIBRATION_READY_BUT_DATA_REQUIRED | OA-4 |
| Soak | 168h | Infra | protocol tests | No | PARTIAL | SOAK_NOT_YET_EXECUTED | OA-5 |
| CI | GitHub Actions | Template only | N/A | No | BLOCKED | M-GAP-004 | OA-7 |
| Documentation | Synchronized truth | Yes | — | N/A | PASS | matrix+audit+owner | Maintain |

## 12. Next development phase

After owner merges PR #19 and begins OA-* execution:

1. Wire live evidence accrual on laptop (OA-3/4).  
2. Execute soak + nightly backups (OA-5/6).  
3. Telegram gateway E2E (OA-1/2).  
4. Only then consider production-gate language — never before artifacts exist.
