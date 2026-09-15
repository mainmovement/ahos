"""D-05 remediation: claims must pass through CHALLENGED before VERIFIED.

The claim lifecycle previously allowed ``SUBMITTED -> VERIFIED`` while the
knowledge candidate lifecycle already forced ``CHALLENGED`` first.  A claim
is an interpretation of evidence, not a fact (spec section 14); letting it
skip challenge made claim-VERIFIED strictly weaker than candidate-VERIFIED
for no reason the spec states.  The map edge is removed; every other claim
edge is unchanged.
"""

from __future__ import annotations

import unittest

from agent_org.epistemic import Claim, ClaimState, LEGAL_ARTIFACT_TRANSITIONS


class D05ClaimChallengePathTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def test_map_excludes_submitted_to_verified(self) -> None:
        claim_rules = LEGAL_ARTIFACT_TRANSITIONS[Claim]
        self.assertNotIn(
            ClaimState.VERIFIED, claim_rules[ClaimState.SUBMITTED]
        )
        self.assertIn(ClaimState.CHALLENGED, claim_rules[ClaimState.SUBMITTED])
        self.assertIn(ClaimState.VERIFIED, claim_rules[ClaimState.CHALLENGED])

    def test_submitted_to_verified_denied_through_tcb(self) -> None:
        claim = self.fx.claim(self.fx.valid_evidence())
        self.assertTrue(self.fx.transition(claim, ClaimState.SUBMITTED).accepted)
        current = self.fx.env.plane.projections.artifact(claim.claim_id)
        denied = self.fx.transition(current, ClaimState.VERIFIED)
        self.assertFalse(denied.accepted, denied)
        self.assertIn("illegal epistemic transition", denied.reason)
        live = self.fx.env.plane.projections.artifact(claim.claim_id)
        self.assertIs(live.lifecycle_state, ClaimState.SUBMITTED)
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_full_claim_challenge_path_verifies(self) -> None:
        evidence = self.fx.valid_evidence()
        claim = self.fx.claim(evidence)
        self.assertTrue(self.fx.transition(claim, ClaimState.SUBMITTED).accepted)
        current = self.fx.env.plane.projections.artifact(claim.claim_id)
        self.assertTrue(self.fx.transition(current, ClaimState.CHALLENGED).accepted)
        current = self.fx.env.plane.projections.artifact(claim.claim_id)
        from agent_org.commands import CreateVerificationPayload
        from agent_org.contracts import CommandType
        from agent_org.epistemic import (
            VerificationKind,
            VerificationRecord,
            VerificationStatus,
        )
        from tests2b.support import make_command, provenance, submit

        def payload(cid: str) -> CreateVerificationPayload:
            return CreateVerificationPayload(
                VerificationRecord(
                    verification_id=self.fx.env.ids.new("verification"),
                    target_artifact_id=current.claim_id,
                    producer_principal_id=self.fx.producer.principal_id,
                    verifier_principal_id=self.fx.env.plane.operator.principal_id,
                    verification_kind=VerificationKind.INDEPENDENT,
                    status=VerificationStatus.PASS,
                    evidence_ids=(evidence.evidence_id,),
                    method="independent-claim-review",
                    provenance=provenance(self.fx.env, cid),
                    lifecycle_state=VerificationStatus.PASS,
                    created_at=self.fx.env.clock.now(),
                    updated_at=self.fx.env.clock.now(),
                )
            )

        verified = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.CREATE_VERIFICATION,
                payload,
                task_scope=self.fx.task.task_id,
                expected_state_version=current.version,
            ),
        )
        self.assertTrue(verified.accepted, verified)
        current = self.fx.env.plane.projections.artifact(claim.claim_id)
        result = self.fx.transition(current, ClaimState.VERIFIED)
        self.assertTrue(result.accepted, result)
        live = self.fx.env.plane.projections.artifact(claim.claim_id)
        self.assertIs(live.lifecycle_state, ClaimState.VERIFIED)

    def test_draft_to_verified_still_denied(self) -> None:
        claim = self.fx.claim(self.fx.valid_evidence())
        denied = self.fx.transition(claim, ClaimState.VERIFIED)
        self.assertIn("illegal epistemic transition", denied.reason)


if __name__ == "__main__":
    unittest.main()
