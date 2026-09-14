"""RT-01..RT-24: explicit attack → denial/safe-behavior regression tests."""

from __future__ import annotations

import ast
import threading
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from pathlib import Path

from agent_org.audit import AuditIntegrityError, AuditLedger
from agent_org.authority import CapabilityGrant
from agent_org.commands import (
    CreateApprovalPayload,
    CreateTaskPayload,
    CreateVerificationPayload,
    DelegateAuthorityPayload,
    PromoteKnowledgePayload,
    RegisterAgentPayload,
    RegisterArtifactPayload,
    RevokeGrantPayload,
    TransitionTaskPayload,
    UpdatePolicyPayload,
)
from agent_org.contracts import (
    Capability,
    CommandStatus,
    CommandType,
    GovernedTask,
    IdentityStatus,
    IdentityType,
    Operation,
    POLICY_VERSION,
    Resource,
    TaskState,
)
from agent_org.epistemic import (
    Approval,
    ApprovalState,
    Claim,
    ClaimState,
    Evidence,
    EvidenceState,
    MemoryKind,
    MemoryRecord,
    MemoryState,
    VerificationKind,
    VerificationRecord,
    VerificationStatus,
)
from agent_org.identity import AgentIdentity
from tests2b.support import (
    create_task,
    delegate_for_command,
    grant_task_commands,
    make_command,
    new_env,
    provenance,
    ready_task,
    register_agent,
    submit,
)


