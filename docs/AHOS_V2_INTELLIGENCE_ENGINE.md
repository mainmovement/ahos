# AHOS v2 — Intelligence Engine Foundation

**Date:** 2026-08-17  
**Version:** `intelligence@2.0.0`  
**Branch:** `arena/01a0115f-ahos`  
**Status:** INTELLIGENCE LAYER — Feature Registry, Scoring v2, Risk Engine, Explanations

This document specifies the Intelligence Engine built **on top of** the Evidence Architecture (`core/` + `providers/`). All functions are evidence-only, deterministic, and advisory. No trading execution, no wallet signing.

---

## 1. Architecture Overview

```
core/                          ← unified evidence atom (source,value,timestamp,confidence,verification,metadata)
providers/                     ← fetch / health_check / normalize → Evidence-anchored Observations
intelligence/                  ← ★ NEW: intelligence on evidence
├── features/
│   └── registry.py            FeatureRegistry, FeatureDefinition (name, description, source_evidence, calculation_method, version)
├── scoring/
│   └── engine.py              OpportunityScoringEngineV2 (Evidence → sub-scores → Decision-compatible)
├── risk/
│   ├── base.py                RiskAnalyzer (interface), RiskResult, RiskLevel
│   ├── contract_risk.py       ContractRiskAnalyzer (honeypot, mint/freeze, unverified)
│   ├── liquidity_risk.py      LiquidityRiskAnalyzer (liq < $500 CRITICAL, FDV/liq dilution)
│   ├── concentration_risk.py  ConcentrationRiskAnalyzer (top10_share, holders_count)
│   ├── manipulation_risk.py   ManipulationRiskAnalyzer (wash: volume vs txn divergence, buys_ratio)
│   └── engine.py              RiskEngine (aggregate 4 analyzers → aggregate_score/level)
└── explanations/
    └── generator.py           ExplanationGenerator (ScoreResult + RiskEngineResult → Persian text)

docs/AHOS_V2_INTELLIGENCE_ENGINE.md — this file
tests/test_intelligence_engine.py  — 25 tests (scoring, risk, explanation, registry)
```

**Law:** Intelligence never reads raw `NormalizedTokenCandidate` fields directly; it reads `Evidence.value` via `evidence_map: dict[str, Evidence]`. Missing evidence → low confidence / `UNKNOWN`, never fabricated.

```
discovery/ + architecture/*  (legacy, untouched)
        ↓ adapters (pure mappers)
core (Evidence atom)  →  providers.normalize() → Observation(Evidence)
        ↓
intelligence.features  (registry, versioned descriptors)
        ↓
intelligence.scoring   (evidence-only weighted blend minus risk)
        ↓
intelligence.risk      (4 analyzers, evidence-only)
        ↓
intelligence.explanations (Persian, evidence-cited, advisory footer)
        ↓
core Decision (advisory_only=True) → telegram_ai (rendering) / paper_trading (paper)
```

---

## 2. Feature Registry

### 2.1 Contract

Every feature **must** contain (enforced at construction + registry):

| Field | Type | Rule |
|-------|------|------|
| `name` | `str` | snake_case `^[a-z][a-z0-9_]{2,49}$` |
| `description` | `str` | human purpose, ≥10 chars |
| `source_evidence` | `str` | descriptor of required Evidence source(s), e.g. `"dexscreener:price_usd, security_gate:is_honeypot"` |
| `calculation_method` | `str` | identifier like `relative_change`, `log_ratio`, `threshold_check`, `concentration_ratio` |
| `version` | `str` | semver `X.Y.Z` — bump on formula change, immutable per `(name, version)` |
| `calculation_callable` | `Callable` optional | pure `(Evidence | list[Evidence] | dict) -> value`, not serialized |
| `category` | `str` | `market | security | liquidity | whale | social | risk` |
| `metadata` | `dict` | unit, range, thresholds, etc. |

`FeatureDefinition` is frozen; `provenance = sha256(name|description|source_evidence|method|version|category)[:16]` for audit.

`FeatureRegistry` is append-only keyed by `name@version`:

```python
from intelligence.features import FeatureRegistry, FeatureDefinition

reg = FeatureRegistry()
f = FeatureDefinition(
    name="liquidity_depth",
    description="Liquidity depth relative to pool reserves, derived from liquidity_usd evidence.",
    source_evidence="dexscreener:liquidity_usd, geckoterminal:reserve_in_usd",
    calculation_method="log_ratio",
    version="1.0.0",
    category="liquidity",
)
reg.register(f)
reg.get("liquidity_depth")          # latest
reg.get("liquidity_depth", "1.0.0") # pinned
reg.list(category="security")
reg.validate_all()  # [] = valid
```

