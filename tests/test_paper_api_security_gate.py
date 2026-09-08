#!/usr/bin/env python3
"""Paper API and TypeScript alert gate must consume canonical overlay PASS."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_paper_route_requires_security_gate_and_ignores_client_state():
    text = (ROOT / "app" / "api" / "paper" / "route.ts").read_text(encoding="utf-8")
    assert "PaperSecurityDenied" in text
    assert "SECURITY_GATE" in text
    assert "void body.canonicalSecurityState" in text
    assert "addPaper(" in text
    # Must not pass client overlay state into addPaper.
    assert "canonicalSecurityState: body" not in text


def test_add_paper_calls_overlay_before_insert():
    text = (ROOT / "engine.ts").read_text(encoding="utf-8")
    assert "resolveCanonicalSecurityForPaper" in text
    assert "paperOpenDecision" in text
    assert "PaperSecurityDenied" in text
    insert_at = text.index("insert(paperPositions)")
    gate_at = text.index("paperOpenDecision")
    assert gate_at < insert_at


def test_alerts_ts_does_not_use_score_as_security_ok():
    text = (ROOT / "alerts.ts").read_text(encoding="utf-8")
    assert "canonicalSecurityAllowsSideEffect" in text
    assert "function securityOk" not in text
    assert 's === "UNKNOWN"' not in text
    assert "processOpportunityAlerts" in text
    engine = (ROOT / "engine.ts").read_text(encoding="utf-8")
    assert engine.index("await attachCanonicalSecurityStates") < engine.index(
        "await processOpportunityAlerts"
    )


def test_canonical_security_adapter_does_not_evaluate_honeypot():
    text = (ROOT / "canonical_security.ts").read_text(encoding="utf-8")
    assert "parseCanonicalSecurityState" in text
    assert "=== \"PASS\"" in text or "=== 'PASS'" in text
    assert "evaluate(" not in text
    assert "VETO_REGISTRY" not in text
    assert "queryPythonOverlayStates" in text
    assert 'parseCanonicalSecurityState(raw) === "PASS"' in text or \
        "parseCanonicalSecurityState(raw) === 'PASS'" in text


def test_paper_open_decision_table_is_fail_closed():
    """Execution of the paper gate table via overlay_query + PASS-only allow."""
    from architecture.security.overlay_query import run
    from tests.helpers_security import OLD_POOL_TS, passing_security_signals

    now = 1_800_000_000.0
    sec = passing_security_signals()
    passing = run(
        {"tokens": [{"tokenKey": "k", "signals": {
            "is_honeypot": sec.is_honeypot,
            "sell_tax_pct": sec.sell_tax_pct,
            "buy_tax_pct": sec.buy_tax_pct,
            "liquidity_locked_pct": sec.liquidity_locked_pct,
            "has_mint_authority": sec.has_mint_authority,
            "has_freeze_authority": sec.has_freeze_authority,
            "is_contract_verified": sec.is_contract_verified,
            "is_ownership_renounced": sec.is_ownership_renounced,
            "top10_holder_concentration_pct": sec.top10_holder_concentration_pct,
            "deployer_past_rug_count": sec.deployer_past_rug_count,
            "is_blacklisted": sec.is_blacklisted,
            "cannot_sell_all": sec.cannot_sell_all,
            "is_proxy": sec.is_proxy,
        }, "pair_created_ts": OLD_POOL_TS, "retrieved_ts": now}]},
        now=now,
    )
    assert passing["k"] == "PASS"
    missing = run({"tokens": [{"tokenKey": "m"}]}, now=now)
    assert missing.get("m") == "INCOMPLETE"
    honeypot = run(
        {"tokens": [{"tokenKey": "h", "signals": {"is_honeypot": True},
                    "pair_created_ts": OLD_POOL_TS, "retrieved_ts": now}]},
        now=now,
    )
    assert honeypot["h"] == "REJECT"


def test_paper_route_does_not_trust_client_pass():
    text = (ROOT / "app" / "api" / "paper" / "route.ts").read_text(encoding="utf-8")
    assert "SECURITY_GATE" in text
    assert "status: 403" in text
    engine = (ROOT / "engine.ts").read_text(encoding="utf-8")
    assert "queryPythonOverlayStates" in engine
    assert "paperOpenDecision" in engine
