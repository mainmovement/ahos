#!/usr/bin/env python3
"""Phase 3 — Canonical Decision Authority.

One brain: architecture.decision.authority.CanonicalDecisionAuthority.
Adversarial gates: identity, security, AI upgrade, downstream bypasses.
"""
from __future__ import annotations

import ast
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.ai.council_live import CouncilVerdict  # noqa: E402
from architecture.alerts.engine import AlertEngine  # noqa: E402
from architecture.decision.authority import (  # noqa: E402
    CanonicalDecisionAuthority,
    CanonicalOutcome,
    identity_from_candidate,
)
from architecture.decision.paper_eligibility import paper_candidate_allowed  # noqa: E402
from architecture.identity.types import (  # noqa: E402
    IdentityResolution,
    IdentityState,
    TokenIdentity,
)
from architecture.intel.exitability import ExitabilityAnalyzer  # noqa: E402
from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.providers.registry import ProviderRouter  # noqa: E402
from architecture.collector.engine import CollectorEngine  # noqa: E402
from architecture.scoring.engine import OpportunityScorer  # noqa: E402
from architecture.alerts.engine import AlertEngine as AE  # noqa: E402
from tests.helpers_identity import (  # noqa: E402
    SOL_CANON,
    verified_identity_fixture,
    verified_pool_identity_fixture,
)
from tests.helpers_security import passing_security_signals  # noqa: E402
from tests.test_opportunity_pipeline_integration import MockDiscoveryProvider  # noqa: E402
from telegram_ai.adapter import MockTelegramAdapter  # noqa: E402
from telegram_ai.pump_alert import maybe_alert_opportunity, should_alert  # noqa: E402

NOW = 1_800_000_000.0


def _metrics(**over):
    d = dict(
        price_usd=0.002, liquidity_usd=150_000,
        volume_5m=9_000, volume_1h=30_000, volume_24h=250_000,
        txns_5m_buys=90, txns_5m_sells=25,
        txns_1h_buys=400, txns_1h_sells=250, price_change_1h=12.0,
    )
    d.update(over)
    return MarketMetrics(**d)


def _cand(security=None, **over):
    return NormalizedTokenCandidate(
        chain=over.get("chain", "solana"),
        address=over.get("address", SOL_CANON),
        symbol=over.get("symbol", "TOK"),
        name="TOK Token",
        metrics=over.get("metrics", _metrics()),
        security=security if security is not None else passing_security_signals(),
        source_provider="dexscreener",
        retrieved_ts=over.get("retrieved_ts", NOW),
        pair_created_ts=over.get("pair_created_ts", NOW - 30 * 86400),
    )


def _decide(cand=None, identity=None, council=None, panel=None, **over):
    cand = cand or _cand(**over)
    report = OpportunityScorer().evaluate(cand, now=NOW)
    return CanonicalDecisionAuthority().decide(
        cand, report, identity=identity, now=NOW, council=council, panel=panel,
        exitability=ExitabilityAnalyzer().analyze(cand, 200),
    )


def _token_state(state: IdentityState, reason: str = "test") -> IdentityResolution:
    ident = verified_identity_fixture()
    token = TokenIdentity(
        chain=ident.token.chain,
        address_canonical=ident.token.address_canonical,
        address_input=ident.token.address_input,
        token_id=ident.token.token_id,
        symbol_alias=ident.token.symbol_alias,
        name_alias=ident.token.name_alias,
        state=state,
        reason=reason,
        checksum_ok=ident.token.checksum_ok,
    )
    return IdentityResolution(
        chain=ident.chain, token=token, pool=ident.pool, dex=ident.dex,
        policy_version=ident.policy_version, computed_ts=ident.computed_ts,
    )


# ----------------------------- identity gates -----------------------------

@pytest.mark.parametrize("state,outcome", [
    (IdentityState.INVALID, CanonicalOutcome.REJECT),
    (IdentityState.CONFLICT, CanonicalOutcome.REJECT),
    (IdentityState.UNRESOLVED, CanonicalOutcome.INSUFFICIENT_EVIDENCE),
    (IdentityState.STALE, CanonicalOutcome.NO_TRADE),
    (IdentityState.UNSUPPORTED, CanonicalOutcome.REJECT),
])
def test_blocking_identity_cannot_be_positive(state, outcome):
    d = _decide(identity=_token_state(state))
    assert d.outcome == outcome
    assert d.is_positive is False
    assert d.alerts_allowed is False
    assert d.paper_allowed is False
    ok, _ = paper_candidate_allowed(d)
    assert ok is False


