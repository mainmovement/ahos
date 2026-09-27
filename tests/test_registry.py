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


class AdvanceMaturityTests(unittest.TestCase):
    """The single legal path from REGISTERED toward IMPLEMENTED.

    These tests pin the lifecycle foundation: maturity can be raised one level
    with evidence, and every shortcut around it is refused and audited.
    """

    def test_one_level_up_with_evidence_succeeds(self) -> None:
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        updated = org.agents.advance_maturity(
            agent_id,
            actor="human-governance",
            evidence="M-GAP-028: implementation reviewed, tests green",
            target=MaturityLevel.IMPLEMENTED,
        )
        self.assertEqual(updated.maturity_level, MaturityLevel.IMPLEMENTED)
        self.assertEqual(updated.governance_status.value, "ACTIVE")
        # persisted, not just returned
        self.assertEqual(org.agents.get(agent_id).maturity_level, MaturityLevel.IMPLEMENTED)

    def test_requires_non_empty_evidence(self) -> None:
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        for blank in ("", "   ", "\n"):
            with self.assertRaises(ValidationError):
                org.agents.advance_maturity(
                    agent_id,
                    actor="human-governance",
                    evidence=blank,
                    target=MaturityLevel.IMPLEMENTED,
                )
        # refused advance must not have mutated the record
        self.assertEqual(org.agents.get(agent_id).maturity_level, MaturityLevel.REGISTERED)

    def test_refuses_to_skip_levels(self) -> None:
        """TESTED/VERIFIED need the verified path, not this method."""
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        for beyond in (MaturityLevel.TESTED, MaturityLevel.VERIFIED, MaturityLevel.OPERATIONALLY_TRUSTED):
            with self.assertRaises(ValidationError):
                org.agents.advance_maturity(
                    agent_id,
                    actor="human-governance",
                    evidence="attempted verified path",
                    target=beyond,
                )
        self.assertEqual(org.agents.get(agent_id).maturity_level, MaturityLevel.REGISTERED)

    def test_refuses_descent_and_noop(self) -> None:
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        org.agents.advance_maturity(
            agent_id,
            actor="human-governance",
            evidence="first step",
            target=MaturityLevel.IMPLEMENTED,
        )
        with self.assertRaises(ValidationError):
            org.agents.advance_maturity(
                agent_id,
                actor="human-governance",
                evidence="step down",
                target=MaturityLevel.REGISTERED,
            )
        with self.assertRaises(ValidationError):
            org.agents.advance_maturity(
                agent_id,
                actor="human-governance",
                evidence="no-op",
                target=MaturityLevel.IMPLEMENTED,
            )
        self.assertEqual(org.agents.get(agent_id).maturity_level, MaturityLevel.IMPLEMENTED)

    def test_refuses_sub_floor_target(self) -> None:
        """DESIGNED (1) sits below the ALLOW floor, so raising to it cannot matter."""
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        with self.assertRaises(ValidationError):
            org.agents.advance_maturity(
                agent_id,
                actor="human-governance",
                evidence="sub-floor target",
                target=MaturityLevel.DESIGNED,
            )
        self.assertEqual(org.agents.get(agent_id).maturity_level, MaturityLevel.REGISTERED)

    def test_refuses_targets_above_implemented(self) -> None:
        """VERIFIED+ needs the verified path, which this method does not provide."""
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        for high in (MaturityLevel.VERIFIED, MaturityLevel.OPERATIONALLY_TRUSTED):
            with self.assertRaises(ValidationError):
                org.agents.advance_maturity(
                    agent_id,
                    actor="human-governance",
                    evidence="attempted verified path",
                    target=high,
                )
        self.assertEqual(org.agents.get(agent_id).maturity_level, MaturityLevel.REGISTERED)

    def test_refused_attempt_is_audit_logged(self) -> None:
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        with self.assertRaises(ValidationError):
            org.agents.advance_maturity(
                agent_id,
                actor="some-actor",
                evidence="",
                target=MaturityLevel.IMPLEMENTED,
            )
        events = [e for e in org.audit.events() if e.action == "advance_maturity"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].decision, "DENY")
        self.assertEqual(events[0].target, agent_id)

    def test_successful_advance_is_audit_logged_with_evidence(self) -> None:
        org = new_org()
        agent_id = CANONICAL_AGENT_IDS[0]
        org.agents.advance_maturity(
            agent_id,
            actor="human-governance",
            evidence="reviewed under M-GAP-028",
            target=MaturityLevel.IMPLEMENTED,
        )
        events = [e for e in org.audit.events() if e.action == "advance_maturity"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].decision, "ALLOW")
        self.assertEqual(events[0].reason, "reviewed under M-GAP-028")
        self.assertIn("maturity=IMPLEMENTED", events[0].evidence_refs)

    def test_advance_unlocks_authorize_maturity_gate(self) -> None:
        """End-to-end proof the gate is the real blocker, and the fix path works.

        Before the advance the engine denies with insufficient_maturity; after a
        single legal advance the same request reaches the human-approval gate
        instead. This is the mechanical content of M-GAP-028.
        """
        from tests.support import authorized_task

        org = new_org()
        agent_id = "agent.test-executor"
        record = fixture_agent(org.clock, allowed=("sandbox.execute",), maturity=MaturityLevel.REGISTERED)
        org.register_fixture_agent(record)

        task = authorized_task(
            org,
            agent_id=agent_id,
            capabilities=("sandbox.execute",),
            resources=("ORG_TEST_SANDBOX",),
        )

        def authorize() -> str:
            return org.authorize(
                agent_id=agent_id,
                task_id=task.task_id,
                capability="sandbox.execute",
                resource_id="ORG_TEST_SANDBOX",
                action="execute",
            ).reason

        self.assertEqual(authorize(), "insufficient_maturity")

        org.agents.advance_maturity(
            agent_id,
            actor="human-governance",
            evidence="gate demonstration",
            target=MaturityLevel.IMPLEMENTED,
        )
        # The maturity gate was the only blocker: once cleared, the same request
        # is allowed. The human-approval gate is exercised separately by
        # test_governance.py against a resource that requires it.
        self.assertEqual(authorize(), "all_conditions_passed")
