"""D-09 remediation: SUPPORTED / CONFIRMED require observation-grounding.

Before this closure, Hypothesis ``TESTING -> SUPPORTED`` and Prediction
``PROPOSED -> CONFIRMED`` were bare enum flips with no requirement that any
observation ever measured anything.  The closure required an identity-model
repair first: Observation now carries an explicit ``producer_principal_id``
(the Evidence pattern), because with producer resolved from registrar
provenance the single-session plane could never construct an INDEPENDENT
verification for an observation -- the existing VERIFIED gate was
unreachable.  With that repaired:

- Observation VERIFIED requires INDEPENDENT PASS (pre-existing gate, now
  reachable);
- Hypothesis SUPPORTED and Prediction CONFIRMED require at least one
  VERIFIED observation from a non-invalidated run->plan chain bound to the
  hypothesis.

Residual asymmetries recorded in the register: ExperimentPlan has no
transition map entry at all (runs can be INVALIDATED; plans cannot), and
REFUTED / INCONCLUSIVE terminals keep their current semantics pending a
council decision on symmetric evidence requirements.
"""

from __future__ import annotations

import unittest
from datetime import timedelta

from agent_org.epistemic import (
    ExperimentPlan,
    ExperimentRun,
    ExperimentState,
    Hypothesis,
    HypothesisState,
    Observation,
    ObservationState,
    Prediction,
    PredictionState,
)
from tests2b.support import provenance


