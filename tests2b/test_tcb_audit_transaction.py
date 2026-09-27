from __future__ import annotations

import ast
import threading
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from agent_org.audit import AuditIntegrityError, AuditLedger
from agent_org.commands import (
    CreateTaskPayload,
    TransitionTaskPayload,
    UpdatePolicyPayload,
)
from agent_org.contracts import (
    Capability,
    CommandStatus,
    CommandType,
    GovernedTask,
    Resource,
    TaskState,
)
from agent_org.projections import ReadOnlyProjections
from tests2b.support import (
    authorize_task,
    create_task,
    delegate_for_command,
    make_command,
    new_env,
    submit,
)


class TcbAuditTransactionTests(unittest.TestCase):
    def _new_task_command(self, env):
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.TASK_MANAGE,),
            resource_scope=(Resource.TASK_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        return task, make_command(
            env, CommandType.CREATE_TASK, lambda _cid: CreateTaskPayload(task)
        )

    def test_single_command_ingress_commits_state_and_audit_together(self) -> None:
        env = new_env()
        before = len(env.plane.projections.audit_events())
        task, command = self._new_task_command(env)
        result = submit(env, command)
        self.assertTrue(result.accepted)
        self.assertIsNotNone(env.plane.projections.task(task.task_id))
        events = env.plane.projections.audit_events()
        self.assertEqual(len(events), before + 1)
        event = events[-1]
        self.assertEqual(event.command_id, command.command_id)
        self.assertEqual(event.result, CommandStatus.ACCEPTED.value)
        self.assertEqual(event.payload_hash, event.payload_hash.lower())
        self.assertTrue(env.plane.projections.verify_audit())

    def test_state_failure_rolls_back_state_and_audit(self) -> None:
        env = new_env()
        task, command = self._new_task_command(env)
        before = len(env.plane.projections.audit_events())
        env.failures.arm("state_mutation")
        result = submit(env, command)
        self.assertEqual(result.status, CommandStatus.FAILED)
        self.assertIsNone(env.plane.projections.task(task.task_id))
        self.assertEqual(len(env.plane.projections.audit_events()), before)

    def test_audit_failure_rolls_back_state(self) -> None:
        env = new_env()
        task, command = self._new_task_command(env)
        env.failures.arm("audit")
        result = submit(env, command)
        self.assertEqual(result.status, CommandStatus.FAILED)
        self.assertIsNone(env.plane.projections.task(task.task_id))
        self.assertEqual(env.plane.projections.audit_events(), ())

    def test_projection_failure_rolls_back_state_and_audit(self) -> None:
        env = new_env()
        task, command = self._new_task_command(env)
        env.failures.arm("projection")
        result = submit(env, command)
        self.assertEqual(result.status, CommandStatus.FAILED)
        self.assertIsNone(env.plane.projections.task(task.task_id))
        self.assertEqual(env.plane.projections.audit_events(), ())

    def test_invalid_expected_version_denied_without_task_mutation(self) -> None:
        env = new_env()
        task = create_task(env)
        delegate_for_command(env, task.task_id, CommandType.TRANSITION_TASK)
        command = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task_id=task.task_id, target_state=TaskState.AUTHORIZED.value
            ),
            task_scope=task.task_id,
            expected_state_version=999,
        )
        result = submit(env, command)
        self.assertEqual(result.reason, "expected_state_version_mismatch")
        self.assertEqual(
            env.plane.projections.task(task.task_id).state, TaskState.PROPOSED
        )

    def test_replay_cannot_mutate_state_twice(self) -> None:
        env = new_env()
        task, command = self._new_task_command(env)
        first = submit(env, command)
        second = submit(env, command)
        self.assertTrue(first.accepted)
        self.assertEqual(second.status, CommandStatus.REPLAYED)
        self.assertEqual(
            len([item for item in env.plane.projections.tasks() if item.task_id == task.task_id]),
            1,
        )

    def test_double_authorization_race_applies_once(self) -> None:
        env = new_env()
        task, command = self._new_task_command(env)
        barrier = threading.Barrier(3)
        results = []

        def worker() -> None:
            barrier.wait()
            results.append(submit(env, command))

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()
        statuses = sorted(item.status.value for item in results)
        self.assertEqual(
            statuses,
            sorted([CommandStatus.ACCEPTED.value, CommandStatus.REPLAYED.value]),
        )
        self.assertEqual(len(env.plane.projections.tasks()), 1)

    def test_audit_truncation_is_detected_against_internal_checkpoint(self) -> None:
        ledger = AuditLedger()
        env = new_env()
        ledger.append(
            ids=env.ids,
            timestamp=env.clock.now(),
            actor_principal=env.plane.operator.principal_id,
            session_id=env.session.session_id,
            authority_chain=("grant.test",),
            command_id="command.test",
            correlation_id="correlation.test",
            causation_id=None,
            parent_task_id=None,
            resource_id="TASK_STORE",
            operation="CREATE",
            capability_id="task.manage",
            policy_version="slice-2b-v1",
            artifact_version=1,
            evidence_lineage=(),
            previous_state=None,
            previous_version=0,
            resulting_state="PROPOSED",
            resulting_version=1,
            result="ACCEPTED",
            failure_reason=None,
            payload_hash="a" * 64,
        )
        object.__setattr__(ledger, "_AuditLedger__events", [])
        with self.assertRaises(AuditIntegrityError):
            ledger.verify()

    def test_projection_is_copy_only_and_has_no_mutators(self) -> None:
        env = new_env()
        task = create_task(env)
        projected = env.plane.projections.task(task.task_id)
        with self.assertRaises(FrozenInstanceError):
            projected.state = TaskState.COMPLETED  # type: ignore[misc]
        self.assertEqual(
            env.plane.projections.task(task.task_id).state, TaskState.PROPOSED
        )
        forbidden = {"register", "create", "transition", "delete", "commit", "append"}
        self.assertFalse(forbidden & set(dir(ReadOnlyProjections)))

    def test_tcb_does_not_expose_governed_store_or_permit(self) -> None:
        env = new_env()
        public_names = {name for name in dir(env.plane.tcb) if not name.startswith("_")}
        self.assertEqual(public_names, {"submit"})

    def test_untrusted_import_boundary_blocks_store_mutators_and_aliases(self) -> None:
        root = Path(__file__).resolve().parents[1] / "agent_org" / "untrusted"
        forbidden = {
            "agent_org.stores",
            "agent_org.tcb",
            "agent_org.audit",
            "agent_org.authority",
            "agent_org.governance",
        }
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name, forbidden, path.name)
                if isinstance(node, ast.ImportFrom) and node.module:
                    self.assertNotIn(node.module, forbidden, path.name)

    def test_policy_mutation_and_cognitive_execution_are_global_denies(self) -> None:
        env = new_env()
        command = make_command(
            env,
            CommandType.UPDATE_POLICY,
            lambda _cid: UpdatePolicyPayload("attacker-policy"),
        )
        result = submit(env, command)
        self.assertFalse(result.accepted)
        self.assertIn(
            result.reason,
            {"capability_global_deny", "operation_global_deny", "no_exact_capability_grant"},
        )
        with self.assertRaises(ValueError):
            replace(
                command,
                command_type=CommandType.CREATE_TASK,
                capability_scope=Capability.EXECUTION,
                requested_operation=command.requested_operation,
                resource_scope=Resource.EXTERNAL_EXECUTION,
            )

    def test_task_transition_preserves_slice1_legal_semantics(self) -> None:
        env = new_env()
        task = authorize_task(env, create_task(env))
        self.assertEqual(task.state, TaskState.AUTHORIZED)
        command = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task_id=task.task_id, target_state=TaskState.COMPLETED.value
            ),
            task_scope=task.task_id,
            expected_state_version=task.version,
        )
        result = submit(env, command)
        self.assertEqual(result.reason, "illegal_task_transition")
