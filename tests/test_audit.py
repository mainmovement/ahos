from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ahos_org.audit import AuditLog, GENESIS_HASH, canonical_json, sha256_text
from ahos_org.clock import FrozenClock
from ahos_org.errors import AppendOnlyViolationError, TamperDetectedError
from ahos_org.ids import SequentialIdFactory
from ahos_org.models import EventType, TaskState
from tests.support import authorized_task, fixture_agent, new_org


class AuditLogTests(unittest.TestCase):
    def test_every_governance_decision_creates_an_event(self) -> None:
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
        )
        before = len(org.audit)
        org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        authz = [
            e
            for e in org.audit.events()[before:]
            if e.event_type == EventType.AUTHZ_DECISION
        ]
        self.assertEqual(len(authz), 1)
        self.assertEqual(authz[0].decision, "ALLOW")

    def test_every_state_transition_creates_an_event(self) -> None:
        org = new_org()
        task = org.tasks.create(
            task_type="audit-check",
            requester="tester",
            assigned_agent="agent.red-team",
            requested_capabilities=("redteam.probe",),
            target_resources=("ORG_TEST_SANDBOX",),
            actor="tester",
        )
        before = len(org.audit)
        org.tasks.transition(
            task.task_id, TaskState.CANCELLED, actor="tester", reason="stop"
        )
        transitions = [
            e
            for e in org.audit.events()[before:]
            if e.event_type == EventType.TASK_TRANSITION
        ]
        self.assertEqual(len(transitions), 1)

    def test_hashes_are_deterministic(self) -> None:
        first = new_org()
        second = new_org()
        self.assertEqual(
            [e.event_hash for e in first.audit.events()],
            [e.event_hash for e in second.audit.events()],
        )
        self.assertEqual(first.audit.events()[0].previous_event_hash, GENESIS_HASH)

    def test_tampering_detection_works(self) -> None:
        org = new_org()
        events = list(org.audit.events())
        tampered = replace(events[3], reason="tampered-in-place")
        org.audit._events[3] = tampered  # noqa: SLF001 — explicit integrity attack
        with self.assertRaises(TamperDetectedError):
            org.audit.verify_integrity()

    def test_event_ordering_is_preserved(self) -> None:
        org = new_org()
        hashes = [e.event_hash for e in org.audit.events()]
        previous = [e.previous_event_hash for e in org.audit.events()]
        self.assertEqual(previous[0], GENESIS_HASH)
        self.assertEqual(previous[1:], hashes[:-1])
        org.audit.verify_integrity()

    def test_append_only_violations_rejected(self) -> None:
        log = AuditLog(clock=FrozenClock(), ids=SequentialIdFactory())
        log.append(
            event_type=EventType.INTEGRITY_VERIFIED,
            actor="system",
            action="probe",
            target="audit",
            reason="start",
        )
        with self.assertRaises(AppendOnlyViolationError):
            log.replace()
        with self.assertRaises(AppendOnlyViolationError):
            log.rewrite()
        with self.assertRaises(AppendOnlyViolationError):
            log.delete()
        with self.assertRaises(AppendOnlyViolationError):
            log.clear()

    def test_jsonl_persistence_is_append_only_and_reloadable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            clock = FrozenClock()
            ids = SequentialIdFactory()
            log = AuditLog(clock=clock, ids=ids, path=path)
            log.append(
                event_type=EventType.INTEGRITY_VERIFIED,
                actor="system",
                action="write",
                target="file",
                reason="one",
            )
            clock.advance(1)
            log.append(
                event_type=EventType.INTEGRITY_VERIFIED,
                actor="system",
                action="write",
                target="file",
                reason="two",
            )
            reloaded = AuditLog(clock=FrozenClock(), ids=SequentialIdFactory(), path=path)
            self.assertEqual(len(reloaded), 2)
            reloaded.verify_integrity()
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            mutated = lines[0].replace("one", "OWN")
            path.write_text(mutated + "\n" + lines[1] + "\n", encoding="utf-8")
            with self.assertRaises(TamperDetectedError):
                AuditLog(clock=FrozenClock(), ids=SequentialIdFactory(), path=path)

    def test_hash_function_is_stable(self) -> None:
        payload = {"a": 1, "b": ["x", "y"]}
        self.assertEqual(
            sha256_text(canonical_json(payload)),
            sha256_text(canonical_json(payload)),
        )