Global singleton `get_global_registry()` pre-registers 6 genesis features (market_momentum, liquidity_depth, security_verdict, whale_concentration, social_velocity, risk_aggregate) covering all scoring dimensions.

### 2.2 Versioning law

`(name, version)` is unique and immutable. Changing a formula → new `version`; threshold tuning alone does **not** bump. `FeatureRegistry.register` raises on duplicate, never overwrites. `provenance()` over all features gives a deterministic digest for CI (`tests/test_paths_and_cross_platform`-style).

---

## 3. Opportunity Scoring Engine v2

### 3.1 Contract

* **Input:** `Evidence` objects only (`evidence_map: dict[str, Evidence]` or `list[Evidence]`). Raw dicts/values → `ValueError`.
* **Output:** `ScoreResult` (frozen) + `Decision`-compatible via `to_decision(token, evidence_objs)`.

Required sub-scores (0-100, deterministic):

```
market_score     — price momentum (price_change_6h 5-80% + volume_24h tiers)
security_score   — honeypot→0, mint/freeze -30, unverified -20, locked <50% -15
liquidity_score  — liquidity_usd tiers (100k→85, 50k→70, 10k→50, 2k→30) minus FDV/liq >400× (-40) / >120× (-20)
whale_score      — top10_share (>80→20, >70→40, >50→40, >30→65, ≤30→85); unknown→50 neutral
social_score     — narrative_score / volume_acceleration (5×→70, 3×→60, >10× capped 65)
risk_penalty     — 0-100, max of security inverse + thin liquidity + concentration
confidence       — derived from evidence confidences (HIGH ≥60% HIGH, else LOW if ≥50% LOW, else MEDIUM; UNKNOWN if no evidence)
total_score      — weighted blend (market 25%, security 25%, liquidity 20%, whale 15%, social 15%) minus risk_deduction (risk_penalty/100 * 50), clamped 0-100
```

### 3.2 Usage

```python
from core.models.evidence import Evidence, Confidence, VerificationStatus
from intelligence.scoring import OpportunityScoringEngineV2

engine = OpportunityScoringEngineV2()
m = {
    "price_change_6h": Evidence(source="dexscreener", timestamp=ts, confidence=Confidence.HIGH, verification_status=VerificationStatus.DERIVED, raw_reference=sha, value=20, metadata={}),
    "volume_24h": Evidence(source="dexscreener", timestamp=ts, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=sha, value=60000, metadata={}),
    "liquidity_usd": Evidence(source="dexscreener", timestamp=ts, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=sha, value=80000, metadata={}),
    "is_honeypot": Evidence(source="security_gate", timestamp=ts, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=sha, value=False, metadata={}),
}
res = engine.score_from_map(m)                 # or engine.score(evidence_list)
res.market_score, res.security_score, res.liquidity_score, res.whale_score, res.social_score, res.risk_penalty, res.confidence, res.total_score
res.breakdown  # {market_score, security_score, ..., risk_deduction, blended, total_score}
res.provenance # deterministic digest

# Decision-compatible
from core.models.token import Token
decision = res.to_decision({"chain": "solana", "address": "So111…"}, evidence_objs=list(m.values()))
assert decision.advisory_only is True
```

*Empty / unknown evidence* → `confidence=UNKNOWN`, `total_score=0`, `missing_count` tallied, breakdown notes `"no evidence"` — never fabricated.

Deterministic: same evidence map + same `now` → same `total_score` and `provenance`.

### 3.3 Decision mapping

| Condition | `Decision.action` |
|-----------|-------------------|
| `confidence==UNKNOWN` or `evidence_count==0` | `INSUFFICIENT_EVIDENCE` |
| `risk_penalty ≥70` | `AVOID` |
| `total_score ≥70` and `confidence==HIGH` and `risk_penalty<30` | `WATCH` (ENTER requires human confirmation; engine never emits `ENTER` directly) |
| `total_score ≥50` | `WATCH` |
| otherwise | `WAIT` |

Risk level for `Decision.risk_level` derived from `risk_penalty`.

---

## 4. Risk Engine

### 4.1 Interface

`intelligence.risk.base.RiskAnalyzer` (ABC, evidence-only):

```python
class RiskAnalyzer(ABC):
    analyzer_id: str
    def analyze(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> RiskResult: ...
```

`RiskResult(analyzer, level, score, reasons, evidence_refs, metadata, computed_at)` frozen, `level ∈ {LOW,MEDIUM,HIGH,CRITICAL,UNKNOWN}`, `score 0-100`.

