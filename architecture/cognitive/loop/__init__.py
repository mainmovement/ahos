"""P3 cognitive loop: retrieve → assemble → reason → critique → learn → remember."""

from architecture.cognitive.loop.adapters import (
    finance_observation,
    operations_observation,
    science_observation,
    software_observation,
)
from architecture.cognitive.loop.benchmark import run_memory_vs_no_memory
from architecture.cognitive.loop.context import assemble_context
from architecture.cognitive.loop.contracts import (
    CognitiveResult,
    CognitiveTask,
    CognitiveVerdict,
    ContextBudget,
    ReasoningMode,
    TaskType,
)
from architecture.cognitive.loop.metacognition import metacognitive_state
from architecture.cognitive.loop.metrics import METRIC_SPECS, compute_lesson_reuse
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator
from architecture.cognitive.loop.retrieval import MemoryRetriever
from architecture.cognitive.loop.tools import ToolSelectionPlan, plan_tools
from architecture.cognitive.loop.world_boundary import current_world_model_boundary

__all__ = [
    "CognitiveOrchestrator",
    "CognitiveResult",
    "CognitiveTask",
    "CognitiveVerdict",
    "ContextBudget",
    "METRIC_SPECS",
    "MemoryRetriever",
    "ReasoningMode",
    "TaskType",
    "ToolSelectionPlan",
    "assemble_context",
    "compute_lesson_reuse",
    "current_world_model_boundary",
    "finance_observation",
    "metacognitive_state",
    "operations_observation",
    "plan_tools",
    "run_memory_vs_no_memory",
    "science_observation",
    "software_observation",
]
