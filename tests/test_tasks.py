from __future__ import annotations

import unittest

from ahos_org.errors import IllegalTransitionError, UnknownIdentityError
from ahos_org.models import EventType, LEGAL_TRANSITIONS, TaskState, TERMINAL_TASK_STATES
from tests.support import new_org


class TaskStateMachineTests(unittest.TestCase):
    def test_valid_transitions_accepted(self) -> None:
        org = new_org()
        task = org.tasks.create(
            task_type="demo",
            requester="tester",
            assigned_agent="agent.chief-orchestrator",
            requested_capabilities=("task.inspect",),
            target_resources=("ORG_TASK_STORE",),
            actor="tester",
        )
        self.assertEqual(task.current_state, TaskState.PROPOSED)
        authorized = org.tasks.transition(
            task.task_id, TaskState.AUTHORIZED, actor="tester", reason="ok"
        )
        running = org.tasks.transition(
            authorized.task_id, TaskState.RUNNING, actor="tester", reason="start"
        )
        completed = org.tasks.transition(
            running.task_id, TaskState.COMPLETED, actor="tester", reason="done"
        )
        self.assertEqual(completed.current_state, TaskState.COMPLETED)

    def test_invalid_transitions_rejected(self) -> None:
        org = new_org()
        task = org.tasks.create(
            task_type="demo",
            requester="tester",
            assigned_agent="agent.chief-orchestrator",
            requested_capabilities=("task.inspect",),
            target_resources=("ORG_TASK_STORE",),
            actor="tester",
        )
        with self.assertRaises(IllegalTransitionError):
            org.tasks.transition(
                task.task_id, TaskState.COMPLETED, actor="tester", reason="skip"
            )
        with self.assertRaises(IllegalTransitionError):
            org.tasks.transition(
                task.task_id, TaskState.RUNNING, actor="tester", reason="skip"
            )
        self.assertEqual(org.tasks.get(task.task_id).current_state, TaskState.PROPOSED)

    def test_every_transition_audited(self) -> None:
        org = new_org()
        before = len(org.audit)
        task = org.tasks.create(
            task_type="demo",
            requester="tester",
            assigned_agent="agent.chief-orchestrator",
            requested_capabilities=("task.inspect",),
            target_resources=("ORG_TASK_STORE",),
            actor="tester",
        )
        org.tasks.transition(task.task_id, TaskState.REJECTED, actor="tester", reason="no")
        created = [
            e for e in org.audit.events()[before:] if e.event_type == EventType.TASK_CREATED
        ]
        transitions = [
            e
            for e in org.audit.events()[before:]
            if e.event_type == EventType.TASK_TRANSITION
        ]
        self.assertEqual(len(created), 1)
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0].task_id, task.task_id)

    def test_impossible_state_mutation_rejected(self) -> None:
        org = new_org()
        task = org.tasks.create(
            task_type="demo",
            requester="tester",
            assigned_agent="agent.chief-orchestrator",
            requested_capabilities=("task.inspect",),
            target_resources=("ORG_TASK_STORE",),
            actor="tester",
        )
        with self.assertRaises(IllegalTransitionError):
            org.tasks.set_state(task.task_id, TaskState.COMPLETED)
        with self.assertRaises(IllegalTransitionError):
            org.tasks.mutate_state(task.task_id, "COMPLETED")
        self.assertEqual(org.tasks.get(task.task_id).current_state, TaskState.PROPOSED)

    def test_terminal_states_have_no_exits(self) -> None:
        for state in TERMINAL_TASK_STATES:
            self.assertEqual(LEGAL_TRANSITIONS[state], frozenset())

    def test_unknown_parent_rejected(self) -> None:
        org = new_org()
        with self.assertRaises(UnknownIdentityError):
            org.tasks.create(
                task_type="child",
                requester="tester",
                assigned_agent="agent.chief-orchestrator",
                requested_capabilities=("task.inspect",),
                target_resources=("ORG_TASK_STORE",),
                parent_task_id="task-missing",
                actor="tester",
            )
