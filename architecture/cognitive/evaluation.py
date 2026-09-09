"""Evaluation interfaces. Fabricated intelligence scores are rejected."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architecture.cognitive.contracts import CapabilityAssessment, CapabilityStatus


class FabricatedScoreError(ValueError):
    """Raised when a caller tries to record an unaudited intelligence percentage."""


ALLOWED_DATA_LABELS = frozenset({"REAL", "SYNTHETIC", "SIMULATION", "TEST", "UNKNOWN"})


def refuse_fabricated_score(label: str, value: float) -> None:
    """99.9% intelligence is an aspiration, not a recordable property."""
    raise FabricatedScoreError(
        f"Refusing to record unaudited score {label}={value}. "
        "Numerical targets require a documented measurement methodology and evidence."
    )


@dataclass(frozen=True)
class EvaluationResult:
    """A labeled metric. value may be None when the measurement was refused."""

    metric_name: str
    value: float | None
    data_label: str
    methodology_ref: str
    refused: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "data_label": self.data_label,
            "methodology_ref": self.methodology_ref,
            "refused": self.refused,
        }


def record_evaluation_result(
    *,
    metric_name: str,
    value: float | None,
    data_label: str,
    methodology_ref: str,
    allow_unmethodical_percentage: bool = False,
) -> EvaluationResult:
    label = str(data_label).strip().upper()
    if label not in ALLOWED_DATA_LABELS:
        raise ValueError(f"data_label must be typed; got {data_label!r}")
    if (
        value is not None
        and value >= 0.999
        and not methodology_ref.strip()
        and not allow_unmethodical_percentage
    ):
        refuse_fabricated_score(metric_name, value)
    return EvaluationResult(
        metric_name=metric_name,
        value=value,
        data_label=label,
        methodology_ref=methodology_ref,
        refused=False,
    )


@dataclass(frozen=True)
class BenchmarkPlanRef:
    """Pointer to the written benchmark plan — not a result."""

    path: str = "reports/agi_aci_evolution/BENCHMARK_PLAN.md"
    results_fabricated: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "results_fabricated": self.results_fabricated,
            "status": CapabilityStatus.DOCUMENTATION_ONLY.value,
        }


def evaluation_capability_claim() -> CapabilityAssessment:
    return CapabilityAssessment(
        capability="evaluation_framework",
        status=CapabilityStatus.PARTIAL,
        evidence=(
            "architecture/cognitive/evaluation.py",
            "architecture/cognitive/benchmark/",
            "reports/agi_aci_evolution/P4_1_COGNITIVE_BENCHMARK_REPORT.md",
            "reports/agi_aci_evolution/BENCHMARK_PLAN.md",
        ),
        architecture_target=(
            "Compare against current AHOS, previous best, simple baseline, "
            "statistical baseline, ML baseline, external tool baseline."
        ),
        gap=(
            "P4.1 executed a SYNTHETIC cognitive-correctness suite (not an AGI suite). "
            "Soak/financial calibration and six-baseline comparison remain unmeasured."
        ),
    )
