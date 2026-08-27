# AHOS — Final Truth Audit

**Date:** 2026-08-27 (UTC)  
**Repo:** `github.com/mainmovement/ahos`  
**Branch audited:** `cursor/ahos-cleanup-alignment-4bde`  
**Companion matrix:** `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`  
**Honesty law:** Truth > appearance. This document does **not** claim production-ready completion.

---

## 1. What AHOS IS

Artificial Hybrid Opportunity Scoring System — an **evidence-first crypto opportunity intelligence** platform (early discovery, multi-source evidence, deterministic scoring, security gating, paper trading, learning harness).  
**Not** a live trading bot. **Not** a wallet signer. Persian-first operator UX.

## 2. What AHOS DOES

1. Discovers emerging market pairs via replaceable providers (DexScreener, GeckoTerminal, pump.fun, …).  
2. Preserves UNKNOWN instead of fabricating prices/confidence.  
3. Runs security gates (GoPlus / RugCheck adapters) before attractive ranking.  
4. Scores deterministically (Python Lane-A path + TS Command Center path).  
5. Explains reasons / risks / unknowns; AI council is advisory-only.  
6. Tracks paper positions and outcomes; writes score ledger for future calibration.  
7. Serves Web Command Center (`npm run dev`) and optional Telegram via **Conversation Gateway only (W57)**.

## 3. What is fully implemented (code evidence)

- Discovery + provider registry + circuit breakers  
- Security adapters + Lane-A security gate  
- Paper trading v3 lifecycle  
- Lane-A freeze integrity (`config/lane_a_freeze.sha256`)  
- Advisory AI council contracts  
- One-Brain Web chat gateway (`conversation_gateway.ts`)  
- Windows/local launchers  
- Document truth map + superseded READY banners  
- W57 Telegram gateway-only lockdown (+ aligned tests, this pass)

## 4. What is partially implemented

- **Calibration measurement** (harness yes; local pairs no)  
- **Live provider SUCCESS** on hosts with blocked egress  
- **Telegram end-to-end** (needs BotFather token + `AHOS_GATEWAY_URL`)  
- **n8n** (JSON + validator yes; live activation credential-gated)  
- **168h soak evidence** (protocol yes; committed 168h artifacts no)  
- **Dual-stack ops** (TS chat brain + Python observation daemon — intentional, documented)

## 5. What is externally blocked

| ID | Blocker |
|----|---------|
| M-GAP-003 | 168h laptop soak |
| M-GAP-004 | GitHub App `workflows` permission for CI |
| M-GAP-007 | Live egress provider SUCCESS |
| M-GAP-008 | Accrued `local` calibration pairs |
| M-GAP-009 | Telegram credentials + live transcript |
| M-GAP-010 residual | 7 distinct nightly backup dates |

## 6. Intentionally deferred

- Real-money trading (DISABLED)  
- Social scrape of X/IG/TikTok (OUT_OF_POLICY / COST_BLOCKED)  
- Freezing `paper_trading/strategies.json` into Lane-A hash (documented exclusion)  
- AI council decision authority (advisory-only by doctrine)

## 7. Exact production blockers

AHOS is **not** production-complete. Remaining blockers are the open M-GAP rows above plus truthful absence of 168h soak + live Telegram + measured calibration. Older `READY_FOR_DEPLOYMENT` files are **historical only**.

## 8. Exact verification commands

```bash
# TypeScript
npm run typecheck

# Python gates (venv)
.venv/bin/python -m pytest tests/ -q --tb=line

# Lane-A freeze
.venv/bin/python scripts/freeze_lane_a.py

# n8n structural
.venv/bin/python tests/validate_n8n.py

# Optional runtime smoke (needs network for providers)
python -m architecture.runtime --single-cycle
```

## 9. Final test results (this completion pass)

| Area | Command | Result | Notes |
|------|---------|--------|-------|
| Typecheck | `npm run typecheck` | **PASS** | Clean |
| Full pytest | `.venv/bin/python -m pytest tests/ -q` | **1385 passed, 0 failed** | Artifact: `/opt/cursor/artifacts/completion_pytest_final.log` |
| Telegram W57 | conversational + service + adapters | **PASS** | INTENTIONAL LOCKDOWN preserved |
| Config env docs | `tests/test_config_validation.py` | **PASS** | Scans Python + One-Brain TS |
| Lane-A freeze | `scripts/freeze_lane_a.py` | **OK (36 files)** | |
| n8n structural | `tests/validate_n8n.py` | **6/6 PASS** | |

Pre-fix baseline on this branch: 28 failed / 1389 passed (stale W57 Telegram expectations + missing env docs). Those failures were classified **STALE TEST** / **DOCUMENTATION DRIFT**, not production bugs.

## 10. Final repository status

**Status:** `LOCAL_OPERATOR_READY_WITH_EXPLICIT_GAPS`  
**Not:** `PRODUCTION_READY` / `READY_FOR_DEPLOYMENT`

The repository now tells one coherent truth about what is implemented, what is blocked, and what operators must still do. Merge remains a human decision after reviewing remaining external gaps.
