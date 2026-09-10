"""Deterministic P3 benchmark helpers. Synthetic data only. No intelligence score."""

from __future__ import annotations

import time
from typing import Any

from architecture.cognitive.hypothesis import HypothesisStore
from architecture.cognitive.loop.contracts import CognitiveTask, TaskType
from architecture.cognitive.loop.metrics import compute_lesson_reuse
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator
from architecture.cognitive.memory.observation import (
    AcquisitionRecord,
    persist_observed_acquisition,
)
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import EpistemicKind, SourceType


def run_memory_vs_no_memory(
    memory: CognitiveMemoryStore,
    hypotheses: HypothesisStore,
    ledger_path,
    *,
    now: float = 1_800_000_000.0,
) -> dict[str, Any]:
    """Compare NO_MEMORY vs MEMORY+LOOP on lesson reuse. SYNTHETIC_TEST_DATA."""
    persist_observed_acquisition(
        memory,
        AcquisitionRecord(
            statement="SYNTHETIC_TEST_DATA retries after HTTP timeout recovered the request.",
            source_type=SourceType.SYSTEM.value,
            source_id="bench-timeout",
            observed_at=now - 100.0,
            domain="software",
            source_location="architecture.cognitive.loop.benchmark",
            producer="p3-benchmark",
            producer_version="p3-v1",
            created_at=now - 50.0,
            payload={"data_label": "SYNTHETIC_TEST_DATA"},
        ),
    )
    orch = CognitiveOrchestrator(
        memory=memory, hypotheses=hypotheses, ledger_path=ledger_path
    )
    t1 = CognitiveTask(
        task_id="bench-1",
        task_type=TaskType.INVESTIGATE.value,
        objective="Investigate timeout recovery",
        question="Do retries after timeout help?",
        domain="software",
        requester="benchmark",
        created_at=now,
        data_label="SYNTHETIC_TEST_DATA",
    )
    t0 = time.perf_counter()
    r1 = orch.run(t1, now=now, use_memory=True)
    cycle_s = time.perf_counter() - t0
    t2 = CognitiveTask(
        task_id="bench-2",
        task_type=TaskType.LEARN.value,
        objective="Reuse prior timeout lesson",
        question="What did we learn about timeout retries?",
        domain="software",
        requester="benchmark",
        created_at=now + 1.0,
        data_label="SYNTHETIC_TEST_DATA",
    )
    r2_mem = orch.run(t2, now=now + 1.0, use_memory=True)
    r2_none = orch.run(
        CognitiveTask(
            task_id="bench-2-nomem",
            task_type=TaskType.LEARN.value,
            objective="Reuse prior timeout lesson",
            question="What did we learn about timeout retries?",
            domain="software",
            requester="benchmark",
            created_at=now + 2.0,
            write_back=False,
            data_label="SYNTHETIC_TEST_DATA",
        ),
        now=now + 2.0,
        use_memory=False,
    )
    kinds_mem = [i.epistemic_kind for i in r2_mem.retrieved]
    kinds_none = [i.epistemic_kind for i in r2_none.retrieved]
    reuse_mem = compute_lesson_reuse(kinds_mem, used_memory=True)
    reuse_none = compute_lesson_reuse(kinds_none, used_memory=False)
    return {
        "data_label": "SYNTHETIC_TEST_DATA",
        "no_memory_lesson_reuse": reuse_none,
        "memory_loop_lesson_reuse": reuse_mem,
        "measured_improvement": reuse_mem - reuse_none,
        "episode1_lesson_id": r1.lesson_memory_id,
        "episode1_hypothesis_id": r1.hypothesis_id,
        "episode1_experiment_id": r1.experiment_id,
        "episode2_retrieved_lesson": r1.lesson_memory_id
        in {i.memory_id for i in (r2_mem.context.lessons if r2_mem.context else ())},
        "e2e_cycle_seconds": cycle_s,
        "unsupported_claim_rate": 1.0 if r1.verdict == "SUPPORTED" else 0.0,
        "integrity": memory.integrity_check(),
        "limitations": (
            "Synthetic software domain only; improvement is lesson reuse presence, "
            "not an intelligence score. Causal/counterfactual modes remain NOT_IMPLEMENTED."
        ),
        "epistemic_kind_lesson": EpistemicKind.LESSON.value,
    }
