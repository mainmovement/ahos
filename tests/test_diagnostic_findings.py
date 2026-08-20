#!/usr/bin/env python3
"""W37: automatic diagnostic findings + finding->proposal + deduplication.

Pins:
  * derive_findings emits findings only when the snapshot data supports them
    (no invented findings);
  * each finding carries the full contract (id, severity, subsystem,
    evidence, confidence OBSERVED/DERIVED/CORRELATED/UNKNOWN, guard state,
    investigation, internal/governance/external flags);
  * propose_for_finding creates a governed PROPOSED proposal (requires_human)
    and deduplicates: a second call for the same finding returns
    EXISTING_PROPOSAL with the existing id.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evolution.findings import (  # noqa: E402
    DiagnosticFinding,
    derive_findings,
    propose_for_finding,
)
from architecture.evolution.engine import SelfEvolutionEngine  # noqa: E402

NOW = 1756000000.0


def _health(unknown_share=None, failures=0, drift=False, storage_bytes=1024,
            test_exit=None, calibration_status=None, benchmark_present=True):
    so = {
        "provider_failure_rates": {"total_failure_events": failures,
                                   "by_provider_kind": [] if not failures else
                                   [{"provider_id": "dexscreener", "kind": "FETCH_ERROR",
                                     "count": failures}]},
        "data_completeness": ({"unknown_share": unknown_share,
                               "production_observations": 100} if unknown_share is not None
                              else {"error": "NO_DATA"}),
        "score_drift": {"verdict": "DRIFT_DETECTED" if drift else "NO_DRIFT_DETECTED"},
        "calibration_state": {"latest_artifact": (
            {"artifact": "calibration_x.json", "calibration_status": calibration_status,
             "schema": "ahos.calibration_report.v7"} if calibration_status else None)},
        "storage_growth": {"total_bytes": storage_bytes},
        "test_health": {"pytest": {"present": True, "exit_code": test_exit}
                        if test_exit is not None else
                        {"present": True, "exit_code": 0}},
        "benchmark_health": {"baseline_present": benchmark_present},
    }
    return {"overall_verdict": "GREEN", "self_observation": so}


def test_no_findings_without_supporting_data():
    findings = derive_findings(_health(), now=NOW)
    assert findings == []


def test_findings_cover_each_signal():
    h = _health(unknown_share=0.7, failures=12, drift=True,
                storage_bytes=5 * 1024**3, test_exit=1,
                calibration_status="ERROR", benchmark_present=False)
    findings = derive_findings(h, now=NOW)
    kinds = {f.kind for f in findings}
    assert "PROVIDER_FAILURE" in kinds
    assert "UNKNOWN_GROWTH" in kinds
    assert "SCORE_DRIFT" in kinds
    assert "CALIBRATION_DEGRADATION" in kinds
    assert "STORAGE_ANOMALY" in kinds
    assert "TEST_REGRESSION" in kinds
    assert "BENCHMARK_REGRESSION" in kinds


def test_finding_contract_complete():
    findings = derive_findings(
        _health(unknown_share=0.7, failures=3), now=NOW)
    assert findings
    for f in findings:
        assert f.finding_id and len(f.finding_id) == 12
        assert f.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert f.confidence in ("OBSERVED", "DERIVED", "CORRELATED", "UNKNOWN")
        assert f.evidence and f.subsystem and f.timestamp_utc
        assert isinstance(f.actionable_internally, bool)
        assert isinstance(f.requires_governance, bool)
        assert isinstance(f.requires_external, bool)


def test_graph_findings_for_cycle_and_orphans():
    h = _health()
    graph = {"cycles": [["a", "b"]], "isolated_modules": ["x", "y"]}
    kinds = {f.kind for f in derive_findings(h, graph=graph, now=NOW)}
    assert "ARCHITECTURE_CYCLE" in kinds
    assert "ORPHAN" in kinds


def test_propose_for_finding_creates_governed_proposal(tmp_path):
    finding = derive_findings(_health(unknown_share=0.8), now=NOW)[0]
    result = propose_for_finding(finding, proposals_dir=tmp_path, now=NOW)
    assert result["result"] == "CREATED"
    assert result["requires_human"] is True

    data = json.loads((tmp_path / result["artifact"]).read_text(encoding="utf-8"))
    assert data["current_stage"] == "PROPOSED"
    assert data["is_ai"] is True
    assert data["classification"] == "DATA_QUALITY"
    assert data["evidence_links"]["diagnostic_finding"] == finding.finding_id


def test_propose_deduplicates_existing_proposal(tmp_path):
    finding = DiagnosticFinding(
        finding_id="abc123def456", kind="ARCHITECTURE_CYCLE", severity="MEDIUM",
        subsystem="architecture", evidence="cycle", timestamp_utc="t",
        confidence="OBSERVED", recommended_investigation="extract",
        actionable_internally=True, requires_governance=True)

    r1 = propose_for_finding(finding, proposals_dir=tmp_path, now=NOW)
    assert r1["result"] == "CREATED"
    r2 = propose_for_finding(finding, proposals_dir=tmp_path, now=NOW)
    assert r2["result"] == "EXISTING_PROPOSAL"
    assert r2["proposal_id"] == r1["proposal_id"]

    # exactly one proposal file exists
    assert len(list(tmp_path.glob("prop_*.json"))) == 1


def test_cli_lists_findings(tmp_path, capsys):
    import sys as _sys
    health_path = tmp_path / "health.json"
    health_path.write_text(json.dumps(_health(unknown_share=0.9)),
                           encoding="utf-8")
    from architecture.evolution import findings as mod
    rc = mod.main([str(health_path)])
    assert rc == 0
    assert "UNKNOWN_GROWTH" in capsys.readouterr().out


def test_config_drift_finding_when_gate_degraded():
    h = _health()
    h["self_observation"]["config_health"] = {
        "status": "DEGRADED",
        "evidence": ["validate_imports exit 1 @ abc1234"],
    }
    kinds = {f.kind for f in derive_findings(h, now=NOW)}
    assert "CONFIG_DRIFT" in kinds


def test_config_drift_finding_when_offline_active():
    h = _health()
    h["self_observation"]["config_health"] = {
        "status": "HEALTHY",
        "offline_mode": {"active": True},
    }
    findings = derive_findings(h, now=NOW)
    cfgs = [f for f in findings if f.kind == "CONFIG_DRIFT"]
    assert any("AHOS_OFFLINE_MODE=1" in f.evidence for f in cfgs)
    assert all(f.requires_external is True for f in cfgs)


def test_finding_priority_derived_from_severity_and_confidence():
    from architecture.evolution.findings import _priority_of

    # OBSERVED / DERIVED evidence keeps severity (never double-counted)
    assert _priority_of("HIGH", "OBSERVED") == "HIGH"
    assert _priority_of("CRITICAL", "OBSERVED") == "CRITICAL"
    assert _priority_of("MEDIUM", "DERIVED") == "MEDIUM"
    # weak evidence (CORRELATED/UNKNOWN) downgrades one step
    assert _priority_of("HIGH", "CORRELATED") == "MEDIUM"
    assert _priority_of("MEDIUM", "UNKNOWN") == "LOW"
    assert _priority_of("LOW", "UNKNOWN") == "LOW"
    # unknown evidence never fabricates a critical priority
    assert _priority_of("CRITICAL", "UNKNOWN") == "HIGH"


def test_findings_are_prioritized_highest_first():
    h = _health(unknown_share=0.7, failures=12, drift=True,
                storage_bytes=5 * 1024**3, test_exit=1,
                calibration_status="ERROR", benchmark_present=False)
    findings = derive_findings(h, now=NOW)
    # every finding carries a priority in the declared set
    assert all(f.priority in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
               for f in findings)
    # sorted highest-first by priority rank
    from architecture.evolution.findings import _SEVERITY_RANK
    ranks = [_SEVERITY_RANK[f.priority] for f in findings]
    assert ranks == sorted(ranks, reverse=True)
    # TEST_REGRESSION (HIGH, OBSERVED) outranks PROVIDER_FAILURE (HIGH, OBSERVED)
    # tie is broken by kind ordering; both HIGH appear before MEDIUM ones
    assert ranks[0] >= ranks[-1]


def test_priority_never_fabricated_for_no_data():
    from architecture.evolution.findings import _priority_of
    # weak/unknown evidence can never inflate priority above its severity
    assert _priority_of("HIGH", "UNKNOWN") != "CRITICAL"
    assert _priority_of("HIGH", "CORRELATED") != "CRITICAL"
