"""Reasoning inventory. Not an orchestrator.

AHOS has deterministic FSMs, scoring, calibration, and advisory council
disagreement. It does not have a domain-general reasoning orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architecture.cognitive.contracts import CapabilityStatus


@dataclass(frozen=True)
class ReasoningInventory:
    modes: dict[str, CapabilityStatus]
    orchestrator: CapabilityStatus
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "modes": {k: v.value for k, v in self.modes.items()},
            "orchestrator": self.orchestrator.value,
            "notes": list(self.notes),
        }


def current_reasoning_inventory() -> ReasoningInventory:
    return ReasoningInventory(
        modes={
            "deductive": CapabilityStatus.PARTIAL,  # lifecycle/security FSMs
            "inductive": CapabilityStatus.PARTIAL,  # calibration / score ledger
            "abductive": CapabilityStatus.NOT_IMPLEMENTED,
            "probabilistic": CapabilityStatus.PARTIAL,  # scoring + calibration
            "analogical": CapabilityStatus.NOT_IMPLEMENTED,
            "temporal": CapabilityStatus.PARTIAL,  # observation age / STALE
            "causal": CapabilityStatus.NOT_IMPLEMENTED,
            "counterfactual": CapabilityStatus.PARTIAL,  # hindsight, financial only
            "adversarial": CapabilityStatus.PARTIAL,  # red-team / council / security
            "multi_step": CapabilityStatus.PARTIAL,  # pipelines, not a general planner
        },
        orchestrator=CapabilityStatus.NOT_IMPLEMENTED,
        notes=(
            "Do not treat scoring.engine or council synthesis as a reasoning orchestrator.",
            "Evidence provenance must survive any future orchestrator.",
        ),
    )
