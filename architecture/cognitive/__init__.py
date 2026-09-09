"""AHOS Cognitive Core (Lane B) — domain-general contracts.

This package does NOT implement AGI/ACI. It defines auditable contracts for
hypothesis/experiment provenance, self-research reports, capability gaps,
agent metadata, world-model abstraction, novelty labels, evaluation hooks,
and sandbox boundaries.

Laws:
  - PAPER_ONLY. No execution path.
  - No imports of discovery / paper_trading / telegram_ai / engine.
  - UNKNOWN / INCOMPLETE never become PASS or BUY.
  - Reuse existing SelfEvolutionEngine and ExperimentLedger; do not duplicate.
  - Soak evidence is never rewritten from this package.
"""
from .contracts import (
    AutonomyLevel,
    CapabilityAssessment,
    CapabilityStatus,
    CognitiveClaim,
    CreativeClass,
    DomainKind,
    EpistemicState,
    HypothesisState,
    CURRENT_AUTONOMY_CEILING,
)
from .hypothesis import HypothesisRecord, HypothesisStore, HypothesisTransitionError
from .experiment_bridge import CognitiveExperiment, record_cognitive_experiment
from .self_research import SelfResearchReport, build_self_research_report
from .world_model import WorldModelStatus, current_world_model_status
from .agents import AgentPassport, council_capability_claim, load_council_passports
from .novelty import NoveltyClass, classify_novelty
from .evaluation import (
    BenchmarkPlanRef,
    EvaluationResult,
    FabricatedScoreError,
    evaluation_capability_claim,
    refuse_fabricated_score,
)
from .sandbox import SandboxPolicy, assert_sandbox_holds
from .capability import BASELINE_GAPS, CapabilityGap, CapabilityRegister
from .evolution_gate import LaneAChangeRequired, propose_lane_b_evolution
from .counterfactual import CounterfactualPolicy, current_counterfactual_policy
from .reasoning import ReasoningInventory, current_reasoning_inventory

# Stable aliases used in the charter / tests.
WorldModelView = WorldModelStatus
world_model_status = current_world_model_status
NoveltyLabel = NoveltyClass
SandboxBoundary = SandboxPolicy
assert_cognitive_sandbox = assert_sandbox_holds

__all__ = [
    "AutonomyLevel",
    "CapabilityAssessment",
    "CapabilityStatus",
    "CognitiveClaim",
    "CreativeClass",
    "DomainKind",
    "EpistemicState",
    "HypothesisState",
    "CURRENT_AUTONOMY_CEILING",
    "HypothesisRecord",
    "HypothesisStore",
    "HypothesisTransitionError",
    "CognitiveExperiment",
    "record_cognitive_experiment",
    "SelfResearchReport",
    "build_self_research_report",
    "WorldModelStatus",
    "WorldModelView",
    "current_world_model_status",
    "world_model_status",
    "AgentPassport",
    "council_capability_claim",
    "load_council_passports",
    "NoveltyClass",
    "NoveltyLabel",
    "classify_novelty",
    "BenchmarkPlanRef",
    "EvaluationResult",
    "FabricatedScoreError",
    "evaluation_capability_claim",
    "refuse_fabricated_score",
    "SandboxPolicy",
    "SandboxBoundary",
    "assert_sandbox_holds",
    "assert_cognitive_sandbox",
    "BASELINE_GAPS",
    "CapabilityGap",
    "CapabilityRegister",
    "LaneAChangeRequired",
    "propose_lane_b_evolution",
    "CounterfactualPolicy",
    "current_counterfactual_policy",
    "ReasoningInventory",
    "current_reasoning_inventory",
]
