# AHOS v2 — Evidence-Driven Intelligence Architecture

**Date:** 2026-08-17  
**Version:** `core@2.1.0-evidence`  
**Branch:** `arena/01a0115f-ahos`  
**Status:** EVIDENCE LAYER — unified evidence, gated council, adapter-compatible

This document is the Phase 3 companion to `AHOS_V2_CORE_FOUNDATION.md`. It
specifies the evidence contract that every intelligence decision must satisfy,
how the Cognitive Council is bound to evidence, and how `discovery/` remains
untouched via adapters.

---

## 1. Motivation: from values to evidence

Phase 2 established a pure `core/` with an Evidence anchor:

> source, timestamp, confidence, verification_status, raw_reference

Phase 3 generalises that anchor to the **intelligence atom** that both the
deterministic scorer and the panel lenses consume:

```
source              — provider or subsystem that asserts the fact
value               — the measured / computed payload (price, score, boolean, dict)
timestamp           — epoch seconds UTC of the assertion
confidence          — HIGH | MEDIUM | LOW | UNKNOWN
verification_status — VERIFIED | DERIVED | PENDING | UNVERIFIED | REJECTED | STALE | UNKNOWN
metadata            — free-form audit dict (latency, http_status, raw_reference, kind, …)
```

* `raw_reference` (sha256 hex) is retained verbatim for backward compatibility
  and is mirrored to `metadata["raw_reference"]` so both Phase-2 and Phase-3
  readers round-trip. `value` + `metadata` are now first-class; `raw_reference`
  is the archival pointer, `value` is the measurement, `metadata` is the audit envelope.
* `value=None` is allowed **only** for `UNKNOWN/UNKNOWN` placeholder evidence
  (missing data preserved as `UNKNOWN`, never zero-filled).
* Every `Evidence` is frozen, carries `evidence_id` (uuid4 hex) and
  `provenance_sha256 = sha256(source|timestamp|raw_reference|confidence|status|value)`
  for deterministic deduplication.

Law restated: **no number without evidence, no evidence without provenance,
no council input without eligibility.**

Paper-only, no wallet, no secrets — unchanged and enforced by
`core.governance.safety_rules.SafetyEngine`.

---

## 2. New architecture

### 2.1 Layout (delta from Phase 2)

```
core/
├── models/
│   ├── evidence.py         — Evidence (unified Phase-2 + Phase-3, 6-field + raw_reference compat)
│   │                          + has_required_fields(), is_council_eligible(), describe()
│   ├── token.py            — Token (unchanged, evidence-anchored identity)
│   ├── observation.py      — Observation (unchanged, evidence-anchored snapshot)
│   └── decision.py         — Decision (unchanged, advisory_only=True)
├── events/
│   ├── event_types.py      — Event, EventType, create_event()
│   └── event_bus.py        — EventBus (subscribe/publish, isolation, history, correlation_id)
├── governance/
│   ├── safety_rules.py     — SafetyEngine (paper-only, EVIDENCE_REQUIRED, VERIFICATION_REQUIRED)
│   └── council_evidence.py — ★ NEW: CouncilEvidenceGate, CouncilInput
│                              ingest_candidate, partition, build_context, assert_eligible, audit
└── adapters/
    ├── discovery_adapter.py — discovery row / candidate → Observation (unchanged)
    ├── scoring_adapter.py   — OpportunityScoreReport → Decision (unchanged)
    └── council_adapter.py   — ★ NEW: deliberation_with_evidence(panel, candidate, …)
                               evidence-gated wrapper around CognitivePanel

providers/
└── base_provider.py        — BaseProvider(fetch, health_check, normalize)
                               + ProviderResult, ProviderHealth, validate_contract
                               + fetch_normalized()

tests/
├── test_core_foundation.py     — Evidence / Event / Provider (24 tests, Phase 2)
└── test_council_evidence.py    — ★ NEW: 14 tests (council evidence gate + adapter)

docs/
├── AHOS_V2_CORE_FOUNDATION.md      — Phase 2 foundation (preserved)
└── AHOS_V2_EVIDENCE_ARCHITECTURE.md— this file (Phase 3 evidence layer)
```

