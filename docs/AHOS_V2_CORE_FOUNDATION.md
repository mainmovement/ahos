# AHOS v2 — Core Intelligence Foundation

**Date:** 2026-08-17  
**Version:** `core@2.0.0`  
**Branch:** `arena/01a0115f-ahos`  
**Status:** FOUNDATION — new domain layer introduced, no legacy module deleted

This document describes the new `core/` + `providers/` domain foundation,
its relationship to the existing `discovery/` / `architecture/` / `paper_trading/` /
`telegram_ai/` fleet, and the migration path to a unified AHOS v2 runtime.

---

## 1. Why a core foundation

AHOS grew in lanes:

* **Lane A** (`discovery/`, `paper_trading/`, `research/`) — SQLite-canonical, pre-registered research
* **Lane B** (`architecture/`) — 25 agents, panel, scoring, pipeline, runtime

Both lanes implement the same ideas with different contracts:

* `architecture/providers/contracts.py:NormalizedTokenCandidate` vs `discovery` raw observations
* `architecture/scoring/engine.py:EvidenceItem` vs `architecture/knowledge` lenses vs `discovery` error_state
* Two schedulers, two health surfaces, three paper engines

The v2 foundation does **not** replace any of them. It introduces a
**pure domain layer** that makes the shared concepts explicit and testable
offline:

```
Evidence   — every fact carries (source, timestamp, confidence, verification_status, raw_reference)
Token      — canonical chain:address identity, evidence-anchored
Observation — token + provider + metrics + evidence, frozen, stale-aware
Decision   — advisory (ENTER/WATCH/WAIT/AVOID/REDUCE/EXIT/HOLD), never executes
Event      — append-only domain fact (TOKEN_DISCOVERED, SCORE_COMPUTED, DECISION_PROPOSED …)
EventBus   — in-memory fan-out with handler-error isolation, history, correlation_id
SafetyEngine — paper-only, no-wallet-signing, verification-required gates
BaseProvider — fetch() / health_check() / normalize() contract (+ validate_contract)
```

`core/` has **no I/O, no network, no DB, no trading**. It is a library
that the runtime, discovery, and paper lab import through **adapters** —
never the other way around.  Lane isolation (`tests/test_architecture_p1.py`)
continues to enforce `architecture/*` never importing `discovery/` directly;
`core/` is the neutral vocabulary both sides can map into.

---

## 2. New architecture

### 2.1 Layout

```
core/
├── __init__.py
├── models/
│   ├── evidence.py       — Evidence (frozen) : source, timestamp, confidence,
│   │                         verification_status, raw_reference, provenance_sha256
│   ├── token.py          — Token (frozen) : chain, address, token_id (sha256(chain:addr)[:32]),
│   │                         symbol/name/decimals, first_seen_ts, evidence
│   ├── observation.py    — Observation (frozen) : token, observed_at, provider,
│   │                         metrics{price, liq, vol…}, evidence, observation_id
│   └── decision.py       — Decision (frozen advisory) : token, action, rationale,
│                               evidence_refs[], score?, confidence, risk, advisory_only=True
├── events/
│   ├── event_types.py    — EventType vocabulary + Event (frozen) + create_event()
│   └── event_bus.py      — EventBus : subscribe/publish/unsubscribe, history,
│                               handler-error isolation, wildcard, replay
├── governance/
│   └── safety_rules.py   — SafetyRule, SafetyViolation, SafetyEngine
│                               (PAPER_ONLY, NO_WALLET_SIGNING, EVIDENCE_REQUIRED …)
└── adapters/
    ├── discovery_adapter.py — discovery row / candidate → Observation / Evidence
    └── scoring_adapter.py   — OpportunityScoreReport → Decision

providers/
├── __init__.py
└── base_provider.py      — BaseProvider(ABC) : fetch(chain,limit), health_check(), normalize(raw)
                               + ProviderResult, ProviderHealth, validate_contract()
                               + fetch_normalized() convenience

tests/test_core_foundation.py — 24 tests (Evidence / Event / Provider contracts)
```

Existing modules are **unchanged**:

```
discovery/                — canonical SQLite store, PAL, lifecycle, security gate
paper_trading/            — v1/v2/v3 engines, 34 append-only triggers
architecture/             — scoring, panel, collector, pipeline, runtime, scheduling
telegram_ai/              — Persian NLU + domain service + adapter
strategy_lab/ research/   — pre-registered hypothesis lab
```

### 2.2 Evidence object — the atom of AHOS v2