All analyzers **reject raw values** — `for k,v in evidence_map.items(): if not isinstance(v, Evidence): raise TypeError`.

### 4.2 Four foundation analyzers

* **ContractRiskAnalyzer** (`contract_risk`) — inputs `is_honeypot`, `has_mint_authority`, `has_freeze_authority`, `contract_verified`
  * `is_honeypot True → CRITICAL 100` (honeypot Persian reason)
  * `mint True` or `freeze True → HIGH 70`
  * `verified False → MEDIUM 50`
  * clean → `LOW 10`

* **LiquidityRiskAnalyzer** (`liquidity_risk`) — `liquidity_usd`, `fdv_usd`
  * `<$500 → CRITICAL 95`, `<$2k → HIGH 80`, `<$10k → MEDIUM 50`, `<$50k → MEDIUM 30`, `≥$50k → LOW 15`; `None → UNKNOWN 50`
  * `FDV/liq >400× → score max 70, level HIGH` (dilution)

* **ConcentrationRiskAnalyzer** (`concentration_risk`) — `top10_share` (0-100 or 0-1), `holders_count`
  * `>80 → CRITICAL 90`, `>70 → HIGH 75`, `>50 → MEDIUM 50`, `>30 → MEDIUM 30`, `≤30 → LOW 15`; `None → UNKNOWN 40`; holders <20 adds `max 60`

* **ManipulationRiskAnalyzer** (`manipulation_risk`) — `volume_acceleration`, `txn_acceleration`, `buys_ratio`, `narrative_score`
  * `vol/txn divergence ≥4 and vol≥5 → HIGH 75` (wash)
  * `buys_ratio ≥0.97 → HIGH 70` (coordinated)
  * no relevant evidence → `UNKNOWN 30`

### 4.3 Aggregate engine

`RiskEngine(analyzers=[4 defaults])`

```python
engine = RiskEngine()
result = engine.assess(evidence_map)
# result.aggregate_score: max valid score, floor 75 if any CRITICAL
# result.aggregate_level: max hierarchy CRITICAL>HIGH>MEDIUM>LOW>UNKNOWN
# result.highest_reasons: top 2 analyzers × 2 reasons
# result.evidence_refs: deduped evidence_ids
result.to_dict()
engine.is_safe(result)  # True iff not CRITICAL/HIGH
```

Isolation: one analyzer exception → `UNKNOWN 50` with error reason, never crashes pipeline.

---

## 5. Explanation Generator

`intelligence.explanations.generator.ExplanationGenerator`

```python
gen = ExplanationGenerator()
exp = gen.generate(score_result, risk_result, evidence_audit={"total":7, "eligible":6})
exp.brief  # "امتیاز 53 (HIGH) — ریسک LOW — بازار: 85/100"
exp.text   # full Persian block with sections:
           # 🟢 امتیاز 53/100 — اعتماد HIGH — ریسک LOW
           # چرا این امتیاز: • بازار: 85 … (5 bullets)
           # ریسک‌ها: • توزیع مناسب: 25.0% …
           # شواهد: • ارجاع شواهد: a1b2c3d4 …
           # ابطال/گام بعد: • پایش نقدینگی …
           # تصمیم نهایی با کاربر است — …
exp.bullets  # {"why":[...], "risks":[...], "evidence":[...], "invalidation":[...]}
exp.evidence_citations  # evidence_ids cited (max 8)
exp.confidence, exp.score, exp.risk_level
```

Deterministic: same inputs + same `now` → same `text`. No LLM, Persian-first, evidence-cited, advisory footer always present.

---

## 6. Evidence-only enforcement

* Scoring: `score(list[Evidence])` and `score_from_map(dict[str, Evidence])` both validate `isinstance(ev, Evidence)` → `ValueError` on raw.
* Risk: each analyzer validates `isinstance(v, Evidence)` → `TypeError` on raw.
* FeatureRegistry: `source_evidence` is a string descriptor referencing `Evidence.source`, not a raw data read.
* Explanation: consumes `ScoreResult`/`RiskResult` (which themselves are derived from Evidence) — never raw.

CI litmus: `tests/test_zero_money_invariant.py` still 13 checks green; no `import ccxt`, `web3`, `signTransaction`, `private_key`, `mnemonic` in `intelligence/` (verified via `grep -R`).

---

## 7. Compatibility & Migration

### Compatibility (no legacy file deleted)

