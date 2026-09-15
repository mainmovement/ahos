"""D-14 disposition: evidence_lineage is audit annotation, not an authority input.

Register analysis conclusion (SPEC_CONFORMANT_BY_DESIGN): the command
envelope's ``evidence_lineage`` belongs to the audit envelope (spec 27).
Eligibility is enforced at *consumption points* -- evidence VALID gates,
candidate verification, promotion revalidation, contradiction-resolution
eligibility -- because requiring eligibility at citation time would make
honest curation flows unsubmittable (you could never revoke stale evidence
while citing it, never resolve a contradiction against superseded
evidence, never annotate a failure).  These tests pin that boundary:

1. lineage naming a missing or non-evidence artifact is denied;
2. citing VALID-but-uneligible-ineligible evidence in an audit lineage
   remains legal for curation flows (existence/prefix only);
3. the consumption gates still reject ineligible positive support
   (covered elsewhere; asserted here through the revoke flow).
"""

from __future__ import annotations

import unittest

from agent_org.commands import TransitionArtifactPayload
from agent_org.contracts import CommandType
from agent_org.epistemic import EvidenceState
from tests2b.support import make_command, submit


class D14LineageBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def test_lineage_missing_or_non_evidence_denied(self) -> None:
        env = self.fx.env
        evidence = self.fx.valid_evidence()
        result = submit(
            env,
            make_command(
                env,
                CommandType.TRANSITION_ARTIFACT,
                lambda _cid: TransitionArtifactPayload(
                    artifact_id=evidence.evidence_id,
                    target_state=EvidenceState.REVOKED,
                ),
                task_scope=self.fx.task.task_id,
                expected_state_version=evidence.version,
                evidence_lineage=("evidence.does-not-exist",),
            ),
        )
        self.assertEqual(result.reason, "invalid_evidence_lineage")

    def test_stale_evidence_stays_citable_for_curation(self) -> None:
        """Citing stale/aging evidence in order to revoke it must remain
        submittable: the lineage records what the curator looked at, while
        the REVOKED transition does not consume the evidence as positive
        support."""
        env = self.fx.env
        source = self.fx.source()
        aging = self.fx.evidence(source, expires_in=5)
        review = self.fx.evidence(source)
        verified, _record = self.fx.verify(
            aging, self.fx.producer.principal_id, (review.evidence_id,)
        )
        self.assertTrue(verified.accepted, verified)
        env.clock.advance(3)
        result = submit(
            env,
            make_command(
                env,
                CommandType.TRANSITION_ARTIFACT,
                lambda _cid: TransitionArtifactPayload(
                    artifact_id=aging.evidence_id,
                    target_state=EvidenceState.REVOKED,
                ),
                task_scope=self.fx.task.task_id,
                expected_state_version=aging.version + 1,
                evidence_lineage=(aging.evidence_id,),
            ),
        )
        self.assertTrue(result.accepted, result)
        live = env.plane.projections.artifact(aging.evidence_id)
        self.assertIs(live.lifecycle_state, EvidenceState.REVOKED)
        self.assertTrue(env.plane.projections.verify_audit())


if __name__ == "__main__":
    unittest.main()
