"""D-06 remediation: verification must not cite its target as its own support.

Before this closure a PASS verification could name the target evidence inside
its own ``evidence_ids`` -- a circular proof ("E is trustworthy because E says
so").  The closure is layered, mirroring the D-01 promotion policy pattern:

1. contract layer  -- ``VerificationRecord`` refuses construction;
2. TCB layer       -- even a record mutated around the contract (same-process
                      ``object.__setattr__`` residual, D-12) is denied with
                      ``verification_cannot_cite_target_itself`` before any
                      state change.

Non-self citations (a claim/candidate verification citing its underlying
evidence, an evidence verification citing a distinct review artifact) remain
legal.
"""

from __future__ import annotations

import unittest

from agent_org.commands import CreateVerificationPayload
from agent_org.contracts import CommandType
from agent_org.epistemic import (
    EvidenceState,
    VerificationKind,
    VerificationRecord,
    VerificationStatus,
)


class D06VerificationSelfCitationTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def test_contract_rejects_citing_target_at_construction(self) -> None:
        from tests2b.support import provenance

        with self.assertRaises(ValueError):
            VerificationRecord(
                verification_id="verification.circular",
                target_artifact_id="evidence.target",
                producer_principal_id="principal.some-producer",
                verifier_principal_id="principal.some-verifier",
                verification_kind=VerificationKind.INDEPENDENT,
                status=VerificationStatus.PASS,
                evidence_ids=("evidence.target",),
                method="circular",
                provenance=provenance(self.fx.env, "command.circular"),
                lifecycle_state=VerificationStatus.PASS,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )

    def test_target_self_citation_denied_even_under_constructor_bypass(self) -> None:
        """Same-process reflection must not reopen the circular-proof path."""
        from tests2b.support import make_command, provenance, submit

        env = self.fx.env
        source = self.fx.source()
        evidence = self.fx.evidence(source)
        review_base = self.fx.evidence(source)

        def circular_payload(cid: str) -> CreateVerificationPayload:
            record = VerificationRecord(
                verification_id=env.ids.new("verification"),
                target_artifact_id=evidence.evidence_id,
                producer_principal_id=self.fx.producer.principal_id,
                verifier_principal_id=env.plane.operator.principal_id,
                verification_kind=VerificationKind.INDEPENDENT,
                status=VerificationStatus.PASS,
                evidence_ids=(evidence.evidence_id,),
                method="circular-self-citation",
                provenance=provenance(env, cid),
                lifecycle_state=VerificationStatus.PASS,
                created_at=env.clock.now(),
                updated_at=env.clock.now(),
            )
            return CreateVerificationPayload(record)

        # Construction alone is a contract failure; bypass it the way a
        # same-process attacker with import access would (D-12 residual).
        with self.assertRaises(ValueError):
            circular_payload(env.ids.new("command"))

        def forged_payload(cid: str) -> CreateVerificationPayload:
            record = VerificationRecord(
                verification_id=env.ids.new("verification"),
                target_artifact_id=evidence.evidence_id,
                producer_principal_id=self.fx.producer.principal_id,
                verifier_principal_id=env.plane.operator.principal_id,
                verification_kind=VerificationKind.INDEPENDENT,
                status=VerificationStatus.PASS,
                evidence_ids=(review_base.evidence_id,),
                method="circular-self-citation",
                provenance=provenance(env, cid),
                lifecycle_state=VerificationStatus.PASS,
                created_at=env.clock.now(),
                updated_at=env.clock.now(),
            )
            object.__setattr__(record, "evidence_ids", (evidence.evidence_id,))
            return CreateVerificationPayload(record)

        result = submit(
            env,
            make_command(
                env,
                CommandType.CREATE_VERIFICATION,
                forged_payload,
                task_scope=self.fx.task.task_id,
                expected_state_version=evidence.version,
            ),
        )
        self.assertFalse(result.accepted, result)
        self.assertEqual(result.reason, "verification_cannot_cite_target_itself")
        live = env.plane.projections.artifact(evidence.evidence_id)
        self.assertIs(live.verification_status, VerificationStatus.UNVERIFIED)
        self.assertTrue(env.plane.projections.verify_audit())

    def test_self_citation_cannot_bootstrap_validity(self) -> None:
        """After the circular verification is refused, VALID stays locked."""
        env = self.fx.env
        source = self.fx.source()
        evidence = self.fx.evidence(source)
        block = self.fx.transition(evidence, EvidenceState.VALID)
        self.assertEqual(block.reason, "evidence_requires_independent_verification")
        live = env.plane.projections.artifact(evidence.evidence_id)
        self.assertIs(live.lifecycle_state, EvidenceState.REGISTERED)
        self.assertIs(live.verification_status, VerificationStatus.UNVERIFIED)

    def test_distinct_review_artifact_citation_accepted(self) -> None:
        env = self.fx.env
        source = self.fx.source()
        evidence = self.fx.evidence(source)
        review_base = self.fx.evidence(source)
        result, record = self.fx.verify(
            evidence,
            self.fx.producer.principal_id,
            (review_base.evidence_id,),
        )
        self.assertTrue(result.accepted, result)
        self.assertEqual(record.evidence_ids, (review_base.evidence_id,))
        live = env.plane.projections.artifact(evidence.evidence_id)
        self.assertIs(live.verification_status, VerificationStatus.PASS)
        promoted = self.fx.transition(live, EvidenceState.VALID)
        self.assertTrue(promoted.accepted, promoted)

    def test_claim_verification_citing_underlying_evidence_still_legal(self) -> None:
        """A verification of a claim cites the *underlying* evidence:
        cited id (`evidence.*`) can never equal the target id (`claim.*`),
        so the D-06 gate must remain silent here."""
        from tests2b.support import make_command, provenance, submit

        env = self.fx.env
        evidence = self.fx.valid_evidence()
        claim = self.fx.claim(evidence)

        def payload(cid: str) -> CreateVerificationPayload:
            return CreateVerificationPayload(
                VerificationRecord(
                    verification_id=env.ids.new("verification"),
                    target_artifact_id=claim.claim_id,
                    producer_principal_id=self.fx.producer.principal_id,
                    verifier_principal_id=env.plane.operator.principal_id,
                    verification_kind=VerificationKind.INDEPENDENT,
                    status=VerificationStatus.PASS,
                    evidence_ids=(evidence.evidence_id,),
                    method="independent-claim-review",
                    provenance=provenance(env, cid),
                    lifecycle_state=VerificationStatus.PASS,
                    created_at=env.clock.now(),
                    updated_at=env.clock.now(),
                )
            )

        result = submit(
            env,
            make_command(
                env,
                CommandType.CREATE_VERIFICATION,
                payload,
                task_scope=self.fx.task.task_id,
                expected_state_version=claim.version,
            ),
        )
        self.assertTrue(result.accepted, result)


if __name__ == "__main__":
    unittest.main()
