from __future__ import annotations

import unittest

from ahos_org.models import AuthzDecision, MaturityLevel, RiskLevel
from ahos_org.resources import PROTECTED_AHOS_RESOURCE_IDS
from tests.support import authorized_task, fixture_agent, new_org


class GovernanceTests(unittest.TestCase):
    def test_default_deny_for_canonical_registered_agent(self) -> None:
        org = new_org()
        task = authorized_task(
            org,
            agent_id="agent.chief-orchestrator",
            capabilities=("policy.inspect",),
            resources=("ORG_REGISTRY",),
        )
        result = org.authorize(
            agent_id="agent.chief-orchestrator",
            task_id=task.task_id,
            capability="policy.inspect",
            resource_id="ORG_REGISTRY",
            action="inspect",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertEqual(result.reason, "insufficient_maturity")
        self.assertFalse(result.is_granted())

    def test_authorized_operation_allowed_only_when_all_conditions_pass(self) -> None:
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
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.ALLOW)
        self.assertEqual(result.reason, "all_conditions_passed")
        self.assertTrue(result.is_granted())

    def test_insufficient_maturity_denied(self) -> None:
        org = new_org()
        org.register_fixture_agent(
            fixture_agent(org.clock, maturity=MaturityLevel.DESIGNED)
        )
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
        self.assertEqual(result.reason, "insufficient_maturity")

    def test_missing_capability_denied(self) -> None:
        org = new_org()
        org.register_fixture_agent(
            fixture_agent(org.clock, allowed=("audit.read", "policy.inspect"))
        )
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

    def test_protected_resource_denied_by_default(self) -> None:
        org = new_org()
        org.register_fixture_agent(
            fixture_agent(org.clock, maturity=MaturityLevel.VERIFIED)
        )
        for resource_id in PROTECTED_AHOS_RESOURCE_IDS:
            task = authorized_task(
                org,
                agent_id="agent.test-executor",
                capabilities=("sandbox.execute",),
                resources=(resource_id,),
            )
            org.tasks.grant_human_approval(task.task_id, approver="human-1")
            result = org.authorize(
                agent_id="agent.test-executor",
                task_id=task.task_id,
                capability="sandbox.execute",
                resource_id=resource_id,
                action="execute",
            )
            self.assertEqual(result.decision, AuthzDecision.DENY, resource_id)
            self.assertIn(
                result.reason,
                {"forbidden_operation", "operation_not_allowed"},
                resource_id,
            )

    def test_human_approval_requirement_enforced(self) -> None:
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("release.review",),
            resources=("ORG_CHANGE_CONTROL",),
        )
        denied = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="release.review",
            resource_id="ORG_CHANGE_CONTROL",
            action="review",
        )
        self.assertEqual(denied.decision, AuthzDecision.REQUIRES_REVIEW)
        self.assertFalse(denied.is_granted())
        org.tasks.grant_human_approval(task.task_id, approver="human-1")
        allowed = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="release.review",
            resource_id="ORG_CHANGE_CONTROL",
            action="review",
        )
        self.assertEqual(allowed.decision, AuthzDecision.ALLOW)

    def test_unknown_resource_denied(self) -> None:
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
            resource_id="NOT_A_RESOURCE",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertEqual(result.reason, "unknown_resource")

    def test_unknown_capability_denied(self) -> None:
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
            capability="quantum.override",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.DENY)
        self.assertEqual(result.reason, "unknown_capability")

    def test_high_risk_requires_review(self) -> None:
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
            risk=RiskLevel.CRITICAL,
        )
        result = org.authorize(
            agent_id="agent.test-executor",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision, AuthzDecision.REQUIRES_REVIEW)
        self.assertFalse(result.is_granted())
