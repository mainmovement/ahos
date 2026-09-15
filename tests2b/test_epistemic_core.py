from __future__ import annotations

import unittest
from datetime import timedelta

from agent_org.commands import (
    CreateApprovalPayload,
    CreateContradictionPayload,
    CreateVerificationPayload,
    PromoteKnowledgePayload,
    RegisterArtifactPayload,
    RevokeApprovalPayload,
    TransitionArtifactPayload,
)
from agent_org.contracts import Capability, CommandType, Operation, Resource
from agent_org.epistemic import (
    Approval,
    ApprovalState,
    Claim,
    ClaimState,
    ContradictionCase,
    ContradictionState,
    Evidence,
    EvidenceState,
    ExperimentPlan,
    ExperimentRun,
    ExperimentState,
    Hypothesis,
    HypothesisState,
    KnowledgeCandidate,
    KnowledgeState,
    MemoryKind,
    MemoryRecord,
    MemoryState,
    Observation,
    ObservationState,
    Prediction,
    PredictionState,
    ResearchMission,
    ResearchMissionState,
    Source,
    SourceState,
    VerificationKind,
    VerificationRecord,
    VerificationStatus,
)
from tests2b.support import (
    grant_task_commands,
    make_command,
    new_env,
    provenance,
    ready_task,
    register_agent,
    submit,
)


class EpistemicCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = new_env()
        self.producer = register_agent(self.env, "principal.agent-producer")
        self.task = ready_task(self.env)
        grant_task_commands(
            self.env,
            self.task.task_id,
            (
                CommandType.REGISTER_ARTIFACT,
                CommandType.TRANSITION_ARTIFACT,
                CommandType.CREATE_CONTRADICTION,
                CommandType.CREATE_VERIFICATION,
                CommandType.CREATE_APPROVAL,
                CommandType.REVOKE_APPROVAL,
                CommandType.PROMOTE_KNOWLEDGE,
            ),
        )

    def register(self, factory):
        holder = {}

        def payload(command_id):
            item = factory(command_id)
            holder["item"] = item
            return RegisterArtifactPayload(item)

        command = make_command(
            self.env,
            CommandType.REGISTER_ARTIFACT,
            payload,
            task_scope=self.task.task_id,
        )
        result = submit(self.env, command)
        return result, holder.get("item")

    def source(self) -> Source:
        result, item = self.register(
            lambda cid: Source(
                source_id=self.env.ids.new("source"),
                source_type="LOCAL_SYNTHETIC",
                locator="fixture://source",
                content_hash="a" * 64,
                provenance=provenance(self.env, cid),
                lifecycle_state=SourceState.REGISTERED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        return item

    def evidence(self, source: Source, *, expires_in: int = 600) -> Evidence:
        result, item = self.register(
            lambda cid: Evidence(
                evidence_id=self.env.ids.new("evidence"),
                source_id=source.source_id,
                producer_principal_id=self.producer.principal_id,
                retrieval_timestamp=self.env.clock.now(),
                observation_timestamp=self.env.clock.now(),
                content_hash="b" * 64,
                content_ref="fixture://evidence",
                extraction_method="deterministic-fixture",
                validity_status=EvidenceState.REGISTERED,
                freshness_max_age_seconds=expires_in,
                expires_at=self.env.clock.now() + timedelta(seconds=expires_in),
                assurance=80,
                provenance=provenance(self.env, cid),
                lifecycle_state=EvidenceState.REGISTERED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        return item

    def verify(self, target, producer_id: str, evidence_ids: tuple[str, ...], *, kind=VerificationKind.INDEPENDENT):
        from agent_org.epistemic import artifact_id

        holder = {}

        def payload(cid):
            record = VerificationRecord(
                verification_id=self.env.ids.new("verification"),
                target_artifact_id=artifact_id(target),
                producer_principal_id=producer_id,
                verifier_principal_id=self.env.plane.operator.principal_id,
                verification_kind=kind,
                status=VerificationStatus.PASS,
                evidence_ids=evidence_ids,
                method="independent-fixture-review",
                provenance=provenance(self.env, cid),
                lifecycle_state=VerificationStatus.PASS,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
            holder["record"] = record
            return CreateVerificationPayload(record)

        command = make_command(
            self.env,
            CommandType.CREATE_VERIFICATION,
            payload,
            task_scope=self.task.task_id,
            expected_state_version=target.version,
            evidence_lineage=evidence_ids,
        )
        return submit(self.env, command), holder["record"]

    def transition(self, item, target_state):
        command = make_command(
            self.env,
            CommandType.TRANSITION_ARTIFACT,
            lambda _cid: TransitionArtifactPayload(
                artifact_id=(
                    item.evidence_id
                    if isinstance(item, Evidence)
                    else item.claim_id
                    if isinstance(item, Claim)
                    else item.hypothesis_id
                    if isinstance(item, Hypothesis)
                    else item.prediction_id
                    if isinstance(item, Prediction)
                    else item.observation_id
                    if isinstance(item, Observation)
                    else item.candidate_id
                    if isinstance(item, KnowledgeCandidate)
                    else item.contradiction_id
                    if isinstance(item, ContradictionCase)
                    else item.mission_id
                    if isinstance(item, ResearchMission)
                    else item.experiment_run_id
                    if isinstance(item, ExperimentRun)
                    else item.memory_id
                ),
                target_state=target_state,
            ),
            task_scope=self.task.task_id,
            expected_state_version=item.version,
        )
        return submit(self.env, command)

    def valid_evidence(self) -> Evidence:
        source = self.source()
        evidence = self.evidence(source)
        review_base = self.evidence(source)
        result, _record = self.verify(
            evidence, self.producer.principal_id, (review_base.evidence_id,)
        )
        self.assertTrue(result.accepted, result)
        updated = self.env.plane.projections.artifact(evidence.evidence_id)
        result = self.transition(updated, EvidenceState.VALID)
        self.assertTrue(result.accepted, result)
        return self.env.plane.projections.artifact(evidence.evidence_id)

    def claim(self, evidence: Evidence) -> Claim:
        result, item = self.register(
            lambda cid: Claim(
                claim_id=self.env.ids.new("claim"),
                statement="Synthetic claim, not a fact",
                evidence_ids=(evidence.evidence_id,),
                producer_principal_id=self.producer.principal_id,
                provenance=provenance(self.env, cid),
                lifecycle_state=ClaimState.DRAFT,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        return item

    def candidate(self, claim: Claim, evidence: Evidence, *, producer_id=None):
        result, item = self.register(
            lambda cid: KnowledgeCandidate(
                candidate_id=self.env.ids.new("candidate"),
                proposition="Candidate knowledge, not truth",
                producer_principal_id=producer_id or self.producer.principal_id,
                claim_ids=(claim.claim_id,),
                evidence_ids=(evidence.evidence_id,),
                verification_ids=(),
                contradiction_ids=(),
                provenance=provenance(self.env, cid),
                lifecycle_state=KnowledgeState.SUBMITTED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        return item

    def test_fake_evidence_id_fails_registration(self) -> None:
        result, _ = self.register(
            lambda cid: Claim(
                claim_id=self.env.ids.new("claim"),
                statement="fabricated support",
                evidence_ids=("evidence.does-not-exist",),
                producer_principal_id=self.producer.principal_id,
                provenance=provenance(self.env, cid),
                lifecycle_state=ClaimState.DRAFT,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "invalid_epistemic_reference")

    def test_artifact_producer_must_resolve_to_active_principal(self) -> None:
        evidence = self.valid_evidence()
        result, _ = self.register(
            lambda cid: Claim(
                claim_id=self.env.ids.new("claim"),
                statement="identity-confused claim",
                evidence_ids=(evidence.evidence_id,),
                producer_principal_id="principal.unregistered-producer",
                provenance=provenance(self.env, cid),
                lifecycle_state=ClaimState.DRAFT,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertEqual(result.reason, "unknown_or_inactive_artifact_principal")

    def test_evidence_cannot_self_declare_verified_or_valid(self) -> None:
        source = self.source()
        result, _ = self.register(
            lambda cid: Evidence(
                evidence_id=self.env.ids.new("evidence"),
                source_id=source.source_id,
                producer_principal_id=self.producer.principal_id,
                retrieval_timestamp=self.env.clock.now(),
                observation_timestamp=self.env.clock.now(),
                content_hash="c" * 64,
                content_ref="fixture://forged",
                extraction_method="claim-only",
                validity_status=EvidenceState.VALID,
                freshness_max_age_seconds=60,
                expires_at=self.env.clock.now() + timedelta(seconds=60),
                assurance=100,
                provenance=provenance(self.env, cid),
                lifecycle_state=EvidenceState.VALID,
                verification_status=VerificationStatus.PASS,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "artifact_initial_state_invalid")

    def test_stale_evidence_cannot_silently_become_valid(self) -> None:
        source = self.source()
        evidence = self.evidence(source, expires_in=2)
        review_base = self.evidence(source)
        verified, _ = self.verify(
            evidence, self.producer.principal_id, (review_base.evidence_id,)
        )
        self.assertTrue(verified.accepted)
        self.env.clock.advance(3)
        current = self.env.plane.projections.artifact(evidence.evidence_id)
        result = self.transition(current, EvidenceState.VALID)
        self.assertEqual(result.reason, "stale_evidence_cannot_become_valid")

    def test_claim_hypothesis_prediction_observation_are_distinct(self) -> None:
        evidence = self.valid_evidence()
        claim = self.claim(evidence)
        hypothesis_result, hypothesis = self.register(
            lambda cid: Hypothesis(
                hypothesis_id=self.env.ids.new("hypothesis"),
                statement="A falsifiable hypothesis",
                supporting_claim_ids=(claim.claim_id,),
                falsification_criteria=("observation differs",),
                producer_principal_id=self.producer.principal_id,
                provenance=provenance(self.env, cid),
                lifecycle_state=HypothesisState.PROPOSED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(hypothesis_result.accepted)
        prediction_result, prediction = self.register(
            lambda cid: Prediction(
                prediction_id=self.env.ids.new("prediction"),
                hypothesis_id=hypothesis.hypothesis_id,
                expected_observation="synthetic value 1",
                evaluation_deadline=self.env.clock.now() + timedelta(minutes=5),
                provenance=provenance(self.env, cid),
                lifecycle_state=PredictionState.PROPOSED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(prediction_result.accepted)
        self.assertNotEqual(type(claim), type(hypothesis))
        self.assertNotEqual(type(hypothesis), type(prediction))
        self.assertEqual(claim.lifecycle_state, ClaimState.DRAFT)
        self.assertEqual(hypothesis.lifecycle_state, HypothesisState.PROPOSED)
        self.assertEqual(prediction.lifecycle_state, PredictionState.PROPOSED)

    def test_illegal_epistemic_transition_denied(self) -> None:
        claim = self.claim(self.valid_evidence())
        result = self.transition(claim, ClaimState.VERIFIED)
        self.assertFalse(result.accepted)
        self.assertIn("illegal epistemic transition", result.reason)

    def test_claim_cannot_be_verified_without_independent_record(self) -> None:
        claim = self.claim(self.valid_evidence())
        self.assertTrue(self.transition(claim, ClaimState.SUBMITTED).accepted)
        current = self.env.plane.projections.artifact(claim.claim_id)
        self.assertTrue(self.transition(current, ClaimState.CHALLENGED).accepted)
        current = self.env.plane.projections.artifact(claim.claim_id)
        result = self.transition(current, ClaimState.VERIFIED)
        self.assertEqual(result.reason, "missing_independent_verification")

    def _file_challenge(self, candidate, left_artifact_id, right_artifact_id):
        holder = {}

        def payload(cid):
            contradiction = ContradictionCase(
                contradiction_id=self.env.ids.new("contradiction"),
                left_artifact_id=left_artifact_id,
                right_artifact_id=right_artifact_id,
                rationale="Documented challenge to the candidate",
                affects_candidate_ids=(candidate.candidate_id,),
                provenance=provenance(self.env, cid),
                lifecycle_state=ContradictionState.OPEN,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
            holder["item"] = contradiction
            return CreateContradictionPayload(contradiction)

        result = submit(
            self.env,
            make_command(
                self.env,
                CommandType.CREATE_CONTRADICTION,
                payload,
                task_scope=self.task.task_id,
                expected_state_version=candidate.version,
            ),
        )
        self.assertTrue(result.accepted, result)
        return holder["item"]

    def _resolve_challenge(self, contradiction, evidence: Evidence):
        result = submit(
            self.env,
            make_command(
                self.env,
                CommandType.TRANSITION_ARTIFACT,
                lambda _cid: TransitionArtifactPayload(
                    artifact_id=contradiction.contradiction_id,
                    target_state=ContradictionState.RESOLVED,
                    evidence_ids=(evidence.evidence_id,),
                ),
                task_scope=self.task.task_id,
                expected_state_version=contradiction.version,
            ),
        )
        self.assertTrue(result.accepted, result)
        return result

    def test_independent_verification_required_for_candidate(self) -> None:
        evidence = self.valid_evidence()
        left = self.claim(evidence)
        right = self.claim(evidence)
        candidate = self.candidate(left, evidence)
        under_review = self.transition(candidate, KnowledgeState.UNDER_REVIEW)
        self.assertTrue(under_review.accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        self._file_challenge(current, left.claim_id, right.claim_id)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        self.assertTrue(self.transition(current, KnowledgeState.CHALLENGED).accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        result = self.transition(current, KnowledgeState.VERIFIED)
        self.assertEqual(result.reason, "missing_independent_verification")

    def test_candidate_cannot_skip_challenged_stage(self) -> None:
        evidence = self.valid_evidence()
        candidate = self.candidate(self.claim(evidence), evidence)
        self.assertTrue(self.transition(candidate, KnowledgeState.UNDER_REVIEW).accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        result = self.transition(current, KnowledgeState.VERIFIED)
        self.assertIn("illegal epistemic transition", result.reason)

    def test_self_check_does_not_satisfy_promotion_verification(self) -> None:
        evidence = self.valid_evidence()
        left = self.claim(evidence)
        right = self.claim(evidence)
        candidate = self.candidate(
            left,
            evidence,
            producer_id=self.env.plane.operator.principal_id,
        )
        self.assertTrue(self.transition(candidate, KnowledgeState.UNDER_REVIEW).accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        self._file_challenge(current, left.claim_id, right.claim_id)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        self.assertTrue(self.transition(current, KnowledgeState.CHALLENGED).accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        result, _ = self.verify(
            current,
            self.env.plane.operator.principal_id,
            (evidence.evidence_id,),
            kind=VerificationKind.SELF_CHECK,
        )
        self.assertTrue(result.accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        denied = self.transition(current, KnowledgeState.VERIFIED)
        self.assertEqual(denied.reason, "missing_independent_verification")

    def _verified_candidate(self):
        evidence = self.valid_evidence()
        left = self.claim(evidence)
        right = self.claim(evidence)
        candidate = self.candidate(left, evidence)
        self.assertTrue(self.transition(candidate, KnowledgeState.UNDER_REVIEW).accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        challenge = self._file_challenge(current, left.claim_id, right.claim_id)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        self.assertTrue(self.transition(current, KnowledgeState.CHALLENGED).accepted)
        challenge = self.env.plane.projections.artifact(challenge.contradiction_id)
        self._resolve_challenge(challenge, evidence)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        verification, record = self.verify(
            current, self.producer.principal_id, (evidence.evidence_id,)
        )
        self.assertTrue(verification.accepted, verification)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        verified = self.transition(current, KnowledgeState.VERIFIED)
        self.assertTrue(verified.accepted, verified)
        return self.env.plane.projections.artifact(candidate.candidate_id), evidence, record

    def _approval(self, candidate):
        holder = {}

        def payload(cid):
            approval = Approval(
                approval_id=self.env.ids.new("approval"),
                approver_principal_id=self.env.plane.operator.principal_id,
                task_id=self.task.task_id,
                candidate_id=candidate.candidate_id,
                action=Operation.PROMOTE.value,
                resource_id=Resource.EPISTEMIC_STORE,
                capability_id=Capability.KNOWLEDGE_PROMOTE,
                policy_version="slice-2b-v1",
                issued_at=self.env.clock.now(),
                expires_at=self.env.clock.now() + timedelta(minutes=5),
                provenance=provenance(self.env, cid),
                lifecycle_state=ApprovalState.ACTIVE,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
            holder["approval"] = approval
            return CreateApprovalPayload(approval)

        result = submit(
            self.env,
            make_command(
                self.env,
                CommandType.CREATE_APPROVAL,
                payload,
                task_scope=self.task.task_id,
            ),
        )
        self.assertTrue(result.accepted, result)
        return holder["approval"]

    def test_verified_candidate_promotes_with_scoped_active_approval(self) -> None:
        candidate, _evidence, _verification = self._verified_candidate()
        approval = self._approval(candidate)
        command = make_command(
            self.env,
            CommandType.PROMOTE_KNOWLEDGE,
            lambda _cid: PromoteKnowledgePayload(
                candidate.candidate_id, approval.approval_id
            ),
            task_scope=self.task.task_id,
            expected_state_version=candidate.version,
        )
        result = submit(self.env, command)
        self.assertTrue(result.accepted, result)
        promoted = self.env.plane.projections.artifact(candidate.candidate_id)
        self.assertEqual(promoted.lifecycle_state, KnowledgeState.PROMOTED)

    def test_expired_approval_cannot_promote(self) -> None:
        candidate, _evidence, _verification = self._verified_candidate()
        approval = self._approval(candidate)
        self.env.clock.advance(301)
        result = submit(
            self.env,
            make_command(
                self.env,
                CommandType.PROMOTE_KNOWLEDGE,
                lambda _cid: PromoteKnowledgePayload(
                    candidate.candidate_id, approval.approval_id
                ),
                task_scope=self.task.task_id,
                expected_state_version=candidate.version,
            ),
        )
        self.assertEqual(result.reason, "approval_expired")

    def test_revoked_approval_cannot_promote(self) -> None:
        candidate, _evidence, _verification = self._verified_candidate()
        approval = self._approval(candidate)
        revoke = make_command(
            self.env,
            CommandType.REVOKE_APPROVAL,
            lambda _cid: RevokeApprovalPayload(approval.approval_id),
            task_scope=self.task.task_id,
            expected_state_version=approval.version,
        )
        self.assertTrue(submit(self.env, revoke).accepted)
        result = submit(
            self.env,
            make_command(
                self.env,
                CommandType.PROMOTE_KNOWLEDGE,
                lambda _cid: PromoteKnowledgePayload(
                    candidate.candidate_id, approval.approval_id
                ),
                task_scope=self.task.task_id,
                expected_state_version=candidate.version,
            ),
        )
        self.assertEqual(result.reason, "approval_revoked")

    def test_revoked_evidence_cannot_support_positive_promotion(self) -> None:
        candidate, evidence, _verification = self._verified_candidate()
        self.assertTrue(self.transition(evidence, EvidenceState.REVOKED).accepted)
        approval = self._approval(candidate)
        result = submit(
            self.env,
            make_command(
                self.env,
                CommandType.PROMOTE_KNOWLEDGE,
                lambda _cid: PromoteKnowledgePayload(
                    candidate.candidate_id, approval.approval_id
                ),
                task_scope=self.task.task_id,
                expected_state_version=candidate.version,
            ),
        )
        self.assertEqual(result.reason, "evidence_not_eligible_for_promotion")

    def test_open_contradiction_blocks_verification_and_promotion(self) -> None:
        evidence = self.valid_evidence()
        left = self.claim(evidence)
        right = self.claim(evidence)
        candidate = self.candidate(left, evidence)
        self.assertTrue(self.transition(candidate, KnowledgeState.UNDER_REVIEW).accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        filed = self._file_challenge(current, left.claim_id, right.claim_id)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        self.assertTrue(self.transition(current, KnowledgeState.CHALLENGED).accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        verified, _record = self.verify(
            current, self.producer.principal_id, (evidence.evidence_id,)
        )
        self.assertTrue(verified.accepted)
        current = self.env.plane.projections.artifact(candidate.candidate_id)
        denied = self.transition(current, KnowledgeState.VERIFIED)
        self.assertEqual(denied.reason, "unresolved_contradiction")
        self.assertIsNotNone(
            self.env.plane.projections.artifact(filed.contradiction_id)
        )
        no_evidence = self.transition(filed, ContradictionState.RESOLVED)
        self.assertEqual(
            no_evidence.reason, "contradiction_resolution_requires_evidence"
        )

    def test_memory_cannot_silently_become_truth(self) -> None:
        evidence = self.valid_evidence()
        result, memory = self.register(
            lambda cid: MemoryRecord(
                memory_id=self.env.ids.new("memory"),
                memory_kind=MemoryKind.FAILURE,
                subject="synthetic failure",
                content_ref="fixture://failure",
                evidence_ids=(evidence.evidence_id,),
                assurance=50,
                provenance=provenance(self.env, cid),
                lifecycle_state=MemoryState.CANDIDATE,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
                failure_outcome="negative evidence",
            )
        )
        self.assertTrue(result.accepted)
        denied = self.transition(memory, MemoryState.PROMOTED)
        self.assertEqual(denied.reason, "memory_cannot_silently_become_truth")

    def test_research_mission_is_contract_only_and_bounded(self) -> None:
        evidence = self.valid_evidence()
        claim = self.claim(evidence)
        result, hypothesis = self.register(
            lambda cid: Hypothesis(
                hypothesis_id=self.env.ids.new("hypothesis"),
                statement="Research hypothesis",
                supporting_claim_ids=(claim.claim_id,),
                falsification_criteria=("counter observation",),
                producer_principal_id=self.producer.principal_id,
                provenance=provenance(self.env, cid),
                lifecycle_state=HypothesisState.PROPOSED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted)
        result, mission = self.register(
            lambda cid: ResearchMission(
                mission_id=self.env.ids.new("mission"),
                question="What remains unknown?",
                unknowns=("unknown-x",),
                hypothesis_ids=(hypothesis.hypothesis_id,),
                required_evidence=("independent observation",),
                constraints=("offline",),
                allowed_methods=("synthetic inspection",),
                assigned_agent_id=self.producer.principal_id,
                authority_capabilities=(Capability.EPISTEMIC_WRITE,),
                authority_resources=(Resource.EPISTEMIC_STORE,),
                expires_at=self.env.clock.now() + timedelta(hours=1),
                deliverables=("evidence record",),
                verification_required=True,
                success_criteria=("question narrowed",),
                failure_criteria=("no valid evidence",),
                parent_mission_id=None,
                causal_lineage=("cause.synthetic",),
                provenance=provenance(self.env, cid),
                lifecycle_state=ResearchMissionState.PROPOSED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        self.assertEqual(mission.lifecycle_state, ResearchMissionState.PROPOSED)

    def test_experiment_completed_does_not_mean_proven(self) -> None:
        evidence = self.valid_evidence()
        claim = self.claim(evidence)
        _, hypothesis = self.register(
            lambda cid: Hypothesis(
                hypothesis_id=self.env.ids.new("hypothesis"),
                statement="Experiment hypothesis",
                supporting_claim_ids=(claim.claim_id,),
                falsification_criteria=("negative result",),
                producer_principal_id=self.producer.principal_id,
                provenance=provenance(self.env, cid),
                lifecycle_state=HypothesisState.PROPOSED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        plan_result, plan = self.register(
            lambda cid: ExperimentPlan(
                experiment_plan_id=self.env.ids.new("experiment-plan"),
                hypothesis_id=hypothesis.hypothesis_id,
                method="offline synthetic method",
                preconditions=("fixture ready",),
                expected_observations=("value",),
                reproducibility_requirements=("same fixture",),
                provenance=provenance(self.env, cid),
                lifecycle_state=ExperimentState.PLANNED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(plan_result.accepted)
        run_result, run = self.register(
            lambda cid: ExperimentRun(
                experiment_run_id=self.env.ids.new("experiment-run"),
                experiment_plan_id=plan.experiment_plan_id,
                outcome="",
                failure_class=None,
                provenance=provenance(self.env, cid),
                lifecycle_state=ExperimentState.PLANNED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(run_result.accepted)
        self.assertTrue(self.transition(run, ExperimentState.RUNNING).accepted)
        current = self.env.plane.projections.artifact(run.experiment_run_id)
        self.assertTrue(self.transition(current, ExperimentState.COMPLETED).accepted)
        completed = self.env.plane.projections.artifact(run.experiment_run_id)
        self.assertEqual(completed.lifecycle_state, ExperimentState.COMPLETED)
        observation_result, observation = self.register(
            lambda cid: Observation(
                observation_id=self.env.ids.new("observation"),
                experiment_run_id=run.experiment_run_id,
                measured_value="synthetic value",
                observation_method="offline fixture read",
                producer_principal_id=self.producer.principal_id,
                provenance=provenance(self.env, cid),
                lifecycle_state=ObservationState.RECORDED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        self.assertTrue(observation_result.accepted)
        self.assertEqual(observation.lifecycle_state, ObservationState.RECORDED)
        self.assertNotEqual(
            hypothesis.lifecycle_state, HypothesisState.SUPPORTED
        )

    def test_inconclusive_and_failed_experiments_are_first_class(self) -> None:
        evidence = self.valid_evidence()
        claim = self.claim(evidence)
        _, hypothesis = self.register(
            lambda cid: Hypothesis(
                hypothesis_id=self.env.ids.new("hypothesis"),
                statement="Negative-result hypothesis",
                supporting_claim_ids=(claim.claim_id,),
                falsification_criteria=("negative result",),
                producer_principal_id=self.producer.principal_id,
                provenance=provenance(self.env, cid),
                lifecycle_state=HypothesisState.PROPOSED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        _, plan = self.register(
            lambda cid: ExperimentPlan(
                experiment_plan_id=self.env.ids.new("experiment-plan"),
                hypothesis_id=hypothesis.hypothesis_id,
                method="offline",
                preconditions=("fixture",),
                expected_observations=("value",),
                reproducibility_requirements=("same fixture",),
                provenance=provenance(self.env, cid),
                lifecycle_state=ExperimentState.PLANNED,
                created_at=self.env.clock.now(),
                updated_at=self.env.clock.now(),
            )
        )
        for terminal in (ExperimentState.FAILED, ExperimentState.INCONCLUSIVE):
            _, run = self.register(
                lambda cid, terminal=terminal: ExperimentRun(
                    experiment_run_id=self.env.ids.new("experiment-run"),
                    experiment_plan_id=plan.experiment_plan_id,
                    outcome=f"valuable {terminal.value.lower()} result",
                    failure_class="method" if terminal is ExperimentState.FAILED else None,
                    provenance=provenance(self.env, cid),
                    lifecycle_state=ExperimentState.PLANNED,
                    created_at=self.env.clock.now(),
                    updated_at=self.env.clock.now(),
                )
            )
            self.assertTrue(self.transition(run, ExperimentState.RUNNING).accepted)
            current = self.env.plane.projections.artifact(run.experiment_run_id)
            self.assertTrue(self.transition(current, terminal).accepted)
            recorded = self.env.plane.projections.artifact(run.experiment_run_id)
            self.assertEqual(recorded.lifecycle_state, terminal)
