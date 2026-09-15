"""D-04: knowledge-promotion Approval is bound to KnowledgeCandidate.candidate_id.

Critical cases cross TrustedCommandBoundary.submit. Missing binding is not a
wildcard. D-01 generic TRANSITION_ARTIFACT -> PROMOTED remains denied.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta

from agent_org.commands import (
    CreateApprovalPayload,
    PromoteKnowledgePayload,
    TransitionArtifactPayload,
)
from agent_org.contracts import (
    Capability,
    CommandStatus,
    CommandType,
    Decision,
    Operation,
    Resource,
)
from agent_org.epistemic import (
    Approval,
    ApprovalState,
    KNOWLEDGE_PROMOTION_DENIED_REASON,
    KnowledgeCandidate,
    KnowledgeState,
)
from tests2b.support import (
    grant_task_commands,
    make_command,
    provenance,
    ready_task,
    submit,
)


class D04CandidateBoundApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _issue_approval(
        self,
        candidate: KnowledgeCandidate | None,
        *,
        candidate_id: str | None | object = ...,
        task_id: str | None = None,
        action: str | None = None,
        resource_id: Resource | None = None,
        capability_id: Capability | None = None,
        policy_version: str = "slice-2b-v1",
        task_scope: str | None = None,
    ):
        holder = {}
        bound = None if candidate_id is ... else candidate_id
        if candidate_id is ...:
            bound = None if candidate is None else candidate.candidate_id

        def payload(cid):
            approval = Approval(
                approval_id=self.fx.env.ids.new("approval"),
                approver_principal_id=self.fx.env.plane.operator.principal_id,
                task_id=task_id if task_id is not None else self.fx.task.task_id,
                candidate_id=bound,  # type: ignore[arg-type]
                action=action or Operation.PROMOTE.value,
                resource_id=resource_id or Resource.EPISTEMIC_STORE,
                capability_id=capability_id or Capability.KNOWLEDGE_PROMOTE,
                policy_version=policy_version,
                issued_at=self.fx.env.clock.now(),
                expires_at=self.fx.env.clock.now() + timedelta(minutes=5),
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=ApprovalState.ACTIVE,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
            holder["approval"] = approval
            return CreateApprovalPayload(approval)

        result = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.CREATE_APPROVAL,
                payload,
                task_scope=task_scope or self.fx.task.task_id,
            ),
        )
        return result, holder.get("approval")

    def _promote(self, candidate, approval_id, *, task_scope=None, policy_version="slice-2b-v1"):
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        command = make_command(
            self.fx.env,
            CommandType.PROMOTE_KNOWLEDGE,
            lambda _cid: PromoteKnowledgePayload(current.candidate_id, approval_id),
            task_scope=task_scope or self.fx.task.task_id,
            expected_state_version=current.version,
            policy_version=policy_version,
        )
        return command, submit(self.fx.env, command), current

    def _assert_denied(self, result, reason, candidate, before_state=KnowledgeState.VERIFIED):
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        event = self.fx.env.plane.projections.audit_events()[-1]
        self.assertEqual(result.status, CommandStatus.DENIED)
        self.assertEqual(result.decision, Decision.DENY)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, reason)
        self.assertIs(live.lifecycle_state, before_state)
        self.assertEqual(event.result, CommandStatus.DENIED.value)
        self.assertEqual(event.failure_reason, reason)
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_a_matching_candidate_promotes_through_tcb(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(candidate)
        self.assertTrue(created.accepted, created)
        self.assertEqual(approval.candidate_id, candidate.candidate_id)
        command, result, _before = self._promote(candidate, approval.approval_id)
        self.assertTrue(result.accepted, result)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.PROMOTED)
        event = self.fx.env.plane.projections.audit_events()[-1]
        self.assertEqual(event.command_id, command.command_id)
        self.assertEqual(event.result, CommandStatus.ACCEPTED.value)
        self.assertEqual(event.resulting_state, KnowledgeState.PROMOTED.value)

    def test_b_mismatched_candidate_denied_through_tcb(self) -> None:
        first, _e1, _ = self.fx._verified_candidate()
        second, _e2, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(first)
        self.assertTrue(created.accepted, created)
        _command, result, _before = self._promote(second, approval.approval_id)
        self._assert_denied(result, "approval_candidate_mismatch", second)
        self.assertIs(
            self.fx.env.plane.projections.artifact(first.candidate_id).lifecycle_state,
            KnowledgeState.VERIFIED,
        )

    def test_c_missing_candidate_binding_is_not_wildcard(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(None, candidate_id=None)
        self.assertTrue(created.accepted, created)
        self.assertIsNone(approval.candidate_id)
        _command, result, _before = self._promote(candidate, approval.approval_id)
        self._assert_denied(result, "approval_missing_candidate_binding", candidate)

    def test_d_expired_matching_approval_denied(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(candidate)
        self.assertTrue(created.accepted, created)
        self.fx.env.clock.advance(301)
        _command, result, _before = self._promote(candidate, approval.approval_id)
        self._assert_denied(result, "approval_expired", candidate)

    def test_e_revoked_matching_approval_denied(self) -> None:
        from agent_org.commands import RevokeApprovalPayload

        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(candidate)
        self.assertTrue(created.accepted, created)
        revoke = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.REVOKE_APPROVAL,
                lambda _cid: RevokeApprovalPayload(approval.approval_id),
                task_scope=self.fx.task.task_id,
                expected_state_version=approval.version,
            ),
        )
        self.assertTrue(revoke.accepted, revoke)
        _command, result, _before = self._promote(candidate, approval.approval_id)
        self._assert_denied(result, "approval_revoked", candidate)

    def test_f_wrong_task_denied(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        other = ready_task(self.fx.env)
        grant_task_commands(
            self.fx.env,
            other.task_id,
            (CommandType.CREATE_APPROVAL, CommandType.PROMOTE_KNOWLEDGE),
        )
        created, approval = self._issue_approval(candidate)
        self.assertTrue(created.accepted, created)
        _command, result, _before = self._promote(
            candidate, approval.approval_id, task_scope=other.task_id
        )
        self._assert_denied(result, "approval_scope_mismatch", candidate)

    def test_g_wrong_capability_denied(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(
            candidate, capability_id=Capability.EPISTEMIC_WRITE
        )
        self.assertTrue(created.accepted, created)
        _command, result, _before = self._promote(candidate, approval.approval_id)
        self._assert_denied(result, "approval_scope_mismatch", candidate)

    def test_h_wrong_resource_denied(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(
            candidate, resource_id=Resource.TASK_STORE
        )
        self.assertTrue(created.accepted, created)
        _command, result, _before = self._promote(candidate, approval.approval_id)
        self._assert_denied(result, "approval_scope_mismatch", candidate)

    def test_i_wrong_policy_version_denied(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(candidate)
        self.assertTrue(created.accepted, created)
        _command, result, _before = self._promote(
            candidate, approval.approval_id, policy_version="slice-2b-v2"
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "policy_version_mismatch")
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.VERIFIED)

    def test_j_one_approval_cannot_promote_two_candidates(self) -> None:
        first, _e1, _ = self.fx._verified_candidate()
        second, _e2, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(first)
        self.assertTrue(created.accepted, created)
        _cmd_a, result_a, _ = self._promote(first, approval.approval_id)
        self.assertTrue(result_a.accepted, result_a)
        self.assertIs(
            self.fx.env.plane.projections.artifact(first.candidate_id).lifecycle_state,
            KnowledgeState.PROMOTED,
        )
        _cmd_b, result_b, _ = self._promote(second, approval.approval_id)
        self._assert_denied(result_b, "approval_candidate_mismatch", second)
        self.assertIs(
            self.fx.env.plane.projections.artifact(first.candidate_id).lifecycle_state,
            KnowledgeState.PROMOTED,
        )

    def test_unknown_candidate_binding_cannot_be_issued(self) -> None:
        created, _approval = self._issue_approval(
            None, candidate_id="candidate.does-not-exist"
        )
        self.assertEqual(created.reason, "approval_candidate_unknown")
        self.assertFalse(created.accepted)

    def test_approval_candidate_binding_is_immutable(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(candidate)
        self.assertTrue(created.accepted, created)
        with self.assertRaises(FrozenInstanceError):
            approval.candidate_id = "candidate.other"  # type: ignore[misc]
        live = self.fx.env.plane.projections.artifact(approval.approval_id)
        with self.assertRaises(FrozenInstanceError):
            live.candidate_id = "candidate.other"  # type: ignore[misc]
        mutated_copy = replace(approval, candidate_id="candidate.other")
        stored = self.fx.env.plane.projections.artifact(approval.approval_id)
        self.assertEqual(stored.candidate_id, candidate.candidate_id)
        self.assertEqual(mutated_copy.candidate_id, "candidate.other")
        self.assertIsNot(mutated_copy, stored)

    def test_d01_generic_transition_still_denied_with_bound_approval(self) -> None:
        candidate, _evidence, _ = self.fx._verified_candidate()
        created, approval = self._issue_approval(candidate)
        self.assertTrue(created.accepted, created)
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        command = make_command(
            self.fx.env,
            CommandType.TRANSITION_ARTIFACT,
            lambda _cid: TransitionArtifactPayload(
                artifact_id=current.candidate_id,
                target_state=KnowledgeState.PROMOTED,
            ),
            task_scope=self.fx.task.task_id,
            expected_state_version=current.version,
        )
        result = submit(self.fx.env, command)
        self.assertEqual(result.reason, KNOWLEDGE_PROMOTION_DENIED_REASON)
        self.assertEqual(result.status, CommandStatus.DENIED)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.VERIFIED)
        event = self.fx.env.plane.projections.audit_events()[-1]
        self.assertEqual(event.failure_reason, KNOWLEDGE_PROMOTION_DENIED_REASON)
        dedicated = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.PROMOTE_KNOWLEDGE,
                lambda _cid: PromoteKnowledgePayload(
                    current.candidate_id, approval.approval_id
                ),
                task_scope=self.fx.task.task_id,
                expected_state_version=current.version,
            ),
        )
        self.assertTrue(dedicated.accepted, dedicated)
        self.assertIs(
            self.fx.env.plane.projections.artifact(candidate.candidate_id).lifecycle_state,
            KnowledgeState.PROMOTED,
        )