```python
from core.models.evidence import Evidence, Confidence, VerificationStatus

ev = Evidence(
    source="dexscreener",
    timestamp=1710000000.0,
    confidence=Confidence.HIGH,
    verification_status=VerificationStatus.VERIFIED,
    raw_reference="a"*64,   # sha256 hex of raw_payloads.payload_json
)
# Frozen: ev.evidence_id (uuid4), ev.provenance_sha256 (deterministic)
# Properties: ev.is_verified, ev.age_seconds, ev.is_fresh(3600)
# Factories: Evidence.verified(...), Evidence.unverified(...), Evidence.unknown(...)
```

Rules:

* `source` non-empty. `timestamp` > 0. `confidence` ∈ {HIGH,MEDIUM,LOW,UNKNOWN}.
  `verification_status` ∈ {VERIFIED,DERIVED,PENDING,UNVERIFIED,REJECTED,STALE,UNKNOWN}.
  `raw_reference` non-empty except when both are UNKNOWN (placeholder for missing data).
* `provenance_sha256 = sha256(source|timestamp|raw_ref|confidence|status)` — stable dedup key.
* Missing data is `UNKNOWN`, never `0` or fabricated. `NULL = UNKNOWN`.

Every Token, Observation, and Decision embeds Evidence. Every Event carries
`evidence_ids[]` and a `correlation_id` to trace one pipeline run end-to-end.

### 2.3 Token / Observation / Decision

**Token** — canonical identity without discovery import at load-time.

```python
from core.models.token import Token
tok = Token(chain="solana", address="So111…", symbol="SOL", evidence=ev)
# tok.token_id_ == sha256(chain ":" address_normalized)[:32]
# EVM lowercases address; Solana preserves case — same law as discovery.identity
# tok.from_discovery_row(row), tok.from_candidate(candidate) — adapters
```

**Observation** — point-in-time market snapshot.

```python
from core.models.observation import Observation
obs = Observation(token=tok, observed_at=1710000000.0, provider="dexscreener",
                  evidence=ev, metrics={"price_usd": 1.25, "liquidity_usd": 50000})
# obs.observation_id == sha256(token_id|provider|observed_at|raw_ref)[:32]
# obs.is_stale(4h), obs.price_usd, obs.liquidity_usd, obs.to_dict()
# Observation.from_discovery_row(row, token), Observation.from_candidate(candidate)
```

**Decision** — advisory only.

```python
from core.models.decision import Decision, DecisionAction
d = Decision(token=tok, action=DecisionAction.WATCH,
             rationale="نقدینگی کافی اما حجم پایین", evidence_refs=[ev],
             score=62.0, confidence=Confidence.MEDIUM, risk_level="MED")
# d.advisory_only == True (ValueError if set False — live execution forbidden)
# d.requires_human_review, d.report_persian(), d.to_dict() ends with
# "تصمیم نهایی با کاربر است — این یک توصیهٔ تحلیلی است، نه دستور معامله."
# Secrets in rationale → ValueError (lit the same patterns as architecture.security)
```

### 2.4 Events & bus

```python
from core.events import EventType, create_event, EventBus

bus = EventBus()
bus.subscribe(EventType.TOKEN_DISCOVERED, lambda e: print(e.describe()))
bus.subscribe("*", audit_sink)  # wildcard

ev = create_event(EventType.TOKEN_DISCOVERED, aggregate_id=tok.token_id_,
                  payload={"symbol": "SOL"}, evidence_ids=[ev.evidence_id],
                  correlation_id="run-20260817")
report = bus.publish(ev)  # {delivered_to, failed, errors[]} — failed handlers are isolated
bus.get_history(event_type=EventType.SCORE_COMPUTED, correlation_id="run-20260817")
bus.replay(sink=replay_sink)
```

Events are frozen, append-only, correlation-grouped. The bus is in-memory;
durability stays in existing SQLite tables (`discovery_observations`,
`paper_trading` triggers). Future runtime snapshots can replay the bus into projections.

### 2.5 Governance

```python
from core.governance import SafetyEngine
eng = SafetyEngine(paper_only=True, require_verification_for_enter=True)
# Text lint:
eng.check_text("sign_transaction(private_key)", context="code review")
# → [SafetyViolation(rule=NO_WALLET_SIGNING, severity=CRITICAL)]
# Evidence / Decision / Event:
eng.evaluate_evidence(ev)   # STALE_EVIDENCE is LOW (advisory)
eng.evaluate_decision(d)    # EVIDENCE_REQUIRED, VERIFICATION_REQUIRED for ENTER, HUMAN_REVIEW_REQUIRED
eng.is_safe(obj)            # True iff no CRITICAL/HIGH violations
eng.assert_safe(obj)        # raises PermissionError fail-closed
```