No file under `discovery/`, `architecture/`, `paper_trading/`, `telegram_ai/`,
`strategy_lab/`, `research/`, `config/`, `contracts/`, `n8n/` was deleted.

### 2.2 Evidence model (unified)

**Type:** `core.models.evidence.Evidence` (frozen dataclass, 9 stored fields)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `source` | `str` | yes | non-empty, stripped |
| `value` | `Any` | yes (may be `None` for UNKNOWN) | measurement payload |
| `timestamp` | `float` | yes | >0 epoch seconds |
| `confidence` | `str` | yes | `Confidence.ALL` |
| `verification_status` | `str` | yes | `VerificationStatus.ALL` |
| `metadata` | `dict` | yes | may be `{}` |
| `raw_reference` | `str` | yes | sha256 or pointer; empty only if UNKNOWN/UNKNOWN |
| `evidence_id` | `str` | auto | uuid4 hex, 32 chars |
| `provenance_sha256` | `str` | auto | deterministic over 6-field + value |

**Factories:**

```python
from core.models.evidence import Evidence, Confidence, VerificationStatus

ev = Evidence(
    source="dexscreener",
    timestamp=1710000000.0,
    confidence=Confidence.HIGH,
    verification_status=VerificationStatus.VERIFIED,
    raw_reference="a"*64,
    value={"price_usd": 1.25, "liquidity_usd": 50000},
    metadata={"latency_ms": 12, "raw_reference": "a"*64},
)
ev.has_required_fields()   # True  — checks 6-field contract
ev.is_council_eligible()   # True  — VERIFIED/HIGH is eligible
ev.describe()              # "منبع=dexscreener | اعتماد=HIGH | وضعیت=VERIFIED | 2.1h پیش | مقدار={'price_...} | ref=a…"

Evidence.verified(source, timestamp, raw_reference, value, confidence, metadata)
Evidence.unverified(source, timestamp, raw_reference, value, confidence, metadata)
Evidence.unknown(source, timestamp, value=None)  # UNKNOWN/UNKNOWN, value=None
Evidence.from_dict(d) / ev.to_dict()  # round-trips all 9 fields + Phase-2 compat
```

**Verification helpers:**

* `has_required_fields()` — checks the 6-field Phase-3 contract.
* `is_council_eligible()` — `REJECTED` never eligible; `UNKNOWN/UNKNOWN` never eligible; `UNVERIFIED+LOW` not eligible; `VERIFIED/DERIVED/PENDING` + `MEDIUM/HIGH` eligible.

### 2.3 Events & bus (unchanged, evidence-linked)

`core.events.event_types.Event` already carries `evidence_ids: list[str]` and
`correlation_id` so a single pipeline run
`TOKEN_DISCOVERED → OBSERVATION_RECORDED → SCORE_COMPUTED → DECISION_PROPOSED → ALERT_EMITTED`
is traceable. `EventBus` remains in-memory, append-only, handler-error-isolated,
with `subscribe("*", audit_sink)` for evidence audit.

Evidence-linked pattern:

```python
from core.events import create_event, EventType
ev = Evidence(..., value=..., raw_reference=raw_sha)
obs_evt = create_event(EventType.OBSERVATION_RECORDED, aggregate_id=tok.token_id_, payload={"price": 1.5}, evidence_ids=[ev.evidence_id])
```

### 2.4 Provider abstraction (unchanged, evidence-anchored normalize)

`providers.base_provider.BaseProvider` still declares:

```python
def fetch(self, chain="solana", limit=10, **kw) -> ProviderResult: ...
def health_check(self) -> ProviderHealth: ...
def normalize(self, raw) -> list[Observation]: ...  # pure, returns Evidence-anchored Observations
```

