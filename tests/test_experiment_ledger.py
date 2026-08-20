#!/usr/bin/env python3
"""W39: learning from failed improvements + knowledge compression.

Pins:
  * record() persists an append-only, integrity-sha256'd experiment;
  * the result vocabulary is enforced (unknown results rejected);
  * lookup() dedups: re-recording the same hypothesis+change returns the
    existing record (a failed optimization is remembered, not retried);
  * failed-experiment reasons are recorded so AHOS learns what did NOT work;
  * read_all/count survive a fresh ledger and tampered lines.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evolution.experiment import (  # noqa: E402
    FAILURE_REASONS,
    RESULTS,
    ExperimentLedger,
)

NOW = 1756000000.0


def test_record_and_read_roundtrip(tmp_path):
    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    rec = ledger.record(
        hypothesis="batched regime queries are faster",
        baseline="475.6 ms per 500 tokens",
        attempted_change="single IN-query instead of per-token connections",
        result="IMPROVED", reusable_lesson="batching DB access compounds",
        evidence_refs=["reports/benchmark_regime_batching.json"],
        now=NOW)
    assert rec.experiment_id
    assert rec.sha256 and len(rec.sha256) == 64

    all_recs = ledger.read_all()
    assert len(all_recs) == 1
    assert all_recs[0]["result"] == "IMPROVED"
    assert ledger.count() == 1


def test_failure_reason_is_recorded(tmp_path):
    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    rec = ledger.record(
        hypothesis="vectorizing mean/var speeds up regime fit",
        baseline="531 ms per 2000 tokens",
        attempted_change="E[x^2]-E[x]^2 vectorization",
        result="NO_MEANINGFUL_CHANGE",
        failure_reason="OPTIMIZATION_BELOW_NOISE_FLOOR",
        reusable_lesson="mean/var was not the bottleneck; quantile was",
        now=NOW)
    assert rec.failure_reason == "OPTIMIZATION_BELOW_NOISE_FLOOR"
    loaded = ledger.read_all()[0]
    assert loaded["reusable_lesson"].endswith("quantile was")


def test_result_vocabulary_enforced(tmp_path):
    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    with pytest.raises(ValueError):
        ledger.record(hypothesis="h", baseline="b", attempted_change="c",
                      result="MAGICAL_IMPROVEMENT", now=NOW)


def test_failure_reason_vocabulary_enforced(tmp_path):
    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    with pytest.raises(ValueError):
        ledger.record(hypothesis="h", baseline="b", attempted_change="c",
                      result="REGRESSION", failure_reason="MAGIC", now=NOW)


def test_lookup_dedups_failed_experiment(tmp_path):
    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    ledger.record(hypothesis="memoize regime", baseline="b",
                  attempted_change="lru_cache on price tuple",
                  result="NO_MEANINGFUL_CHANGE",
                  failure_reason="NO_MEANINGFUL_GAIN", now=NOW)

    # same hypothesis+change -> EXISTING record returned, not re-recorded
    existing = ledger.lookup("memoize regime", "lru_cache on price tuple")
    assert existing is not None
    assert existing.result == "NO_MEANINGFUL_CHANGE"
    assert ledger.count() == 1

    # different change -> not found
    assert ledger.lookup("memoize regime", "different change") is None


def test_tampered_line_is_skipped_not_fatal(tmp_path):
    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    ledger.record(hypothesis="h", baseline="b", attempted_change="c",
                  result="IMPROVED", now=NOW)
    with ledger.path.open("a", encoding="utf-8") as fh:
        fh.write("{this is not json}\n")
    assert ledger.count() == 1   # tampered line skipped, valid line survives


def test_failure_vocabulary_is_complete():
    assert "OPTIMIZATION_BELOW_NOISE_FLOOR" in FAILURE_REASONS
    assert "OUTPUT_PARITY_FAILED" in FAILURE_REASONS
    assert "REGRESSION_DETECTED" in FAILURE_REASONS
    assert set(RESULTS) >= {"IMPROVED", "NO_MEANINGFUL_CHANGE", "REGRESSION",
                            "NOT_COMPARABLE", "INSUFFICIENT_DATA",
                            "GOVERNANCE_BLOCKED"}


def test_recurring_finding_is_marked(tmp_path):
    """W39 P14: if the experiment ledger already contains a change matching a
    finding's investigation, the finding is marked RECURRING_FINDING so the
    same failed optimization is not silently re-proposed."""
    from architecture.evolution.experiment import ExperimentLedger
    from architecture.evolution.findings import derive_findings

    ledger = ExperimentLedger(tmp_path / "experiments.jsonl")
    # the ledger records an attempted change whose text matches the
    # SCORE_DRIFT finding's investigation prefix
    ledger.record(hypothesis="time-segment calibration rates",
                  attempted_change="time-segment calibration rates",
                  baseline="b", result="NO_MEANINGFUL_CHANGE",
                  failure_reason="NO_MEANINGFUL_GAIN", now=NOW)

    # a snapshot that produces a SCORE_DRIFT finding whose investigation
    # matches the previously-attempted change
    h = {
        "overall_verdict": "GREEN",
        "self_observation": {
            "provider_failure_rates": {"total_failure_events": 0},
            "data_completeness": {"error": "NO_DATA"},
            "score_drift": {"verdict": "DRIFT_DETECTED",
                            "first_trigger_at_sample": 42},
            "storage_growth": {"total_bytes": 1024},
            "test_health": {"pytest": {"present": True, "exit_code": 0},
                            "validate": {"present": True, "exit_code": 0}},
        },
    }

    marked = derive_findings(h, now=NOW, experiment_ledger=ledger)
    drift = next(f for f in marked if f.kind == "SCORE_DRIFT")
    assert "RECURRING_FINDING" in drift.recommended_investigation
    assert "previously attempted" in drift.recommended_investigation

    # without a matching ledger entry, no recurrence mark
    clean = derive_findings(h, now=NOW)
    clean_drift = next(f for f in clean if f.kind == "SCORE_DRIFT")
    assert "RECURRING_FINDING" not in clean_drift.recommended_investigation
