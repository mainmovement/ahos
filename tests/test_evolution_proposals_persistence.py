#!/usr/bin/env python3
"""Improvement-proposal persistence + governed CLI (evolution mission §4C).

Pins:
  * save/load roundtrip preserves the full proposal incl. the structured
    analysis fields (problem/evidence/subsystem/benefit/risk/contracts/
    baseline/change/validation).
  * ledger.jsonl integrity lines carry a sha256 that matches the artifact.
  * list_proposals summarizes persisted proposals.
  * The CLI requires the full analysis surface (exit 2 otherwise) and never
    auto-approves; LANE_A_FORBIDDEN proposals are born REJECTED.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evolution.engine import SelfEvolutionEngine  # noqa: E402
from scripts import propose_improvement as cli  # noqa: E402


NOW = 1756000000.0


def _proposal(engine, tmp_path, now=NOW, diagnosis="diagnosis-a"):
    prop = engine.create_proposal(
        detected_by="AG-1", diagnosis=diagnosis, proposed_by="AG-2",
        is_ai=True, target_scope="B_ONLY", governance_touching=False,
        candidate_diff_ref="diff_01", test_battery=["test_a", "test_b"],
        rollback_plan={"trigger": "coverage_drop", "action": "revert"},
        analysis={
            "problem": "problem text",
            "evidence": "evidence text",
            "subsystem": "architecture/learning",
            "expected_benefit": "benefit text",
            "risk": "risk text",
            "affected_contracts": "contracts text",
            "benchmark_baseline": "baseline text",
            "proposed_change": "change text",
            "validation_method": "validation text",
        },
        now=now,
    )
    return prop


def test_save_load_roundtrip_preserves_analysis(tmp_path):
    engine = SelfEvolutionEngine()
    prop = _proposal(engine, tmp_path)
    path = engine.save_proposal(prop, tmp_path)

    assert path.exists()
    loaded = engine.load_proposal(prop.proposal_id, tmp_path)
    assert loaded.proposal_id == prop.proposal_id
    assert loaded.current_stage == "PROPOSED"
    assert loaded.is_ai is True and loaded.requires_human is True
    assert loaded.analysis["problem"] == "problem text"
    assert loaded.analysis["validation_method"] == "validation text"
    assert loaded.rollback_plan == {"trigger": "coverage_drop", "action": "revert"}


def test_ledger_integrity_line_matches_artifact(tmp_path):
    engine = SelfEvolutionEngine()
    prop = _proposal(engine, tmp_path)
    engine.save_proposal(prop, tmp_path)
    engine.save_proposal(prop, tmp_path)   # idempotent artifact, second ledger line

    ledger = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger) == 2
    last = json.loads(ledger[-1])
    assert last["proposal_id"] == prop.proposal_id

    artifact = json.loads((tmp_path / f"{prop.proposal_id}.json").read_text(encoding="utf-8"))
    assert artifact["sha256"] == last["sha256"]
    recomputed = hashlib.sha256(
        json.dumps({k: v for k, v in artifact.items() if k != "sha256"},
                   sort_keys=True).encode("utf-8")).hexdigest()
    assert recomputed == artifact["sha256"]


def test_list_proposals_summaries(tmp_path):
    engine = SelfEvolutionEngine()
    p1 = _proposal(engine, tmp_path, now=NOW, diagnosis="diag-one")
    p2 = _proposal(engine, tmp_path, now=NOW + 1, diagnosis="diag-two")
    engine.save_proposal(p1, tmp_path)
    engine.save_proposal(p2, tmp_path)

    summaries = engine.list_proposals(tmp_path)
    assert len(summaries) == 2
    ids = {s["proposal_id"] for s in summaries}
    assert {p1.proposal_id, p2.proposal_id} == ids
    assert all(s["current_stage"] == "PROPOSED" for s in summaries)
    assert all(s["sha256"] for s in summaries)


def test_cli_requires_full_analysis(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_ROOT", str(tmp_path))
    rc = cli.main(["--diagnosis", "some diagnosis", "--proposals-dir", str(tmp_path)])
    assert rc == 2  # missing analysis fields


def test_cli_creates_persisted_proposal(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_ROOT", str(tmp_path))
    rc = cli.main([
        "--diagnosis", "score drift not surfaced",
        "--problem", "problem",
        "--evidence", "evidence",
        "--subsystem", "architecture/learning",
        "--expected-benefit", "benefit",
        "--risk", "risk",
        "--affected-contracts", "contracts",
        "--benchmark-baseline", "baseline",
        "--proposed-change", "change",
        "--validation-method", "validation",
        "--rollback-trigger", "coverage_drop",
        "--proposals-dir", str(tmp_path),
    ])
    assert rc == 0

    props = list((tmp_path).glob("prop_*.json"))
    assert len(props) == 1
    data = json.loads(props[0].read_text(encoding="utf-8"))
    assert data["current_stage"] == "PROPOSED"
    assert data["requires_human"] is True          # AI proposals need a human gate
    assert data["analysis"]["subsystem"] == "architecture/learning"
    assert data["rollback_plan"]["trigger"] == "coverage_drop"


def test_cli_list_flag(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AHOS_ROOT", str(tmp_path))
    assert cli.main(["--list", "--proposals-dir", str(tmp_path)]) == 0
    assert "no proposals persisted" in capsys.readouterr().out


def test_cli_lane_a_forbidden_is_born_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_ROOT", str(tmp_path))
    rc = cli.main([
        "--diagnosis", "lane-a change attempt",
        "--target-scope", "LANE_A_FORBIDDEN",
        "--problem", "p", "--evidence", "e", "--subsystem", "s",
        "--expected-benefit", "b", "--risk", "r", "--affected-contracts", "c",
        "--benchmark-baseline", "bl", "--proposed-change", "ch",
        "--validation-method", "v",
        "--proposals-dir", str(tmp_path),
    ])
    assert rc == 0
    data = json.loads(next((tmp_path).glob("prop_*.json")).read_text(encoding="utf-8"))
    assert data["current_stage"] == "REJECTED"


def test_classification_is_validated(tmp_path):
    engine = SelfEvolutionEngine()
    # unknown classification rejected loudly
    with pytest.raises(ValueError):
        engine.create_proposal(
            detected_by="a", diagnosis="d", proposed_by="b", is_ai=True,
            target_scope="B_ONLY", governance_touching=False,
            candidate_diff_ref="r", test_battery=[], rollback_plan={"trigger": "t"},
            classification="NOT_A_CLASS", now=NOW)


def test_classification_and_evidence_links_roundtrip(tmp_path):
    engine = SelfEvolutionEngine()
    prop = engine.create_proposal(
        detected_by="AG-1", diagnosis="score drift not surfaced",
        proposed_by="AG-2", is_ai=True, target_scope="B_ONLY",
        governance_touching=False, candidate_diff_ref="diff_01",
        test_battery=["test_a"], rollback_plan={"trigger": "coverage_drop",
                                                "action": "revert"},
        classification="LEARNING",
        evidence_links={
            "health_snapshot": "reports/canonical_health_snapshot.json",
            "diagnostic_finding": "score_drift.DRIFT_DETECTED",
            "benchmark": "reports/benchmark_run_baseline_20260820.json",
        },
        analysis={
            "problem": "p", "evidence": "e", "subsystem": "s",
            "expected_benefit": "b", "risk": "r", "affected_contracts": "c",
            "benchmark_baseline": "bl", "proposed_change": "ch",
            "validation_method": "v",
        },
        now=NOW,
    )
    path = engine.save_proposal(prop, tmp_path)
    loaded = engine.load_proposal(prop.proposal_id, tmp_path)
    assert loaded.classification == "LEARNING"
    assert loaded.evidence_links["health_snapshot"].endswith(
        "canonical_health_snapshot.json")
    assert loaded.evidence_links["diagnostic_finding"] == "score_drift.DRIFT_DETECTED"


def test_cli_accepts_classification_and_evidence_links(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_ROOT", str(tmp_path))
    rc = cli.main([
        "--diagnosis", "benchmark regression",
        "--classification", "PERFORMANCE",
        "--evidence-link-benchmark", "reports/benchmark_run_baseline_20260820.json",
        "--problem", "p", "--evidence", "e", "--subsystem", "s",
        "--expected-benefit", "b", "--risk", "r", "--affected-contracts", "c",
        "--benchmark-baseline", "bl", "--proposed-change", "ch",
        "--validation-method", "v",
        "--proposals-dir", str(tmp_path),
    ])
    assert rc == 0
    data = json.loads(next((tmp_path).glob("prop_*.json")).read_text(encoding="utf-8"))
    assert data["classification"] == "PERFORMANCE"
    assert data["evidence_links"]["benchmark"] == \
        "reports/benchmark_run_baseline_20260820.json"


def test_validate_proposal_pass_and_incomplete(tmp_path):
    engine = SelfEvolutionEngine()

    def _mk(**kw):
        base = dict(
            detected_by="AG-1", diagnosis="d", proposed_by="AG-2",
            is_ai=True, target_scope="B_ONLY", governance_touching=False,
            candidate_diff_ref="diff", test_battery=["t"],
            rollback_plan={"trigger": "x", "action": "revert"},
            classification="LEARNING",
            evidence_links={"benchmark": "reports/benchmark_run_baseline.json"},
            analysis={f: f for f in SelfEvolutionEngine.REQUIRED_ANALYSIS_FIELDS},
        )
        base.update(kw)
        return engine.create_proposal(**base, now=NOW)

    # complete proposal passes
    ok = _mk()
    report = engine.validate_proposal(ok)
    assert report["verdict"] == "PASS"
    assert report["missing_fields"] == [] and report["contract_violations"] == []

    # missing analysis + rollback trigger -> INCOMPLETE
    incomplete = _mk(rollback_plan={"action": "revert"},
                     analysis={"problem": "p"})
    report = engine.validate_proposal(incomplete)
    assert report["verdict"] == "INCOMPLETE"
    assert "analysis.evidence" in report["missing_fields"]
    assert "rollback_plan.trigger" in report["missing_fields"]

    # is_ai without requires_human -> violation
    bad_gov = engine.create_proposal(
        detected_by="a", diagnosis="d", proposed_by="b", is_ai=True,
        target_scope="B_ONLY", governance_touching=False,
        candidate_diff_ref="r", test_battery=[], rollback_plan={"trigger": "t"},
        classification="ARCHITECTURE",
        analysis={f: f for f in SelfEvolutionEngine.REQUIRED_ANALYSIS_FIELDS},
        now=NOW)
    bad_gov.requires_human = False   # simulate a defective proposal
    report = engine.validate_proposal(bad_gov)
    assert report["verdict"] == "INCOMPLETE"
    assert any("requires_human" in v for v in report["contract_violations"])


def test_performance_proposal_requires_benchmark_evidence(tmp_path):
    engine = SelfEvolutionEngine()
    prop = engine.create_proposal(
        detected_by="a", diagnosis="perf", proposed_by="b", is_ai=True,
        target_scope="B_ONLY", governance_touching=False,
        candidate_diff_ref="r", test_battery=["t"],
        rollback_plan={"trigger": "x", "action": "revert"},
        classification="PERFORMANCE",
        analysis={f: f for f in SelfEvolutionEngine.REQUIRED_ANALYSIS_FIELDS},
        evidence_links={},   # no benchmark link
        now=NOW)
    report = engine.validate_proposal(prop)
    assert report["verdict"] == "INCOMPLETE"
    assert any("evidence_links.benchmark" in m for m in report["missing_fields"])
