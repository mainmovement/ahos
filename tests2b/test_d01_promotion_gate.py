"""D-01 regression: KnowledgeCandidate.PROMOTED is not a generic transition.

Every attack here crosses TrustedCommandBoundary.submit unless a test
explicitly names a pure helper or a same-process residual.
"""

from __future__ import annotations

import ast
import re
import unittest
from enum import StrEnum
from pathlib import Path

from agent_org.commands import (
    CreateContradictionPayload,
    PromoteKnowledgePayload,
    TransitionArtifactPayload,
    TransitionTaskPayload,
)
from agent_org.contracts import (
    CommandStatus,
    CommandType,
    Decision,
    Operation,
    TaskState,
)
from agent_org.epistemic import (
    Approval,
    ContradictionCase,
    ContradictionState,
    EvidenceState,
    KNOWLEDGE_PROMOTION_COMMAND,
    KNOWLEDGE_PROMOTION_DENIED_REASON,
    KNOWLEDGE_PROMOTION_STATES,
    KnowledgeCandidate,
    KnowledgeState,
    LEGAL_ARTIFACT_TRANSITIONS,
    refuse_generic_knowledge_promotion,
    transition_artifact,
)
from agent_org.governance import COMMAND_POLICIES
from tests2b.support import make_command, provenance, submit


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "agent_org"


