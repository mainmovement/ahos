"""Negative-path review: ways Slice 1 could incorrectly authorize, then tests that it does not."""

from __future__ import annotations

import unittest

from ahos_org.models import AuthzDecision, MaturityLevel, TaskState
from tests.support import authorized_task, fixture_agent, new_org


class RedTeamTests(unittest.TestCase):
    def test_requires_review_is_not_allow(self) -> None:
        """Failure mode 1: treating REQUIRES_REVIEW as a grant."""
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("release.review",),
            resources=("ORG_CHANGE_CONTROL",),
        )
        result = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="release.review",
            resource_id="ORG_CHANGE_CONTROL",
            action="review",
        )
        self.assertEqual(result.decision, AuthzDecision.REQUIRES_REVIEW)
        self.assertFalse(result.is_granted())

    def test_empty_allow_list_is_not_wildcard(self) -> None:
        """Failure mode 2: empty allowed_capabilities meaning 'all'."""
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock, allowed=()))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
        )
        result = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertEqual(result.reason, "missing_capability")

    def test_resource_id_case_alias_is_unknown(self) -> None:
        """Failure mode 3: case/alias confusion on protected resource IDs."""
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
        )
        result = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ahos_repository",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertEqual(result.reason, "unknown_resource")

    def test_proposed_task_cannot_execute(self) -> None:
        """Failure mode 4: skipping authorization and executing from PROPOSED."""
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = org.tasks.create(
            task_type="premature",
            requester="tester",
            assigned_agent="agent.test-executor",
            requested_capabilities=("sandbox.execute",),
            target_resources=("ORG_TEST_SANDBOX",),
            actor="tester",
        )
        self.assertEqual(task.current_state, TaskState.PROPOSED)
        result = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertEqual(result.reason, "invalid_task_state")

    def test_unassigned_agent_cannot_use_another_agents_task(self) -> None:
        """Failure mode 5: identity substitution onto someone else's task."""
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        org.register_fixture_agent(
            fixture_agent(org.clock, agent_id="agent.test-impostor")
        )
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
        )
        result = org.authorize(
            agent_id="agent.test-impostor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertEqual(result.reason, "agent_not_assigned")

    def test_capability_and_resource_must_be_declared_on_the_task(self) -> None:
        """Failure mode 6: widening the task at decision time."""
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("audit.read",),
            resources=("ORG_AUDIT_LOG",),
        )
        extra_cap = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_AUDIT_LOG",
            action="read",
        )
        extra_res = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="audit.read",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(extra_cap.reason, "capability_not_on_task")
        self.assertEqual(extra_res.reason, "resource_not_on_task")

    def test_verified_maturity_still_cannot_open_ahos(self) -> None:
        """Failure mode 7: maturity spoofing as a substitute for an allow-list."""
        org = new_org()
        org.register_fixture_agent(
            fixture_agent(org.clock, maturity=MaturityLevel.OPERATIONALLY_TRUSTED)
        )
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("AHOS_PRODUCTION",),
        )
        org.tasks.grant_human_approval(task.task_id, approver="human-1")
        result = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="AHOS_PRODUCTION",
            action="connect",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertFalse(result.is_granted())

    def test_blocked_task_returns_blocked_not_allow(self) -> None:
        """Failure mode 8: BLOCKED collapsing to ALLOW or silent continue."""
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
        )
        org.tasks.transition(
            task.task_id, TaskState.BLOCKED, actor="tester", reason="hold"
        )
        result = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.BLOCKED)
        self.assertFalse(result.is_granted())
