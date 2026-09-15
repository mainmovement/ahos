"""D-10 remediation: ResearchMission contracts cannot carry impossible scope.

``authority_resources`` / ``authority_capabilities`` inside a mission were
accepted verbatim while nothing in the grant pipeline could ever confer
protected resources or forbidden capabilities.  A poisoned contract is a
reviewer/UI lie even when execution itself stays blocked.  Registration now
denies both, in the same vocabulary as task creation.
"""

from __future__ import annotations

import unittest
from datetime import timedelta

from agent_org.commands import RegisterArtifactPayload
from agent_org.contracts import (
    Capability,
    CommandType,
    Resource,
)
from agent_org.epistemic import (
    Hypothesis,
    HypothesisState,
    ResearchMission,
    ResearchMissionState,
)
from tests2b.support import make_command, provenance, submit


class D10MissionScopeGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _hypothesis(self):
        evidence = self.fx.valid_evidence()
        claim = self.fx.claim(evidence)
        result, hypothesis = self.fx.register(
            lambda cid: Hypothesis(
                hypothesis_id=self.fx.env.ids.new("hypothesis"),
                statement="hypothesis under test",
                supporting_claim_ids=(claim.claim_id,),
                falsification_criteria=("counter-evidence",),
                producer_principal_id=self.fx.producer.principal_id,
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=HypothesisState.PROPOSED,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )
        )
        self.assertTrue(result.accepted, result)
        return hypothesis

    def _mission_kwargs(self, cid, hypothesis_id, *, resources, capabilities):
        now = self.fx.env.clock.now()
        return {
            "mission_id": self.fx.env.ids.new("mission"),
            "question": "bounded question",
            "unknowns": ("u1",),
            "hypothesis_ids": (hypothesis_id,),
            "required_evidence": ("independent observation",),
            "constraints": ("offline",),
            "allowed_methods": ("synthetic",),
            "assigned_agent_id": self.fx.producer.principal_id,
            "authority_capabilities": capabilities,
            "authority_resources": resources,
            "expires_at": now + timedelta(hours=1),
            "deliverables": ("record",),
            "verification_required": True,
            "success_criteria": ("narrowed",),
            "failure_criteria": ("no evidence",),
            "parent_mission_id": None,
            "causal_lineage": ("cause.synthetic",),
            "provenance": provenance(self.fx.env, cid),
            "lifecycle_state": ResearchMissionState.PROPOSED,
            "created_at": now,
            "updated_at": now,
        }

    def _register_mission(self, **kwargs) -> object:
        def payload(cid):
            return RegisterArtifactPayload(
                ResearchMission(**self._mission_kwargs(cid, **kwargs))
            )

        return submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.REGISTER_ARTIFACT,
                payload,
                task_scope=self.fx.task.task_id,
            ),
        )

    def test_protected_resource_in_contract_denied(self) -> None:
        hypothesis = self._hypothesis()
        result = self._register_mission(
            hypothesis_id=hypothesis.hypothesis_id,
            resources=(Resource.EPISTEMIC_STORE, Resource.AHOS_LANE_A),
            capabilities=(Capability.EPISTEMIC_WRITE,),
        )
        self.assertEqual(result.reason, "mission_cannot_scope_protected_resource")

    def test_forbidden_capability_in_contract_denied(self) -> None:
        hypothesis = self._hypothesis()
        for capability in (Capability.EXECUTION, Capability.POLICY_MODIFY):
            result = self._register_mission(
                hypothesis_id=hypothesis.hypothesis_id,
                resources=(Resource.EPISTEMIC_STORE,),
                capabilities=(Capability.EPISTEMIC_WRITE, capability),
            )
            self.assertEqual(
                result.reason,
                "mission_cannot_scope_forbidden_capability",
                msg=capability.value,
            )

    def test_legal_mission_still_registers(self) -> None:
        hypothesis = self._hypothesis()
        result = self._register_mission(
            hypothesis_id=hypothesis.hypothesis_id,
            resources=(Resource.EPISTEMIC_STORE,),
            capabilities=(Capability.EPISTEMIC_WRITE,),
        )
        self.assertTrue(result.accepted, result)


if __name__ == "__main__":
    unittest.main()