Rules mirror `tests/test_zero_money_invariant.py` (signTransaction, sendRawTransaction,
eth_sendTransaction, create_order, private_key, ccxt/web3 imports) plus
`SECRETS_NOT_IN_CODE` (Telegram token, sk-…, 0x +64 hex).

### 2.6 Provider abstraction

```python
from providers.base_provider import BaseProvider, ProviderResult, ProviderHealth

class MyProvider(BaseProvider):
    provider_id = "my_feed"

    def fetch(self, chain="solana", limit=10, **kw) -> ProviderResult:
        # Return ProviderResult(status=OK|DEGRADED|DOWN|RATE_LIMITED, raw=[...])
        # Never raise on provider failure
        ...

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(ok=True, provider_id=self.provider_id, latency_ms=12.3)

    def normalize(self, raw) -> list[Observation]:
        # Pure mapping raw → list[Observation] (evidence-anchored)
        ...

# Contract lit (used in CI):
report = BaseProvider.validate_contract(MyProvider())
assert report["valid"]  # checks provider_id, signatures, return shapes, trial calls
```

`fetch` and `normalize` are split so `normalize()` can run deterministically
on archived `raw_payloads` without re-fetching — essential for replay, backtests,
and the paper lab. `fetch_normalized()` composes them with a limit cap.

Existing `architecture/providers/*` adapters remain the production implementation;
new `providers/` implementations can delegate to them or be standalone.

---

## 3. Migration path

The foundation is **additive** — zero breaking changes in this commit.

### Phase 2a (this commit) — Foundation, fully additive
* Create `core/` + `providers/` as above.
* Add `core/adapters/*` translators (pure, no store mutation).
* No `discovery/` or `architecture/` file changed (aside from reading via adapters).
* Suite remains 898 → 922 (+24 new core tests, 0 failures).

### Phase 2b — Gradual wiring (next)
1. **Collector** — `architecture/collector/engine.py` and `discovery/collect.py`
   call `providers.base_provider.validate_contract` at boot and emit
   `EventType.PROVIDER_HEALTH_CHANGED` on breaker flips.
2. **Scoring** — `architecture/pipeline/orchestrator.py` post-scoring step
   creates `Observation` → `score_report_to_decision()` → `Event(DECISION_PROPOSED)`
   on the bus, still `WATCH` default (human gates unchanged).
3. **Paper lab** — `paper_trading/engine_v3.py` emits `PAPER_OBSERVATION`
   events from the core path alongside legacy `monitor_event` rows (dual-write).
4. **Telegram** — `telegram_ai/service.py` can render `Decision.report_persian()`
   for the existing `TOP_OPPORTUNITIES` intent behind a flag.

Each step ships **behind a flag** (`AHOS_CORE_ENABLED=0` default) and is
gated by `tests/test_core_foundation.py` + the existing domain suites.

### Phase 2c — Consolidation (later, never destructive)
* Promote `providers.BaseProvider` to the single validated contract;
  existing `architecture/providers/contracts.py:BaseMarketProvider` stays
  as a compatibility shim that adapts into `BaseProvider`.
* Unify health surfaces on `core.governance.SafetyEngine` (single veto path).
* When Evidence coverage of all metrics is validated on live data,
  `discovery/ranker.py` and `architecture/scoring/engine.py` converge on
  `Observation` as the shared snapshot type (ranker still rank-only until the
  E-01 calibration gate — no numeric probability is exposed early).

At no point does `core/` write directly to `e01_discovery.sqlite` or
`paper_trading.sqlite`. Stores remain owned by their discovery / paper modules.

### Rollback

Because no legacy file was deleted or renamed, rolling back is:

```bash
git revert --no-edit HEAD   # drops core/ + providers/ additions
pip install --break-system-packages -r requirements.txt
pytest -q   # 898 passed
```

---

## 4. Compatibility strategy