class Slice2BRedTeamTests(unittest.TestCase):
    def test_rt01_self_register_trusted_denied(self) -> None:
        """ATTACK self-register; EXPECT wrong-principal denial; ACTUAL no agent."""
        env = new_env()

        def payload(cid):
            return RegisterAgentPayload(
                AgentIdentity(
                    principal_id="principal.attacker",
                    identity_type=IdentityType.AGENT,
                    display_name="attacker",
                    status=IdentityStatus.ACTIVE,
                    provenance=replace(
                        provenance(env, cid),
                        creator_principal_id="principal.attacker",
                    ),
                    created_at=env.clock.now(),
                    role="self-declared",
                )
            )

        command = make_command(
            env,
            CommandType.REGISTER_AGENT,
            payload,
            actor_principal_id="principal.attacker",
        )
        result = submit(env, command)
        self.assertEqual(result.reason, "wrong_principal")
        self.assertFalse(
            any(a.principal_id == "principal.attacker" for a in env.plane.projections.agents())
        )

    def test_rt02_forge_human_approval_denied(self) -> None:
        """ATTACK fake approver; EXPECT identity binding; ACTUAL forged denial."""
        env = new_env()
        producer = register_agent(env)
        task = ready_task(env)
        grant_task_commands(env, task.task_id, (CommandType.CREATE_APPROVAL,))

        def payload(cid):
            return CreateApprovalPayload(
                Approval(
                    approval_id=env.ids.new("approval"),
                    approver_principal_id=producer.principal_id,
                    task_id=task.task_id,
                    action=Operation.PROMOTE.value,
                    resource_id=Resource.EPISTEMIC_STORE,
                    capability_id=Capability.KNOWLEDGE_PROMOTE,
                    policy_version=POLICY_VERSION,
                    issued_at=env.clock.now(),
                    expires_at=env.clock.now() + timedelta(minutes=5),
                    provenance=provenance(env, cid),
                    lifecycle_state=ApprovalState.ACTIVE,
                    created_at=env.clock.now(),
                    updated_at=env.clock.now(),
                )
            )

        result = submit(
            env,
            make_command(
                env,
                CommandType.CREATE_APPROVAL,
                payload,
                task_scope=task.task_id,
            ),
        )
        self.assertEqual(result.reason, "forged_human_approval")

    def test_rt03_fabricate_evidence_denied(self) -> None:
        """ATTACK evidence with unknown source; EXPECT resolution; ACTUAL denial."""
        env = new_env()
        producer = register_agent(env)
        task = ready_task(env)
        grant_task_commands(env, task.task_id, (CommandType.REGISTER_ARTIFACT,))

        def payload(cid):
            return RegisterArtifactPayload(
                Evidence(
                    evidence_id=env.ids.new("evidence"),
                    source_id="source.fabricated",
                    producer_principal_id=producer.principal_id,
                    retrieval_timestamp=env.clock.now(),
                    observation_timestamp=env.clock.now(),
                    content_hash="f" * 64,
                    content_ref="fixture://fabricated",
                    extraction_method="fabrication",
                    validity_status=EvidenceState.REGISTERED,
                    freshness_max_age_seconds=60,
                    expires_at=env.clock.now() + timedelta(seconds=60),
                    assurance=1,
                    provenance=provenance(env, cid),
                    lifecycle_state=EvidenceState.REGISTERED,
                    created_at=env.clock.now(),
                    updated_at=env.clock.now(),
                )
            )

        result = submit(
            env,
            make_command(
                env,
                CommandType.REGISTER_ARTIFACT,
                payload,
                task_scope=task.task_id,
            ),
        )
        self.assertEqual(result.reason, "invalid_epistemic_reference")

    def test_rt04_fake_evidence_id_denied(self) -> None:
        """ATTACK claim references fake ID; EXPECT repository check; ACTUAL denial."""
        env = new_env()
        producer = register_agent(env)
        task = ready_task(env)
        grant_task_commands(env, task.task_id, (CommandType.REGISTER_ARTIFACT,))
        result = submit(
            env,
            make_command(
                env,
                CommandType.REGISTER_ARTIFACT,
                lambda cid: RegisterArtifactPayload(
                    Claim(
                        claim_id=env.ids.new("claim"),
                        statement="unsupported",
                        evidence_ids=("evidence.fake",),
                        producer_principal_id=producer.principal_id,
                        provenance=provenance(env, cid),
                        lifecycle_state=ClaimState.DRAFT,
                        created_at=env.clock.now(),
                        updated_at=env.clock.now(),
                    )
                ),
                task_scope=task.task_id,
            ),
        )
        self.assertEqual(result.reason, "invalid_epistemic_reference")

    def test_rt05_forge_verification_denied(self) -> None:
        """ATTACK fake target; EXPECT actual artifact resolution; ACTUAL denial."""
        env = new_env()
        producer = register_agent(env)
        task = ready_task(env)
        grant_task_commands(env, task.task_id, (CommandType.CREATE_VERIFICATION,))

        def payload(cid):
            return CreateVerificationPayload(
                VerificationRecord(
                    verification_id=env.ids.new("verification"),
                    target_artifact_id="candidate.fake",
                    producer_principal_id=producer.principal_id,
                    verifier_principal_id=env.plane.operator.principal_id,
                    verification_kind=VerificationKind.INDEPENDENT,
                    status=VerificationStatus.PASS,
                    evidence_ids=("evidence.fake",),
                    method="forged",
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
                task_scope=task.task_id,
                expected_state_version=1,
            ),
        )
        self.assertEqual(result.reason, "fake_verification_target")

    def test_rt06_self_verification_not_independent(self) -> None:
        """ATTACK producer=verifier; EXPECT contract rejection; ACTUAL ValueError."""
        env = new_env()
        with self.assertRaises(ValueError):
            VerificationRecord(
                verification_id="verification.self",
                target_artifact_id="candidate.target",
                producer_principal_id=env.plane.operator.principal_id,
                verifier_principal_id=env.plane.operator.principal_id,
                verification_kind=VerificationKind.INDEPENDENT,
                status=VerificationStatus.PASS,
                evidence_ids=("evidence.actual",),
                method="self",
                provenance=provenance(env, "command.self"),
                lifecycle_state=VerificationStatus.PASS,
                created_at=env.clock.now(),
                updated_at=env.clock.now(),
            )

    def test_rt07_capability_escalation_denied(self) -> None:
        """ATTACK alter capability; EXPECT fixed command policy; ACTUAL denial."""
        env = new_env()
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.EPISTEMIC_WRITE,),
            resource_scope=(Resource.EPISTEMIC_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        command = make_command(
            env, CommandType.CREATE_TASK, lambda _cid: CreateTaskPayload(task)
        )
        escalated = replace(command, capability_scope=Capability.IDENTITY_MANAGE)
        result = submit(env, escalated)
        self.assertEqual(result.reason, "command_scope_policy_mismatch")

    def test_rt08_excess_child_authority_denied(self) -> None:
        """ATTACK wider child capability; EXPECT attenuation; ACTUAL denial."""
        env = new_env()
        task = create_task(env)
        root = next(
            grant
            for grant in env.plane.projections.capability_status(
                env.plane.operator.principal_id
            ).grants
            if grant.capability_id is Capability.TASK_MANAGE
            and grant.operation is Operation.TRANSITION
        )
        child = CapabilityGrant(
            grant_id=env.ids.new("grant"),
            principal_id=env.plane.operator.principal_id,
            capability_id=Capability.EPISTEMIC_WRITE,
            operation=root.operation,
            resource_id=root.resource_id,
            task_id=task.task_id,
            issued_by_principal_id=env.plane.operator.principal_id,
            issued_at=env.clock.now(),
            expires_at=env.clock.now() + timedelta(minutes=5),
            policy_version=POLICY_VERSION,
            parent_grant_id=root.grant_id,
            delegation_depth=1,
        )
        result = submit(
            env,
            make_command(
                env,
                CommandType.DELEGATE_AUTHORITY,
                lambda _cid: DelegateAuthorityPayload(child),
            ),
        )
        self.assertEqual(result.reason, "child_authority_exceeds_parent")

    def test_rt09_expired_grant_reuse_denied(self) -> None:
        """ATTACK use expired leaf; EXPECT active-time check; ACTUAL denial."""
        env = new_env()
        task = create_task(env)
        delegate_for_command(
            env,
            task.task_id,
            CommandType.TRANSITION_TASK,
            expires_in=timedelta(seconds=1),
        )
        env.clock.advance(2)
        command = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task.task_id, TaskState.AUTHORIZED.value
            ),
            task_scope=task.task_id,
            expected_state_version=task.version,
        )
        self.assertEqual(submit(env, command).reason, "grant_expired")

    def test_rt10_revoked_grant_reuse_denied(self) -> None:
        """ATTACK use revoked leaf; EXPECT revocation check; ACTUAL denial."""
        env = new_env()
        task = create_task(env)
        child = delegate_for_command(env, task.task_id, CommandType.TRANSITION_TASK)
        revoke = make_command(
            env,
            CommandType.REVOKE_GRANT,
            lambda _cid: RevokeGrantPayload(child.grant_id),
        )
        self.assertTrue(submit(env, revoke).accepted)
        transition = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task.task_id, TaskState.AUTHORIZED.value
            ),
            task_scope=task.task_id,
            expected_state_version=task.version,
        )
        self.assertEqual(submit(env, transition).reason, "grant_revoked")

    def test_rt11_task_hijack_denied(self) -> None:
        """ATTACK agent actor on operator session; EXPECT binding; ACTUAL denial."""
        env = new_env()
        attacker = register_agent(env, "principal.agent-attacker")
        task = create_task(env)
        delegate_for_command(env, task.task_id, CommandType.TRANSITION_TASK)
        command = make_command(
            env,
            CommandType.TRANSITION_TASK,
            lambda _cid: TransitionTaskPayload(
                task.task_id, TaskState.AUTHORIZED.value
            ),
            task_scope=task.task_id,
            expected_state_version=task.version,
            actor_principal_id=attacker.principal_id,
        )
        self.assertEqual(submit(env, command).reason, "wrong_principal")

    def test_rt12_command_replay_denied(self) -> None:
        """ATTACK same command twice; EXPECT one mutation; ACTUAL REPLAYED."""
        env = new_env()
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.TASK_MANAGE,),
            resource_scope=(Resource.TASK_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        command = make_command(
            env, CommandType.CREATE_TASK, lambda _cid: CreateTaskPayload(task)
        )
        self.assertTrue(submit(env, command).accepted)
        self.assertEqual(submit(env, command).status, CommandStatus.REPLAYED)
        self.assertEqual(len(env.plane.projections.tasks()), 1)

    def test_rt13_audit_truncation_detected(self) -> None:
        """ATTACK remove events; EXPECT checkpoint mismatch; ACTUAL exception."""
        env = new_env()
        create_task(env)
        snapshot_events = env.plane.projections.audit_events()
        ledger = AuditLedger()
        object.__setattr__(ledger, "_AuditLedger__events", list(snapshot_events))
        with self.assertRaises(AuditIntegrityError):
            ledger.verify()

    def test_rt14_memory_poisoning_denied(self) -> None:
        """ATTACK memory with fake support; EXPECT reference check; ACTUAL denial."""
        env = new_env()
        task = ready_task(env)
        grant_task_commands(env, task.task_id, (CommandType.REGISTER_ARTIFACT,))
        result = submit(
            env,
            make_command(
                env,
                CommandType.REGISTER_ARTIFACT,
                lambda cid: RegisterArtifactPayload(
                    MemoryRecord(
                        memory_id=env.ids.new("memory"),
                        memory_kind=MemoryKind.SEMANTIC,
                        subject="poison",
                        content_ref="fixture://poison",
                        evidence_ids=("evidence.fake",),
                        assurance=100,
                        provenance=provenance(env, cid),
                        lifecycle_state=MemoryState.CANDIDATE,
                        created_at=env.clock.now(),
                        updated_at=env.clock.now(),
                    )
                ),
                task_scope=task.task_id,
            ),
        )
        self.assertEqual(result.reason, "invalid_epistemic_reference")

    def test_rt15_contradiction_suppression_denied(self) -> None:
        """ATTACK suppress open conflict; EXPECT promotion block; ACTUAL tested path."""
        from tests2b.test_epistemic_core import EpistemicCoreTests

        case = EpistemicCoreTests(
            "test_open_contradiction_blocks_verification_and_promotion"
        )
        case.setUp()
        case.test_open_contradiction_blocks_verification_and_promotion()

    def test_rt16_unknown_cannot_become_safe(self) -> None:
        """ATTACK unknown resource enum; EXPECT schema failure; ACTUAL ValueError."""
        with self.assertRaises(ValueError):
            Resource("UNKNOWN_RESOURCE")
        with self.assertRaises(ValueError):
            Capability("unknown.capability")

    def test_rt17_self_modify_policy_denied(self) -> None:
        """ATTACK policy update; EXPECT global deny; ACTUAL no accepted result."""
        env = new_env()
        command = make_command(
            env,
            CommandType.UPDATE_POLICY,
            lambda _cid: UpdatePolicyPayload("attacker-v2"),
        )
        result = submit(env, command)
        self.assertFalse(result.accepted)
        self.assertIn(result.reason, {"operation_global_deny", "capability_global_deny"})

    def test_rt18_cognitive_scope_cannot_become_execution(self) -> None:
        """ATTACK execution task scope; EXPECT global boundary; ACTUAL denial."""
        env = new_env()
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.EXECUTION,),
            resource_scope=(Resource.EXTERNAL_EXECUTION,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        result = submit(
            env,
            make_command(
                env,
                CommandType.CREATE_TASK,
                lambda _cid: CreateTaskPayload(task),
            ),
        )
        self.assertEqual(result.reason, "task_cannot_scope_protected_resource")

    def test_rt19_forged_approval_provenance_denied(self) -> None:
        """ATTACK forged creator; EXPECT provenance binding; ACTUAL denial."""
        env = new_env()
        task = ready_task(env)
        grant_task_commands(env, task.task_id, (CommandType.CREATE_APPROVAL,))

        def payload(cid):
            fake = replace(
                provenance(env, cid), creator_principal_id="principal.fake-human"
            )
            return CreateApprovalPayload(
                Approval(
                    approval_id=env.ids.new("approval"),
                    approver_principal_id=env.plane.operator.principal_id,
                    task_id=task.task_id,
                    action=Operation.PROMOTE.value,
                    resource_id=Resource.EPISTEMIC_STORE,
                    capability_id=Capability.KNOWLEDGE_PROMOTE,
                    policy_version=POLICY_VERSION,
                    issued_at=env.clock.now(),
                    expires_at=env.clock.now() + timedelta(minutes=5),
                    provenance=fake,
                    lifecycle_state=ApprovalState.ACTIVE,
                    created_at=env.clock.now(),
                    updated_at=env.clock.now(),
                )
            )

        result = submit(
            env,
            make_command(
                env,
                CommandType.CREATE_APPROVAL,
                payload,
                task_scope=task.task_id,
            ),
        )
        self.assertEqual(result.reason, "artifact_provenance_mismatch")

    def test_rt20_compromised_verifier_cannot_self_promote(self) -> None:
        """ATTACK SELF_CHECK as independent; EXPECT no verification; ACTUAL denial."""
        from tests2b.test_epistemic_core import EpistemicCoreTests

        case = EpistemicCoreTests(
            "test_self_check_does_not_satisfy_promotion_verification"
        )
        case.setUp()
        case.test_self_check_does_not_satisfy_promotion_verification()

    def test_rt21_double_authorization_race_single_commit(self) -> None:
        """ATTACK concurrent duplicate; EXPECT one commit; ACTUAL one replay."""
        env = new_env()
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.TASK_MANAGE,),
            resource_scope=(Resource.TASK_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        command = make_command(
            env, CommandType.CREATE_TASK, lambda _cid: CreateTaskPayload(task)
        )
        barrier = threading.Barrier(3)
        results = []

        def worker():
            barrier.wait()
            results.append(submit(env, command))

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(result.accepted for result in results), 1)
        self.assertEqual(
            sum(result.status is CommandStatus.REPLAYED for result in results), 1
        )

    def test_rt22_toctou_resource_change_blocked_by_immutable_command(self) -> None:
        """ATTACK mutate scope after check; EXPECT frozen envelope; ACTUAL exception."""
        env = new_env()
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.TASK_MANAGE,),
            resource_scope=(Resource.TASK_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        command = make_command(
            env, CommandType.CREATE_TASK, lambda _cid: CreateTaskPayload(task)
        )
        with self.assertRaises(FrozenInstanceError):
            command.resource_scope = Resource.EPISTEMIC_STORE  # type: ignore[misc]
        self.assertTrue(submit(env, command).accepted)

    def test_rt23_direct_registry_mutation_not_exposed(self) -> None:
        """ATTACK mutate through projection; EXPECT no mutator; ACTUAL immutable tuple."""
        env = new_env()
        principals = env.plane.projections.principals()
        self.assertIsInstance(principals, tuple)
        self.assertFalse(hasattr(principals, "append"))
        self.assertEqual(
            {name for name in dir(env.plane.tcb) if not name.startswith("_")},
            {"submit"},
        )

    def test_rt24_plugin_bypass_import_denied_by_static_boundary(self) -> None:
        """ATTACK trusted import alias; EXPECT static ban; ACTUAL clean plugin API."""
        path = (
            Path(__file__).resolve().parents[1]
            / "agent_org"
            / "untrusted"
            / "plugin_api.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertEqual(imports, {"agent_org.public"})
        text = path.read_text(encoding="utf-8")
        for forbidden in ("stores", "_GovernedState", "_MutationPermit", "commit("):
            self.assertNotIn(forbidden, text)
