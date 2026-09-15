"""D-12 remediation: command envelopes and payloads carry no ``__dict__``.

Without ``__slots__`` every command object silently accepted arbitrary
attribute attachment (``command.smuggled = ...``), which lets same-process
code decorate a governed object with data the audit digest never covered.
The documented ``object.__setattr__`` residual (assign to a declared slot)
is unchanged; undeclared attachment now fails closed with AttributeError.
"""

from __future__ import annotations

import unittest

from dataclasses import FrozenInstanceError

from agent_org.commands import CommandEnvelope, CommandPayload, TransitionTaskPayload
from agent_org.contracts import CommandType, TaskState
from tests2b.support import make_command, new_env, ready_task


class D12EnvelopeSlotsTests(unittest.TestCase):
    def test_envelope_and_payloads_have_slots(self) -> None:
        self.assertIn("__slots__", CommandEnvelope.__dict__)
        for cls in CommandPayload.__args__:
            self.assertIn("__slots__", cls.__dict__, cls.__name__)

    def test_undeclared_attribute_attachment_fails_closed(self) -> None:
        env = new_env()
        task = ready_task(env)
        command = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task_id=task.task_id, target_state=TaskState.AUTHORIZED.value
            ),
            task_scope=task.task_id,
            expected_state_version=task.version,
        )
        # AttributeError on runtimes where slots raise it directly;
        # TypeError on CPython versions whose generated frozen __setattr__
        # raises TypeError for undeclared names.  Both fail closed; the
        # pinned security property is "raises and nothing is stored".
        with self.assertRaises((AttributeError, TypeError)):
            command.smuggled_notes = "not covered by the audit digest"  # type: ignore[attr-defined]
        self.assertFalse(hasattr(command, "smuggled_notes"))
        payload = command.payload
        with self.assertRaises((AttributeError, TypeError)):
            payload.smuggled = True  # type: ignore[attr-defined]
        self.assertFalse(hasattr(payload, "smuggled"))

    def test_frozen_assignment_still_denied(self) -> None:
        env = new_env()
        task = ready_task(env)
        command = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task_id=task.task_id, target_state=TaskState.AUTHORIZED.value
            ),
            task_scope=task.task_id,
            expected_state_version=task.version,
        )
        with self.assertRaises(FrozenInstanceError):
            command.task_scope = "task.other"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