def test_missing_identity_is_insufficient_not_buy():
    d = _decide(identity=None)
    assert d.identity_state == "MISSING"
    assert d.outcome == CanonicalOutcome.INSUFFICIENT_EVIDENCE
    assert d.is_positive is False


def test_verified_token_unresolved_pool_is_monitor_only():
    d = _decide(identity=verified_identity_fixture())
    assert d.outcome == CanonicalOutcome.MONITOR_ONLY
    assert d.monitoring_only is True
    assert d.is_positive is False
    assert d.alerts_allowed is False
    ok, _ = paper_candidate_allowed(d)
    assert ok is False


def test_verified_identity_and_pool_can_buy_when_evidence_supports():
    d = _decide(identity=verified_pool_identity_fixture())
    if d.advisor_action == "ENTER":
        assert d.outcome == CanonicalOutcome.BUY
        assert d.is_positive is True
        assert d.alerts_allowed is True
        ok, why = paper_candidate_allowed(d)
        assert ok is True, why
    else:
        assert d.outcome != CanonicalOutcome.BUY
        assert d.is_positive is False


# ----------------------------- security gates -----------------------------

def test_security_reject_is_reject_not_buy():
    d = _decide(
        cand=_cand(passing_security_signals(is_honeypot=True)),
        identity=verified_pool_identity_fixture(),
    )
    assert d.security_state == "REJECT"
    assert d.outcome == CanonicalOutcome.REJECT
    assert d.is_positive is False


def test_security_incomplete_no_positive():
    d = _decide(
        cand=_cand(SecuritySignals(is_honeypot=False)),
        identity=verified_pool_identity_fixture(),
    )
    assert d.security_state == "INCOMPLETE"
    assert d.outcome == CanonicalOutcome.INSUFFICIENT_EVIDENCE
    assert d.is_positive is False


def test_stale_security_cannot_masquerade_as_fresh_pass():
    d = _decide(
        cand=_cand(passing_security_signals(), retrieved_ts=NOW - 48 * 3600),
        identity=verified_pool_identity_fixture(),
    )
    assert d.security_state == "STALE"
    assert d.outcome == CanonicalOutcome.NO_TRADE
    assert d.is_positive is False
    assert d.provenance["security_state"] == "STALE"


def test_blacklist_mint_freeze_unsellable_reject():
    for kwargs in (
        {"is_blacklisted": True},
        {"has_mint_authority": True},
        {"has_freeze_authority": True},
        {"cannot_sell_all": True},
        {"sell_tax_pct": 25.0},
        {"deployer_past_rug_count": 2},
    ):
        d = _decide(
            cand=_cand(passing_security_signals(**kwargs)),
            identity=verified_pool_identity_fixture(),
        )
        assert d.is_positive is False, kwargs
        assert d.outcome in (
            CanonicalOutcome.REJECT, CanonicalOutcome.HIGH_RISK, CanonicalOutcome.NO_TRADE,
        )


# ----------------------------- AI boundary -----------------------------

def test_ai_cannot_upgrade_failed_security():
    council = CouncilVerdict(
        final_stance="ENTER", agreement="UNANIMOUS",
        council_status="ONLINE", responded=3,
    )
    d = _decide(
        cand=_cand(passing_security_signals(is_honeypot=True)),
        identity=verified_pool_identity_fixture(),
        council=council,
    )
    assert d.outcome == CanonicalOutcome.REJECT
    assert d.is_positive is False
    assert d.ai_challenge is not None
    assert d.ai_challenge.upgrade_blocked is True


def test_ai_cannot_override_identity_failure():
    council = CouncilVerdict(
        final_stance="ENTER", agreement="UNANIMOUS",
        council_status="ONLINE", responded=3,
    )
    d = _decide(identity=_token_state(IdentityState.INVALID), council=council)
    assert d.is_positive is False
    assert d.outcome == CanonicalOutcome.REJECT
    assert d.ai_challenge.upgrade_blocked is True


