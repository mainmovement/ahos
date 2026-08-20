#!/usr/bin/env python3
"""Closed-loop validation verdicts (W36 phase 6).

Pins the verdict vocabulary and its honesty rules:
  * a headline regression OR any failed test => REGRESSION_DETECTED
  * an improvement on a headline metric + green tests => IMPROVEMENT_SUPPORTED
  * sub-threshold deltas => NO_MEASURABLE_IMPROVEMENT
  * no comparable rows => NOT_COMPARABLE
  * governance-required proposals => GOVERNANCE_REQUIRED regardless of numbers
  * latency direction: lower is better; throughput: higher is better
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evolution.validate import (  # noqa: E402
    MEANINGFUL_DELTA_PCT,
    validate_proposal_evidence,
)


def _diff_row(benchmark, metric, delta_pct, comparable=True):
    return {"benchmark": benchmark, "metric": metric, "delta_pct": delta_pct,
            "comparable": comparable}


def test_improvement_supported_when_headline_improves_and_tests_pass():
    v = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("vectorized_backtest", "evaluations_per_sec", +15.0),
            _diff_row("quantstats_tearsheet", "latency_per_tearsheet_ms", -12.0),
        ]},
        tests_passed=120, tests_failed=0,
    )
    assert v.verdict == "IMPROVEMENT_SUPPORTED"
    assert v.test_outcome == "ALL_PASSED"
    assert any("improved" in f for f in v.findings)


def test_regression_detected_on_any_headline_regression():
    v = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("vectorized_backtest", "evaluations_per_sec", +15.0),
            _diff_row("event_driven_backtest", "events_per_sec", -8.0),
        ]},
        tests_passed=120, tests_failed=0,
    )
    assert v.verdict == "REGRESSION_DETECTED"
    assert any("REGRESSED" in f for f in v.findings)


def test_regression_detected_on_failed_tests_even_with_improvements():
    v = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("vectorized_backtest", "evaluations_per_sec", +20.0),
        ]},
        tests_passed=119, tests_failed=1,
    )
    assert v.verdict == "REGRESSION_DETECTED"
    assert v.test_outcome == "FAILURES"


def test_no_measurable_improvement_below_threshold():
    v = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("vectorized_backtest", "evaluations_per_sec", +2.0),
            _diff_row("quantstats_tearsheet", "latency_per_tearsheet_ms", -1.0),
        ]},
        tests_passed=10, tests_failed=0,
    )
    assert v.verdict == "NO_MEASURABLE_IMPROVEMENT"
    assert any("below meaningful threshold" in f for f in v.findings)


def test_not_comparable_without_rows():
    v = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("vectorized_backtest", "evaluations_per_sec", 15.0,
                      comparable=False),
        ]},
        tests_passed=10, tests_failed=0,
    )
    assert v.verdict == "NOT_COMPARABLE"


def test_not_comparable_without_benchmark():
    v = validate_proposal_evidence(tests_passed=10, tests_failed=0)
    assert v.verdict == "NOT_COMPARABLE"
    assert v.test_outcome == "ALL_PASSED"


def test_governance_required_overrides_numbers():
    v = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("vectorized_backtest", "evaluations_per_sec", +50.0),
        ]},
        tests_passed=120, tests_failed=0,
        governance_required=True,
    )
    assert v.verdict == "GOVERNANCE_REQUIRED"
    assert any("human gate" in f for f in v.findings)


def test_latency_direction_is_lower_better():
    # latency improved = negative delta
    v = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("olap_analytics_bridge", "latency_per_aggregation_ms", -25.0),
        ]},
        tests_passed=5, tests_failed=0,
    )
    assert v.verdict == "IMPROVEMENT_SUPPORTED"
    # latency regressed = positive delta
    v2 = validate_proposal_evidence(
        benchmark_diff={"rows": [
            _diff_row("olap_analytics_bridge", "latency_per_aggregation_ms", +25.0),
        ]},
        tests_passed=5, tests_failed=0,
    )
    assert v2.verdict == "REGRESSION_DETECTED"


def test_threshold_constant_is_sane():
    assert 5.0 <= MEANINGFUL_DELTA_PCT <= 10.0
