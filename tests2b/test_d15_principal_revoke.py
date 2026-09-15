"""D-15 remediation: audited agent-principal revocation.

There was no command to revoke (or suspend) a compromised agent identity;
REGISTER_AGENT had no audited counterpart.  REVOKE_AGENT closes it with the
standard pipeline (policy + authority + audit + replay rejection), explicit
denials for unknown/protected/duplicate-toggle requests, and immediate
effect through the existing liveness checks (``revoked_at is None``
everywhere a principal is consumed).
"""

from __future__ import annotations

import unittest

from agent_org.commands import (
    RegisterAgentPayload,
    RegisterArtifactPayload,
    RevokeAgentPayload,
)
from agent_org.contracts import (
    Capability,
    CommandType,
    IdentityStatus,
    IdentityType,
    Resource,
)
from agent_org.epistemic import Claim, ClaimState
from agent_org.identity import AgentIdentity
from tests2b.support import (
    make_command,
    provenance,
    submit,
)


class D15PrincipalRevokeTests(unittest.TestCase):
    def setUp(self) -> None:
        from tests2b.test_epistemic_core import EpistemicCoreTests

        self.fx = EpistemicCoreTests(
            "test_verified_candidate_promotes_with_scoped_active_approval"
        )
        self.fx.setUp()

    def _revoke(self, principal_id: str):
        return submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.REVOKE_AGENT,
                lambda _cid: RevokeAgentPayload(principal_id),
            ),
        )

    def test_revoke_registered_agent_succeeds_and_is_audited(self) -> None:
        agent = self.fx.producer
        result = self._revoke(agent.principal_id)
        self.assertTrue(result.accepted, result)
        live = self._principal(agent.principal_id)
        self.assertIsNotNone(live.revoked_at)
        events = self.fx.env.plane.projections.audit_events()
        self.assertEqual(events[-1].result, "ACCEPTED")
        self.assertTrue(self.fx.env.plane.projections.verify_audit())

    def test_revoked_agent_cannot_produce_new_artifacts(self) -> None:
        agent = self.fx.producer
        evidence = self.fx.valid_evidence()
        self.assertTrue(self._revoke(agent.principal_id).accepted)
        def payload(cid):
            return RegisterArtifactPayload(
                Claim(
                    claim_id=self.fx.env.ids.new("claim"),
                    statement="produced after revocation",
                    evidence_ids=(evidence.evidence_id,),
                    producer_principal_id=agent.principal_id,
                    provenance=provenance(self.fx.env, cid),
                    lifecycle_state=ClaimState.DRAFT,
                    created_at=self.fx.env.clock.now(),
                    updated_at=self.fx.env.clock.now(),
                )
            )

        result = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.REGISTER_ARTIFACT,
                payload,
                task_scope=self.fx.task.task_id,
            ),
        )
        self.assertEqual(result.reason, "unknown_or_inactive_artifact_principal")

    def test_revoked_id_can_never_be_re_registered(self) -> None:
        agent = self.fx.producer
        self.assertTrue(self._revoke(agent.principal_id).accepted)
        result = submit(
            self.fx.env,
            make_command(
                self.fx.env,
                CommandType.REGISTER_AGENT,
                lambda cid: RegisterAgentPayload(
                    AgentIdentity(
                        principal_id=agent.principal_id,
                        identity_type=IdentityType.AGENT,
                        display_name="resurrected",
                        status=IdentityStatus.ACTIVE,
                        provenance=provenance(self.fx.env, cid),
                        created_at=self.fx.env.clock.now(),
                        role="test-logical-agent",
                    )
                ),
            ),
        )
        self.assertEqual(result.reason, "duplicate_principal")

    def test_unknown_principal_denied(self) -> None:
        result = self._revoke("principal.ghost")
        self.assertEqual(result.reason, "unknown_principal")

    def test_protected_identities_cannot_be_revoked(self) -> None:
        for principal_id in (
            self.fx.env.plane.operator.principal_id,
            self.fx.env.plane.system.principal_id,
        ):
            result = self._revoke(principal_id)
            self.assertEqual(
                result.reason, "cannot_revoke_protected_identity", msg=principal_id
            )

    def test_double_revoke_denied(self) -> None:
        agent = self.fx.producer
        self.assertTrue(self._revoke(agent.principal_id).accepted)
        result = self._revoke(agent.principal_id)
        self.assertEqual(result.reason, "identity_already_revoked")

    def test_revoke_agent_policy_row_wired(self) -> None:
        from agent_org.contracts import Operation
        from agent_org.governance import COMMAND_POLICIES

        policy = COMMAND_POLICIES[CommandType.REVOKE_AGENT]
        self.assertIs(policy.capability, Capability.IDENTITY_MANAGE)
        self.assertIs(policy.resource, Resource.IDENTITY_STORE)
        self.assertIs(policy.operation, Operation.REVOKE)
        self.assertFalse(policy.task_required)

    def _principal(self, principal_id):
        for principal in self.fx.env.plane.projections.principals():
            if principal.principal_id == principal_id:
                return principal
        return None


if __name__ == "__main__":
    unittest.main()