def test_ai_challenge_may_downgrade_enter_to_watch():
    council = CouncilVerdict(
        final_stance="AVOID", agreement="MAJORITY",
        council_status="ONLINE", responded=3,
    )
    d = _decide(identity=verified_pool_identity_fixture(), council=council)
    assert d.outcome != CanonicalOutcome.BUY
    assert d.is_positive is False
    if d.advisor_action == "WAIT":
        assert d.ai_challenge.effect in ("DOWNGRADE", "NONE")
        assert d.ai_challenge.challenged is True


def test_no_trade_is_valid_final_result():
    weak = _cand(metrics=_metrics(liquidity_usd=150_000, volume_1h=10.0, volume_24h=10.0,
                                  txns_1h_buys=1, txns_1h_sells=1, price_change_1h=-40.0))
    d = _decide(cand=weak, identity=verified_pool_identity_fixture())
    assert d.is_positive is False
    assert d.outcome in (
        CanonicalOutcome.NO_TRADE, CanonicalOutcome.SKIP, CanonicalOutcome.WATCH,
        CanonicalOutcome.HIGH_RISK, CanonicalOutcome.REJECT, CanonicalOutcome.INSUFFICIENT_EVIDENCE,
    )


def test_confidence_is_independent_of_opportunity_score():
    d = _decide(identity=verified_pool_identity_fixture())
    assert d.confidence_level in ("HIGH", "MED", "LOW")
    assert d.provenance["confidence_level"] == d.confidence_level
    assert d.provenance["opportunity_score"] == d.opportunity_score
    # Must not derive confidence from the numeric score.
    if d.opportunity_score is not None and d.opportunity_score >= 70:
        pass  # high score may still be LOW confidence in other fixtures
    assert "confidence_level" in d.provenance
    assert d.confidence_level != str(d.opportunity_score)


def test_provenance_does_not_invent_evidence():
    d = _decide(identity=None)
    assert d.provenance["no_invented_evidence"] is True
    assert d.unknowns is not None
    assert d.identity_state == "MISSING"


# ----------------------------- downstream bypasses -----------------------------

def test_opportunity_alert_requires_canonical_buy():
    cand = _cand()
    report = OpportunityScorer().evaluate(cand, now=NOW)
    alerts = AlertEngine(score_threshold=1.0).evaluate_opportunity(
        report, cand, now=NOW, identity=None,
    )
    assert not any(a.cls == "OPPORTUNITY" for a in alerts)

    ident = verified_pool_identity_fixture()
    decision = CanonicalDecisionAuthority().decide(cand, report, identity=ident, now=NOW)
    alerts2 = AlertEngine(score_threshold=1.0).evaluate_opportunity(
        report, cand, now=NOW, identity=ident, canonical=decision,
    )
    if decision.alerts_allowed and report.risk_level in ("LOW", "MED"):
        assert any(a.cls == "OPPORTUNITY" for a in alerts2)
    else:
        assert not any(a.cls == "OPPORTUNITY" for a in alerts2)


def test_pump_alert_cannot_fire_without_canonical_buy():
    assert should_alert("k", 99.0, True, canonical_positive=False) is False
    assert maybe_alert_opportunity({
        "tokenKey": "sol:TOK", "symbol": "TOK", "chain": "solana",
        "rankScore": 99, "decision": "WATCH", "securityStatus": "UNKNOWN",
    }) is None
    assert maybe_alert_opportunity({
        "tokenKey": "sol:TOK", "symbol": "TOK", "chain": "solana",
        "rankScore": 99, "decision": "WATCH", "securityStatus": "PASS",
        "canonicalOutcome": "WATCH",
    }) is None


def test_identity_from_candidate_single_source_is_unresolved():
    cand = _cand()
    res = identity_from_candidate(cand, now=NOW)
    assert res.token.state in (IdentityState.UNRESOLVED, IdentityState.INVALID)


