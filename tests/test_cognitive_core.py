"""Lane-B cognitive core contracts — fail-closed, no fabricated intelligence."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive import (  # noqa: E402
    CURRENT_AUTONOMY_CEILING,
    AutonomyLevel,
    CapabilityRegister,
    FabricatedScoreError,
    HypothesisState,
    HypothesisStore,
    HypothesisTransitionError,
    LaneAChangeRequired,
    assert_cognitive_sandbox,
    build_self_research_report,
    classify_novelty,
    council_capability_claim,
    current_counterfactual_policy,
    current_reasoning_inventory,
    current_world_model_status,
    load_council_passports,
    propose_lane_b_evolution,
    record_cognitive_experiment,
    refuse_fabricated_score,
)
from architecture.cognitive.evaluation import record_evaluation_result  # noqa: E402
from architecture.cognitive.sandbox import SandboxPolicy, assert_sandbox_holds  # noqa: E402
from architecture.evolution.engine import SelfEvolutionEngine  # noqa: E402

COGNITIVE_DIR = ROOT / "architecture" / "cognitive"
FORBIDDEN = {"discovery", "paper_trading", "telegram_ai", "engine"}


def _module_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            roots.add(n.module.split(".")[0])
    return roots


def test_cognitive_does_not_import_lane_a_or_engine():
    scanned = 0
    for path in sorted(COGNITIVE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        scanned += 1
        bad = FORBIDDEN & _module_roots(path)
        assert not bad, f"{path.relative_to(ROOT)} imports {sorted(bad)}"
    assert scanned >= 10


def test_autonomy_ceiling_is_analyze_not_live():
    assert CURRENT_AUTONOMY_CEILING == AutonomyLevel.L1_ANALYZE
    assert AutonomyLevel.L6_LIMITED_LIVE_EXECUTION.value != CURRENT_AUTONOMY_CEILING.value


def test_hypothesis_lifecycle_and_supported_requires_experiment(tmp_path: Path):
    store = HypothesisStore(tmp_path / "hypotheses.jsonl")
    rec = store.propose("Join pairs remain zero until outcomes match predictions.")
    assert rec.hypothesis_id == "HYP-000001"
    assert rec.state == HypothesisState.PROPOSED.value
    with pytest.raises(HypothesisTransitionError):
        store.transition(rec.hypothesis_id, HypothesisState.SUPPORTED)
    store.transition(rec.hypothesis_id, HypothesisState.UNDER_REVIEW)
    store.transition(rec.hypothesis_id, HypothesisState.TESTING, experiment_id="exp_test")
    supported = store.transition(rec.hypothesis_id, HypothesisState.SUPPORTED)
    assert supported.state == HypothesisState.SUPPORTED.value
    assert "exp_test" in supported.experiment_ids


def test_record_cognitive_experiment_reuses_ledger(tmp_path: Path):
    store = HypothesisStore(tmp_path / "hypotheses.jsonl")
    rec = store.propose("Novelty is not truth.")
    exp = record_cognitive_experiment(
        hypothesis_store=store,
        hypothesis_id=rec.hypothesis_id,
        baseline="no experiment attached",
        method="attach ExperimentLedger row",
        result="INSUFFICIENT_DATA",
        ledger_path=tmp_path / "experiments.jsonl",
        evidence_refs=["tests/test_cognitive_core.py"],
        reusable_lesson="Cognitive experiments must not overwrite soak rows.",
    )
    assert exp.hypothesis_id == rec.hypothesis_id
    assert exp.experiment_id
    updated = store.get(rec.hypothesis_id)
    assert updated is not None
    assert updated.state == HypothesisState.TESTING.value
    assert exp.experiment_id in updated.experiment_ids
    ledger_text = (tmp_path / "experiments.jsonl").read_text(encoding="utf-8")
    assert rec.statement in ledger_text
    assert "COGNITIVE" in ledger_text


def test_gaps_cannot_close_without_evidence(tmp_path: Path):
    reg = CapabilityRegister(tmp_path / "gaps.jsonl")
    added = reg.seed_baseline()
    assert added >= 5
    with pytest.raises(ValueError):
        reg.close("ACI-GAP-001", evidence="   ")
    still_open = {g.gap_id: g.closed for g in reg.all()}
    assert still_open["ACI-GAP-001"] is False
    closed = reg.close("ACI-GAP-001", evidence="synthetic-close-for-test-only")
    assert closed.closed is True
    assert closed.closed_evidence == "synthetic-close-for-test-only"


def test_refuse_fabricated_intelligence_score():
    with pytest.raises(FabricatedScoreError):
        refuse_fabricated_score("agi_accuracy", 0.999)
    with pytest.raises(FabricatedScoreError):
        record_evaluation_result(
            metric_name="intelligence",
            value=0.999,
            data_label="TEST",
            methodology_ref="",
        )


def test_sandbox_holds_and_rejects_unsafe_policy():
    assert_cognitive_sandbox()
    with pytest.raises(RuntimeError):
        assert_sandbox_holds(SandboxPolicy(paper_only=False))
    with pytest.raises(RuntimeError):
        assert_sandbox_holds(SandboxPolicy(may_write_lane_a=True))
    with pytest.raises(RuntimeError):
        assert_sandbox_holds(SandboxPolicy(may_self_approve_evolution=True))
    with pytest.raises(RuntimeError):
        assert_sandbox_holds(SandboxPolicy(may_enable_live_trading=True))
    with pytest.raises(RuntimeError):
        assert_sandbox_holds(SandboxPolicy(may_start_runtime_daemon=True))


def test_lane_a_evolution_is_stopped():
    with pytest.raises(LaneAChangeRequired):
        propose_lane_b_evolution(
            diagnosis="would touch discovery",
            detected_by="test",
            proposed_by="test",
            is_ai=True,
            candidate_diff_ref="none",
            test_battery=["tests/test_cognitive_core.py"],
            rollback_plan={"trigger": "any", "action": "revert"},
            target_scope="LANE_A_FORBIDDEN",
        )


def test_lane_b_evolution_reuses_engine_and_does_not_self_approve():
    engine = SelfEvolutionEngine()
    prop = propose_lane_b_evolution(
        diagnosis="Add cognitive hypothesis JSONL store",
        detected_by="test_cognitive_core",
        proposed_by="cursor-agent",
        is_ai=True,
        candidate_diff_ref="architecture/cognitive/hypothesis.py",
        test_battery=["tests/test_cognitive_core.py"],
        rollback_plan={"trigger": "tests fail", "action": "revert commit"},
        analysis={
            "problem": "no hypothesis lifecycle",
            "evidence": "audit",
            "subsystem": "architecture.cognitive",
            "expected_benefit": "provenance",
            "risk": "duplicate stores",
            "affected_contracts": "none-lane-a",
            "benchmark_baseline": "none",
            "proposed_change": "JSONL HypothesisStore",
            "validation_method": "pytest",
        },
        engine=engine,
    )
    assert prop.target_scope == "B_ONLY"
    assert prop.requires_human is True
    assert prop.current_stage == "PROPOSED"
    ok, msg = engine.advance_stage(
        prop, "APPROVED", evidence_ref="ev", approver="AI_AGENT", is_human_approver=False
    )
    assert ok is False
    assert (
        "HUMAN" in msg
        or "Stage jump" in msg
        or "approver" in msg.lower()
    )
    assert prop.current_stage == "PROPOSED"


def test_self_research_does_not_claim_cloud_sqlite_as_soak():
    report = build_self_research_report(
        snapshot={
            "OBSERVING": 800,
            "RESOLVED": 1482,
            "outcome_labels": 392,
            "eligible_join_pairs_estimate": 0,
            "live_trading_enabled": False,
        },
        data_label="TEST",
        soak_snapshot_is_authoritative=False,
    )
    assert report.soak_snapshot_is_authoritative is False
    assert any("not the Windows soak authority" in x for x in report.what_i_dont_know)
    assert any("eligible_join_pairs_estimate is 0" in x for x in report.where_i_fail)
    assert any("M-GAP-003" in x for x in report.test_next)
    payload = report.as_dict()
    assert payload["snapshot_fields"]["OBSERVING"] == 800


def test_novelty_is_not_truth():
    novel = classify_novelty(
        seen_before=False, evidence_conflict=False, confidence=None, importance_hint=True
    )
    assert novel["class"] == "POTENTIALLY_IMPORTANT_NOVELTY"
    assert novel["novelty_equals_truth"] is False
    assert novel["auto_promote"] is False
    conflict = classify_novelty(
        seen_before=True, evidence_conflict=True, confidence=0.9
    )
    assert conflict["class"] == "CONTRADICTORY"


def test_world_model_and_reasoning_are_honest():
    wm = current_world_model_status()
    assert wm.causal_model.value == "NOT_IMPLEMENTED"
    assert wm.knowledge_graph.value == "NOT_IMPLEMENTED"
    claim = wm.as_claim()
    assert claim.status.value == "NOT_IMPLEMENTED"
    inv = current_reasoning_inventory()
    assert inv.orchestrator.value == "NOT_IMPLEMENTED"
    cf = current_counterfactual_policy()
    assert cf.may_overwrite_observed_outcomes is False
    assert cf.general_engine_status.value == "NOT_IMPLEMENTED"


def test_agent_passports_are_not_memory_bearing():
    passports = load_council_passports()
    assert any(p.agent_id == "AG-01" for p in passports)
    assert any(p.agent_id == "LENS-MUNGER" for p in passports)
    assert all(p.memory_bearing is False for p in passports)
    assert all(p.independent_tools is False for p in passports)
    claim = council_capability_claim()
    assert claim.status.value == "PARTIAL"
