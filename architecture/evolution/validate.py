#!/usr/bin/env python3
"""Closed-loop validation verdicts (W36 phase 6).

Ties an improvement proposal's validation evidence to a single verdict:

    IMPROVEMENT_SUPPORTED   — headline benchmark(s) improved AND tests green
    NO_MEASURABLE_IMPROVEMENT — comparable benchmarks, no meaningful delta
    REGRESSION_DETECTED     — a headline metric regressed OR tests failed
    NOT_COMPARABLE          — no benchmark on both sides (no before/after)
    INSUFFICIENT_DATA       — cohort/benchmark too small to judge
    GOVERNANCE_REQUIRED     — verdict deferred to the human gate (e.g. the
                              proposal touches governance or is AI-proposed)

Honesty rules (mirrors calibration/benchmark discipline):
  * Only headline metrics present in BOTH artifacts can support a verdict.
  * A regression in ANY headline metric OR any failed test => REGRESSION_DETECTED
    (a single win cannot hide a loss elsewhere).
  * Latency metrics improve on NEGATIVE delta; throughput metrics on POSITIVE.
  * This module only JUDGES evidence; it never approves or merges anything —
    the human gate remains mandatory (SelfEvolutionEngine).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

VERDICTS = (
    "IMPROVEMENT_SUPPORTED", "NO_MEASURABLE_IMPROVEMENT", "REGRESSION_DETECTED",
    "NOT_COMPARABLE", "INSUFFICIENT_DATA", "GOVERNANCE_REQUIRED",
)

#: benchmark name -> headline metric -> direction ("higher_better"|"lower_better")
HEADLINE_METRICS: dict[str, dict[str, str]] = {
    "vectorized_backtest": {"evaluations_per_sec": "higher_better"},
    "quantstats_tearsheet": {"latency_per_tearsheet_ms": "lower_better"},
    "olap_analytics_bridge": {"latency_per_aggregation_ms": "lower_better"},
    "streaming_drift_throughput": {"samples_per_sec": "higher_better"},
    "event_driven_backtest": {"events_per_sec": "higher_better"},
}

#: Relative threshold for "meaningful" improvement/regression. A 1% wobble on
#: a noisy micro-benchmark is not evidence either way.
MEANINGFUL_DELTA_PCT = 5.0


@dataclass
class ValidationVerdict:
    proposal_id: str | None = None
    verdict: str = "NOT_COMPARABLE"
    headline_rows: list[dict[str, Any]] = field(default_factory=list)
    test_outcome: str | None = None          # "ALL_PASSED" | "FAILURES" | "UNKNOWN"
    findings: list[str] = field(default_factory=list)
    #: one of "IMPROVEMENT_SUPPORTED" ... "GOVERNANCE_REQUIRED"
    validated_utc: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_improvement(benchmark: str, metric: str, delta_pct: float) -> bool | None:
    """True = improved, False = regressed, None = not meaningful."""
    direction = HEADLINE_METRICS.get(benchmark, {}).get(metric)
    if direction is None or delta_pct is None:
        return None
    if abs(delta_pct) < MEANINGFUL_DELTA_PCT:
        return None
    if direction == "higher_better":
        return delta_pct > 0
    return delta_pct < 0  # lower_better


def validate_proposal_evidence(*, benchmark_diff: dict[str, Any] | None = None,
                               tests_passed: int | None = None,
                               tests_failed: int | None = None,
                               governance_required: bool = False,
                               proposal_id: str | None = None,
                               now_utc: str = "") -> ValidationVerdict:
    """Determine the closed-loop verdict from the evidence provided.

    governance_required (proposal is AI-proposed or governance-touching)
    overrides to GOVERNANCE_REQUIRED — the verdict is deferred to the human
    gate regardless of the numbers, because approval is never automatic.
    """
    import time as _time

    utc = now_utc or _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
    findings: list[str] = []
    rows: list[dict[str, Any]] = []

    if governance_required:
        return ValidationVerdict(
            proposal_id=proposal_id, verdict="GOVERNANCE_REQUIRED",
            headline_rows=[], test_outcome="UNKNOWN",
            findings=["AI-proposed or governance-touching: verdict deferred "
                      "to the human gate; no automated approval is possible"],
            validated_utc=utc)

    test_outcome = "UNKNOWN"
    if tests_passed is not None or tests_failed is not None:
        test_outcome = ("ALL_PASSED" if (tests_failed or 0) == 0
                        else "FAILURES")
        if test_outcome == "FAILURES":
            findings.append(f"{tests_failed} test(s) failed")

    if not benchmark_diff or not benchmark_diff.get("rows"):
        verdict = "NOT_COMPARABLE"
        findings.append("no comparable before/after benchmark evidence")
        return ValidationVerdict(
            proposal_id=proposal_id, verdict=verdict, headline_rows=[],
            test_outcome=test_outcome, findings=findings, validated_utc=utc)

    for r in benchmark_diff["rows"]:
        if not r.get("comparable"):
            continue
        rows.append(r)
        verdict_ = _is_improvement(r["benchmark"], r["metric"], r["delta_pct"])
        if verdict_ is True:
            findings.append(f"{r['benchmark']}.{r['metric']} improved "
                            f"({r['delta_pct']:+.2f}%)")
        elif verdict_ is False:
            findings.append(f"{r['benchmark']}.{r['metric']} REGRESSED "
                            f"({r['delta_pct']:+.2f}%)")
        else:
            findings.append(f"{r['benchmark']}.{r['metric']} delta "
                            f"{r['delta_pct']:+.2f}% below meaningful "
                            f"threshold ({MEANINGFUL_DELTA_PCT}%)")

    if test_outcome == "FAILURES":
        verdict = "REGRESSION_DETECTED"
    elif any("REGRESSED" in f for f in findings):
        verdict = "REGRESSION_DETECTED"
    elif not rows:
        verdict = "NOT_COMPARABLE"
    elif any("improved" in f for f in findings):
        verdict = "IMPROVEMENT_SUPPORTED"
    else:
        verdict = "NO_MEASURABLE_IMPROVEMENT"

    return ValidationVerdict(
        proposal_id=proposal_id, verdict=verdict, headline_rows=rows,
        test_outcome=test_outcome, findings=findings, validated_utc=utc)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("usage: python -m architecture.evolution.validate "
              "<benchmark_diff_artifact.json>")
        sys.exit(2)
    diff = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    v = validate_proposal_evidence(benchmark_diff=diff)
    print(json.dumps(v.as_dict(), indent=2, ensure_ascii=False))
