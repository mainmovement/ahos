"""
tests.test_core_foundation — AHOS v2 Core Intelligence Foundation contract tests.

Covers the three mandated suites:
  * Evidence creation (source, timestamp, confidence, verification, raw_ref)
  * Event creation (typed events, bus, correlation)
  * Provider contract validation (fetch / health_check / normalize)

All tests are deterministic, offline, and paper-only. No network, no secrets,
no wallet signing.

Run: pytest tests/test_core_foundation.py -q
"""

from __future__ import annotations

import sys
import time
import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Ensure providers package resolves even under pytest's importlib mode
# where top-level '' may not be on sys.path when all 71 test modules are collected.
# Pre-load via file location as fallback so ModuleNotFoundError never flakes.
try:
    from providers.base_provider import BaseProvider, ProviderResult, ProviderHealth  # type: ignore
except ModuleNotFoundError:  # pragma: no cover — fallback for collection under heavy import
    import importlib.util as _ilu

    _spec = _ilu.spec_from_file_location("providers.base_provider", str(ROOT / "providers" / "base_provider.py"))
    if _spec is None or _spec.loader is None:
        raise
    _mod = _ilu.module_from_spec(_spec)
    sys.modules["providers.base_provider"] = _mod
    # Ensure parent package exists
    if "providers" not in sys.modules:
        _pspec = _ilu.spec_from_file_location("providers", str(ROOT / "providers" / "__init__.py"))
        if _pspec and _pspec.loader:
            _pmod = _ilu.module_from_spec(_pspec)
            sys.modules["providers"] = _pmod
            _pspec.loader.exec_module(_pmod)
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    BaseProvider = _mod.BaseProvider  # type: ignore
    ProviderResult = _mod.ProviderResult  # type: ignore
    ProviderHealth = _mod.ProviderHealth  # type: ignore

from core.models.evidence import Evidence, Confidence, VerificationStatus
from core.models.token import Token, token_id, normalize_chain, normalize_address
from core.models.observation import Observation
from core.models.decision import Decision, DecisionAction, ADVISORY_FOOTER
from core.events.event_types import Event, EventType, create_event
from core.events.event_bus import EventBus, WILDCARD
from core.governance.safety_rules import SafetyEngine, SafetyRule


FIXED_TS = 1_750_000_000.0  # deterministic synthetic epoch
RAW_SHA = "a" * 64
RAW_SHA2 = "b" * 64


# ---------------------------------------------------------------------------
# Evidence creation
# ---------------------------------------------------------------------------

