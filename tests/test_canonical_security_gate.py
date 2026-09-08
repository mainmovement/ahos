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
from architecture.providers.adapters import GoPlusSecurityAdapter, RugCheckSecurityAdapter  # noqa: E402
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
from tests.helpers_identity import verified_identity_fixture  # noqa: E402
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
    alerts = AlertEngine(score_threshold=1.0).evaluate_opportunity(report, cand, now=NOW)
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
    from discovery.security_gate import CRITICAL
    checks = [
        {"check_key": k, "value": "FALSE", "severity": "CRITICAL"}
        for k in CRITICAL
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


def test_no_copied_lane_a_evaluator_in_overlay():
    src = (ROOT / "architecture" / "security" / "gate.py").read_text(encoding="utf-8")
    assert "_lane_a_evaluate" not in src
    assert "from discovery.security_gate import" in src
    assert "evaluate as lane_a_evaluate" in src


def test_critical_set_is_frozen_lane_a_not_the_full_registry():
    from discovery.security_gate import CRITICAL, VETO_REGISTRY
    from architecture.security.gate import LANE_A_CRITICAL_KEYS, SIGNAL_CRITICAL_PROJECTION
    assert list(LANE_A_CRITICAL_KEYS) == list(CRITICAL)
    high = {k for k, s in VETO_REGISTRY.items() if s == "HIGH"}
    assert high == {
        "proxy_risk_upgradeable",
        "ownership_renounced_absent",
        "holder_concentration_high",
    }
    assert high.isdisjoint(CRITICAL)
    assert set(SIGNAL_CRITICAL_PROJECTION) == set(CRITICAL)


def test_extreme_tax_threshold_matches_frozen_paper_trading():
    from architecture.security.gate import EXTREME_SELL_TAX_PCT
    from paper_trading.security_multi import EXTREME_SELL_TAX
    assert EXTREME_SELL_TAX_PCT == EXTREME_SELL_TAX * 100


def test_all_critical_true_is_reject():
    from discovery.security_gate import CRITICAL
    from architecture.security.gate import compose_security_overlay
    checks = [{"check_key": k, "value": "TRUE", "severity": "CRITICAL"} for k in CRITICAL]
    lane_a = evaluate(checks)
    overlay = compose_security_overlay(lane_a, now=NOW, retrieved_ts=NOW)
    assert lane_a["verdict"] == "SECURITY_VETO"
    assert overlay.state == SecurityState.REJECT
    assert set(overlay.veto_reasons) == set(CRITICAL)
    assert not security_allows_positive_eligibility(overlay)


def test_one_critical_true_is_reject():
    overlay = evaluate_security(passing_security_signals(is_blacklisted=True), now=NOW)
    assert overlay.state == SecurityState.REJECT
    assert "blacklist_function" in overlay.veto_reasons


def test_one_critical_unknown_is_incomplete():
    overlay = evaluate_security(passing_security_signals(has_mint_authority=None), now=NOW)
    assert overlay.state == SecurityState.INCOMPLETE
    assert "mint_authority_active" in overlay.unknown_critical
    assert not security_allows_paper_candidate(overlay)


def test_all_critical_false_can_pass():
    overlay = evaluate_security(
        passing_security_signals(), now=NOW, pair_created_ts=OLD_POOL_TS, retrieved_ts=NOW,
    )
    assert overlay.state == SecurityState.PASS


def test_missing_critical_row_is_incomplete():
    from discovery.security_gate import CRITICAL
    checks = [{"check_key": k, "value": "FALSE", "severity": "CRITICAL"} for k in CRITICAL if k != "honeypot"]
    lane_a = evaluate(checks)
    overlay = compose_security_overlay(lane_a, now=NOW, retrieved_ts=NOW)
    assert lane_a["verdict"] == "PASS_WITH_UNKNOWN"
    assert overlay.state == SecurityState.INCOMPLETE
    assert "honeypot" in overlay.unknown_critical


def test_future_unprojected_critical_cannot_pass():
    """If Lane A later adds a CRITICAL key, missing projection must INCOMPLETE."""
    from discovery import security_gate as sg
    sg.CRITICAL.append("new_future_critical")
    try:
        overlay = evaluate_security(
            passing_security_signals(), now=NOW, pair_created_ts=OLD_POOL_TS, retrieved_ts=NOW,
        )
        assert overlay.state == SecurityState.INCOMPLETE
        assert "new_future_critical" in overlay.unknown_critical
        assert not security_allows_positive_eligibility(overlay)
    finally:
        sg.CRITICAL.remove("new_future_critical")


def test_high_registry_true_does_not_invent_a_critical_veto():
    overlay = evaluate_security(
        passing_security_signals(is_proxy=True, is_ownership_renounced=False),
        now=NOW, pair_created_ts=OLD_POOL_TS, retrieved_ts=NOW,
    )
    assert overlay.state == SecurityState.PASS
    assert overlay.lane_a_verdict == "PASS"


def test_security_veto_cannot_be_downgraded_by_unknown_extras():
    overlay = compose_security_overlay(
        {"verdict": "SECURITY_VETO", "veto_reasons": ["honeypot"], "unknown_critical": [],
         "coverage": 1.0},
        now=NOW, retrieved_ts=NOW, extra_unknowns=("unsellable",),
    )
    assert overlay.state == SecurityState.REJECT


def test_missing_security_object_is_incomplete():
    overlay = evaluate_security(None, now=NOW)
    assert overlay.state == SecurityState.INCOMPLETE
    assert not security_allows_positive_eligibility(overlay)


def test_missing_tax_mint_freeze_ownership_are_incomplete():
    overlay = evaluate_security(
        passing_security_signals(
            sell_tax_pct=None, has_mint_authority=None,
            has_freeze_authority=None, is_ownership_renounced=None,
        ),
        now=NOW,
    )
    assert overlay.state == SecurityState.INCOMPLETE
    assert "sell_tax_extreme" in overlay.unknown_critical
    assert "mint_authority_active" in overlay.unknown_critical
    assert "freeze_authority_active" in overlay.unknown_critical


def test_high_opportunity_plus_incomplete_never_enters():
    cand = _cand(passing_security_signals(is_honeypot=None))
    advice = _advise(cand)
    assert advice.action == "AVOID"
    assert advice.security_state == "INCOMPLETE"
    assert advice.is_actionable is False


def test_ai_cannot_upgrade_security_reject_or_incomplete():
    from architecture.ai.council_live import CouncilVerdict
    council = CouncilVerdict(
        final_stance="ENTER", agreement="UNANIMOUS",
        council_status="ONLINE", responded=5,
    )
    rejected = _advise(_cand(passing_security_signals(is_honeypot=True)), council=council)
    assert rejected.action == "AVOID"
    assert rejected.security_state == "REJECT"
    incomplete = _advise(_cand(SecuritySignals()), council=council)
    assert incomplete.action == "AVOID"
    assert incomplete.security_state == "INCOMPLETE"


def test_paper_candidate_requires_security_pass():
    bad = evaluate_security(passing_security_signals(cannot_sell_all=True), now=NOW)
    assert bad.state == SecurityState.REJECT
    assert not security_allows_paper_candidate(bad)
    incomplete = evaluate_security(SecuritySignals(), now=NOW)
    assert not security_allows_paper_candidate(incomplete)
    stale = evaluate_security(
        passing_security_signals(), now=NOW, pair_created_ts=OLD_POOL_TS,
        retrieved_ts=NOW - 48 * 3600,
    )
    assert stale.state == SecurityState.STALE
    assert not security_allows_paper_candidate(stale)


def test_alert_without_pass_has_no_opportunity_side_effect():
    cand = _cand(passing_security_signals(is_honeypot=True))
    report = OpportunityScorer().evaluate(cand)
    alerts = AlertEngine(score_threshold=1.0).evaluate_opportunity(report, cand, now=NOW)
    assert not any(a.cls == "OPPORTUNITY" for a in alerts)


def test_rugcheck_missing_risks_does_not_infer_safe():
    adapter = RugCheckSecurityAdapter(
        transport=lambda req, timeout=None: MockHttpResponse({"tokenMeta": {"symbol": "X"}}),
    )
    resp = adapter.fetch_token_metrics("solana", "Tok111")
    assert resp.status == "OK"
    sec = resp.tokens[0].security
    assert sec.is_honeypot is None
    assert sec.has_mint_authority is None
    assert sec.has_freeze_authority is None
    overlay = evaluate_security(sec, now=NOW)
    assert overlay.state == SecurityState.INCOMPLETE


def test_goplus_missing_tax_and_authorities_stay_unknown():
    payload = {
        "code": 1,
        "message": "OK",
        "result": {
            "0x1111111111111111111111111111111111111111": {
                "is_honeypot": "0",
            }
        },
    }
    adapter = GoPlusSecurityAdapter(
        transport=lambda req, timeout=None: MockHttpResponse(payload),
    )
    sec = adapter.fetch_token_metrics(
        "ethereum", "0x1111111111111111111111111111111111111111",
    ).tokens[0].security
    assert sec.is_honeypot is False
    assert sec.sell_tax_pct is None
    assert sec.has_mint_authority is None
    assert sec.has_freeze_authority is None
    assert sec.is_ownership_renounced is None
    overlay = evaluate_security(sec, now=NOW)
    assert overlay.state == SecurityState.INCOMPLETE


def test_unknown_pool_age_is_incomplete_even_if_lp_locked():
    """Lane A returns UNKNOWN when pair_created_ts is missing; overlay must not PASS."""
    overlay = evaluate_security(
        passing_security_signals(), now=NOW, pair_created_ts=None, retrieved_ts=NOW,
    )
    assert overlay.state == SecurityState.INCOMPLETE
    assert "lp_not_locked_fresh_pool" in overlay.unknown_critical
    assert not security_allows_positive_eligibility(overlay)


def test_pump_alert_unknown_or_reject_cannot_fire(monkeypatch, tmp_path):
    from telegram_ai import pump_alert

    monkeypatch.setattr(pump_alert, "ALERT_STATE_PATH", tmp_path / "pump.json")
    monkeypatch.setattr(pump_alert, "push_telegram_alert", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(pump_alert, "should_alert", lambda *a, **k: True)
    monkeypatch.setattr(pump_alert, "mark_sent", lambda *a, **k: None)
    base = {
        "tokenKey": "solana:x",
        "symbol": "X",
        "chain": "solana",
        "rankScore": 90,
        "decision": "WATCH",
    }
    assert pump_alert.maybe_alert_opportunity({**base, "securityStatus": "UNKNOWN"}) is None
    assert pump_alert.maybe_alert_opportunity({**base, "securityStatus": "INCOMPLETE"}) is None
    assert pump_alert.maybe_alert_opportunity({**base, "securityStatus": "STALE"}) is None
    assert pump_alert.maybe_alert_opportunity({**base, "securityStatus": "REJECT"}) is None
    assert pump_alert.maybe_alert_opportunity({**base, "securityStatus": ""}) is None
    sent = pump_alert.maybe_alert_opportunity({**base, "securityStatus": "PASS"})
    assert sent is not None
