# AHOS Roadmap v3 — Operational Intelligence Platform (6 Months)

**Date:** 2026-08-18 · **Baseline:** main @ 95f5e14 · **Audit:** AHOS_REALITY_AUDIT_v2.md
**Mission:** Transform the verified research-grade architecture into a reliable operational
Crypto Opportunity Intelligence Platform. NOT a rebuild — an activation + hardening program.

**Program laws (inherited, non-negotiable):** $0/month ceiling · UNKNOWN over invention ·
evidence-first scoring with mandatory explanations · paper-only (no execution, no wallets) ·
Lane-A freeze (discovery/ + paper_trading/ hash-pinned) · small verified steps.

---

## 1. Month 1 — Operational Engine (24/7 core)

**Goal:** AHOS runs unattended on a VPS, survives restarts, and *proves it* with telemetry.

| Work item | Maps to audit gap | Acceptance criterion (evidence, not claims) |
|---|---|---|
| Fix clock-drift stub; real NTP-free drift measurement | B | Unit test: injected wall-clock step > threshold ⇒ cycle ABORTED_DRIFT |
| Heartbeat staleness watchdog (`architecture/scheduling`) | C | `--status` reports stale components from `scheduler_heartbeats`; unit-tested |
| systemd unit `deployment/ahos-runtime.service` (Restart=always, watchdog integration) | C, D | Unit file ships; VPS boot log in evidence register |
| First-run bootstrap runbook (fresh clone → init DBs → daemon) | §4.3 | RUNBOOK with executed transcript (timestamps + heartbeat rows) |
| **Soak run ≥ 7 days** daemon, gap register reviewed | D | `reports/soak_*.json`: uptime, cycles, missed windows, breaker trips |
| SQLite backup/rotate script + schedule | K | Cron proof: 7 consecutive nightly backups, restore drill passes |
| GitHub Actions CI (blocked: App `workflows` permission) | A | PR turns CI green once permission granted |

## 2. Month 2 — Provider Expansion

**Goal:** Broader real-data coverage; fewer UNKNOWN fields; multi-chain beyond solana.

**Scheduler/infra decision (directive Step 3 evaluation) — decided Month 1, recorded here:**

| Option | Simplicity | Reliability | Maintenance | Verdict |
|---|---|---|---|---|
| **Temporal** | Low (server + SDK + clustering) | High | Heavy (extra service, versioning) | ❌ Overkill for single-VPS $0 ceiling |
| **Celery** | Low-Med (broker required: Redis/RabbitMQ) | High | Heavy (broker ops, cost, monitoring) | ❌ Violates $0/offline-install laws for zero benefit at this scale |
| **APScheduler** | High (in-process) | Med-High (SQLite jobstore) | Med (3rd-party dep, 4.x migration churn) | ❌ Duplicates what in-house scheduler already does (lease locks, gap register) |
| **In-house `ProductionScheduler` (retain + harden)** | **Highest** (stdlib-only, already 947-test-green suite) | **High** (SQLite atomic leases, heartbeat, missed-window audit — tested) | **Lowest** (no deps; code owned, frozen-lane compatible) | ✅ **CHOSEN** |

Rationale: the existing scheduler already implements lease locking, heartbeats, downtime detection
and honest gap registration with tests; adding a framework would re-import those features at the
cost of a dependency and operational surface. Directive criteria (simplicity, reliability,
maintenance) all favor retention. Decision recorded; revisit only if multi-host scheduling is ever
required (it is not, by design).

| Work item | Acceptance criterion |
|---|---|
| CoinGecko adapter (keyless public API, chain-aware contract lookup) | Unit tests with fixture payloads; live probe recorded in provider reachability register |
| ChainExplorer adapter (public RPC: contract-exists / account signals, chain map incl. avalanche) | Unit tests; UNKNOWN fields explicit where RPC can't answer |
| Unified `collect(token)` facade over ProviderRouter (merge + provenance + UNKNOWN report) | Phase 7 Step 4 (started now — see PHASE7_REPORT); multi-provider merge test |
| Multi-chain E2E: ethereum, bsc, base, arbitrum, polygon, **avalanche** (new) | ≥ 50 real candidates/chain collected & persisted; coverage report (fields known vs UNKNOWN) |
| CoinMarketCap + Launchpad adapters (free tiers) | Same standard as CoinGecko |
| Rate-limit registry sync with discovery/providers.yaml (PAL side stays frozen) | Cross-check test: no rate/breaker divergence between PAL yaml and architecture adapters |

## 3. Month 3 — Scoring Intelligence

**Goal:** Scores become *measurable*, not just explainable.

| Work item | Acceptance criterion |
|---|---|
| Calibration harness: replay accumulated E-01 observations through scorer | Report: score-vs-outcome buckets (7 horizons), per-feature weight sensitivity |
| Weight governance: versioned weight sets + acceptance test on historical data | Any weight change ⇒ calibration diff report attached to PR |
| Narrative + smart-money inputs promoted from B/C to C/D (intel/news, viral, whales) | Feed-through test: evidence items appear in explanations with provenance |
| Confidence & invalidation quality audit | Manual review of 30 sampled Persian cards vs underlying evidence |

## 4. Month 4 — Telegram Product (Persian-first)

| Work item | Acceptance criterion |
|---|---|
| **Token rotation + live boot (USER BLOCKER — highest priority)** | Real Telegram transcript archived as evidence |
| Consolidate legacy `engine/bot_skeleton.py` path into `telegram_ai/` | One stack; legacy shim only; import gate green |
| Persian UX pass per TELEGRAM_PERSIAN_UX_DESIGN (opportunity cards, decision advisory) | 9-intent live matrix PASS; footer/WHY-law test-pinned |
| Alert hygiene: dedupe, quiet hours, severity routing | Soak-week alert log: 0 duplicate storms |

## 5. Month 5 — Learning Engine

| Work item | Acceptance criterion |
|---|---|
| Outcome labels (frozen Lane-A labeler) → scorer feedback loop (architecture-side only) | Weekly learning report; no Lane-A edits (freeze law) |
| Knowledge store claims promoted by evidence thresholds | Claim ledger diff reviewable; contradictions surfaced |
| Post-trade lessons → paper-strategy review | Lessons report correlates decisions with outcomes |

## 6. Month 6 — Production Deployment

| Work item | Acceptance criterion |
|---|---|
| Postgres boot + schema v1_3 live (server lane) | psql integrity checks green; SQLite→PG sync job proven |
| n8n activation (6 workflows, credentials vaulted) | Execution logs for all 6 |
| Full-stack docker-compose.production on VPS + restore drill | 30-day stability report; backup restore to fresh host < 30 min |
| **Production readiness re-audit (v3)** | Evidence-linked scorecard; READY only if every gap from audit v2 §5 closed |

---

## Stage Gates (strict)

- No stage advances on claims — every month closes with an evidence artifact committed under `reports/`.
- Live-gate law stands: 0 accepted strategies ⇒ no capital risk features are even designed.
- Any Lane-A need ⇒ governance proposal (freeze regeneration), never a silent edit.

## Dependency Ladder

```
M1 operational engine ──► M2 provider expansion ──► M3 scoring calibration
        │                                                    │
        └──► M4 Telegram (needs token blocker cleared) ◄─────┘   M5 learning (needs M3 + ≥8w data)
                                                                     │
                                              M6 production ◄────────┘
```
