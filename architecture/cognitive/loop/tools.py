"""Tool-selection interface. P3 is INTERFACE_ONLY / PARTIAL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from architecture.cognitive.contracts import CapabilityStatus


@dataclass(frozen=True)
class ToolSelectionPlan:
    status: str = CapabilityStatus.NOT_IMPLEMENTED.value
    note: str = (
        "P3 does not select or execute tools. Future: TASK→capability match→"
        "cost/risk→selection→result→memory. Execution remains forbidden here."
    )

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "note": self.note}


def plan_tools(_task: Any) -> ToolSelectionPlan:
    return ToolSelectionPlan()
