"""Metric results with mandatory numerator/denominator. No composite AGI score."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architecture.cognitive.benchmark.thresholds import BENCHMARK_VERSION, THRESHOLDS

NOT_MEASURED = "NOT_MEASURED"
NOT_APPLICABLE = "NOT_APPLICABLE"
PASS = "PASS"
FAIL = "FAIL"


@dataclass(frozen=True)
class MetricResult:
    metric_id: str
    name: str
    definition: str
    numerator: float
    denominator: float
    value: float | None
    threshold: float | None
    threshold_kind: str
    threshold_class: str
    status: str
    population: str
    benchmark_version: str
    limitations: str
    n: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "definition": self.definition,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "value": self.value,
            "threshold": self.threshold,
            "threshold_kind": self.threshold_kind,
            "threshold_class": self.threshold_class,
            "status": self.status,
            "population": self.population,
            "benchmark_version": self.benchmark_version,
            "limitations": self.limitations,
            "n": self.n,
        }


def ratio_status(
    *,
    numerator: float,
    denominator: float,
    kind: str,
    threshold: float,
) -> tuple[float | None, str]:
    if denominator == 0:
        return None, NOT_MEASURED
    value = float(numerator) / float(denominator)
    if kind == "ZERO":
        ok = numerator == 0
    elif kind == "MIN":
        ok = value >= threshold
    elif kind == "MAX":
        ok = value <= threshold
    else:
        return value, NOT_APPLICABLE
    return value, PASS if ok else FAIL


def make_metric(
    metric_id: str,
    *,
    name: str,
    definition: str,
    numerator: float,
    denominator: float,
    population: str,
    limitations: str,
    n: int | None = None,
) -> MetricResult:
    spec = THRESHOLDS.get(metric_id, {})
    kind = str(spec.get("kind") or "MIN")
    threshold = spec.get("threshold")
    tclass = str(spec.get("class") or "PROVISIONAL")
    value, status = ratio_status(
        numerator=numerator,
        denominator=denominator,
        kind=kind,
        threshold=float(threshold) if threshold is not None else 0.0,
    )
    return MetricResult(
        metric_id=metric_id,
        name=name,
        definition=definition,
        numerator=float(numerator),
        denominator=float(denominator),
        value=value,
        threshold=None if threshold is None else float(threshold),
        threshold_kind=kind,
        threshold_class=tclass,
        status=status,
        population=population,
        benchmark_version=BENCHMARK_VERSION,
        limitations=limitations,
        n=int(n if n is not None else denominator),
    )


def f1(precision: float | None, recall: float | None) -> tuple[float, float, float]:
    """Return (numerator_proxy, denominator_proxy, value) for harmonic mean reporting."""
    if precision is None or recall is None:
        return 0.0, 0.0, 0.0
    if precision + recall == 0:
        return 0.0, 1.0, 0.0
    value = 2.0 * precision * recall / (precision + recall)
    return value, 1.0, value