`normalize()` **must** anchor every `Observation` to an `Evidence` with the
6-field contract. `validate_contract()` enforces the three methods, `provider_id`,
and return shapes.

### 2.5 Cognitive Council — evidence-gated (new)

**Problem the gate solves:** `CognitivePanel.deliberate(candidate, ctx)` used
to receive raw `candidate.metrics` and raw context dicts. A lens that read
`candidate.metrics.volume_1h` had no way to know whether that number was
`VERIFIED` or `UNVERIFIED+LOW`. Bugs D1–D15 in `AUDIT_FINDINGS.md` were all
of this shape: a value existed, looked legitimate, and was never checked.

**Gate:** `core.governance.council_evidence.CouncilEvidenceGate`

```python
gate = CouncilEvidenceGate(require_verified=False)  # default: blocks REJECTED and UNVERIFIED+LOW
inputs = gate.ingest_candidate(candidate, now=time.time())
# inputs: list[CouncilInput] — each is (name, Evidence(value, source, ts, confidence, verification, metadata))
eligible, ineligible = gate.partition(inputs)
audit = gate.audit(inputs)  # {"total", "eligible", "ineligible", "eligible_names", ...}
ctx = gate.build_context(inputs, score_report=report, exitability=exit)
gate.assert_eligible(ctx)  # raises PermissionError if raw leakage detected
```

Policy:

* `VERIFIED` / `DERIVED` → eligible (any confidence except UNKNOWN)
* `PENDING` + `MEDIUM/HIGH` → eligible
* `UNVERIFIED` + `MEDIUM` → eligible (flagged in audit but not blocked — lean council)
* `UNVERIFIED` + `LOW` → **ineligible** (withheld, lens abstains)
* `REJECTED` / `UNKNOWN/UNKNOWN` → **ineligible**

Raw context values (e.g. `score_report={"opportunity_score":90}`) are wrapped
as `UNVERIFIED+LOW` evidence and therefore **blocked** by default — a lens
receives `None` and ABSTAINs rather than guessing. Callers must pre-wrap
verified reports as proper Evidence to make them eligible.

**Adapter:** `core.adapters.council_adapter.deliberation_with_evidence`

```python
from core.adapters.council_adapter import deliberation_with_evidence
from architecture.knowledge.panel import CognitivePanel

panel = CognitivePanel()
verdict = deliberation_with_evidence(
    panel, candidate,
    score_report=report,       # raw → blocked; Evidence-wrapped report → eligible
    exitability=exitability,
    require_verified=False,
    now=time.time(),
)
verdict.verdict                # APPROVE / CAUTION / VETO / INSUFFICIENT_EVIDENCE
verdict.advisory_only          # always True
verdict.evidence_audit         # {"total", "eligible", "ineligible", ...}
```

The adapter:

1. `ingest_candidate` → per-metric Evidence
2. `build_context` → withholds ineligible, injects only eligible into kwargs for `panel.deliberate`
3. `assert_eligible` defense-in-depth
4. Attaches `evidence_audit` to the returned `PanelVerdict` for observability

No legacy lens was edited; the gate is pure and testable.

---

## 3. Migration path

All steps are additive and reversible (`git revert` drops `core/governance/council_evidence.py` + `core/adapters/council_adapter.py` only).

### 3a — Evidence model upgrade (this commit)

* Extend `Evidence` with `value` while keeping `raw_reference` compat. Old callers
  (`Evidence(source, timestamp, confidence, verification_status, raw_reference)`)
  continue to work because `value` defaults to `None`.
* New callers set `value` explicitly; old `to_dict()` consumers receive the new
  `value` key (explicit `None` is a valid value for UNKNOWN).
* No `discovery/` file changed; `core` remains dependency-free.

**Gate:** `pytest tests/test_core_foundation.py` still 24/24 green (backward compat).

### 3b — Council wiring (this commit, flagged)