| Legacy area | Compatibility mechanism | Test guard |
|---|---|---|
| **Discovery rows** | `core.adapters.discovery_adapter.discovery_row_to_observation` + `Token.from_discovery_row` — pure mappers over `discovery_observations` / `tokens` dicts. No import of `discovery` at load-time. | `tests/test_core_foundation.py` + existing `tests/test_discovery.py` unchanged |
| **NormalizedTokenCandidate** | `Token.from_candidate` / `Observation.from_candidate` / `observation.candidate_to_observation` — late local import of typing only. | `tests/test_provider_abstraction.py` still covers `architecture/providers` |
| **Scoring reports** | `core.adapters.scoring_adapter.score_report_to_decision` accepts `OpportunityScoreReport` or plain dict (duck-typed). | `tests/test_opportunity_scoring.py` |
| **PAL / provider registry** | New `providers.BaseProvider` does not replace `discovery.pal.PAL` or `architecture.providers.registry.ProviderRouter`. `fetch/normalize` split is additive. | `tests/test_provider_failure_resilience.py` |
| **Events vs SQLite history** | `core.events.EventBus` is memory-only; durable history remains the existing append-only tables (triggers enforce). A future `core/store.py` (not in this phase) can persist events as a separate `core_events` table without touching those tables. | `tests/test_f1_s1.py` (append-only) |
| **Safety** | `core.governance.SafetyEngine` mirrors `architecture.security` regexes + `tests/test_zero_money_invariant.py` forbidden patterns. Runtime must still pass both. | `tests/test_zero_money_invariant.py` (13 checks) + `tests/test_core_foundation.py::test_safety_*` |
| **Telegram** | `Decision.report_persian()` produces Persian text with `ADVISORY_FOOTER` but does not call `telegram_ai/adapter.py`. `telegram_ai/service.py` can optionally render it — no coupling introduced. | `tests/test_telegram_persian_nlu_matrix.py` |
| **Paper trading** | `core` never writes to `paper_trading` stores. SafetyEngine flags any `fetch` containing `sign_transaction` etc. as CRITICAL. | `tests/test_paper_trading*.py` |

**Naming collisions:**  
* `core/models/evidence.py` vs `architecture/scoring/engine.py:EvidenceItem` — distinct types; adapters map between them explicitly (`scoring_adapter` normalizes RiskItem → dict).  
* `providers/` (top-level) vs `architecture/providers/` — separate packages; imports are qualified (`import providers.base_provider` vs `from architecture.providers.adapters import …`). Both linters keep them distinct.  
* `core/models/token.py:token_id` vs `discovery.identity.token_id` — same law (sha256 chain:addr), re-declared locally so `core` never imports `discovery`. Parity is tested via value-equality on fixtures (solana case-sensitive, EVM lowercased).

---

## 5. Evidence First & Paper-Only laws (unchanged, reinforced)

* **Evidence First** — every core object carries Evidence. Placeholder helpers
  (`Evidence.unknown()`, `Observation` with empty metrics → None) preserve
  UNKNOWN discipline. No adapter invents a value.
* **Paper-Only** — `SafetyEngine.paper_only = True` by default; any
  `Decision` with `advisory_only=False` is rejected at construction.
  `SafetyEngine.check_text` vetos wallet-signing / live-order strings as
  `CRITICAL`. No `ccxt`, `web3`, `solana`, signing SDK is imported anywhere
  in `core/` or `providers/`.
* **No secrets** — `Decision.__post_init__` + `SafetyEngine` + `Evidence.metadata`
  are scanned against Telegram-token / `sk-` / `0x`-64 patterns. `REPORT`/spec
  files are not logged beyond sha transforms.
* **Append-only** — `EventBus` history never shrinks except via explicit
  `clear_all()` (test reset). `Evidence` / `Token` / `Observation` / `Decision`
  are frozen dataclasses (immutable).

---

## 6. Quickstart for contributors

```bash
# Core only — offline, no network, no DB setup needed
python -m pytest tests/test_core_foundation.py -q          # 24 passed
python -c "from core.models.evidence import Evidence; print(Evidence.unknown().describe())"

# Validate a provider
python -c "
from providers.base_provider import BaseProvider
from providers.my_provider import MyProvider
print(BaseProvider.validate_contract(MyProvider()))
"

# Full suite — core must not regress any existing domain test
pytest -q                                                   # 898 legacy + 24 core
```

---

## 7. Files introduced in this commit

```
core/__init__.py
core/models/__init__.py
core/models/evidence.py          — Evidence atom
core/models/token.py             — Token identity (evidence-anchored)
core/models/observation.py       — Observation snapshot
core/models/decision.py          — Advisory Decision (paper-only)
core/events/__init__.py
core/events/event_types.py       — Event + EventType
core/events/event_bus.py         — EventBus
core/governance/__init__.py
core/governance/safety_rules.py  — SafetyEngine
core/adapters/__init__.py
core/adapters/discovery_adapter.py
core/adapters/scoring_adapter.py
providers/__init__.py
providers/base_provider.py       — BaseProvider + validate_contract
tests/test_core_foundation.py    — 24 tests
docs/AHOS_V2_CORE_FOUNDATION.md  — this file
```

No file under `discovery/`, `architecture/`, `paper_trading/`, `telegram_ai/`,
`strategy_lab/`, `research/`, `config/`, `contracts/`, or `n8n/` was modified.

---

*Evidence First · Paper-Only · Adapt, Don't Replace.*
