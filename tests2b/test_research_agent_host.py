from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_org.contracts import Capability, Resource
from agent_org.epistemic import KnowledgeCandidate, KnowledgeState
from agent_org.research_host import (
    API_BOUNDARY,
    PROCESS_ISOLATION_PROVIDED,
    SAME_PROCESS_RESIDUAL,
    SAME_PROCESS_RUNTIME,
    OperationClass,
    build_research_agent_host,
)
from agent_org.research_host.contracts import RESEARCH_CONTEXT_KIND, RESEARCH_PRINCIPAL_ID
from tests2b.support import new_env


HASH_A = "a" * 64
HASH_B = "b" * 64


class ResearchAgentHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = new_env()
        self.workspace = Path(tempfile.mkdtemp())
        self.host = build_research_agent_host(
            plane=self.env.plane,
            session=self.env.session,  # type: ignore[arg-type]
            clock=self.env.clock.now,
            ids=self.env.ids.new,
            workspace_root=self.workspace,
        )
        self.api = self.host.facade()
        self.host.expose_supplied_artifact("notes/local.txt", "supplied local evidence")

    def _seed_hypothesis(self):
        source = self.api.record_source(
            source_type="LOCAL_SYNTHETIC",
            locator="research://supplied/notes/local.txt",
            content_hash=HASH_A,
        )
        self.assertTrue(source.accepted, source)
        evidence = self.api.record_evidence(
            source_id=source.artifact_id,
            content_hash=HASH_B,
            content_ref="notes/local.txt",
        )
        self.assertTrue(evidence.accepted, evidence)
        claim = self.api.create_claim(
            statement="Local synthetic claim, not a fact",
            evidence_ids=(evidence.artifact_id,),
        )
        self.assertTrue(claim.accepted, claim)
        hypothesis = self.api.create_hypothesis(
            statement="Host-mediated hypothesis",
            falsification_criteria=("counter observation",),
            supporting_claim_ids=(claim.artifact_id,),
        )
        self.assertTrue(hypothesis.accepted, hypothesis)
        return source, evidence, claim, hypothesis

    def test_read_context_is_not_human_identity_or_session(self) -> None:
        result = self.api.read_context()
        self.assertTrue(result.accepted)
        self.assertEqual(result.classification, OperationClass.READ)
        payload = result.payload
        context = payload["research_agent_context"]
        self.assertEqual(context.kind, RESEARCH_CONTEXT_KIND)
        self.assertFalse(context.issues_sessions)
        self.assertFalse(context.production_authority)
        self.assertNotEqual(context.principal_id, self.env.plane.operator.principal_id)
        self.assertEqual(context.principal_id, RESEARCH_PRINCIPAL_ID)
        runtime = payload["runtime"]
        self.assertEqual(runtime.api_boundary, API_BOUNDARY)
        self.assertFalse(runtime.process_isolation)
        self.assertEqual(runtime.same_process_runtime, SAME_PROCESS_RUNTIME)
        self.assertTrue(runtime.same_process_residual)
        self.assertFalse(runtime.agent_one_implemented)
        self.assertIn("notes/local.txt", payload["workspace_artifacts"])

    def test_research_write_path_and_review_without_promotion(self) -> None:
        _source, evidence, claim, hypothesis = self._seed_hypothesis()
        mission = self.api.create_mission(
            question="What remains unknown in the sandbox?",
            unknowns=("unknown-x",),
            hypothesis_ids=(hypothesis.artifact_id,),
            required_evidence=("local observation",),
            constraints=("offline", "no network"),
            allowed_methods=("inspection of supplied artifacts",),
            deliverables=("claim record",),
            success_criteria=("question narrowed",),
            failure_criteria=("no local evidence",),
        )
        self.assertTrue(mission.accepted, mission)
        research_caps = self.env.plane.projections.capability_status(RESEARCH_PRINCIPAL_ID)
        self.assertEqual(research_caps.grants, ())
        self.assertEqual(research_caps.delegations, ())
        candidate = self.api.create_candidate(
            proposition="Candidate knowledge, not truth",
            claim_ids=(claim.artifact_id,),
            evidence_ids=(evidence.artifact_id,),
        )
        self.assertTrue(candidate.accepted, candidate)
        review = self.api.request_review(candidate_id=candidate.artifact_id)
        self.assertTrue(review.accepted, review)
        stored = self.env.plane.projections.artifact(candidate.artifact_id)
        assert isinstance(stored, KnowledgeCandidate)
        self.assertEqual(stored.lifecycle_state, KnowledgeState.UNDER_REVIEW)
        self.assertNotEqual(stored.lifecycle_state, KnowledgeState.PROMOTED)
        contradiction = self.api.record_contradiction(
            left_artifact_id=claim.artifact_id,
            right_artifact_id=evidence.artifact_id,
            rationale="Challenge, not promotion",
            candidate_id=candidate.artifact_id,
        )
        self.assertTrue(contradiction.accepted, contradiction)
        prediction = self.api.create_prediction(
            hypothesis_id=hypothesis.artifact_id,
            expected_observation="sandbox remains offline",
        )
        self.assertTrue(prediction.accepted, prediction)
        plan = self.api.propose_experiment(
            hypothesis_id=hypothesis.artifact_id,
            method="read supplied artifact",
            preconditions=("workspace file exists",),
            expected_observations=("file contents readable",),
        )
        self.assertTrue(plan.accepted, plan)
        run = self.api.record_experiment_result(
            experiment_plan_id=plan.artifact_id,
            outcome="observed local text; not proven globally",
        )
        self.assertTrue(run.accepted, run)
        observation = self.api.record_observation(
            experiment_run_id=run.artifact_id,
            measured_value="supplied local evidence",
            observation_method="workspace read",
        )
        self.assertTrue(observation.accepted, observation)
        state = self.api.read_epistemic_state()
        self.assertTrue(state.accepted)
        self.assertFalse(state.payload["mutable"])
        self.assertFalse(state.payload["authoritative"])
        self.assertTrue(self.host.audit_records())
        self.assertTrue(
            any(
                record.research_agent_context.startswith("research-context.")
                and record.operation == "request_review"
                for record in self.host.audit_records()
            )
        )

    def test_workspace_read_and_string_invoke_rejected(self) -> None:
        result = self.api.read_supplied_artifact("notes/local.txt")
        self.assertTrue(result.accepted, result)
        self.assertEqual(result.payload, "supplied local evidence")
        observed = self.host.invoke(lambda api: api.read_supplied_artifact("notes/local.txt"))
        self.assertTrue(observed.accepted)
        with self.assertRaises(TypeError):
            self.host.invoke("eval('1')")  # type: ignore[arg-type]
        runtime = self.host.runtime_classification()
        self.assertEqual(runtime.same_process_runtime, SAME_PROCESS_RUNTIME)
        self.assertFalse(PROCESS_ISOLATION_PROVIDED)
        self.assertTrue(SAME_PROCESS_RESIDUAL)

    def test_mission_protected_resource_is_not_capability(self) -> None:
        _source, _evidence, _claim, hypothesis = self._seed_hypothesis()
        denied = self.api.create_mission(
            question="Investigate live systems?",
            unknowns=("live state",),
            hypothesis_ids=(hypothesis.artifact_id,),
            required_evidence=("none authorized",),
            constraints=("must remain research",),
            allowed_methods=("none",),
            authority_capabilities=(Capability.EPISTEMIC_WRITE,),
            authority_resources=(Resource.AHOS_LIVE_TRADING,),
            deliverables=("none",),
            success_criteria=("denied",),
            failure_criteria=("granted",),
        )
        self.assertFalse(denied.accepted)
        self.assertEqual(denied.reason, "protected_resource_declaration_denied")
        promote_intent = self.api.create_mission(
            question="Self-promote?",
            unknowns=("authority",),
            hypothesis_ids=(hypothesis.artifact_id,),
            required_evidence=("none",),
            constraints=("none",),
            allowed_methods=("none",),
            authority_capabilities=(Capability.KNOWLEDGE_PROMOTE,),
            authority_resources=(Resource.EPISTEMIC_STORE,),
            deliverables=("none",),
            success_criteria=("denied",),
            failure_criteria=("granted",),
        )
        self.assertFalse(promote_intent.accepted)
        self.assertEqual(
            promote_intent.reason, "research_mission_forbidden_capability_intent"
        )