* Introduce `CouncilEvidenceGate` + `deliberation_with_evidence` as **opt-in**;
  existing code continues calling `panel.deliberate(candidate, ctx)` directly.
* New code (and tests) call through the adapter; governance can enforce
  `require_verified=True` behind a feature flag when verification coverage is high.
* Audit is non-blocking (`evidence_audit` attached to verdict) so existing
  Telegram rendering is unaffected.

**Gate:** `pytest tests/test_council_evidence.py` 14/14 (raw leakage, honeypot veto, strict mode, advisory guarantee).

### 3c — Provider evidence (next, flagged)

* Each `BaseProvider.normalize()` populates `Evidence(metadata={"raw_reference": sha, "kind": "metric"})` and `value` from the parsed metric. No new provider is added; existing adapters gain a thin wrapper that delegates to `core.models.observation.Observation.from_candidate` which already sets Evidence.
* Verification upstream stays in `discovery/pal.py` / `discovery/security_gate.py`; the gate does not auto-verify, it only withholds.

### 3d — Runtime observability (next, additive)

* A future `core/events/store.py` (not in this phase) can persist `EventBus` history
  to `data/core_events.sqlite` without touching `e01_discovery.sqlite` or
  `paper_trading.sqlite` (separate store, separate triggers). Until then, events remain
  memory-only and SQLite remains source of truth.

Rollback at any point:

```bash
git revert HEAD --no-edit
pytest -q  # 898 legacy green, evidence layer removed
```

---

## 4. Compatibility strategy

| Legacy area | Compatibility | How gate preserves it | Test |
|-------------|---------------|----------------------|------|
| **Evidence callers (Phase 2)** | `Evidence(source, ts, conf, status, raw_ref)` still works (`value=None` default) | New field is additive, old position unchanged; `from_dict` accepts both shapes | `test_core_foundation.py::TestEvidenceCreation` |
| **Observation / Token** | `Observation(token, observed_at, provider, evidence, metrics…)` unchanged | `evidence.value` is ignored by `Observation`; provenance still via `evidence.raw_reference` | `test_core_foundation::TestTokenObservationDecision` |
| **Decision** | `Decision(advisory_only=True)` unchanged | `SafetyEngine` + evidence validation unchanged; `value` not required for advisory | `test_core_foundation::test_decision_advisory_only` |
| **PAL / security gate** | Discovery remains owner of verification; council gate does **not** re-verify | `ingest_candidate` labels metrics `DERIVED` / `VERIFIED` based on provider kind; raw `UNVERIFIED+LOW` is withheld | `test_council_evidence::test_gate_blocks_low_unverified` |
| **CognitivePanel lenses** | 0 lens files edited in `architecture/knowledge/` | Adapter filters kwargs before `deliberate`; lens sees `None` → ABSTAIN (existing behavior, not new logic) | `test_council_evidence::test_council_adapter_never_passes_raw_unverified` |
| **Provider contract** | `BaseProvider(fetch, health_check, normalize)` unchanged | No new required method; evidence anchoring is a property of `normalize`'s return type | `test_core_foundation::TestProviderContractValidation` |
| **Imports** | `core/` never imports `discovery/` at load-time; adapters late-import | `CouncilEvidenceGate.ingest_candidate` reads `candidate.metrics` via `getattr`, not import | `test_architecture_p1::test_lane_isolation_static` (lane isolation) |
| **Storage** | No new table in `data/*.sqlite`; `raw_reference` still the raw payload sha | Evidence `provenance_sha256` still over `(source|ts|raw|conf|status|value)` for dedup | `test_paths_and_cross_platform` |

**Naming:** `providers/` (top-level) vs `architecture/providers/` remain distinct
qualified imports (`from providers.base_provider import …` vs `from architecture.providers.adapters import …`).

**Six-field litmus** — every Evidence, whether created by `Evidence(...)` directly
or by `CouncilEvidenceGate.evidence_for_metric`, satisfies:

