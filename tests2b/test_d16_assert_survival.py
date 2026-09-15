"""D-16 remediation: payload type checks survive ``python -O``.

Handlers verified ``assert isinstance(payload, ...)`` -- a statement the
interpreter strips under ``-O``.  Payload-type binding at envelope
construction is real validation (never an assert), but the handler checks
are the governed backstop against a same-process forged or mutated
envelope, and they must not vanish under optimization.  All twelve handler
sites now raise explicitly.

These tests pin both layers:

1. the TCB handler denies a same-process payload forgery with
   ``payload_type_mismatch`` in the ordinary interpreter;
2. the agent_org source tree contains no ``assert`` statements at all;
3. the same forgery is still denied under ``python -O`` executed in a
   subprocess, which is the only honest way to prove survival under
   optimization since this test runner itself compiled without -O here.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

from agent_org.commands import CreateTaskPayload, TransitionTaskPayload
from agent_org.contracts import CommandType, TaskState
from tests2b.support import (
    grant_task_commands,
    make_command,
    new_env,
    ready_task,
    submit,
)

ROOT = Path(__file__).resolve().parents[1]

FORGERY_SCENARIO = r"""
from tests2b.support import grant_task_commands, make_command, new_env, ready_task, submit
from agent_org.commands import CreateTaskPayload, TransitionTaskPayload
from agent_org.contracts import CommandType, TaskState

env = new_env()
task = ready_task(env)
grant_task_commands(env, task.task_id, (CommandType.TRANSITION_TASK,))
command = make_command(
    env,
    CommandType.TRANSITION_TASK,
    lambda _cid: TransitionTaskPayload(
        task_id=task.task_id, target_state=TaskState.AUTHORIZED.value
    ),
    task_scope=task.task_id,
    expected_state_version=task.version,
)
object.__setattr__(command, "payload", CreateTaskPayload(task))
result = submit(env, command)
expected = "payload_type_mismatch"
if result.reason != expected:
    raise SystemExit(f"unexpected: {result.status.value} {result.reason}")
if result.accepted:
    raise SystemExit("forgery accepted")
print("FORGERY_DENIED_UNDER_OPTIMIZATION")
"""


class D16AssertSurvivalTests(unittest.TestCase):
    def _forge(self, env, task):
        command = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task_id=task.task_id, target_state=TaskState.AUTHORIZED.value
            ),
            task_scope=task.task_id,
            expected_state_version=task.version,
        )
        object.__setattr__(command, "payload", CreateTaskPayload(task))
        return command

    def test_forged_payload_type_denied_in_handler(self) -> None:
        env = new_env()
        task = ready_task(env)
        grant_task_commands(env, task.task_id, (CommandType.TRANSITION_TASK,))
        result = submit(env, self._forge(env, task))
        self.assertFalse(result.accepted, result)
        self.assertEqual(result.reason, "payload_type_mismatch")
        live = env.plane.projections.task(task.task_id)
        self.assertIs(live.state, TaskState.AUTHORIZED)
        self.assertTrue(env.plane.projections.verify_audit())

    def test_no_assert_statements_in_agent_org_sources(self) -> None:
        offenders: list[tuple[str, int]] = []
        for path in (ROOT / "agent_org").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    offenders.append((str(path), node.lineno))
        self.assertEqual(offenders, [])

    def test_handle_checks_survive_python_dash_o(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-O", "-c", FORGERY_SCENARIO],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout={completed.stdout!r} stderr={completed.stderr!r}",
        )
        self.assertIn("FORGERY_DENIED_UNDER_OPTIMIZATION", completed.stdout)


if __name__ == "__main__":
    unittest.main()