class D01PromotionGateRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _generic_promote(self, candidate: KnowledgeCandidate, target=KnowledgeState.PROMOTED):
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        command = make_command(
            self.fx.env,
            CommandType.TRANSITION_ARTIFACT,
            lambda _cid: TransitionArtifactPayload(
                artifact_id=current.candidate_id,
                target_state=target,
            ),
            task_scope=self.fx.task.task_id,
            expected_state_version=current.version,
        )
        return command, submit(self.fx.env, command), current

    def _assert_generic_promotion_denied(self, candidate, command, result, before):
        self.assertEqual(result.status, CommandStatus.DENIED)
        self.assertEqual(result.decision, Decision.DENY)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, KNOWLEDGE_PROMOTION_DENIED_REASON)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.VERIFIED)
        self.assertEqual(live.version, before.version)
        promoted = [
            item
            for item in self.fx.env.plane.projections.epistemic_objects()
            if isinstance(item, KnowledgeCandidate)
            and item.lifecycle_state is KnowledgeState.PROMOTED
        ]
        self.assertEqual(promoted, [])
        event = self.fx.env.plane.projections.audit_events()[-1]
        self.assertEqual(event.command_id, command.command_id)
        self.assertEqual(event.result, CommandStatus.DENIED.value)
        self.assertEqual(event.failure_reason, KNOWLEDGE_PROMOTION_DENIED_REASON)
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def _open_contradiction(self, candidate: KnowledgeCandidate, evidence) -> None:
        right = self.fx.claim(evidence)
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)

        def payload(cid):
            return CreateContradictionPayload(
                ContradictionCase(
                    contradiction_id=self.fx.env.ids.new("contradiction"),
                    left_artifact_id=candidate.claim_ids[0],
                    right_artifact_id=right.claim_id,
                    rationale="Open conflict after verification",
                    affects_candidate_ids=(candidate.candidate_id,),
                    provenance=provenance(self.fx.env, cid),
                    lifecycle_state=ContradictionState.OPEN,
                    created_at=self.fx.env.clock.now(),
                    updated_at=self.fx.env.clock.now(),
                )
            )

        result = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.CREATE_CONTRADICTION,
                payload,
                task_scope=self.fx.task.task_id,
                expected_state_version=current.version,
            ),
        )
        self.assertTrue(result.accepted, result)

    def test_generic_map_excludes_knowledge_promotion_states(self) -> None:
        rules = LEGAL_ARTIFACT_TRANSITIONS[KnowledgeCandidate]
        for targets in rules.values():
            for target in targets:
                self.assertNotIn(target, KNOWLEDGE_PROMOTION_STATES)
        self.assertIn(KnowledgeState.PROMOTED, KNOWLEDGE_PROMOTION_STATES)
        self.assertIs(KNOWLEDGE_PROMOTION_COMMAND, CommandType.PROMOTE_KNOWLEDGE)

    def test_generic_transition_table_cannot_be_rewritten(self) -> None:
        with self.assertRaises(TypeError):
            LEGAL_ARTIFACT_TRANSITIONS[KnowledgeCandidate] = {}  # type: ignore[index]
        with self.assertRaises(TypeError):
            LEGAL_ARTIFACT_TRANSITIONS[KnowledgeCandidate][KnowledgeState.VERIFIED] = (  # type: ignore[index]
                frozenset({KnowledgeState.PROMOTED})
            )

    def test_only_promote_knowledge_command_has_promote_operation(self) -> None:
        promote_commands = [
            command_type
            for command_type, policy in COMMAND_POLICIES.items()
            if policy.operation is Operation.PROMOTE
        ]
        self.assertEqual(promote_commands, [CommandType.PROMOTE_KNOWLEDGE])
        self.assertIs(
            COMMAND_POLICIES[CommandType.TRANSITION_ARTIFACT].operation,
            Operation.TRANSITION,
        )

    def test_attack_a_verified_to_promoted_via_transition_artifact_denied(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        command, result, before = self._generic_promote(candidate)
        self._assert_generic_promotion_denied(candidate, command, result, before)

    def test_attack_b_open_contradiction_generic_promotion_denied(self) -> None:
        candidate, evidence, _record = self.fx._verified_candidate()
        self._open_contradiction(candidate, evidence)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.VERIFIED)
        command, result, before = self._generic_promote(live)
        self._assert_generic_promotion_denied(live, command, result, before)

    def test_attack_c_no_approval_generic_promotion_denied(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        approvals = [
            item
            for item in self.fx.env.plane.projections.epistemic_objects()
            if isinstance(item, Approval)
        ]
        self.assertEqual(approvals, [])
        command, result, before = self._generic_promote(candidate)
        self._assert_generic_promotion_denied(candidate, command, result, before)

    def test_attack_d_valid_approval_does_not_enable_generic_promotion(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        approval = self.fx._approval(candidate)
        command, result, before = self._generic_promote(candidate)
        self._assert_generic_promotion_denied(candidate, command, result, before)
        dedicated = make_command(
            self.fx.env,
            CommandType.PROMOTE_KNOWLEDGE,
            lambda _cid: PromoteKnowledgePayload(
                candidate.candidate_id, approval.approval_id
            ),
            task_scope=self.fx.task.task_id,
            expected_state_version=before.version,
        )
        promoted = submit(self.fx.env, dedicated)
        self.assertTrue(promoted.accepted, promoted)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.PROMOTED)

    def test_attack_e_revoked_evidence_generic_promotion_denied(self) -> None:
        candidate, evidence, _record = self.fx._verified_candidate()
        self.assertTrue(self.fx.transition(evidence, EvidenceState.REVOKED).accepted)
        command, result, before = self._generic_promote(candidate)
        self._assert_generic_promotion_denied(candidate, command, result, before)

    def test_attack_e_stale_evidence_generic_promotion_denied(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        self.fx.env.clock.advance(601)
        command, result, before = self._generic_promote(candidate)
        self._assert_generic_promotion_denied(candidate, command, result, before)

    def test_dedicated_promotion_happy_path_still_requires_gates(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        missing = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.PROMOTE_KNOWLEDGE,
                lambda _cid: PromoteKnowledgePayload(
                    candidate.candidate_id, "approval.missing"
                ),
                task_scope=self.fx.task.task_id,
                expected_state_version=candidate.version,
            ),
        )
        self.assertEqual(missing.reason, "missing_required_approval")
        approval = self.fx._approval(candidate)
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
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.PROMOTED)
        event = self.fx.env.plane.projections.audit_events()[-1]
        self.assertEqual(event.result, CommandStatus.ACCEPTED.value)
        self.assertEqual(event.resulting_state, KnowledgeState.PROMOTED.value)
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_valid_promotion_replay_cannot_mutate_twice(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        approval = self.fx._approval(candidate)
        command = make_command(
            self.fx.env,
            CommandType.PROMOTE_KNOWLEDGE,
            lambda _cid: PromoteKnowledgePayload(
                candidate.candidate_id, approval.approval_id
            ),
            task_scope=self.fx.task.task_id,
            expected_state_version=candidate.version,
        )
        first = submit(self.fx.env, command)
        second = submit(self.fx.env, command)
        self.assertTrue(first.accepted, first)
        self.assertEqual(second.status, CommandStatus.REPLAYED)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.PROMOTED)
        self.assertEqual(live.version, candidate.version + 1)

    def test_malformed_string_target_state_denied(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        command, result, before = self._generic_promote(candidate, target="PROMOTED")
        self._assert_generic_promotion_denied(candidate, command, result, before)

    def test_aliased_strenum_target_state_denied(self) -> None:
        class Alias(StrEnum):
            PROMOTED = "PROMOTED"

        candidate, _evidence, _record = self.fx._verified_candidate()
        command, result, before = self._generic_promote(candidate, target=Alias.PROMOTED)
        self._assert_generic_promotion_denied(candidate, command, result, before)

    def test_direct_lifecycle_helper_cannot_produce_promoted_candidate(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        with self.assertRaises(ValueError) as ctx:
            transition_artifact(
                candidate, KnowledgeState.PROMOTED, self.fx.env.clock.now()
            )
        self.assertEqual(str(ctx.exception), KNOWLEDGE_PROMOTION_DENIED_REASON)
        with self.assertRaises(ValueError):
            refuse_generic_knowledge_promotion(candidate, KnowledgeState.PROMOTED)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.VERIFIED)

    def test_register_artifact_cannot_enter_as_promoted(self) -> None:
        evidence = self.fx.valid_evidence()
        claim = self.fx.claim(evidence)
        result, _item = self.fx.register(
            lambda cid: KnowledgeCandidate(
                candidate_id=self.fx.env.ids.new("candidate"),
                proposition="Cannot start promoted",
                producer_principal_id=self.fx.producer.principal_id,
                claim_ids=(claim.claim_id,),
                evidence_ids=(evidence.evidence_id,),
                verification_ids=(),
                contradiction_ids=(),
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=KnowledgeState.PROMOTED,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
        )
        self.assertEqual(result.reason, "artifact_initial_state_invalid")
        self.assertFalse(
            any(
                isinstance(item, KnowledgeCandidate)
                and item.lifecycle_state is KnowledgeState.PROMOTED
                for item in self.fx.env.plane.projections.epistemic_objects()
            )
        )

    def test_alternate_command_type_cannot_promote(self) -> None:
        candidate, _evidence, _record = self.fx._verified_candidate()
        task = self.fx.env.plane.projections.task(self.fx.task.task_id)
        self.assertIsNotNone(task)
        result = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.TRANSITION_TASK,
                lambda _cid: TransitionTaskPayload(
                    task_id=task.task_id,
                    target_state=TaskState.RUNNING.value,
                ),
                task_scope=task.task_id,
                expected_state_version=task.version,
            ),
        )
        self.assertTrue(result.accepted, result)
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.VERIFIED)

    def test_production_code_has_one_knowledge_promoted_write(self) -> None:
        pattern = re.compile(r"lifecycle_state\s*=\s*KnowledgeState\.PROMOTED")
        hits: list[tuple[str, int]] = []
        for path in PACKAGE.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append((path.name, lineno))
        self.assertEqual(len(hits), 1, hits)
        self.assertEqual(hits[0][0], "tcb.py")
        tcb_text = (PACKAGE / "tcb.py").read_text(encoding="utf-8")
        promote_at = tcb_text.index("def __promote(")
        next_def = tcb_text.find("\n    def ", promote_at + 1)
        assignment_at = tcb_text.index("lifecycle_state=KnowledgeState.PROMOTED")
        self.assertGreater(assignment_at, promote_at)
        self.assertLess(assignment_at, next_def)

    def test_no_hidden_promote_helper_or_test_bypass_in_production(self) -> None:
        forbidden_names = {
            "force_promote",
            "unsafe_promote",
            "test_promote",
            "bypass_promotion",
        }
        for path in PACKAGE.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
            self.assertFalse(names & forbidden_names, (path, names & forbidden_names))

    def test_reflection_store_access_is_same_process_residual(self) -> None:
        """Classify hostile reflection; do not implement a bypass."""
        store = self.fx.env.plane.tcb._TrustedCommandBoundary__store
        self.assertTrue(hasattr(store, "_GovernedStore__state"))
        self.assertTrue(hasattr(self.fx.env.plane.tcb, "_TrustedCommandBoundary__permit"))
        live = self.fx.env.plane.projections.epistemic_objects()
        self.assertTrue(isinstance(live, tuple))
