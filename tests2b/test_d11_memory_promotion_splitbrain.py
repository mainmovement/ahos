"""D-11 remediation: the memory lifecycle map no longer names PROMOTED.

Policy split-brain (a table permitting what the TCB denies) is forbidden by
spec section 24.  Closure, layered:

1. ``LEGAL_ARTIFACT_TRANSITIONS[MemoryRecord]`` contains no edge whose
   target is ``MemoryState.PROMOTED`` (one frozen map, one policy);
2. the pure helper ``transition_artifact`` therefore refuses;
3. the TCB short-circuits the request before map evaluation and keeps the
   precise denial ``memory_cannot_silently_become_truth``;
4. ``MemoryState.PROMOTED`` stays in the enum (spec section-26 concept) but
   is unreachable through TRANSITION_ARTIFACT.
"""

from __future__ import annotations

import unittest
from datetime import timedelta

from agent_org.epistemic import (
    LEGAL_ARTIFACT_TRANSITIONS,
    MemoryRecord,
    MemoryState,
    transition_artifact,
)


class D11MemoryPromotionSplitBrainTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _memory(self):
        from agent_org.epistemic import MemoryKind

        evidence = self.fx.valid_evidence()

        def factory(cid: str) -> MemoryRecord:
            from tests2b.support import provenance

            return MemoryRecord(
                memory_id=self.fx.env.ids.new("memory"),
                memory_kind=MemoryKind.EPISODIC,
                subject="synthetic memory, not truth",
                content_ref="fixture://memory",
                evidence_ids=(evidence.evidence_id,),
                assurance=40,
                provenance=provenance(self.fx.env, cid),
                lifecycle_state=MemoryState.CANDIDATE,
                created_at=self.fx.env.clock.now(),
                updated_at=self.fx.env.clock.now(),
            )

        result, memory = self.fx.register(factory)
        self.assertTrue(result.accepted, result)
        return memory

    def test_map_has_no_promotion_edge_for_memory(self) -> None:
        rules = LEGAL_ARTIFACT_TRANSITIONS[MemoryRecord]
        for source, targets in rules.items():
            self.assertNotIn(
                MemoryState.PROMOTED,
                targets,
                f"split-brain edge {source}->PROMOTED",
            )

    def test_pure_helper_refuses_memory_promotion(self) -> None:
        from agent_org.epistemic import MemoryKind, MemoryState as MS
        from agent_org.contracts import Provenance

        now = self.fx.env.clock.now()
        memory = MemoryRecord(
            memory_id="memory.helper-level",
            memory_kind=MemoryKind.FAILURE,
            subject="helper-level refusal",
            content_ref="fixture://x",
            evidence_ids=("evidence.x",),
            assurance=10,
            provenance=Provenance(
                creator_principal_id="principal.system-tcb",
                session_id="session.bootstrap",
                command_id="command.bootstrap",
                method="helper-level",
            ),
            lifecycle_state=MemoryState.CANDIDATE,
            created_at=now,
            updated_at=now,
        )
        with self.assertRaises(ValueError):
            transition_artifact(memory, MS.PROMOTED, now + timedelta(seconds=1))

    def test_tcb_denies_candidate_to_promoted_with_precise_reason(self) -> None:
        memory = self._memory()
        denied = self.fx.transition(memory, MemoryState.PROMOTED)
        self.assertEqual(denied.reason, "memory_cannot_silently_become_truth")
        live = self.fx.env.plane.projections.artifact(memory.memory_id)
        self.assertIs(live.lifecycle_state, MemoryState.CANDIDATE)
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_tcb_denies_challenged_to_promoted_as_well(self) -> None:
        memory = self._memory()
        challenged = self.fx.transition(memory, MemoryState.CHALLENGED)
        self.assertTrue(challenged.accepted, challenged)
        live = self.fx.env.plane.projections.artifact(memory.memory_id)
        denied = self.fx.transition(live, MemoryState.PROMOTED)
        self.assertEqual(denied.reason, "memory_cannot_silently_become_truth")

    def test_memory_challenge_and_reject_still_work(self) -> None:
        memory = self._memory()
        self.assertTrue(
            self.fx.transition(memory, MemoryState.CHALLENGED).accepted
        )
        live = self.fx.env.plane.projections.artifact(memory.memory_id)
        self.assertTrue(self.fx.transition(live, MemoryState.REJECTED).accepted)


if __name__ == "__main__":
    unittest.main()
