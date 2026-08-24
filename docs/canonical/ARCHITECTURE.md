# AHOS CANONICAL — ARCHITECTURE

> **W57 RECONCILED (documentation-only, per `docs/canonical/RECONCILIATION_R1.md`).** The layer map further
> below is the **Lane-A canonical/target evidence chain**; it is not the whole running system. The verified
> W57 architecture has three lanes and **two separate scoring engines**. Status legend:
> `CURRENT/IMPLEMENTED · PARTIAL · EXPERIMENTAL/OFF · MISSING · UNVERIFIED · CONTRADICTED`.

## W57 verified architecture (three lanes, two scoring engines)

- **Lane A — protected / frozen / evidence-producing** (`discovery/*`, `paper_trading/*`). Hash-frozen via
  `config/lane_a_freeze.sha256`; **must not be modified without an explicit human re-anchor**
  (`scripts/freeze_lane_a.py --write`). Enforces rank-first and a real Security-VETO / WATCH cap
  (`discovery/security_gate.py`). Writes `data/e01_discovery.sqlite`, `data/paper_trading.sqlite`.
- **Lane B — control plane / intelligence / scoring / research / evolution** (`architecture/*`). Runs as the
  Python daemon (`python -m architecture.runtime` → `OpportunityPipelineOrchestrator`). Import-isolated from
  Lane A (`architecture/__init__.py`, CI-tested). **Contains current architectural gaps** (see below). Writes
  `data/ahos_local.sqlite`, `data/ahos_knowledge.sqlite`; may write Lane-A evidence only through frozen
  Lane-A functions.
- **Web One Brain surface — Next.js/TypeScript** (`engine.ts`, `scoring.ts`, `council.ts`, `chat.ts`,
  `conversation_gateway.ts`) on **PostgreSQL/Drizzle**. Live cycling engine + Persian RTL Command Center.

### One Brain — PARTIAL
- CURRENT: a **canonical conversation contract + gateway** exists (`conversation_gateway.ts`, canonical
  `types.ts`/`opportunity_canonical.ts`/`alert_canonical.ts`; W57 Telegram routes here via `AHOS_GATEWAY_URL`).
- CONTRADICTED / PARTIAL: **scoring remains duplicated** between the Python pipeline (`architecture/`) and the
  TypeScript engine (`scoring.ts`), on **different datastores** (SQLite vs PostgreSQL).
- Therefore One Brain is **PARTIALLY IMPLEMENTED**. A single production "brain" does **not** yet exist; the
  engine-unification architectural decision is **future work** (see `docs/canonical/ROADMAP.md`).

### Security truth — P0 gap (documented, NOT fixed here)
- Lane-A security boundary **exists and is enforced** (`discovery/security_gate.py`: UNKNOWN security ⇒ ≤ WATCH; VETO ⇒ excluded).
- The **Lane-B production pipeline currently has a security-enforcement gap**: UNKNOWN security applies
  penalties but does **not** apply an absolute WATCH cap, so a candidate with UNKNOWN security can still
  receive a numeric `opportunity_score`. Reconciling the WATCH-cap/VETO into Lane-B is **P0**; this
  documentation PR does **not** implement the fix.

### Rank-first vs numeric scoring — CONTRADICTED
- Canonical doctrine (MISSION law #3, invariant 4 below) is **rank-first, no numeric score until the research
  gate**. Lane-A honors this (`discovery/ranker.py`). The Lane-B pipeline **always emits a numeric score and
  sorts on it** (`architecture/pipeline/orchestrator.py`). Documented here; **scoring code is not changed**.

### Provider truth (production Python collector)
Distinguish **registry capability** from **actual production connectivity**. Do **not** describe
registered-but-idle adapters as LIVE.
- **CONNECTED** (used by the production `CollectorEngine`): DexScreener, GeckoTerminal, GoPlus, RugCheck.
- **IMPLEMENTED_BUT_DISABLED**: CoinGecko, CoinMarketCap (`NO_KEY`), Pump.fun, DEXTools, DexScreener-boosts.
- **ABSTRACTED_ONLY**: chain-explorer (Blockscout). **MOCKED**: DefiLlama.
- **MISSING in Python** (web-only in `providers.ts`): Jupiter, Binance, CoinCap, CryptoCompare, CoinPaprika, mempool.
- The **web engine** fans out to many providers, but that is a separate engine from the Python collector.

---

## Lane-A canonical/target evidence chain
Detail: docs/TARGET_ARCHITECTURE_vNext.md, docs/ARCHITECTURE_FINAL.md (legacy base), docs/mission_v1_1/C.
(Historical note: the "12 LIVE-probed 2026-08-11" line reflects a Wave-6 probe, not current runtime — see
provider truth above.)

```
PROVIDERS (12 LIVE-probed 2026-08-11; fallbacks per capability)   [docs/canonical/PROVIDERS.md]
  → PAL (discovery/pal.py; envelope contract; breaker; budget; cache; raw-archive)
  → DISCOVERY (discovery/collect.py — GT new_pools + DEX profiles; 5-min poll capable)
  → IDENTITY (canonical token_id/pair_id; chain registry)         [discovery/identity.py]
  → STORE (schema v1.2: tokens/pairs/observations/raw_payloads/…; sqlite canonical, pg twin)
  → LIFECYCLE 72h (DISCOVERED→OBSERVING→DEAD→RESOLVED; gaps registered, never faked)
  → SECURITY GATE (veto registry; UNKNOWN≠PASS; fixtures)         [discovery/security_gate.py]
  → FEATURE STORE fs_v0.1 (16 features; leakage L1–L4)            [discovery/feature_store.py]
  → OUTCOMES (7 horizons × 4 classes; no-peeking horizon closure) [discovery/outcomes.py]
  → RANK (rank-first; no numeric score; NO OPPORTUNITY valid)     [discovery/ranker.py]
  → RESEARCH LAB (H1–H13 rejected evidence; H14+ from E-01 data)  [strategy_lab/]
  → TELEGRAM (Persian contract frozen; REAL pending blocker①)     [docs/mission_v1_1/I]
```

## Invariants (enforced by tests/CI)
1. Every persisted row carries provider+timestamps (replayable). 2. Security veto precedes ranking.
3. Deterministic code owns numbers; AI layer is advisory text only (future: AI-PAL, free-tier first).
4. Score weights are lab hypotheses — none ship unvalidated. 5. n8n orchestrates; core logic lives in Python services
   (Execute Command avoided for new flows after R-10). 6. $0/month.
