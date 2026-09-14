from __future__ import annotations

import unittest

from ahos_org.errors import UnknownIdentityError, ValidationError
from ahos_org.models import MaturityLevel
from ahos_org.policy import GLOBAL_DENY_CAPABILITIES
from ahos_org.registry import CANONICAL_AGENT_IDS, validate_maturity
from tests.support import fixture_agent, new_org


class AgentRegistryTests(unittest.TestCase):
    def test_all_19_roles_registered(self) -> None:
        org = new_org()
        roles = {agent.role for agent in org.agents.list_agents()}
        expected = {
            "Chief Orchestrator",
            "Reality Forensics",
            "Evidence Transport",
            "Security",
            "Identity",
            "Canonical Decision Auditor",
            "Scoring Science",
            "Paper Trading",
            "Learning / Memory",
            "Calibration",
            "Cognitive / AGI-ACI",
            "Windows Runtime",
            "Provider / Data",
            "Integration",
            "Frontend / UX",
            "Independent Verification",
            "Red Team",
            "Change Architect",
            "Release / Governance Reviewer",
        }
        self.assertEqual(roles, expected)
        self.assertEqual(len(CANONICAL_AGENT_IDS), 19)
        self.assertEqual(set(org.agents.ids()) & set(CANONICAL_AGENT_IDS), set(CANONICAL_AGENT_IDS))

    def test_stable_ids(self) -> None:
        first = new_org().agents.ids()
        second = new_org().agents.ids()
        self.assertEqual(first, CANONICAL_AGENT_IDS)
        self.assertEqual(first, second)

    def test_initial_maturity_is_registered_only(self) -> None:
        org = new_org()
        for agent in org.agents.list_agents():
            self.assertEqual(agent.maturity_level, MaturityLevel.REGISTERED)
            self.assertLess(int(agent.maturity_level), int(MaturityLevel.IMPLEMENTED))

    def test_invalid_maturity_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_maturity(-1)
        with self.assertRaises(ValidationError):
            validate_maturity(6)
        with self.assertRaises(ValidationError):
            validate_maturity(99)

    def test_disabled_agent_cannot_execute(self) -> None:
        org = new_org()
        org.register_fixture_agent(fixture_agent(org.clock))
        org.agents.disable("agent.test-executor", actor="tester")
        from tests.support import authorized_task

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
        self.assertEqual(result.decision.value, "DENY")
        self.assertEqual(result.reason, "agent_disabled")
        self.assertFalse(result.is_granted())

    def test_unknown_agent_denied(self) -> None:
        org = new_org()
        with self.assertRaises(UnknownIdentityError):
            org.agents.get("agent.does-not-exist")
        from tests.support import authorized_task

        org.register_fixture_agent(fixture_agent(org.clock))
        task = authorized_task(
            org,
            agent_id="agent.test-executor",
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
        )
        result = org.authorize(
            agent_id="agent.unknown-ghost",
            task_id=task.task_id,
            capability="sandbox.execute",
            resource_id="ORG_TEST_SANDBOX",
            action="execute",
        )
        self.assertEqual(result.decision.value, "DENY")
        self.assertEqual(result.reason, "unknown_agent")

    def test_globally_denied_capability_cannot_be_registered_as_allowed(self) -> None:
        org = new_org()
        cap = next(iter(GLOBAL_DENY_CAPABILITIES))
        record = fixture_agent(org.clock, allowed=(cap,))
        with self.assertRaises(ValidationError):
            org.register_fixture_agent(record)
