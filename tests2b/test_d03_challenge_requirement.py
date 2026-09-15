"""D-03 remediation: knowledge CHALLENGED / VERIFIED require a real challenge.

Before this closure ``UNDER_REVIEW -> CHALLENGED`` was a bare enum flip: a
candidate could sail through CHALLENGED and VERIFIED without any
``ContradictionCase`` ever existing. VERIFIED then falsely meant "survived
challenge" when nothing had ever challenged the candidate.

Closure (live gate, no dead defense branches):

- transition into ``KnowledgeState.CHALLENGED`` is denied unless a stored
  ``ContradictionCase`` names the candidate in ``affects_candidate_ids``;
- the map still allows VERIFIED only from CHALLENGED (already true);
- unresolved contradiction still blocks VERIFIED, so the composed, fully
  reachable chain is:

      file contradiction -> CHALLENGED -> resolve with eligible evidence
      -> independent PASS verification -> VERIFIED -> PROMOTE_KNOWLEDGE

A separate "VERIFIED requires a challenge" branch inside
``__require_candidate_verification`` would be unreachable through the TCB
precisely because of the gate above; it was deliberately not added, and the
composed chain is what these tests pin.
"""

from __future__ import annotations

import unittest

from agent_org.commands import (
    PromoteKnowledgePayload,
    TransitionArtifactPayload,
)
from agent_org.contracts import CommandType
from agent_org.epistemic import (
    ContradictionState,
    KnowledgeState,
)
from tests2b.support import make_command, submit


class D03ChallengeRequirementTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _candidate_under_review(self):
        evidence = self.fx.valid_evidence()
        left = self.fx.claim(evidence)
        right = self.fx.claim(evidence)
        candidate = self.fx.candidate(left, evidence)
        self.assertTrue(
            self.fx.transition(candidate, KnowledgeState.UNDER_REVIEW).accepted
        )
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        return current, evidence, left, right

    def test_challenged_without_any_challenge_artifact_denied(self) -> None:
        candidate, _evidence, _left, _right = self._candidate_under_review()
        result = self.fx.transition(candidate, KnowledgeState.CHALLENGED)
        self.assertFalse(result.accepted, result)
        self.assertEqual(
            result.reason, "knowledge_challenge_requires_contradiction_case"
        )
        live = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(live.lifecycle_state, KnowledgeState.UNDER_REVIEW)
        self.assertEqual(live.version, candidate.version)
        self.assertEqual(live.contradiction_ids, ())
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_challenge_for_other_candidate_does_not_count(self) -> None:
        candidate, evidence, left, right = self._candidate_under_review()
        other, _other_evidence, other_left, other_right = (
            self._candidate_under_review()
        )
        self.fx._file_challenge(other, other_left.claim_id, other_right.claim_id)
        result = self.fx.transition(candidate, KnowledgeState.CHALLENGED)
        self.assertEqual(
            result.reason, "knowledge_challenge_requires_contradiction_case"
        )
        _ = (evidence, left, right)

    def test_full_challenge_lifecycle_reaches_verified_and_promoted(self) -> None:
        candidate = self.fx._verified_candidate()[0]
        self.assertIs(candidate.lifecycle_state, KnowledgeState.VERIFIED)
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
        challenges = [
            item
            for item in self.fx.env.plane.projections.epistemic_objects()
            if item.__class__.__name__ == "ContradictionCase"
            and candidate.candidate_id in item.affects_candidate_ids
        ]
        self.assertEqual(len(challenges), 1)
        self.assertIs(challenges[0].lifecycle_state, ContradictionState.RESOLVED)
        self.assertEqual(len(challenges[0].resolution_evidence_ids), 1)
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_unresolved_challenge_still_blocks_verified_transition(self) -> None:
        candidate, evidence, left, right = self._candidate_under_review()
        self.fx._file_challenge(candidate, left.claim_id, right.claim_id)
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertTrue(
            self.fx.transition(current, KnowledgeState.CHALLENGED).accepted
        )
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        verify, _record = self.fx.verify(
            current, self.fx.producer.principal_id, (evidence.evidence_id,)
        )
        self.assertTrue(verify.accepted, verify)
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        denied = self.fx.transition(current, KnowledgeState.VERIFIED)
        self.assertEqual(denied.reason, "unresolved_contradiction")

    def test_resolution_with_ineligible_evidence_denied(self) -> None:
        candidate, _evidence, left, right = self._candidate_under_review()
        challenge = self.fx._file_challenge(
            candidate, left.claim_id, right.claim_id
        )
        # Cite evidence that was never independently verified -> ineligible.
        stale_source = self.fx.source()
        ineligible = self.fx.evidence(stale_source)
        result = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.TRANSITION_ARTIFACT,
                lambda _cid: TransitionArtifactPayload(
                    artifact_id=challenge.contradiction_id,
                    target_state=ContradictionState.RESOLVED,
                    evidence_ids=(ineligible.evidence_id,),
                ),
                task_scope=self.fx.task.task_id,
                expected_state_version=challenge.version,
            ),
        )
        self.assertEqual(result.reason, "contradiction_resolution_evidence_invalid")

    def test_verified_candidate_can_be_rechallenged_only_with_artifact(self) -> None:
        candidate, evidence, _record = self.fx._verified_candidate()
        # The lifecycle already holds one RESOLVED challenge, so re-entry
        # into CHALLENGED is backed by an artifact; a fresh OPEN challenge
        # must also block promotion while unresolved.
        left = self.fx.claim(evidence)
        right = self.fx.claim(evidence)
        self.fx._file_challenge(candidate, left.claim_id, right.claim_id)
        current = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        result = self.fx.transition(current, KnowledgeState.CHALLENGED)
        self.assertTrue(result.accepted, result)
        challenged = self.fx.env.plane.projections.artifact(candidate.candidate_id)
        self.assertIs(challenged.lifecycle_state, KnowledgeState.CHALLENGED)
        approval = self.fx._approval(challenged)
        blocked = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.PROMOTE_KNOWLEDGE,
                lambda _cid: PromoteKnowledgePayload(
                    challenged.candidate_id, approval.approval_id
                ),
                task_scope=self.fx.task.task_id,
                expected_state_version=challenged.version,
            ),
        )
        self.assertEqual(blocked.reason, "candidate_not_verified")


if __name__ == "__main__":
    unittest.main()
