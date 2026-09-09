"""World-model *boundary* for P3. Not a world model.

P4/P5 may persist ENTITY/STATE/EVENT/RELATION/CAUSE/EFFECT/TIME/UNCERTAINTY/
COUNTERFACTUAL payloads on the P2 store. Storing those keys is not a causal
engine. Operations remain NOT_IMPLEMENTED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architecture.cognitive.contracts import CapabilityStatus
from architecture.cognitive.memory.types import WORLD_MODEL_OBJECT_KINDS


@dataclass(frozen=True)
class WorldModelBoundary:
    status: str = CapabilityStatus.NOT_IMPLEMENTED.value
    allowed_object_kinds: tuple[str, ...] = tuple(sorted(WORLD_MODEL_OBJECT_KINDS))
    note: str = (
        "P3 does not implement a knowledge graph, causal model, or counterfactual "
        "engine. Compatible payload kinds may be stored; that is not a world model."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "allowed_object_kinds": list(self.allowed_object_kinds),
            "note": self.note,
        }


def current_world_model_boundary() -> WorldModelBoundary:
    return WorldModelBoundary()
