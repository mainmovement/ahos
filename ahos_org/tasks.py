"""Deterministic task lifecycle. States change only through legal transitions."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ahos_org.audit import AuditLog
from ahos_org.clock import Clock, SystemClock, isoformat_utc
from ahos_org.errors import IllegalTransitionError, UnknownIdentityError, ValidationError
from ahos_org.ids import IdFactory, UuidFactory
from ahos_org.models import (
    EventType,
    LEGAL_TRANSITIONS,
    RiskLevel,
    TERMINAL_TASK_STATES,
    TaskState,
)


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    task_type: str
    requester: str
    assigned_agent: str
    current_state: TaskState
    requested_capabilities: tuple[str, ...]
    target_resources: tuple[str, ...]
    risk_level: RiskLevel
    created_at: str
    updated_at: str
    evidence_refs: tuple[str, ...]
    parent_task_id: str | None
    human_approved: bool
    human_approver: str

    def is_terminal(self) -> bool:
        return self.current_state in TERMINAL_TASK_STATES


class TaskStateMachine:
    def __init__(
        self,
        audit: AuditLog,
        clock: Clock | None = None,
        ids: IdFactory | None = None,
    ) -> None:
        self._audit = audit
        self._clock = clock or SystemClock()
        self._ids = ids or UuidFactory()
        self._tasks: dict[str, TaskRecord] = {}

    def create(
        self,
        *,
        task_type: str,
        requester: str,
        assigned_agent: str,
        requested_capabilities: tuple[str, ...] | list[str],
        target_resources: tuple[str, ...] | list[str],
        risk_level: RiskLevel | str = RiskLevel.LOW,
        evidence_refs: tuple[str, ...] | list[str] | None = None,
        parent_task_id: str | None = None,
        actor: str = "system",
    ) -> TaskRecord:
        if not task_type.strip():
            raise ValidationError("task_type is required")
        if not requester.strip():
            raise ValidationError("requester is required")
        if not assigned_agent.strip():
            raise ValidationError("assigned_agent is required")
        if parent_task_id and parent_task_id not in self._tasks:
            raise UnknownIdentityError(f"Unknown parent_task_id: {parent_task_id}")
        now = isoformat_utc(self._clock.now())
        risk = RiskLevel(str(risk_level))
        record = TaskRecord(
            task_id=self._ids.new("task"),
            task_type=task_type.strip(),
            requester=requester.strip(),
            assigned_agent=assigned_agent.strip(),
            current_state=TaskState.PROPOSED,
            requested_capabilities=tuple(requested_capabilities),
            target_resources=tuple(target_resources),
            risk_level=risk,
            created_at=now,
            updated_at=now,
            evidence_refs=tuple(evidence_refs or ()),
            parent_task_id=parent_task_id,
            human_approved=False,
            human_approver="",
        )
        self._tasks[record.task_id] = record
        self._audit.append(
            event_type=EventType.TASK_CREATED,
            actor=actor,
            action="create",
            target=record.task_id,
            reason=f"task proposed in {record.current_state}",
            task_id=record.task_id,
            decision=record.current_state,
            evidence_refs=record.evidence_refs,
        )
        return record

    def get(self, task_id: str) -> TaskRecord:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise UnknownIdentityError(f"Unknown task: {task_id}") from exc

    def exists(self, task_id: str) -> bool:
        return task_id in self._tasks

    def list_tasks(self) -> tuple[TaskRecord, ...]:
        return tuple(self._tasks.values())

    def grant_human_approval(
        self,
        task_id: str,
        *,
        approver: str,
        actor: str = "human",
        reason: str = "human approval recorded",
    ) -> TaskRecord:
        task = self.get(task_id)
        if not approver.strip():
            raise ValidationError("approver is required")
        updated = replace(
            task,
            human_approved=True,
            human_approver=approver.strip(),
            updated_at=isoformat_utc(self._clock.now()),
        )
        self._tasks[task_id] = updated
        self._audit.append(
            event_type=EventType.TASK_TRANSITION,
            actor=actor,
            action="human_approve",
            target=task_id,
            reason=reason,
            task_id=task_id,
            decision="RECORDED",
        )
        return updated

    def transition(
        self,
        task_id: str,
        new_state: TaskState | str,
        *,
        actor: str,
        reason: str,
        evidence_refs: tuple[str, ...] | list[str] | None = None,
    ) -> TaskRecord:
        task = self.get(task_id)
        target = TaskState(str(new_state))
        legal = LEGAL_TRANSITIONS.get(task.current_state, frozenset())
        if target not in legal:
            raise IllegalTransitionError(
                f"Illegal transition {task.current_state} -> {target} for {task_id}"
            )
        refs = tuple(evidence_refs or ())
        merged_refs = task.evidence_refs + tuple(r for r in refs if r not in task.evidence_refs)
        updated = replace(
            task,
            current_state=target,
            updated_at=isoformat_utc(self._clock.now()),
            evidence_refs=merged_refs,
        )
        self._tasks[task_id] = updated
        self._audit.append(
            event_type=EventType.TASK_TRANSITION,
            actor=actor,
            action=f"{task.current_state}->{target}",
            target=task_id,
            reason=reason,
            task_id=task_id,
            decision=str(target),
            evidence_refs=refs,
        )
        return updated

    def set_state(self, *_args: object, **_kwargs: object) -> None:
        raise IllegalTransitionError("Arbitrary state mutation is forbidden.")

    def mutate_state(self, *_args: object, **_kwargs: object) -> None:
        raise IllegalTransitionError("Arbitrary state mutation is forbidden.")