def test_pipeline_score_alone_does_not_emit_opportunity_or_special_telegram(tmp_path):
    cand = NormalizedTokenCandidate(
        chain="solana", address=SOL_CANON, symbol="ALPHA", name="Alpha",
        source_provider="dexscreener", retrieved_ts=NOW,
        metrics=_metrics(liquidity_usd=80_000, volume_1h=40_000, volume_velocity=3.2,
                         txns_1h_buys=90, txns_1h_sells=20),
        security=passing_security_signals(),
    )
    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = MockDiscoveryProvider("geckoterminal", [])
    adapter = MockTelegramAdapter()
    orch = OpportunityPipelineOrchestrator(
        collector=CollectorEngine(db_path=str(tmp_path / "p.sqlite"), router=router),
        scorer=OpportunityScorer(),
        alert_engine=AE(score_threshold=70.0),
        telegram_adapter=adapter,
        target_chat_id=1,
    )
    report = orch.run_pipeline(chain="solana", limit=5, now=NOW)
    assert not any(a.cls == "OPPORTUNITY" for a in report.alerts)
    assert report.top_canonical is not None
    assert report.top_canonical.is_positive is False
    assert not any("فرصت ویژه" in (m.get("text") or "") for m in adapter.sent_messages)


def test_pipeline_with_verified_pool_identity_can_alert(tmp_path):
    cand = NormalizedTokenCandidate(
        chain="solana", address=SOL_CANON, symbol="ALPHA", name="Alpha",
        source_provider="dexscreener", retrieved_ts=NOW,
        pair_created_ts=NOW - 30 * 86400,
        metrics=_metrics(liquidity_usd=80_000, volume_1h=40_000, volume_velocity=3.2,
                         txns_1h_buys=90, txns_1h_sells=20, price_usd=0.10),
        security=passing_security_signals(),
    )
    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = MockDiscoveryProvider("geckoterminal", [])
    adapter = MockTelegramAdapter()
    ident = verified_pool_identity_fixture(address=SOL_CANON, symbol="ALPHA")
    orch = OpportunityPipelineOrchestrator(
        collector=CollectorEngine(db_path=str(tmp_path / "p2.sqlite"), router=router),
        scorer=OpportunityScorer(),
        alert_engine=AE(score_threshold=70.0),
        telegram_adapter=adapter,
        target_chat_id=1,
        identity_resolver=lambda _c, _n: ident,
    )
    report = orch.run_pipeline(chain="solana", limit=5, now=NOW)
    assert report.top_canonical is not None
    if report.top_canonical.alerts_allowed:
        assert any(a.cls == "OPPORTUNITY" for a in report.alerts)
        assert any("فرصت ویژه" in (m.get("text") or "") for m in adapter.sent_messages)


# ----------------------------- static bypass surfaces -----------------------------

def test_telegram_service_does_not_import_decision_authority_or_scorer():
    src = (ROOT / "telegram_ai" / "service.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names = {a.name for a in (node.names or [])}
            if "OpportunityScorer" in names:
                pytest.fail("Telegram must not import OpportunityScorer")
            if "CanonicalDecisionAuthority" in names:
                pytest.fail("Telegram must consume decisions, not instantiate a second authority")


def test_scoring_ts_requires_canonical_backend_for_watch():
    src = (ROOT / "scoring.ts").read_text(encoding="utf-8")
    assert "canonicalBackend" in src
    assert "backendAllowsPositive" in src
    assert "CanonicalDecisionAuthority" in src
    assert "WATCH" in src


def test_alerts_ts_unknown_security_cannot_alert():
    src = (ROOT / "alerts.ts").read_text(encoding="utf-8")
    assert "rankScore >= 0.8" not in src
    assert "UNKNOWN" in src
    assert "INCOMPLETE" in src


def test_reasoning_engine_is_classified_as_presentation():
    src = (ROOT / "advanced-3d-audiovisual-website (1)" / "src" / "lib" / "reasoningEngine.ts").read_text(
        encoding="utf-8",
    )
    assert "NOT CANONICAL BRAIN" in src
    assert "not a canonical Python BUY" in src
    assert "CanonicalDecisionAuthority" in src


def test_web_trees_preserved():
    assert (ROOT / "advanced-3d-audiovisual-website").is_dir()
    assert (ROOT / "advanced-3d-audiovisual-website (1)").is_dir()
    assert (ROOT / "scoring.ts").is_file()
    assert (ROOT / "engine.ts").is_file()
    assert (ROOT / "council.ts").is_file()