```python
assert ev.has_required_fields() is True
assert set(ev.to_dict()) >= {"source", "value", "timestamp", "confidence", "verification_status", "metadata"}
assert ev.is_council_eligible() in (True, False)  # defined for every evidence
```

---

## 5. Evidence First & Paper-Only laws (reinforced)

* **Evidence First** — every council input is `CouncilInput(evidence)`; placeholder is
  `Evidence.unknown()` (explicit null, never `0`). Gate audit is evidence, not claim.
* **Paper-Only** — `SafetyEngine` + `CouncilEvidenceGate` never enable execution;
  `Decision.advisory_only` remains `True`, `deliberation_with_evidence` returns
  `PanelVerdict(advisory_only=True)`, Telegram rendering appends advisory footer.
* **No secrets** — `Evidence.metadata` and `Decision.rationale` are scanned by
  `SafetyEngine._contains_secret_like`; `raw_reference` is a sha, not a payload.
* **Append-only** — `Evidence`/`Token`/`Observation`/`Decision` frozen; `EventBus`
  history append-only; council audit does not mutate evidence.

---

## 6. Quickstart for contributors (evidence layer)

```bash
# Evidence contract
python -c "
from core.models.evidence import Evidence, Confidence, VerificationStatus
ev = Evidence(source='dexscreener', timestamp=1710000000, confidence=Confidence.HIGH,
              verification_status=VerificationStatus.VERIFIED, raw_reference='a'*64,
              value={'price_usd':1.25}, metadata={'latency_ms':10})
print(ev.has_required_fields(), ev.is_council_eligible(), ev.describe())
"

# Council gate — raw unverified is withheld
python -c "
from core.governance.council_evidence import CouncilEvidenceGate
from core.models.evidence import Evidence, Confidence, VerificationStatus
gate = CouncilEvidenceGate()
good = Evidence(source='a', timestamp=1710000000, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference='a'*64, value=1)
bad  = Evidence(source='b', timestamp=1710000000, confidence=Confidence.LOW, verification_status=VerificationStatus.UNVERIFIED, raw_reference='a'*64, value=2)
print(gate.is_eligible(good), gate.is_eligible(bad))
"

# Evidence-gated deliberation
python -c "
from core.adapters.council_adapter import deliberation_with_evidence
from architecture.knowledge.panel import CognitivePanel
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals
panel = CognitivePanel()
cand = NormalizedTokenCandidate(chain='solana', address='So11111111111111111111111111111111111111112', symbol='TEST', name='Test', metrics=MarketMetrics(price_usd=1.5, liquidity_usd=50000), security=SecuritySignals(is_honeypot=False), source_provider='dexscreener', retrieved_ts=1710000000, raw_payload_sha256='a'*64)
print(deliberation_with_evidence(panel, cand, now=1710000000).verdict)
"

# Tests
pytest tests/test_core_foundation.py -q          # 24
pytest tests/test_council_evidence.py -q         # 14
pytest -q                                        # 936 (898 legacy + 38 evidence-driven)
```

---

## 7. Files touched in this commit

```
core/models/evidence.py             — extend with value + has_required_fields/is_council_eligible, compat
core/governance/council_evidence.py — NEW: CouncilEvidenceGate, CouncilInput (evidence-gated council)
core/adapters/council_adapter.py    — NEW: deliberation_with_evidence (adapter, no legacy edit)
tests/test_council_evidence.py      — NEW: 14 tests (evidence 6-field, eligibility, adapter)
docs/AHOS_V2_EVIDENCE_ARCHITECTURE.md — this file
```

No file under `discovery/`, `paper_trading/`, `architecture/`, `telegram_ai/`,
`strategy_lab/`, `research/`, `config/`, `contracts/`, `n8n/` was deleted.
`providers/base_provider.py` required no change (already evidence-anchored).

---

*Evidence First · Gated Council · Adapt, Don't Replace.*