| Legacy area | How intelligence preserves it |
|-------------|-------------------------------|
| `architecture/scoring/engine.py` (8-stage) | Remains canonical for paper pipeline; `intelligence.scoring` is a **new v2** alongside it. Adapters can translate `OpportunityScoreReport → evidence_map` for comparison, but production still uses architecture scoring until v2 is validated. |
| `discovery/` | Not imported. Intelligence reads via `core` Evidence (produced by `providers.normalize()` or `discovery_adapter`). |
| `paper_trading/` | Not touched. Intelligence produces `Decision` (advisory) that paper lab may consume as signal, never as order. |
| `core/` + `providers/` | Intelligence imports `Evidence` and `Token` only. Evidence contract (6-field) is reused; no new Evidence type. |

### Migration path

1. **Phase 4a (this commit)** — Foundation only: registry, scoring v2, 4 risk analyzers, explanation generator, tests, this doc. No wiring into `architecture/pipeline/orchestrator.py` yet.
2. **Phase 4b (next, flagged)** — Wire `intelligence.scoring` behind `AHOS_INTELLIGENCE_ENABLED` flag in pipeline (parallel score, compare with architecture score, emit `Evidence` for both). Risk engine runs in shadow.
3. **Phase 4c (later)** — When v2 scores are validated on E-01 cohorts (≥200 horizons), promote `intelligence.scoring` as primary, keep architecture scoring as fallback, and route `intelligence.explanations` to `telegram_ai` rendering.

Rollback: `git revert HEAD --no-edit` drops `intelligence/` only, 0 legacy deletions.

---

## 8. Quickstart

```bash
# Feature registry
python -c "
from intelligence.features import get_global_registry
print(get_global_registry().count(), get_global_registry().list_names()[:3])
"

# Scoring (evidence-only)
python -c "
from core.models.evidence import Evidence, Confidence, VerificationStatus
from intelligence.scoring import OpportunityScoringEngineV2
engine = OpportunityScoringEngineV2()
ev = lambda k,v: Evidence(source='test', timestamp=1710000000, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference='a'*64, value=v, metadata={})
res = engine.score_from_map({'price_change_6h':ev('price',20), 'volume_24h':ev('vol',60000), 'liquidity_usd':ev('liq',80000), 'is_honeypot':ev('honey',False)})
print(res.total_score, res.confidence)
"

# Risk
python -c "
from core.models.evidence import Evidence, Confidence, VerificationStatus
from intelligence.risk import RiskEngine
ev = lambda v: Evidence(source='s', timestamp=1710000000, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference='a'*64, value=v, metadata={})
print(RiskEngine().assess({'is_honeypot':ev(False), 'liquidity_usd':ev(50000)}).aggregate_level)
"

# Explanation
python -c "
from intelligence.explanations import ExplanationGenerator
from intelligence.scoring import OpportunityScoringEngineV2
from intelligence.risk import RiskEngine
from core.models.evidence import Evidence, Confidence, VerificationStatus
ev = lambda v: Evidence(source='s', timestamp=1710000000, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference='a'*64, value=v, metadata={})
res = OpportunityScoringEngineV2().score_from_map({'price_change_6h':ev(10), 'liquidity_usd':ev(50000)})
print(ExplanationGenerator().generate(res, RiskEngine().assess({'liquidity_usd':ev(50000)})).brief)
"

# Tests
pytest tests/test_intelligence_engine.py -q          # 25
pytest -q                                            # 961 (936 + 25)
```

---

## 9. Files touched in this commit

```
intelligence/__init__.py
intelligence/features/__init__.py
intelligence/features/registry.py         — FeatureDefinition + FeatureRegistry + genesis 6
intelligence/scoring/__init__.py
intelligence/scoring/engine.py            — OpportunityScoringEngineV2 + ScoreResult
intelligence/risk/__init__.py
intelligence/risk/base.py                 — RiskAnalyzer, RiskResult, RiskLevel
intelligence/risk/contract_risk.py        — ContractRiskAnalyzer
intelligence/risk/liquidity_risk.py       — LiquidityRiskAnalyzer
intelligence/risk/concentration_risk.py   — ConcentrationRiskAnalyzer
intelligence/risk/manipulation_risk.py    — ManipulationRiskAnalyzer
intelligence/risk/engine.py               — RiskEngine (aggregate)
intelligence/explanations/__init__.py
intelligence/explanations/generator.py    — ExplanationGenerator + Explanation
tests/test_intelligence_engine.py         — 25 tests (registry, scoring, risk, explanation)
docs/AHOS_V2_INTELLIGENCE_ENGINE.md       — this file
```

No file under `discovery/`, `architecture/`, `core/`, `providers/`, `paper_trading/`, `telegram_ai/`, `research/`, `config/`, `contracts/` was deleted.

---

*Evidence Only · Explainable · Advisory.*