class D09ObservationGateTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _hypothesis(self, statement="hypothesis under D-09"):
        evidence = self.fx.valid_evidence()
        claim = self.fx.claim(evidence)
        result, hypothesis = self.fx.register(
            lambda cid: Hypothesis(
                hypothesis_id=self.fx.env.ids.new("hypothesis"),
                statement=statement,
                supporting_claim_ids=(claim.claim_id,),
                falsification_criteria=("counter observation",),
                producer_principal_id=self.fx.producer.principal_id,
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=HypothesisState.PROPOSED,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        return hypothesis, evidence

    def _experiment_chain(self, hypothesis, *, complete=True):
        result, plan = self.fx.register(
            lambda cid: ExperimentPlan(
                experiment_plan_id=self.fx.env.ids.new("experiment-plan"),
                hypothesis_id=hypothesis.hypothesis_id,
                method="offline synthetic method",
                preconditions=("fixture",),
                expected_observations=("value",),
                reproducibility_requirements=("same fixture",),
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=ExperimentState.PLANNED,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        result, run = self.fx.register(
            lambda cid: ExperimentRun(
                experiment_run_id=self.fx.env.ids.new("experiment-run"),
                experiment_plan_id=plan.experiment_plan_id,
                outcome="",
                failure_class=None,
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=ExperimentState.PLANNED,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        self.assertTrue(self.fx.transition(run, ExperimentState.RUNNING).accepted)
        current = self.fx.env.plane.projections.artifact(run.experiment_run_id)
        if complete:
            self.assertTrue(
                self.fx.transition(current, ExperimentState.COMPLETED).accepted
            )
            run = self.fx.env.plane.projections.artifact(run.experiment_run_id)
        return plan, run

    def _observation(self, run):
        result, observation = self.fx.register(
            lambda cid: Observation(
                observation_id=self.fx.env.ids.new("observation"),
                experiment_run_id=run.experiment_run_id,
                measured_value="synthetic measurement",
                observation_method="offline fixture read",
                producer_principal_id=self.fx.producer.principal_id,
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=ObservationState.RECORDED,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        return observation

    def _verified_observation(self, run, evidence):
        observation = self._observation(run)
        verified, _record = self.fx.verify(
            observation,
            self.fx.producer.principal_id,
            (evidence.evidence_id,),
        )
        self.assertTrue(verified.accepted, verified)
        live = self.fx.env.plane.projections.artifact(observation.observation_id)
        promoted = self.fx.transition(live, ObservationState.VERIFIED)
        self.assertTrue(promoted.accepted, promoted)
        return self.fx.env.plane.projections.artifact(observation.observation_id)

    def test_hypothesis_supported_requires_any_observation(self) -> None:
        hypothesis, _evidence = self._hypothesis()
        self.assertTrue(self.fx.transition(hypothesis, HypothesisState.TESTING).accepted)
        current = self.fx.env.plane.projections.artifact(hypothesis.hypothesis_id)
        denied = self.fx.transition(current, HypothesisState.SUPPORTED)
        self.assertEqual(
            denied.reason, "hypothesis_supported_requires_verified_observation"
        )

    def test_unverified_observation_does_not_support(self) -> None:
        hypothesis, evidence = self._hypothesis()
        _plan, run = self._experiment_chain(hypothesis)
        self._observation(run)
        self.assertTrue(self.fx.transition(hypothesis, HypothesisState.TESTING).accepted)
        current = self.fx.env.plane.projections.artifact(hypothesis.hypothesis_id)
        denied = self.fx.transition(current, HypothesisState.SUPPORTED)
        self.assertEqual(
            denied.reason, "hypothesis_supported_requires_verified_observation"
        )

    def test_observation_of_other_hypothesis_does_not_support(self) -> None:
        hypothesis, _evidence = self._hypothesis("target hypothesis")
        other, other_evidence = self._hypothesis("other hypothesis")
        _plan, run = self._experiment_chain(other)
        self._verified_observation(run, other_evidence)
        self.assertTrue(self.fx.transition(hypothesis, HypothesisState.TESTING).accepted)
        current = self.fx.env.plane.projections.artifact(hypothesis.hypothesis_id)
        denied = self.fx.transition(current, HypothesisState.SUPPORTED)
        self.assertEqual(
            denied.reason, "hypothesis_supported_requires_verified_observation"
        )

    def test_invalidated_run_observation_does_not_support(self) -> None:
        hypothesis, evidence = self._hypothesis()
        plan, run = self._experiment_chain(hypothesis)
        observation = self._verified_observation(run, evidence)
        current_run = self.fx.env.plane.projections.artifact(run.experiment_run_id)
        invalidated = self.fx.transition(current_run, ExperimentState.INVALIDATED)
        self.assertTrue(invalidated.accepted, invalidated)
        self.assertTrue(self.fx.transition(hypothesis, HypothesisState.TESTING).accepted)
        current = self.fx.env.plane.projections.artifact(hypothesis.hypothesis_id)
        denied = self.fx.transition(current, HypothesisState.SUPPORTED)
        self.assertEqual(
            denied.reason, "hypothesis_supported_requires_verified_observation"
        )

    def test_full_chain_supports_hypothesis(self) -> None:
        hypothesis, evidence = self._hypothesis()
        _plan, run = self._experiment_chain(hypothesis)
        self._verified_observation(run, evidence)
        self.assertTrue(self.fx.transition(hypothesis, HypothesisState.TESTING).accepted)
        current = self.fx.env.plane.projections.artifact(hypothesis.hypothesis_id)
        result = self.fx.transition(current, HypothesisState.SUPPORTED)
        self.assertTrue(result.accepted, result)
        live = self.fx.env.plane.projections.artifact(hypothesis.hypothesis_id)
        self.assertIs(live.lifecycle_state, HypothesisState.SUPPORTED)
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_prediction_confirmed_requires_verified_observation(self) -> None:
        hypothesis, evidence = self._hypothesis()
        result, prediction = self.fx.register(
            lambda cid: Prediction(
                prediction_id=self.fx.env.ids.new("prediction"),
                hypothesis_id=hypothesis.hypothesis_id,
                expected_observation="synthetic measurement",
                evaluation_deadline=self.fx.env.clock.now() + timedelta(minutes=10),
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=PredictionState.PROPOSED,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        denied = self.fx.transition(prediction, PredictionState.CONFIRMED)
        self.assertEqual(
            denied.reason, "prediction_confirmed_requires_verified_observation"
        )
        _plan, run = self._experiment_chain(hypothesis)
        self._verified_observation(run, evidence)
        result = self.fx.transition(prediction, PredictionState.CONFIRMED)
        self.assertTrue(result.accepted, result)


if __name__ == "__main__":
    unittest.main()