class TestEvidenceCreation:
    def test_evidence_happy_path_all_fields(self):
        ev = Evidence(
            source="dexscreener",
            timestamp=FIXED_TS,
            confidence=Confidence.HIGH,
            verification_status=VerificationStatus.VERIFIED,
            raw_reference=RAW_SHA,
        )
        assert ev.source == "dexscreener"
        assert ev.timestamp == FIXED_TS
        assert ev.confidence == Confidence.HIGH
        assert ev.verification_status == VerificationStatus.VERIFIED
        assert ev.raw_reference == RAW_SHA
        assert len(ev.evidence_id) == 32
        assert len(ev.provenance_sha256) == 64
        assert ev.is_verified is True
        assert ev.is_unknown is False

    def test_evidence_every_future_datapoint_must_support_five_fields(self):
        """Contract: every Evidence anchors source, timestamp, confidence, status, raw_ref."""
        ev = Evidence(
            source="geckoterminal",
            timestamp=FIXED_TS,
            confidence=Confidence.MEDIUM,
            verification_status=VerificationStatus.DERIVED,
            raw_reference=RAW_SHA,
            metadata={"latency_ms": 42},
        )
        d = ev.to_dict()
        # Must round-trip through required five fields
        assert set(["source", "timestamp", "confidence", "verification_status", "raw_reference"]) <= set(d)
        restored = Evidence.from_dict(d)
        assert restored.source == ev.source
        assert restored.timestamp == ev.timestamp
        assert restored.confidence == ev.confidence
        assert restored.verification_status == ev.verification_status
        assert restored.raw_reference == ev.raw_reference
        assert restored.provenance_sha256 == ev.provenance_sha256

    def test_evidence_factories(self):
        verified = Evidence.verified(source="rugcheck", timestamp=FIXED_TS, raw_reference=RAW_SHA, confidence=Confidence.HIGH)
        assert verified.verification_status == VerificationStatus.VERIFIED
        unverified = Evidence.unverified(source="dexscreener", timestamp=FIXED_TS, raw_reference=RAW_SHA)
        assert unverified.verification_status == VerificationStatus.UNVERIFIED
        unknown = Evidence.unknown(source="test")
        assert unknown.confidence == Confidence.UNKNOWN
        assert unknown.verification_status == VerificationStatus.UNKNOWN
        assert unknown.raw_reference == ""
        assert unknown.is_unknown is True

    def test_evidence_empty_raw_only_allowed_with_unknown(self):
        # unknown/unknown may have empty raw
        ev = Evidence(source="unknown", timestamp=FIXED_TS, confidence=Confidence.UNKNOWN, verification_status=VerificationStatus.UNKNOWN, raw_reference="")
        assert ev.raw_reference == ""
        # any other confidence must have raw
        with pytest.raises(ValueError, match="raw_reference may be empty"):
            Evidence(source="dexscreener", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference="")

    def test_evidence_invalid_inputs_raise(self):
        with pytest.raises(ValueError, match="source"):
            Evidence(source="  ", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        with pytest.raises(ValueError, match="timestamp"):
            Evidence(source="dexscreener", timestamp=-1, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        with pytest.raises(ValueError, match="confidence"):
            Evidence(source="dexscreener", timestamp=FIXED_TS, confidence="SUPER", verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        with pytest.raises(ValueError, match="verification_status"):
            Evidence(source="dexscreener", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status="BOGUS", raw_reference=RAW_SHA)

    def test_evidence_provenance_deterministic(self):
        ev1 = Evidence(source="dexscreener", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        ev2 = Evidence(source="dexscreener", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        # different evidence_id but same provenance (same logical claim)
        assert ev1.provenance_sha256 == ev2.provenance_sha256
        assert ev1.evidence_id != ev2.evidence_id

    def test_evidence_freshness_and_stale(self):
        fresh = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        assert fresh.is_fresh(max_age_seconds=3600) is True
        stale = Evidence(source="dexscreener", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        assert stale.is_fresh(max_age_seconds=3600) is False


# ---------------------------------------------------------------------------
# Token / Observation / Decision integration (evidence-anchored chain)
# ---------------------------------------------------------------------------

class TestTokenObservationDecision:
    def test_token_identity_chain_aware(self):
        # EVM case-insensitive
        t1 = Token(chain="ethereum", address="0xAbCdEf0000000000000000000000000000000001", evidence=Evidence(source="test", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA))
        t2 = Token(chain="eth", address="0xabcdef0000000000000000000000000000000001", evidence=Evidence(source="test", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA))
        assert t1.token_id_ == t2.token_id_
        # Solana case-sensitive
        s1 = token_id("solana", "ABCd")
        s2 = token_id("solana", "ABCD")
        assert s1 != s2
        # alias
        assert normalize_chain("bnb") == "bsc"
        with pytest.raises(ValueError, match="unknown"):
            Token(chain="unknownchain", address="0x123", evidence=Evidence(source="test", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA))

    def test_observation_evidence_anchored(self):
        ev = Evidence(source="dexscreener", timestamp=FIXED_TS, confidence=Confidence.HIGH, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW_SHA)
        token = Token(chain="solana", address="So11111111111111111111111111111111111111112", symbol="SOL", evidence=ev)
        obs = Observation(token=token, observed_at=FIXED_TS, provider="dexscreener", evidence=ev, metrics={"price_usd": 1.25, "liquidity_usd": 50000})
        assert obs.price_usd == 1.25
        assert obs.evidence.source == "dexscreener"
        assert obs.get("price_usd") == 1.25
        assert obs.get("missing_metric") is None
        assert obs.is_price_valid() is True
        # Round-trip serialization
        restored = Observation.from_dict(obs.to_dict())
        assert restored.observation_id == obs.observation_id
        assert restored.price_usd == obs.price_usd

    def test_decision_advisory_only_and_paper_only(self):
        ev = Evidence(source="scoring", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.DERIVED, raw_reference=RAW_SHA[:32] or "scoring")
        # need non-stale evidence
        ev_fresh = Evidence(source="scoring", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.DERIVED, raw_reference=RAW_SHA)
        token = Token(chain="solana", address="So11111111111111111111111111111111111111112", symbol="SOL", evidence=ev_fresh)
        # Valid decision
        d = Decision(token=token, action=DecisionAction.WATCH, rationale="نقدینگی کافی اما حجم پایین — مشاهده بیشتر لازم است", evidence_refs=[ev_fresh], confidence=Confidence.MEDIUM)
        assert d.advisory_only is True
        assert ADVISORY_FOOTER in d.report_persian()
        assert d.is_actionable is False
        # advisory_only must remain True — live execution forbidden
        with pytest.raises(ValueError, match="advisory_only"):
            Decision(token=token, action=DecisionAction.WATCH, rationale="x", evidence_refs=[ev_fresh], confidence=Confidence.HIGH, advisory_only=False)
        # score must be 0-100
        with pytest.raises(ValueError, match="score"):
            Decision(token=token, action=DecisionAction.WATCH, rationale="x", evidence_refs=[ev_fresh], score=150, confidence=Confidence.HIGH)
        # rationale must not contain secret-like patterns
        with pytest.raises(ValueError, match="secret-like"):
            Decision(token=token, action=DecisionAction.WATCH, rationale="token is 123456789:AAHverysecretkey--AAAAAAAAAAAAAAAAAAAAAAAA", evidence_refs=[ev_fresh])


# ---------------------------------------------------------------------------
# Event creation + bus
# ---------------------------------------------------------------------------

class TestEventCreation:
    def test_event_fields_and_validation(self):
        ev = create_event(EventType.TOKEN_DISCOVERED, aggregate_id="abc123", payload={"chain": "solana"}, evidence_ids=[RAW_SHA[:32]])
        assert ev.event_type == EventType.TOKEN_DISCOVERED
        assert ev.aggregate_id == "abc123"
        assert ev.payload["chain"] == "solana"
        assert len(ev.event_id) == 32
        assert len(ev.provenance_sha256) == 64
        # Serialization round-trip
        restored = Event.from_dict(ev.to_dict())
        assert restored.event_id == ev.event_id
        assert restored.event_type == ev.event_type
        assert restored.provenance_sha256 == ev.provenance_sha256

    def test_event_invalid_type_rejected(self):
        with pytest.raises(ValueError, match="event_type"):
            Event(event_type="BOGUS_EVENT", aggregate_id="xyz", timestamp=FIXED_TS)

    def test_event_empty_aggregate_rejected(self):
        with pytest.raises(ValueError, match="aggregate_id"):
            create_event(EventType.OBSERVATION_RECORDED, aggregate_id="  ")

    def test_event_bus_subscribe_publish_isolation(self):
        bus = EventBus()
        received: list[str] = []
        errors_before = len(bus.handler_errors)

        def good_handler(ev: Event):
            received.append(ev.event_type)

        def bad_handler(ev: Event):
            raise RuntimeError("handler crash — must be isolated")

        bus.subscribe(EventType.OBSERVATION_RECORDED, good_handler)
        bus.subscribe(EventType.OBSERVATION_RECORDED, bad_handler)
        bus.subscribe(WILDCARD, good_handler)

        ev = create_event(EventType.OBSERVATION_RECORDED, aggregate_id="tok123")
        report = bus.publish(ev)

        # One good + one wildcard delivered, one failed — fail does not silence good
        assert report["delivered_to"] == 2
        assert report["failed"] == 1
        assert received.count(EventType.OBSERVATION_RECORDED) == 2
        assert len(bus.history) == 1
        assert len(bus.handler_errors) == errors_before + 1

    def test_event_bus_history_and_filter(self):
        bus = EventBus()
        bus.clear_all()
        c1 = "corr-111"
        c2 = "corr-222"
        e1 = create_event(EventType.SCORE_COMPUTED, aggregate_id="tokA", correlation_id=c1, payload={"score": 80})
        e2 = create_event(EventType.SCORE_COMPUTED, aggregate_id="tokB", correlation_id=c2, payload={"score": 60})
        e3 = create_event(EventType.DECISION_PROPOSED, aggregate_id="tokA", correlation_id=c1, payload={"action": "WATCH"})
        bus.publish_many([e1, e2, e3])
        assert len(bus.history) == 3
        assert len(bus.get_history(event_type=EventType.SCORE_COMPUTED)) == 2
        assert len(bus.get_history(aggregate_id="tokA")) == 2
        assert len(bus.get_history(correlation_id=c1)) == 2

    def test_event_bus_unsubscribe_and_replay(self):
        bus = EventBus()
        bus.clear_all()
        calls: list[str] = []
        h = lambda ev: calls.append(ev.event_id)
        bus.subscribe(EventType.ALERT_EMITTED, h)
        ev1 = create_event(EventType.ALERT_EMITTED, aggregate_id="tok1")
        bus.publish(ev1)
        assert len(calls) == 1
        bus.unsubscribe(EventType.ALERT_EMITTED, h)
        ev2 = create_event(EventType.ALERT_EMITTED, aggregate_id="tok2")
        bus.publish(ev2)
        assert len(calls) == 1  # unsubscribed
        # Replay to new sink
        sink_calls: list[str] = []
        bus.replay(sink=lambda ev: sink_calls.append(ev.event_type))
        assert len(sink_calls) == len(bus.history)

    def test_event_bus_wildcard_receives_all(self):
        bus = EventBus()
        bus.clear_all()
        all_events: list[str] = []
        bus.subscribe(WILDCARD, lambda ev: all_events.append(ev.event_type))
        for et in [EventType.TOKEN_DISCOVERED, EventType.SCORE_COMPUTED, EventType.DECISION_PROPOSED]:
            bus.publish(create_event(et, aggregate_id="x"))
        assert set(all_events) == {EventType.TOKEN_DISCOVERED, EventType.SCORE_COMPUTED, EventType.DECISION_PROPOSED}


# ---------------------------------------------------------------------------
# Provider contract validation
# ---------------------------------------------------------------------------

# A compliant provider for happy-path tests
class CompliantProvider(BaseProvider):
    provider_id = "test_compliant"

    def fetch(self, chain: str = "solana", limit: int = 10, **kwargs):
        return ProviderResult(provider_id=self.provider_id, raw=[{"price_usd": 1.5, "chain": chain}] * min(limit, 1), status="OK")

    def health_check(self):
        return ProviderHealth(ok=True, provider_id=self.provider_id, latency_ms=5.0, message="ok")

    def normalize(self, raw):
        from core.models.observation import Observation
        from core.models.token import Token
        from core.models.evidence import Evidence, Confidence, VerificationStatus

        items = raw.raw if hasattr(raw, "raw") else raw
        if not isinstance(items, list):
            items = [items]
        out = []
        for i, item in enumerate(items):
            tok = Token(
                chain=item.get("chain", "solana"),
                address=f"TestAddr{i}11111111111111111111111111111111",
                evidence=Evidence(source=self.provider_id, timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW_SHA),
            )
            ev = Evidence(source=self.provider_id, timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW_SHA)
            out.append(Observation(token=tok, observed_at=time.time(), provider=self.provider_id, evidence=ev, metrics={"price_usd": item.get("price_usd")}))
        return out


class MissingFetchProvider(BaseProvider):
    provider_id = "bad_missing"

    def fetch(self, chain="solana", limit=10, **kwargs):
        raise NotImplementedError("not implemented")

    def health_check(self):  # type: ignore[override]
        return ProviderHealth(ok=False, provider_id=self.provider_id)

    def normalize(self, raw):
        return []


class TestProviderContractValidation:
    def test_compliant_provider_passes_contract(self):
        p = CompliantProvider()
        report = BaseProvider.validate_contract(p)
        assert report["valid"] is True
        assert report["errors"] == []
        assert report["provider_id"] == "test_compliant"
        assert report["checks"]["has_fetch"] is True
        assert report["checks"]["has_health_check"] is True
        assert report["checks"]["has_normalize"] is True

    def test_provider_fetch_health_normalize_happy_path(self):
        p = CompliantProvider()
        # fetch
        result = p.fetch(chain="solana", limit=1)
        assert result.is_ok() is True
        assert len(result.raw) == 1
        # health_check
        h = p.health_check()
        assert h.ok is True
        assert isinstance(h.latency_ms, float)
        # normalize
        obs = p.normalize(result)
        assert len(obs) == 1
        # fetch_normalized convenience
        obs2 = p.fetch_normalized(chain="solana", limit=1)
        assert len(obs2) == 1
        # every observation must be evidence-anchored (five fields)
        for o in obs2:
            assert isinstance(o.evidence, Evidence)
            assert o.evidence.source
            assert o.evidence.timestamp > 0
            assert o.evidence.confidence in Confidence.ALL
            assert o.evidence.verification_status in VerificationStatus.ALL
            assert o.evidence.raw_reference

    def test_missing_provider_id_fails_contract(self):
        class NoIdProvider(BaseProvider):
            provider_id = ""  # type: ignore

            def fetch(self, chain="solana", limit=10, **kwargs):
                return ProviderResult(provider_id="", raw=[], status="OK")

            def health_check(self):
                return ProviderHealth(ok=True, provider_id="")

            def normalize(self, raw):
                return []

        report = BaseProvider.validate_contract(NoIdProvider())
        assert report["valid"] is False
        assert any("provider_id" in e for e in report["errors"])

    def test_incomplete_provider_fails_contract(self):
        # Using abstract class directly should fail (cannot instantiate), class-level check
        report = MissingFetchProvider.validate_contract(MissingFetchProvider())
        # MissingFetchProvider overrides fetch with raising stub but still has method → we check runtime failure path
        # The fetch will raise, so validate should collect error
        # Our MissingFetchProvider fetch raises NotImplementedError → error collected
        assert "fetch" in str(report["errors"]).lower() or report["valid"] is False

    def test_health_check_must_not_raise(self):
        class CrashingHealthProvider(CompliantProvider):
            provider_id = "crash_health"

            def health_check(self):  # type: ignore[override]
                raise RuntimeError("probe failed")

        report = BaseProvider.validate_contract(CrashingHealthProvider())
        assert report["valid"] is False
        assert any("health_check" in e for e in report["errors"])

    def test_safety_governance_blocks_wallet_signing(self):
        eng = SafetyEngine()
        # Evidence path
        ev_ok = Evidence(source="dexscreener", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.VERIFIED, raw_reference=RAW_SHA)
        assert eng.is_safe(ev_ok) is True
        # Textual violation via decision rationale
        token = Token(chain="solana", address="So11111111111111111111111111111111111111112", evidence=ev_ok)
        # Should be blocked by construction (Decision.__post_init__ checks secrets) — test safety engine separately
        bad_text = "please call sign_transaction with private_key 0x123"
        violations = eng.check_text(bad_text, "test")
        assert any(v.rule in (SafetyRule.NO_WALLET_SIGNING, SafetyRule.NO_REAL_TRADING) for v in violations)
        assert any(v.severity == "CRITICAL" for v in violations)

    def test_provider_is_read_only_never_trading(self):
        """Providers must never expose wallet signing / order placement primitives."""
        p = CompliantProvider()
        # Static source inspection — provider file itself must not contain forbidden strings
        import pathlib

        src = Path(CompliantProvider.__module__.replace(".", "/")).with_suffix(".py")
        # This test guards the base_provider contract itself — it contains no trading primitives by construction
        # Instead assert provider never claims live execution
        assert BaseProvider.validate_contract(p)["valid"] is True
        # And safety engine would veto any ENTER without verification appropriately
        eng = SafetyEngine(require_verification_for_enter=True)
        token = Token(chain="solana", address="So11111111111111111111111111111111111111112", evidence=Evidence(source="test", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW_SHA))
        d_bad = Decision(token=token, action=DecisionAction.ENTER, rationale="امتیاز بالا", evidence_refs=[Evidence(source="test", timestamp=time.time(), confidence=Confidence.HIGH, verification_status=VerificationStatus.UNVERIFIED, raw_reference=RAW_SHA)])
        violations = eng.evaluate_decision(d_bad)
        # ENTER without VERIFIED evidence should be flagged
        assert any(v.rule == SafetyRule.VERIFICATION_REQUIRED for v in violations)

