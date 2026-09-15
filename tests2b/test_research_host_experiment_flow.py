"""Runtime coverage for the research host's experiment-chain constructor sites.

Motivation (defect + RCA recorded in the Slice 2B remediation register):
adding ``Observation.producer_principal_id`` (D-09) left the host's
``record_observation`` factory structurally broken — the required field was
missing — while every test stayed green because NO test exercised that
production constructor.  These tests exercise the host facade end-to-end:

- ``test_record_observation_succeeds_and_resolves_producer`` — committed
  observation carries the host's research principal as producer, is visible
  in projections, and its producer is the registered research principal
  (precondition for later INDEPENDENT verification by the operator per D-09).
- ``test_record_observation_unknown_run_denied`` — the TCB still rejects an
  observation targeting a nonexistent run (runtime, not just contract), and
  the denial leaves no residue.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_org.epistemic import Observation
from agent_org.research_host.contracts import RESEARCH_PRINCIPAL_ID
from agent_org.research_host.host import build_research_agent_host
from tests2b.support import new_env


class ResearchHostExperimentFlowTests(unittest.TestCase):
    @staticmethod
    def _experiment_chain(api) -> str:
        hypothesis = api.create_hypothesis(
            statement="host runtime path is covered",
            falsification_criteria=("a failing reconstruction of this test",),
        )
        assert hypothesis.accepted, hypothesis.reason
        plan = api.propose_experiment(
            hypothesis_id=hypothesis.artifact_id,
            method="smoke",
            preconditions=("local workspace",),
            expected_observations=("observation commits with producer",),
        )
        assert plan.accepted, plan.reason
        run = api.record_experiment_result(
            experiment_plan_id=plan.artifact_id, outcome="pass"
        )
        assert run.accepted, run.reason
        return run.artifact_id

    def _new_host(self) -> tuple:
        # The host bootstrap is legitimate operator bootstrapping (mirrors
        # production wiring): it registers the research principal and binds
        # the bootstrap task through the audited operator session.
        env = new_env()
        workspace = Path(tempfile.mkdtemp(prefix="ahos-host-rt-"))
        host = build_research_agent_host(
            plane=env.plane,
            session=env.session,
            clock=env.clock.now,
            ids=env.ids.new,
            workspace_root=workspace,
        )
        return env, host

    def test_record_observation_succeeds_and_resolves_producer(self) -> None:
        env, host = self._new_host()
        api = host.facade()
        run_id = self._experiment_chain(api)

        result = api.record_observation(
            experiment_run_id=run_id,
            measured_value="host-runtime",
            observation_method="construction-coverage",
        )
        self.assertTrue(result.accepted, result.reason)

        item = env.plane.projections.artifact(result.artifact_id)
        self.assertIsInstance(item, Observation)
        self.assertEqual(item.producer_principal_id, RESEARCH_PRINCIPAL_ID)
        # The producer must be a live registered principal so the operator
        # (never the in-slice producer) can later INDEPENDENTLY verify it.
        principals = {
            p.principal_id: p for p in env.plane.projections.principals()
        }
        self.assertIn(RESEARCH_PRINCIPAL_ID, principals)

    def test_record_observation_unknown_run_denied(self) -> None:
        env, host = self._new_host()
        result = host.facade().record_observation(
            experiment_run_id="experiment-run.does-not-exist",
            measured_value="x",
            observation_method="y",
        )
        self.assertFalse(result.accepted)
        # And the denial must leave no residue in the governed store.
        observations = [
            a
            for a in env.plane.projections.epistemic_objects()
            if isinstance(a, Observation)
        ]
        self.assertEqual(observations, [])


if __name__ == "__main__":
    unittest.main()
