#!/usr/bin/env python3
"""W39: evidence-driven improvement selection.

Pins:
  * candidates are ranked lexicographically by impact -> evidence ->
    leverage -> reversibility -> cost;
  * a candidate missing any required dimension is NOT_COMPARABLE and never
    receives a fabricated mid-score;
  * if nothing is comparable the verdict is INSUFFICIENT_EVIDENCE, never a
    fake ranking;
  * determinism: identical input => identical selection;
  * the module only COMPARES — it never approves or merges anything.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evolution.selection import (  # noqa: E402
    ImprovementCandidate,
    ImprovementSelectionEngine,
    candidate_id,
)


def _cand(cid, **kw):
    base = dict(
        candidate_id=cid,
        finding_id="f1",
        classification="PERFORMANCE",
        subsystem="architecture/learning",
        problem=f"problem {cid}",
        proposed_change="change",
        expected_benefit="benefit",
        impact="HIGH",
        confidence="OBSERVED",
        reversibility="HIGH",
        leverage="HIGH",
        implementation_cost="LOW",
        benchmark_requirement=True,
        validation_requirement="full pytest + benchmark compare",
    )
    base.update(kw)
    return ImprovementCandidate(**base)


def test_lexicographic_ranking_impact_then_evidence():
    c_low = _cand("low", impact="LOW", confidence="OBSERVED")
    c_high = _cand("high", impact="HIGH", confidence="CORRELATED")
    result = ImprovementSelectionEngine.evaluate([c_low, c_high])
    assert result["verdict"] == "SELECTED"
    assert result["selected"] == "high"      # impact outranks evidence


def test_evidence_breaks_impact_tie():
    c_derived = _cand("derived", impact="HIGH", confidence="DERIVED")
    c_observed = _cand("observed", impact="HIGH", confidence="OBSERVED")
    result = ImprovementSelectionEngine.evaluate([c_derived, c_observed])
    assert result["selected"] == "observed"  # stronger evidence wins tie


def test_leverage_breaks_evidence_tie():
    c_low_lev = _cand("l", impact="HIGH", confidence="OBSERVED", leverage="LOW")
    c_high_lev = _cand("h", impact="HIGH", confidence="OBSERVED", leverage="HIGH")
    result = ImprovementSelectionEngine.evaluate([c_low_lev, c_high_lev])
    assert result["selected"] == "h"         # leverage wins (intelligence multiplication)


def test_incomplete_candidate_is_not_comparable():
    c_missing = _cand("m", reversibility=None, leverage=None)
    c_ok = _cand("ok")
    result = ImprovementSelectionEngine.evaluate([c_missing, c_ok])
    assert result["verdict"] == "SELECTED"
    assert result["selected"] == "ok"
    nc = next(e for e in result["ranking"] if e["candidate_id"] == "m")
    assert nc["status"] == "NOT_COMPARABLE"
    assert "reversibility" in nc["missing_dimensions"]
    # the incomplete candidate never got a fabricated rank
    assert nc["reversibility"] is None


def test_no_comparable_candidate_is_insufficient_evidence():
    c = _cand("only", impact=None, confidence=None, reversibility=None,
              leverage=None, benchmark_requirement=False)
    result = ImprovementSelectionEngine.evaluate([c])
    assert result["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert result["selected"] is None


def test_deterministic_selection():
    cands = [_cand("a", impact="MEDIUM", confidence="DERIVED"),
             _cand("b", impact="HIGH", confidence="CORRELATED")]
    r1 = ImprovementSelectionEngine.evaluate(cands)
    r2 = ImprovementSelectionEngine.evaluate(cands)
    assert r1["selected"] == r2["selected"] == "b"
    assert r1["ranking"] == r2["ranking"]


def test_cost_breaks_final_tie():
    c_cheap = _cand("cheap", impact="MEDIUM", confidence="OBSERVED",
                    leverage="MEDIUM", reversibility="HIGH",
                    implementation_cost="LOW")
    c_expensive = _cand("expensive", impact="MEDIUM", confidence="OBSERVED",
                        leverage="MEDIUM", reversibility="HIGH",
                        implementation_cost="HIGH")
    result = ImprovementSelectionEngine.evaluate([c_expensive, c_cheap])
    assert result["selected"] == "cheap"


def test_candidate_id_is_deterministic():
    assert candidate_id("same problem") == candidate_id("same problem")
    assert candidate_id("same problem") != candidate_id("other problem")


def test_candidates_from_findings_and_selection():
    """W39 end-to-end: findings -> candidates -> selection chooses the
    highest-leverage, best-evidenced candidate."""
    from architecture.evolution.findings import (
        DiagnosticFinding,
        candidates_from_findings,
        select_improvement,
    )

    findings = [
        DiagnosticFinding(
            finding_id="f1", kind="UNKNOWN_GROWTH", severity="HIGH",
            subsystem="architecture/providers", evidence="unknown share 80%",
            timestamp_utc="t", confidence="OBSERVED",
            recommended_investigation="add provider coverage",
            actionable_internally=True),
        DiagnosticFinding(
            finding_id="f2", kind="ORPHAN", severity="LOW",
            subsystem="architecture", evidence="isolated module x",
            timestamp_utc="t", confidence="OBSERVED",
            recommended_investigation="review",
            actionable_internally=True),
    ]

    cands = candidates_from_findings(findings)
    assert len(cands) == 2
    assert cands[0].finding_id == "f1"
    assert cands[0].leverage == "HIGH"       # UNKNOWN_GROWTH is high-leverage
    assert cands[1].leverage == "LOW"        # ORPHAN is low-leverage

    sel = select_improvement(findings)
    assert sel["verdict"] == "SELECTED"
    # UNKNOWN_GROWTH (HIGH impact + HIGH leverage + OBSERVED) outranks ORPHAN
    assert sel["selected"] == candidates_from_findings(findings)[0].candidate_id


def test_select_highest_value_with_ledger_recurrence(tmp_path):
    """W39 P13: one-call priority re-evaluation — a known-failed optimization
    is downgraded (confidence->UNKNOWN) so it cannot win selection."""
    from architecture.evolution.experiment import ExperimentLedger
    from architecture.evolution.findings import DiagnosticFinding
    from architecture.evolution.selection import select_highest_value

    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    ledger.record(hypothesis="time-segment calibration",
                  attempted_change="time-segment calibration",
                  baseline="b", result="NO_MEANINGFUL_CHANGE",
                  failure_reason="NO_MEANINGFUL_GAIN", now=time.time())

    findings = [
        DiagnosticFinding(
            finding_id="f1", kind="SCORE_DRIFT", severity="MEDIUM",
            subsystem="architecture/learning", evidence="score drift",
            timestamp_utc="t", confidence="OBSERVED",
            recommended_investigation="time-segment calibration rates; "
                                      "investigate what changed",
            actionable_internally=True, requires_governance=True),
        DiagnosticFinding(
            finding_id="f2", kind="UNKNOWN_GROWTH", severity="HIGH",
            subsystem="architecture/providers", evidence="unknown 80%",
            timestamp_utc="t", confidence="OBSERVED",
            recommended_investigation="add provider coverage",
            actionable_internally=True),
    ]

    sel = select_highest_value(findings=findings, experiment_ledger=ledger)
    assert sel["verdict"] == "SELECTED"
    assert sel["selected"] is not None
    # the recurring candidate (SCORE_DRIFT fix) has confidence downgraded to
    # UNKNOWN, so the non-recurring UNKNOWN_GROWTH fix wins selection
    ranked = {r["candidate_id"]: r for r in sel["ranking"]}
    assert any(r["evidence"] == "UNKNOWN" for r in sel["ranking"])
    winner = ranked[sel["selected"]]
    assert winner["evidence"] == "OBSERVED"


def test_select_highest_value_no_findings():
    from architecture.evolution.selection import select_highest_value
    sel = select_highest_value(findings=[])
    assert sel["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert sel["selected"] is None
