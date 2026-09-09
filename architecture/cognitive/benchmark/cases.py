"""BenchmarkCase schema. Future families can add expected_* fields."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from architecture.cognitive.benchmark.thresholds import BENCHMARK_VERSION


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    family: str
    domain: str
    task_type: str
    question: str
    objective: str
    expected_relevant_ids: tuple[str, ...] = ()
    expected_absent_ids: tuple[str, ...] = ()
    expected_verdict_class: str = ""
    expected_uncertainty_class: str = ""
    expected_contradiction_state: str = ""
    expected_reasoning_mode: str = ""
    expected_namespace: str = ""
    expected_properties: dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    requested_evidence: tuple[str, ...] = ()
    constraints: dict[str, Any] = field(default_factory=dict)
    write_back: bool = False
    benchmark_version: str = BENCHMARK_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "family": self.family,
            "domain": self.domain,
            "task_type": self.task_type,
            "question": self.question,
            "objective": self.objective,
            "expected_relevant_ids": list(self.expected_relevant_ids),
            "expected_absent_ids": list(self.expected_absent_ids),
            "expected_verdict_class": self.expected_verdict_class,
            "expected_uncertainty_class": self.expected_uncertainty_class,
            "expected_contradiction_state": self.expected_contradiction_state,
            "expected_reasoning_mode": self.expected_reasoning_mode,
            "expected_namespace": self.expected_namespace,
            "expected_properties": dict(self.expected_properties),
            "agent_id": self.agent_id,
            "requested_evidence": list(self.requested_evidence),
            "constraints": dict(self.constraints),
            "write_back": self.write_back,
            "benchmark_version": self.benchmark_version,
        }
