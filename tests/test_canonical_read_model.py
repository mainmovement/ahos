#!/usr/bin/env python3
"""Canonical decision read-model — Python writes, TS only presents."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.decision.authority import CanonicalDecisionAuthority  # noqa: E402
from architecture.decision.read_model import (  # noqa: E402
    load_canonical_read_model,
    lookup_decision,
    write_canonical_read_model,
    write_unavailable_canonical_read_model,
)
from architecture.intel.exitability import ExitabilityAnalyzer  # noqa: E402
from architecture.scoring.engine import OpportunityScorer  # noqa: E402
from tests.helpers_identity import verified_pool_identity_fixture  # noqa: E402
from tests.test_canonical_decision_authority import _cand  # noqa: E402

NOW = 1_800_000_000.0


def test_missing_read_model_is_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_CANONICAL_READ_MODEL", str(tmp_path / "missing.json"))
    model = load_canonical_read_model(now=NOW)
    assert model["status"] == "UNAVAILABLE"
    assert model["decisions"] == []
    assert model["no_invented_evidence"] is True


def test_corrupt_read_model_is_unavailable(tmp_path, monkeypatch):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv("AHOS_CANONICAL_READ_MODEL", str(path))
    model = load_canonical_read_model(now=NOW)
    assert model["status"] == "UNAVAILABLE"
    assert "corrupt" in str(model.get("reason") or "")


def test_stale_read_model_cannot_stay_positive(tmp_path, monkeypatch):
    cand = _cand()
    report = OpportunityScorer().evaluate(cand, now=NOW)
    decision = CanonicalDecisionAuthority().decide(
        cand, report, identity=verified_pool_identity_fixture(), now=NOW,
        exitability=ExitabilityAnalyzer().analyze(cand, 200),
    )
    path = tmp_path / "model.json"
    monkeypatch.setenv("AHOS_CANONICAL_READ_MODEL", str(path))
    write_canonical_read_model([(cand, decision)], now=NOW - 48 * 3600, path=path)
    model = load_canonical_read_model(now=NOW)
    assert model["status"] == "STALE"
    assert model["reason"] == "stale_read_model"
    for row in model["decisions"]:
        assert row["is_positive"] is False
        assert row["paper_allowed"] is False
        assert row["alerts_allowed"] is False
        assert row["outcome"] == "STALE"
        assert row.get("recorded_outcome")
        assert row.get("advisor_action") in (None, "")


def test_write_and_lookup_roundtrip(tmp_path, monkeypatch):
    cand = _cand()
    report = OpportunityScorer().evaluate(cand, now=NOW)
    decision = CanonicalDecisionAuthority().decide(
        cand, report, identity=verified_pool_identity_fixture(), now=NOW,
        exitability=ExitabilityAnalyzer().analyze(cand, 200),
    )
    path = tmp_path / "model.json"
    monkeypatch.setenv("AHOS_CANONICAL_READ_MODEL", str(path))
    write_canonical_read_model([(cand, decision)], now=NOW, path=path)
    model = load_canonical_read_model(now=NOW)
    assert model["status"] == "AVAILABLE"
    row = lookup_decision(model, chain=cand.chain, address=cand.address)
    assert row is not None
    assert row["opportunity_score"] == decision.opportunity_score
    assert row["confidence_level"] == decision.confidence_level
    assert row["outcome"] == decision.outcome.value
    assert lookup_decision(model, chain="ethereum", address="0xdead") is None


def test_unavailable_writer(tmp_path, monkeypatch):
    path = tmp_path / "unav.json"
    monkeypatch.setenv("AHOS_CANONICAL_READ_MODEL", str(path))
    write_unavailable_canonical_read_model(reason="daemon_not_started", now=NOW, path=path)
    model = load_canonical_read_model(now=NOW)
    assert model["status"] == "UNAVAILABLE"
    assert model["decisions"] == []


def test_engine_ts_loads_python_read_model_not_hardcoded_null():
    src = (ROOT / "engine.ts").read_text(encoding="utf-8")
    assert "loadCanonicalReadModel" in src
    assert "toBackendDecision" in src
    assert "canonicalBackend: null" not in src


def test_snapshot_overlays_canonical_and_command_center_does_not_green_watch():
    snap = (ROOT / "snapshot.ts").read_text(encoding="utf-8")
    assert "overlayOpportunity" in snap
    assert "canonicalReadModel" in snap
    assert "failClosedCommandSnapshot" in snap
    assert "presentCanonicalDecisions" in snap
    assert "loadCanonicalReadModel" in snap
    cc = (ROOT / "CommandCenter.tsx").read_text(encoding="utf-8")
    assert "canonicalReadModel" in cc
    assert "canonicalDecisions" in cc
    assert "UNAVAILABLE" in cc
    assert "paperAllowed" in cc
    # WATCH must not be treated as a success/positive pill.
    assert 'status === "WATCH" || status === "HIGH"' not in cc
    assert "WATCH" in cc  # still displayed as a non-positive state
    route = (ROOT / "app" / "api" / "command" / "route.ts").read_text(encoding="utf-8")
    assert "failClosedCommandSnapshot" in route
    assert "command_snapshot_failed" not in route


def test_canonical_api_route_is_auth_gated():
    src = (ROOT / "app" / "api" / "canonical" / "route.ts").read_text(encoding="utf-8")
    assert "authorizeWebApi" in src
    assert "loadCanonicalReadModel" in src


def test_pipeline_persists_read_model(tmp_path, monkeypatch):
    from architecture.collector.engine import CollectorEngine
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    from architecture.providers.contracts import NormalizedTokenCandidate
    from architecture.providers.registry import ProviderRouter
    from architecture.scoring.engine import OpportunityScorer
    from architecture.alerts.engine import AlertEngine
    from tests.helpers_security import passing_security_signals
    from tests.test_canonical_decision_authority import _metrics
    from tests.test_opportunity_pipeline_integration import MockDiscoveryProvider
    from tests.helpers_identity import SOL_CANON

    path = tmp_path / "rm.json"
    monkeypatch.setenv("AHOS_CANONICAL_READ_MODEL", str(path))
    cand = NormalizedTokenCandidate(
        chain="solana", address=SOL_CANON, symbol="ALPHA", name="Alpha",
        source_provider="dexscreener", retrieved_ts=NOW,
        metrics=_metrics(), security=passing_security_signals(),
    )
    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = MockDiscoveryProvider("geckoterminal", [])
    orch = OpportunityPipelineOrchestrator(
        collector=CollectorEngine(db_path=str(tmp_path / "p.sqlite"), router=router),
        scorer=OpportunityScorer(),
        alert_engine=AlertEngine(score_threshold=70.0),
    )
    orch.run_pipeline(chain="solana", limit=5, now=NOW)
    model = load_canonical_read_model(now=NOW)
    assert model["status"] == "AVAILABLE"
    assert model["decision_count"] >= 1
    row = lookup_decision(model, chain="solana", address=SOL_CANON)
    assert row is not None
    assert row["is_positive"] is False  # single-source identity is not VERIFIED


def test_alerts_ts_requires_python_alerts_allowed_not_ts_watch():
    src = (ROOT / "alerts.ts").read_text(encoding="utf-8")
    assert "alertsAllowedFromCanonical" in src
    assert "loadCanonicalReadModel" in src
    assert "lookupCanonicalRow" in src
    assert 'opp.decision !== "WATCH"' not in src
    engine = (ROOT / "engine.ts").read_text(encoding="utf-8")
    assert "displayDecision" in engine
    assert "canonRow?.is_positive" in engine
    assert "countCanonicalOutcomesForTokens" in engine
    assert 'r.decision === "WATCH"' not in engine
    chat = (ROOT / "chat.ts").read_text(encoding="utf-8")
    assert "canonicalDecisions" in chat
    assert "canonicalFocusTokenKey" in chat


def test_command_center_renders_python_decisions_without_db_rows():
    cc = (ROOT / "CommandCenter.tsx").read_text(encoding="utf-8")
    assert "canonicalDecisions" in cc
    assert "احکام کانونیکال پایتون" in cc
    assert "لایه وب BUY/WATCH نمی‌سازد" in cc
    for forbidden in (
        'from "./engine"',
        'from "./scoring"',
        'from "./canonical_security"',
        'from "./alerts"',
        'from "./council"',
        'from "@/engine"',
        'from "@/scoring"',
    ):
        assert forbidden not in cc, forbidden


def test_env_example_documents_canonical_read_model_path():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "AHOS_CANONICAL_READ_MODEL=" in text


def test_chat_greeting_counts_python_canonical_not_ts_watch():
    chat = (ROOT / "chat.ts").read_text(encoding="utf-8")
    assert "canonicalDecisions" in chat
    greeting = chat.split("function greetingReply")[1].split("function helpReply")[0]
    assert 'o.decision === "WATCH"' not in greeting
    opportunities = chat.split('intent === "opportunities"')[1].split("intent === \"news\"")[0]
    assert "canonicalFocusTokenKey" in opportunities
    general = chat.split("async function generalReply")[1].split("function findOpp")[0]
    assert "canonicalDecisions" in general
    assert "o.decision === \"BUY\"" not in general
    reject = chat.split('intent === "reject"')[1].split("intent === \"greeting\"")[0]
    assert "canonicalDecisions" in reject
    assert "whyCanonicalReply" in chat
    assert "findCanonicalDecision" in chat
    assert "running = Boolean(state?.running)" in chat
    detect = chat.split("function detectIntent")[1].split("function greetingReply")[0]
    assert detect.index("(رد شد|چرا رد|reject)") < detect.index("(چرا|دلیل|شواهد|explain)")


def test_paper_api_requires_canonical_buy():
    src = (ROOT / "app" / "api" / "paper" / "route.ts").read_text(encoding="utf-8")
    assert "paperAllowedFromCanonical" in src
    assert "CANONICAL_PAPER_DENIED" in src
    chat = (ROOT / "chat.ts").read_text(encoding="utf-8")
    assert "paperAllowedFromCanonical" in chat
    assert "CANONICAL_PAPER_DENIED" in chat


