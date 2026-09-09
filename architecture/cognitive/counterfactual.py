"""Counterfactual policy. Observed outcomes must never be overwritten.

Trading-domain hindsight already exists in architecture/evolution/hindsight.py.
That is not a general world-model counterfactual engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architecture.cognitive.contracts import CapabilityAssessment, CapabilityStatus


@dataclass(frozen=True)
class CounterfactualPolicy:
    may_overwrite_observed_outcomes: bool
    financial_hindsight_status: CapabilityStatus
    general_engine_status: CapabilityStatus
    financial_hindsight_path: str
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "may_overwrite_observed_outcomes": self.may_overwrite_observed_outcomes,
            "financial_hindsight_status": self.financial_hindsight_status.value,
            "general_engine_status": self.general_engine_status.value,
            "financial_hindsight_path": self.financial_hindsight_path,
            "notes": list(self.notes),
        }

    def as_claim(self) -> CapabilityAssessment:
        return CapabilityAssessment(
            capability="counterfactual_engine",
            status=CapabilityStatus.PARTIAL,
            evidence=(
                "architecture/evolution/hindsight.py",
                "architecture/cognitive/counterfactual.py",
                "paper_trading/lessons.py (NO_COUNTERFACTUAL_PROTOCOL_YET for some lesson fields)",
            ),
            architecture_target=(
                "Observed reality vs alternative scenario records that never "
                "mutate observation/outcome tables."
            ),
            gap=(
                "General counterfactual engine is NOT_IMPLEMENTED. Financial "
                "hindsight is out-of-sample review of paper decisions, not a "
                "causal world-model simulator."
            ),
        )


def current_counterfactual_policy() -> CounterfactualPolicy:
    return CounterfactualPolicy(
        may_overwrite_observed_outcomes=False,
        financial_hindsight_status=CapabilityStatus.PARTIAL,
        general_engine_status=CapabilityStatus.NOT_IMPLEMENTED,
        financial_hindsight_path="architecture/evolution/hindsight.py",
        notes=(
            "Hindsight may judge a decision, never justify it (OUT_OF_SAMPLE_REVIEW).",
            "Do not treat displayed-price backtests as realizable exits.",
            "paper_trading/lessons.py still records NO_COUNTERFACTUAL_PROTOCOL_YET "
            "for early/late entry accuracy — that gap remains open.",
        ),
    )
