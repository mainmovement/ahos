"""P3 cognitive orchestrator. Coordinates memory, retrieval, reason, HYP, ledger.

Does not query soak DBs, does not import discovery/paper_trading, does not
authorize execution. LLM-free.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from architecture.cognitive.experiment_bridge import record_cognitive_experiment
from architecture.cognitive.hypothesis import HypothesisStore
from architecture.cognitive.loop.context import assemble_context
from architecture.cognitive.loop.contracts import (
    CognitiveResult,
    CognitiveTask,
    ContextBudget,
    TaskType,
)
from architecture.cognitive.loop.reason import NOT_IMPLEMENTED_MODES, evaluate_reason
from architecture.cognitive.loop.binding import (
    assemble_evidence_binding,
    contradicted_memory_ids,
    load_bind_snapshot,
)
from architecture.cognitive.loop.episode import reusable_writeback_permitted
from architecture.cognitive.loop.retrieval import MemoryRetriever
from architecture.cognitive.memory.observation import (
    ISSUER_ID,
    is_forbidden_production_secret,
    observation_grant_permits_factual,
)
from architecture.cognitive.memory.store import CognitiveMemoryStore, MemoryAuthorizationError, MemoryRecord
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType
from architecture.cognitive.novelty import classify_novelty


@dataclass
class LoopPaths:
    memory: CognitiveMemoryStore
    hypotheses: HypothesisStore
    ledger_path: Path


class CognitiveOrchestrator:
    def __init__(
        self,
        *,
        memory: CognitiveMemoryStore,
        hypotheses: HypothesisStore,
        ledger_path: Path | str,
        retriever: MemoryRetriever | None = None,
    ) -> None:
        self.memory = memory
        self.hypotheses = hypotheses
        self.ledger_path = Path(ledger_path)
        self.retriever = retriever or MemoryRetriever()
        secret = os.urandom(32)
        while is_forbidden_production_secret(secret):
            secret = os.urandom(32)
        self._grant_verify_secret = secret
        self._verify_issuer_id = ISSUER_ID

    def __repr__(self) -> str:
        return (
            f"CognitiveOrchestrator(memory={self.memory!r}, "
            f"ledger_path={self.ledger_path!r})"
        )

    def authorize_execution(self, *_a: Any, **_k: Any) -> None:
        raise MemoryAuthorizationError("Cognitive loop cannot authorize execution")

    def record_failure(
        self,
        task: CognitiveTask,
        *,
        observed_failure: str,
        attempted_action: str,
        failure_type: str = "reasoning_episode",
        component: str = "architecture.cognitive.loop",
        recovery: str = "UNKNOWN",
        recovery_worked: bool | None = None,
        now: float | None = None,
    ) -> MemoryRecord:
        """Persist a FAILURE memory. Does not authorize recovery execution."""
        return self.memory.record_failure(
            failure_type=failure_type,
            component=component,
            attempted_action=attempted_action,
            observed_failure=observed_failure,
            recovery=recovery,
            recovery_worked=recovery_worked,
            agent_id=task.agent_id,
            now=now,
            producer="architecture.cognitive.loop",
        )

    def run(
        self,
        task: CognitiveTask,
        *,
        budget: ContextBudget | None = None,
        now: float | None = None,
        use_memory: bool = True,
    ) -> CognitiveResult:
        ts = time.time() if now is None else now
        if task.data_label not in {"SYNTHETIC_TEST_DATA", "TEST", "REAL", "UNKNOWN"}:
            raise ValueError("task.data_label must be typed")
        return self._run_with_episode_clock(
            task, budget=budget, ts=ts, use_memory=use_memory
        )

    def _permits_observation_grant(
        self,
        *,
        statement: str,
        epistemic_kind: str,
        memory_type: str,
        source_type: str,
        source_id: str,
        observed_at: float | None,
        valid_until: float | None,
        domain: str,
        payload: dict[str, Any] | None,
        now: float,
        status: str = "",
    ) -> bool:
        """Instance-owned production verification. Key is never a caller argument."""
        return observation_grant_permits_factual(
            statement=statement,
            epistemic_kind=epistemic_kind,
            memory_type=memory_type,
            source_type=source_type,
            source_id=source_id,
            observed_at=observed_at,
            valid_until=valid_until,
            domain=domain,
            payload=payload,
            now=now,
            status=status,
            key=self._grant_verify_secret,
            expected_issuer_id=self._verify_issuer_id,
        )

    def _bind_item(
        self,
        item: Any,
        task: CognitiveTask,
        *,
        store: CognitiveMemoryStore | None,
        contradicted_ids: set[str] | None,
        index: int,
        now: float,
    ) -> Any:
        snap = load_bind_snapshot(item, store)
        grant_ok = self._permits_observation_grant(
            statement=snap.statement,
            epistemic_kind=snap.epistemic_kind,
            memory_type=snap.memory_type,
            source_type=snap.source_type,
            source_id=snap.source_id,
            observed_at=snap.observed_at,
            valid_until=snap.valid_until,
            domain=snap.domain,
            payload=snap.payload,
            now=float(now),
            status=snap.status,
        )
        return assemble_evidence_binding(
            item,
            task,
            snap,
            grant_ok=grant_ok,
            contradicted_ids=contradicted_ids,
            index=index,
            trusted_now=float(now),
        )

    def _bind_context(self, ctx: Any, task: CognitiveTask, *, now: float) -> list[Any]:
        contradicted = contradicted_memory_ids(ctx)
        bindings = []
        for i, item in enumerate(ctx.all_included()):
            bindings.append(
                self._bind_item(
                    item,
                    task,
                    store=self.memory,
                    contradicted_ids=contradicted,
                    index=i + 1,
                    now=now,
                )
            )
        return bindings

    def _reason_episode(
        self,
        task: CognitiveTask,
        ctx: Any,
        *,
        retrieved_ids: list[str],
        now: float,
    ) -> Any:
        bindings = self._bind_context(ctx, task, now=now)
        return evaluate_reason(task, ctx, bindings, retrieved_ids=retrieved_ids)

    def _run_with_episode_clock(
        self,
        task: CognitiveTask,
        *,
        budget: ContextBudget | None,
        ts: float,
        use_memory: bool,
    ) -> CognitiveResult:
        retrieved = (
            self.retriever.retrieve(self.memory, task, now=ts) if use_memory else []
        )
        ctx = assemble_context(retrieved, self.memory, budget=budget, now=ts)
        retrieved_ids = [i.memory_id for i in retrieved]
        verdict, epistemic, trace, critique, _assumptions = self._reason_episode(
            task, ctx, retrieved_ids=retrieved_ids, now=ts
        )

        seen_before = bool(ctx.lessons or ctx.failures)
        novelty = classify_novelty(
            seen_before=seen_before,
            evidence_conflict=ctx.contradiction_present,
            confidence=None,
        )

        hyp_id = ""
        exp_id = ""
        lesson_id = ""
        episode_id = ""

        should_hyp = task.task_type in {
            TaskType.HYPOTHESIZE.value,
            TaskType.INVESTIGATE.value,
            TaskType.TEST.value,
            TaskType.ANALYZE.value,
        } and task.reasoning_mode not in NOT_IMPLEMENTED_MODES

        # Unresolved/insufficient/contested must not become reusable hypotheses.
        # Verdict string WEAKLY_SUPPORTED is not sufficient; episode polarity is.
        reusable_writeback = reusable_writeback_permitted(
            verdict, self._bind_context(ctx, task, now=ts)
        )
        # Rebind from RetrievedItems, not reason() DTO copies, so mutated
        # EvidenceBinding metadata cannot authorize persistence.
        if should_hyp and task.write_back and reusable_writeback:
            hyp = self.hypotheses.propose(
                f"{task.question} [{task.data_label}]",
                domain=task.domain,
                provenance={
                    "task_id": task.task_id,
                    "data_label": task.data_label,
                    "falsification_condition": task.constraints.get(
                        "falsification_condition",
                        "An observation contradicting the statement with provenance",
                    ),
                    "supporting_memory_ids": [i.memory_id for i in ctx.facts],
                    "contradicting_memory_ids": [
                        c.get("from_id") for c in ctx.contradictions
                    ],
                    "novelty_equals_truth": False,
                },
                now=ts,
            )
            hyp_id = hyp.hypothesis_id
            self.memory.remember(
                memory_type=MemoryType.HYPOTHESIS,
                epistemic_kind=EpistemicKind.HYPOTHESIS,
                statement=hyp.statement,
                source_type=SourceType.HYPOTHESIS_STORE,
                source_id=hyp_id,
                source_location=str(self.hypotheses.path),
                producer="architecture.cognitive.loop",
                producer_version="p3-v1",
                domain=task.domain,
                context=task.task_id,
                created_at=ts,
                hypothesis_id=hyp_id,
                payload={"data_label": task.data_label, "novelty": novelty},
            )

        should_test = task.task_type in {TaskType.TEST.value, TaskType.INVESTIGATE.value}
        if should_test and hyp_id and task.write_back:
            result_code = "INSUFFICIENT_DATA"
            if verdict == "UNRESOLVED":
                result_code = "NOT_COMPARABLE"
            exp = record_cognitive_experiment(
                hypothesis_store=self.hypotheses,
                hypothesis_id=hyp_id,
                baseline="no prior experiment on this task",
                method="deterministic_context_evaluation",
                result=result_code,
                ledger_path=self.ledger_path,
                evidence_refs=retrieved_ids,
                reusable_lesson=trace.conclusion,
            )
            exp_id = exp.experiment_id
            self.memory.remember(
                memory_type=MemoryType.EXPERIMENT,
                epistemic_kind=EpistemicKind.INFERENCE,
                statement=f"experiment {exp_id} result={result_code}",
                source_type=SourceType.EXPERIMENT_LEDGER,
                source_id=exp_id,
                source_location=str(self.ledger_path),
                producer="architecture.cognitive.loop",
                producer_version="p3-v1",
                domain=task.domain,
                context=task.task_id,
                created_at=ts,
                hypothesis_id=hyp_id,
                experiment_id=exp_id,
                payload={"data_label": task.data_label, "result": result_code},
            )

        if task.write_back and use_memory:
            if reusable_writeback:
                lesson_statement = (
                    f"LESSON [{task.data_label}]: {trace.conclusion} "
                    f"about {task.question} {task.objective} "
                    f"verdict={verdict} failures_seen={len(ctx.failures)}"
                )
                lesson_payload = {
                    "data_label": task.data_label,
                    "what_worked": "structured retrieval+critique",
                    "what_failed": "; ".join(ctx.unknowns) or "none listed",
                    "applicability": task.domain,
                    "boundary_conditions": "synthetic/test unless data_label=REAL",
                }
                if task.constraints.get("component"):
                    lesson_payload["component"] = str(task.constraints["component"])
                lesson = self.memory.remember(
                    memory_type=MemoryType.AGENT if task.agent_id else MemoryType.SEMANTIC,
                    epistemic_kind=EpistemicKind.LESSON,
                    statement=lesson_statement,
                    source_type=SourceType.SYSTEM,
                    source_id=task.task_id,
                    source_location="architecture.cognitive.loop.orchestrator",
                    producer="architecture.cognitive.loop",
                    producer_version="p3-v1",
                    domain=task.domain,
                    context=task.context_id or task.task_id,
                    created_at=ts,
                    hypothesis_id=hyp_id,
                    experiment_id=exp_id,
                    agent_id=task.agent_id,
                    agent_namespace=task.agent_id,
                    payload=lesson_payload,
                )
                lesson_id = lesson.memory_id
            episode = self.memory.remember(
                memory_type=MemoryType.EPISODIC,
                epistemic_kind=EpistemicKind.INFERENCE,
                statement=f"episode {task.task_id} {verdict}",
                source_type=SourceType.SYSTEM,
                source_id=task.task_id,
                source_location="architecture.cognitive.loop.orchestrator",
                producer="architecture.cognitive.loop",
                producer_version="p3-v1",
                domain=task.domain,
                context=task.task_id,
                created_at=ts,
                observed_at=ts,
                hypothesis_id=hyp_id,
                experiment_id=exp_id,
                agent_id=task.agent_id,
                agent_namespace=task.agent_id,
                payload={"data_label": task.data_label, "verdict": verdict},
            )
            episode_id = episode.memory_id

        inf = (trace.inference_records or ({},))[0]
        if task.write_back and use_memory and inf.get("conclusion") and reusable_writeback:
            support_ids = list(inf.get("supporting_evidence_ids") or [])
            self.memory.remember(
                memory_type=MemoryType.SEMANTIC,
                epistemic_kind=EpistemicKind.INFERENCE,
                statement=f"INFERENCE [{task.data_label}]: {trace.conclusion}",
                source_type=SourceType.SYSTEM,
                source_id=task.task_id,
                source_location="architecture.cognitive.loop.orchestrator",
                producer="architecture.cognitive.loop",
                producer_version="p5-v1",
                domain=task.domain,
                context=task.task_id,
                created_at=ts,
                hypothesis_id=hyp_id,
                experiment_id=exp_id,
                agent_id=task.agent_id,
                agent_namespace=task.agent_id or "cognitive-inference",
                derived_from=support_ids,
                payload={
                    "data_label": task.data_label,
                    "conclusion_class": inf.get("conclusion_class") or "INFERENCE",
                    "critic_action": critique.action,
                },
            )

        return CognitiveResult(
            task_id=task.task_id,
            verdict=verdict,
            epistemic=epistemic,
            conclusion=trace.conclusion,
            critique=critique,
            trace=trace,
            context=ctx,
            retrieved=tuple(retrieved),
            hypothesis_id=hyp_id,
            experiment_id=exp_id,
            lesson_memory_id=lesson_id,
            episode_memory_id=episode_id,
            novelty=novelty,
            authorized_execution=False,
            lesson_applied=bool(inf.get("lesson_applied")),
            failure_applied=bool(inf.get("failure_applied")),
            critic_action=critique.action,
            reusable_writeback=reusable_writeback,
        )
