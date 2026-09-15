"""D-20 remediation: ``Approval.action`` is a typed ``Operation``.

A free-form ``str`` action let approvals carry operations the command
vocabulary never defined.  The contract now coerces known values
(``"PROMOTE"`` kept working for existing call sites) and fails closed on
anything else; the promotion gate compares identity against
``Operation.PROMOTE``.
"""

from __future__ import annotations

import unittest
from datetime import timedelta

from agent_org.commands import PromoteKnowledgePayload
from agent_org.contracts import (
    Capability,
    CommandType,
    Operation,
    Resource,
)
from agent_org.epistemic import Approval, ApprovalState
from tests2b.support import make_command, provenance, submit


class D20ApprovalActionTypingTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _approval_kwargs(self, cid: str, action) -> dict:
        now = self.fx.env.clock.now()
        candidate, _evidence, _record = self.fx._verified_candidate()
        return {
            "approval_id": self.fx.env.ids.new("approval"),
            "approver_principal_id": self.fx.env.plane.operator.principal_id,
            "task_id": self.fx.task.task_id,
            "candidate_id": candidate.candidate_id,
            "action": action,
            "resource_id": Resource.EPISTEMIC_STORE,
            "capability_id": Capability.KNOWLEDGE_PROMOTE,
            "policy_version": "slice-2b-v1",
            "issued_at": now,
            "expires_at": now + timedelta(minutes=5),
            "provenance": provenance(self.fx.env, cid),
            "lifecycle_state": ApprovalState.ACTIVE,
            "created_at": now,
            "updated_at": now,
        }

    def test_string_value_coerces_to_operation(self) -> None:
        approval = Approval(**self._approval_kwargs("command.a1", "PROMOTE"))
        self.assertIs(approval.action, Operation.PROMOTE)

    def test_enum_member_stays_operation(self) -> None:
        approval = Approval(
            **self._approval_kwargs("command.a2", Operation.APPROVE)
        )
        self.assertIs(approval.action, Operation.APPROVE)

    def test_unknown_action_string_fails_closed(self) -> None:
        for forged in ("PROMOT", "DELETE_EVERYTHING", "PROMOTE ", ""):
            with self.assertRaises(ValueError, msg=forged):
                Approval(**self._approval_kwargs("command.a3", forged))

    def test_promotion_gate_still_accepts_coerced_approval(self) -> None:
        candidate = self.fx._verified_candidate()[0]
        approval = self.fx._approval(candidate)
        live_approval = self.fx.env.plane.projections.artifact(
            approval.approval_id
        )
        self.assertIs(live_approval.action, Operation.PROMOTE)
        result = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.PROMOTE_KNOWLEDGE,
                lambda _cid: PromoteKnowledgePayload(
                    candidate.candidate_id, approval.approval_id
                ),
                task_scope=self.fx.task.task_id,
                expected_state_version=candidate.version,
            ),
        )
        self.assertTrue(result.accepted, result)


if __name__ == "__main__":
    unittest.main()
