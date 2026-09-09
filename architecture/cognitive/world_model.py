"""World-model *status* — not a causal graph.

AHOS persists observations, overlays, and predictions. That is not a
knowledge graph, temporal causal model, or counterfactual engine.
This module records that fact so later implementations cannot claim
otherwise without evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architecture.cognitive.contracts import CapabilityAssessment, CapabilityStatus


@dataclass(frozen=True)
class WorldModelStatus:
    """Honest inventory of world-model layers."""

    knowledge_graph: CapabilityStatus
    temporal_model: CapabilityStatus
    causal_model: CapabilityStatus
    probabilistic_relationships: CapabilityStatus
    counterfactual_reasoning: CapabilityStatus
    notes: tuple[str, ...]

    def as_claim(self) -> CapabilityAssessment:
        return CapabilityAssessment(
            capability="world_model",
            status=CapabilityStatus.NOT_IMPLEMENTED,
            evidence=(
                "architecture/cognitive/world_model.py:WorldModelStatus",
                "No KnowledgeGraph / CausalModel / CounterfactualEngine types exist in Lane B.",
            ),
            architecture_target=(
                "Knowledge graph + temporal + causal + probabilistic + counterfactual, "
                "none of which may overwrite observed outcomes."
            ),
            gap=(
                "Observations, overlays, and predictions are not a multi-domain world model. "
                "Probabilistic scoring/calibration is a related but distinct layer."
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "knowledge_graph": self.knowledge_graph.value,
            "temporal_model": self.temporal_model.value,
            "causal_model": self.causal_model.value,
            "probabilistic_relationships": self.probabilistic_relationships.value,
            "counterfactual_reasoning": self.counterfactual_reasoning.value,
            "notes": list(self.notes),
            "claim": self.as_claim().as_dict(),
        }


def current_world_model_status() -> WorldModelStatus:
    return WorldModelStatus(
        knowledge_graph=CapabilityStatus.NOT_IMPLEMENTED,
        temporal_model=CapabilityStatus.NOT_IMPLEMENTED,
        causal_model=CapabilityStatus.NOT_IMPLEMENTED,
        probabilistic_relationships=CapabilityStatus.PARTIAL,
        counterfactual_reasoning=CapabilityStatus.NOT_IMPLEMENTED,
        notes=(
            "Probabilistic scoring and calibration exist in Lane A/B evidence surfaces; "
            "they are not a world-model causal layer.",
            "Observation rows are not entities in a multi-domain world model.",
            "Do not treat DexScreener/Gecko snapshots as a knowledge graph.",
            "architecture/evolution/hindsight.py is financial out-of-sample review, "
            "not this world-model layer.",
        ),
    )
