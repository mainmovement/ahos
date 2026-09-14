from __future__ import annotations

import unittest

from ahos_org.errors import UnknownIdentityError
from ahos_org.resources import PROTECTED_AHOS_RESOURCE_IDS
from tests.support import authorized_task, fixture_agent, new_org


class ProtectedResourceTests(unittest.TestCase):
    def test_all_protected_resources_registered(self) -> None:
        org = new_org()
        ids = set(org.resources.ids())
        self.assertTrue(set(PROTECTED_AHOS_RESOURCE_IDS).issubset(ids))
        self.assertEqual(len(PROTECTED_AHOS_RESOURCE_IDS), 12)

    def test_forbidden_operations_denied(self) -> None:
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
            action="connect",
        )
        self.assertEqual(result.decision.value, "DENY")
        self.assertEqual(result.reason, "globally_denied_operation")

    def test_unknown_resources_fail_closed(self) -> None:
        org = new_org()
        with self.assertRaises(UnknownIdentityError):
            org.resources.get("AHOS_NOT_REAL")
        self.assertFalse(org.resources.exists("AHOS_REPOSITORY".lower()))

    def test_ahos_resources_have_empty_allow_list(self) -> None:
        org = new_org()
        for resource_id in PROTECTED_AHOS_RESOURCE_IDS:
            resource = org.resources.get(resource_id)
            self.assertEqual(resource.allowed_operations, ())
            self.assertTrue(resource.requires_human_approval)
            self.assertTrue(resource.requires_verified_agent)
            self.assertEqual(resource.classification, "PROTECTED_EXTERNAL")

    def test_registry_does_not_hold_live_handles(self) -> None:
        org = new_org()
        for resource in org.resources.list_resources():
            self.assertIsInstance(resource.resource_id, str)
            self.assertIsInstance(resource.notes, str)
            self.assertNotIn("socket", type(resource).__name__.lower())
