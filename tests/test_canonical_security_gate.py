#!/usr/bin/env python3
"""Phase 2 — Lane B security overlay.

Does not edit frozen discovery/security_gate.py. Composes Lane A verdicts
into PASS / REJECT / INCOMPLETE / STALE. Missing critical evidence is never
treated as safe.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.alerts.engine import AlertEngine  # noqa: E402
from architecture.decision.advisor import DecisionAdvisor  # noqa: E402
from architecture.intel.exitability import ExitabilityAnalyzer  # noqa: E402
from architecture.providers.adapters import GoPlusSecurityAdapter  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402
from architecture.security.gate import (  # noqa: E402
    SecurityState,
    compose_security_overlay,
    evaluate_security,
    evaluate_security_from_candidate,
    security_allows_alert,
    security_allows_paper_candidate,
    security_allows_positive_eligibility,
)
from discovery.security_gate import evaluate  # noqa: E402
from tests.helpers_identity import verified_identity_fixture, verified_pool_identity_fixture  # noqa: E402
from tests.helpers_security import OLD_POOL_TS, passing_security_signals  # noqa: E402
from tests.test_provider_abstraction import MockHttpResponse  # noqa: E402

NOW = 1_800_000_000.0


def _cand(security=None, **over):
    return NormalizedTokenCandidate(
        chain=over.get("chain", "solana"),
        address=over.get("address", "Tok111"),
        symbol=over.get("symbol", "TOK"),
        name="TOK Token",
        metrics=over.get(
            "metrics",
            MarketMetrics(
                price_usd=0.002, liquidity_usd=150_000,
                volume_5m=9_000, volume_1h=30_000, volume_24h=250_000,
                txns_5m_buys=90, txns_5m_sells=25,
                txns_1h_buys=400, txns_1h_sells=250, price_change_1h=12.0,
            ),
        ),
        security=security if security is not None else passing_security_signals(),
        source_provider="dexscreener",
        retrieved_ts=over.get("retrieved_ts", NOW),
        pair_created_ts=over.get("pair_created_ts", OLD_POOL_TS),
    )


def _advise(cand, **kw):
    report = OpportunityScorer().evaluate(cand)
    kw.setdefault("identity", verified_identity_fixture())
    kw.setdefault("exitability", ExitabilityAnalyzer().analyze(cand, 200))
    return DecisionAdvisor(bankroll_usd=1000.0).advise_entry(cand, report, **kw)


def test_passing_security_is_pass():
    overlay = evaluate_security(
        passing_security_signals(), now=NOW, pair_created_ts=OLD_POOL_TS, retrieved_ts=NOW,
    )
    assert overlay.state == SecurityState.PASS
    assert overlay.lane_a_verdict == "PASS"
    assert security_allows_positive_eligibility(overlay)
    assert security_allows_alert(overlay)
    assert security_allows_paper_candidate(overlay)


def test_lane_a_pass_with_unknown_maps_to_incomplete():
    overlay = compose_security_overlay(
        {"verdict": "PASS_WITH_UNKNOWN", "veto_reasons": [], "unknown_critical": ["honeypot"],
         "coverage": 0.5},
        now=NOW, retrieved_ts=NOW,
    )
    assert overlay.state == SecurityState.INCOMPLETE
    assert not security_allows_positive_eligibility(overlay)


def test_lane_a_security_veto_maps_to_reject():
    overlay = compose_security_overlay(
        {"verdict": "SECURITY_VETO", "veto_reasons": ["honeypot"], "unknown_critical": [],
         "coverage": 1.0},
        now=NOW, retrieved_ts=NOW,
    )
    assert overlay.state == SecurityState.REJECT


def test_confirmed_honeypot_reject():
    overlay = evaluate_security(passing_security_signals(is_honeypot=True), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "honeypot" in overlay.veto_reasons
    advice = _advise(_cand(passing_security_signals(is_honeypot=True)))
    assert advice.action == "AVOID"
    assert advice.security_state == "REJECT"


def test_unsellable_token_reject():
    overlay = evaluate_security(passing_security_signals(cannot_sell_all=True), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "unsellable" in overlay.veto_reasons


def test_malicious_blacklist_reject():
    overlay = evaluate_security(passing_security_signals(is_blacklisted=True), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "blacklist_function" in overlay.veto_reasons


def test_dangerous_mint_reject():
    overlay = evaluate_security(passing_security_signals(has_mint_authority=True), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "mint_authority_active" in overlay.veto_reasons


def test_dangerous_freeze_reject():
    overlay = evaluate_security(passing_security_signals(has_freeze_authority=True), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "freeze_authority_active" in overlay.veto_reasons


def test_extreme_sell_tax_reject():
    overlay = evaluate_security(passing_security_signals(sell_tax_pct=40.0), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "sell_tax_extreme" in overlay.veto_reasons


def test_rug_deployer_reject():
    overlay = evaluate_security(passing_security_signals(deployer_past_rug_count=2), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "deployer_prior_rug" in overlay.veto_reasons


def test_trapped_liquidity_reject():
    thin = _cand(
        passing_security_signals(),
        metrics=MarketMetrics(price_usd=0.002, liquidity_usd=800),
    )
    ex = ExitabilityAnalyzer().analyze(thin, position_usd=5_000)
    overlay = evaluate_security_from_candidate(thin, now=NOW, exitability=ex)
    assert overlay.state == SecurityState.REJECT
    assert "trapped_liquidity" in overlay.veto_reasons or ex.verdict == "TRAPPED"


def test_unknown_security_incomplete():
    overlay = evaluate_security(SecuritySignals(), now=NOW)
    assert overlay.state == SecurityState.INCOMPLETE
    assert not security_allows_positive_eligibility(overlay)
    advice = _advise(_cand(SecuritySignals()))
    assert advice.action == "AVOID"
    assert advice.security_state == "INCOMPLETE"


def test_missing_honeypot_is_incomplete_not_pass():
    overlay = evaluate_security(passing_security_signals(is_honeypot=None), now=NOW)
    assert overlay.state == SecurityState.INCOMPLETE
    assert "honeypot" in overlay.unknown_critical


def test_stale_security():
    overlay = evaluate_security(
        passing_security_signals(),
        now=NOW,
        pair_created_ts=OLD_POOL_TS,
        retrieved_ts=NOW - 48 * 3600,
    )
    assert overlay.state == SecurityState.STALE
    assert not security_allows_positive_eligibility(overlay)
    honeypot_stale = evaluate_security(
        passing_security_signals(is_honeypot=True),
        now=NOW,
        retrieved_ts=NOW - 48 * 3600,
    )
    assert honeypot_stale.state == SecurityState.REJECT


def test_high_opportunity_plus_critical_security_is_reject():
    cand = _cand(passing_security_signals(is_honeypot=True))
    advice = _advise(cand)
    assert advice.action == "AVOID"
    assert advice.security_state == "REJECT"
    assert advice.deterministic_score is not None


def test_opportunity_alert_suppressed_without_security_pass():
    cand = _cand(SecuritySignals(is_honeypot=False))
    report = OpportunityScorer().evaluate(cand)
    alerts = AlertEngine(score_threshold=1.0).evaluate_opportunity(report, cand, now=NOW)
    assert not any(a.cls == "OPPORTUNITY" for a in alerts)


def test_opportunity_alert_requires_security_pass():
    cand = _cand(passing_security_signals(), retrieved_ts=NOW)
    report = OpportunityScorer().evaluate(cand)
    alerts = AlertEngine(score_threshold=1.0).evaluate_opportunity(
        report, cand, now=NOW,
        identity=verified_pool_identity_fixture(address=cand.address),
    )
    if report.opportunity_score >= 1.0 and report.risk_level in ("LOW", "MED"):
        assert any(a.cls == "OPPORTUNITY" for a in alerts)


def test_goplus_missing_honeypot_stays_unknown():
    payload = {
        "code": 1,
        "message": "OK",
        "result": {
            "0x1111111111111111111111111111111111111111": {
                "buy_tax": "0.01",
                "sell_tax": "0.01",
            }
        },
    }
    adapter = GoPlusSecurityAdapter(
        transport=lambda req, timeout=None: MockHttpResponse(payload),
    )
    resp = adapter.fetch_token_metrics(
        "ethereum", "0x1111111111111111111111111111111111111111",
    )
    assert resp.status == "OK"
    sec = resp.tokens[0].security
    assert sec.is_honeypot is None
    assert sec.has_mint_authority is None
    assert sec.is_ownership_renounced is None
    overlay = evaluate_security(sec, now=NOW)
    assert overlay.state == SecurityState.INCOMPLETE


def test_lane_b_overlay_matches_frozen_evaluate_on_same_rows():
    checks = [
        {"check_key": k, "value": "FALSE", "severity": "CRITICAL"}
        for k in (
            "honeypot", "sell_tax_extreme", "blacklist_function",
            "mint_authority_active", "freeze_authority_active",
            "lp_not_locked_fresh_pool", "deployer_prior_rug",
        )
    ]
    lane_a = evaluate(checks)
    overlay = compose_security_overlay(lane_a, now=NOW, retrieved_ts=NOW)
    assert lane_a["verdict"] == "PASS"
    assert overlay.state == SecurityState.PASS
    unknown = evaluate([{"check_key": "honeypot", "value": "UNKNOWN", "severity": "CRITICAL"}])
    mapped = compose_security_overlay(unknown, now=NOW, retrieved_ts=NOW)
    assert unknown["verdict"] == "PASS_WITH_UNKNOWN"
    assert mapped.state == SecurityState.INCOMPLETE


def test_missing_overlay_is_fail_closed():
    assert not security_allows_positive_eligibility(None)
    assert not security_allows_alert(None)
    assert not security_allows_paper_candidate(None)
