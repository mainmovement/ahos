"""Trusted Command Boundary and atomic in-memory command transaction."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol

from agent_org.audit import digest
from agent_org.authority import (
    AuthorityContext,
    CapabilityGrant,
    Delegation,
    derive_authority,
    validate_delegation,
)
from agent_org.commands import (
    CommandEnvelope,
    CreateApprovalPayload,
    CreateContradictionPayload,
    CreateTaskPayload,
    CreateVerificationPayload,
    DelegateAuthorityPayload,
    PromoteKnowledgePayload,
    RegisterAgentPayload,
    RegisterArtifactPayload,
    RevokeApprovalPayload,
    RevokeGrantPayload,
    TransitionArtifactPayload,
    TransitionTaskPayload,
)
from agent_org.contracts import (
    Capability,
    CommandResult,
    CommandStatus,
    CommandType,
    Decision,
    GovernedTask,
    IdentityStatus,
    IdentityType,
    Operation,
    POLICY_VERSION,
    PROTECTED_RESOURCES,
    Provenance,
    Resource,
    TASK_TRANSITIONS,
    TaskState,
)
from agent_org.epistemic import (
    Approval,
    ApprovalState,
    Artifact,
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
    KNOWLEDGE_PROMOTION_COMMAND,
    KNOWLEDGE_PROMOTION_DENIED_REASON,
    artifact_id,
    is_knowledge_promotion_state,
    refuse_generic_knowledge_promotion,
    transition_artifact,
)
from agent_org.governance import COMMAND_POLICIES, evaluate_command_policy
from agent_org.identity import (
    AgentIdentity,
    Clock,
    HumanIdentity,
    IdFactory,
    LocalOperatorSessionStub,
    Session,
    SystemIdentity,
)
from agent_org.projections import ReadOnlyProjections
from agent_org.stores import _GovernedState, _create_governed_store


class DomainDenied(RuntimeError):
    pass


class InjectedFailure(RuntimeError):
    pass


class FailureInjector(Protocol):
    def trip(self, stage: str) -> None: ...


class NoFailures:
    def trip(self, stage: str) -> None:
        return None


@dataclass(frozen=True)
class MutationOutcome:
    previous_state: str | None
    previous_version: int | None
    resulting_state: str | None
    resulting_version: int | None
    artifact_version: int | None


class TrustedCommandBoundary:
    """The sole mutation ingress for Slice 2B governed state."""

    def __init__(
        self,
        *,
        store: object,
        permit: object,
        sessions: LocalOperatorSessionStub,
        clock: Clock,
        ids: IdFactory,
        failures: FailureInjector | None = None,
    ) -> None:
        self.__store = store
        self.__permit = permit
        self.__sessions = sessions
        self.__clock = clock
        self.__ids = ids
        self.__failures = failures or NoFailures()

    def submit(self, command: CommandEnvelope, session: Session) -> CommandResult:
        """Validate, authorize, apply, audit, project, and atomically commit."""
        store = self.__store
        with store.lock:  # type: ignore[attr-defined]
            working, epoch = store.begin(self.__permit)  # type: ignore[attr-defined]
            baseline = deepcopy(working)
            if command.command_id in working.processed_commands:
                return self.__commit_denial(
                    command,
                    baseline,
                    epoch,
                    reason="duplicate_command_replay",
                    status=CommandStatus.REPLAYED,
                    session=session,
                    authority=None,
                )
            authority: AuthorityContext | None = None
            try:
                resolved = self.__sessions.resolve(session)
                now = self.__clock.now()
                if resolved is None:
                    raise DomainDenied("forged_or_unknown_session")
                if not resolved.is_active(now):
                    reason = (
                        "session_revoked"
                        if resolved.revoked_at is not None
                        else "session_expired"
                    )
                    raise DomainDenied(reason)
                policy = evaluate_command_policy(
                    command, session=resolved, state=working, now=now
                )
                if policy.decision is not Decision.ALLOW:
                    raise DomainDenied(policy.reason)
                authority_eval = derive_authority(
                    working.grants,
                    principal_id=resolved.principal_id,
                    task_id=command.task_scope,
                    capability_id=command.capability_scope,
                    operation=command.requested_operation,
                    resource_id=command.resource_scope,
                    policy_version=command.policy_version,
                    now=now,
                )
                if not authority_eval.allowed or authority_eval.context is None:
                    raise DomainDenied(authority_eval.reason)
                authority = authority_eval.context
                outcome = self.__apply(working, command, resolved, now)
                self.__failures.trip("state_mutation")
                working.processed_commands.add(command.command_id)
                self.__failures.trip("audit")
                event = self.__append_event(
                    working,
                    command,
                    session=resolved,
                    authority=authority,
                    outcome=outcome,
                    result=CommandStatus.ACCEPTED,
                    failure_reason=None,
                )
                self.__failures.trip("projection")
                store.commit(  # type: ignore[attr-defined]
                    working, expected_epoch=epoch, permit=self.__permit
                )
                return CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.ACCEPTED,
                    decision=Decision.ALLOW,
                    reason="command_committed",
                    event_id=event.event_id,
                    resulting_version=outcome.resulting_version,
                )
            except DomainDenied as exc:
                return self.__commit_denial(
                    command,
                    baseline,
                    epoch,
                    reason=str(exc),
                    status=CommandStatus.DENIED,
                    session=session,
                    authority=authority,
                )
            except (InjectedFailure, RuntimeError) as exc:
                return CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED,
                    decision=Decision.DENY,
                    reason=f"transaction_rolled_back:{exc}",
                    event_id=None,
                    resulting_version=None,
                )

    def __commit_denial(
        self,
        command: CommandEnvelope,
        baseline: _GovernedState,
        epoch: int,
        *,
        reason: str,
        status: CommandStatus,
        session: Session,
        authority: AuthorityContext | None,
    ) -> CommandResult:
        try:
            baseline.processed_commands.add(command.command_id)
            self.__failures.trip("audit")
            event = self.__append_event(
                baseline,
                command,
                session=session,
                authority=authority,
                outcome=MutationOutcome(None, None, None, None, None),
                result=status,
                failure_reason=reason,
            )
            self.__failures.trip("projection")
            self.__store.commit(
                baseline, expected_epoch=epoch, permit=self.__permit
            )
            return CommandResult(
                command_id=command.command_id,
                status=status,
                decision=Decision.DENY,
                reason=reason,
                event_id=event.event_id,
                resulting_version=None,
            )
        except (InjectedFailure, RuntimeError) as exc:
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                decision=Decision.DENY,
                reason=f"denial_audit_rolled_back:{exc}",
                event_id=None,
                resulting_version=None,
            )

    def __append_event(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        *,
        session: Session,
        authority: AuthorityContext | None,
        outcome: MutationOutcome,
        result: CommandStatus,
        failure_reason: str | None,
    ):
        return state.audit.append(
            ids=self.__ids,
            timestamp=self.__clock.now(),
            actor_principal=command.actor_principal_id,
            session_id=session.session_id,
            authority_chain=authority.chain.grant_ids if authority else (),
            command_id=command.command_id,
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
            parent_task_id=(
                state.tasks[command.task_scope].parent_task_id
                if command.task_scope in state.tasks
                else None
            ),
            resource_id=command.resource_scope.value,
            operation=command.requested_operation.value,
            capability_id=command.capability_scope.value,
            policy_version=command.policy_version,
            artifact_version=outcome.artifact_version,
            evidence_lineage=command.evidence_lineage,
            previous_state=outcome.previous_state,
            previous_version=outcome.previous_version,
            resulting_state=outcome.resulting_state,
            resulting_version=outcome.resulting_version,
            result=result.value,
            failure_reason=failure_reason,
            payload_hash=digest(command),
        )

    def __apply(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        session: Session,
        now: datetime,
    ) -> MutationOutcome:
        if command.command_type is CommandType.REGISTER_AGENT:
            return self.__register_agent(state, command, session)
        if command.command_type is CommandType.CREATE_TASK:
            return self.__create_task(state, command)
        if command.command_type is CommandType.TRANSITION_TASK:
            return self.__transition_task(state, command, now)
        if command.command_type is CommandType.DELEGATE_AUTHORITY:
            return self.__delegate(state, command, now)
        if command.command_type is CommandType.REVOKE_GRANT:
            return self.__revoke_grant(state, command, now)
        if command.command_type is CommandType.REGISTER_ARTIFACT:
            return self.__register_artifact(state, command, session, now)
        if command.command_type is CommandType.TRANSITION_ARTIFACT:
            return self.__transition_epistemic(state, command, now)
        if command.command_type is CommandType.CREATE_CONTRADICTION:
            return self.__create_contradiction(state, command, session)
        if command.command_type is CommandType.CREATE_VERIFICATION:
            return self.__create_verification(state, command, session, now)
        if command.command_type is CommandType.CREATE_APPROVAL:
            return self.__create_approval(state, command, session, now)
        if command.command_type is CommandType.REVOKE_APPROVAL:
            return self.__revoke_approval(state, command, now)
        if command.command_type is CommandType.PROMOTE_KNOWLEDGE:
            return self.__promote(state, command, now)
        raise DomainDenied("command_type_not_implemented_or_globally_denied")

    @staticmethod
    def __require_provenance(
        artifact: Artifact,
        command: CommandEnvelope,
        session: Session,
    ) -> None:
        provenance = artifact.provenance
        if (
            provenance.creator_principal_id != command.actor_principal_id
            or provenance.session_id != session.session_id
            or provenance.command_id != command.command_id
        ):
            raise DomainDenied("artifact_provenance_mismatch")

    @staticmethod
    def __register_agent(
        state: _GovernedState,
        command: CommandEnvelope,
        session: Session,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, RegisterAgentPayload)
        identity = payload.identity
        if identity.principal_id in state.principals:
            raise DomainDenied("duplicate_principal")
        if identity.identity_type is not IdentityType.AGENT:
            raise DomainDenied("registered_identity_must_be_agent")
        if identity.status is not IdentityStatus.ACTIVE or identity.revoked_at is not None:
            raise DomainDenied("caller_cannot_register_pretrusted_or_revoked_identity")
        provenance = identity.provenance
        if (
            provenance.creator_principal_id != command.actor_principal_id
            or provenance.session_id != session.session_id
            or provenance.command_id != command.command_id
        ):
            raise DomainDenied("identity_provenance_mismatch")
        state.principals[identity.principal_id] = identity
        return MutationOutcome(None, None, "ACTIVE", 1, 1)

    @staticmethod
    def __create_task(
        state: _GovernedState, command: CommandEnvelope
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, CreateTaskPayload)
        task = payload.task
        if command.expected_state_version != 0:
            raise DomainDenied("create_requires_expected_version_zero")
        if task.task_id in state.tasks:
            raise DomainDenied("duplicate_task")
        if task.owner_principal_id not in state.principals:
            raise DomainDenied("unknown_task_owner")
        if task.state is not TaskState.PROPOSED or task.version != 1:
            raise DomainDenied("task_must_start_proposed_at_version_one")
        if set(task.resource_scope) & PROTECTED_RESOURCES:
            raise DomainDenied("task_cannot_scope_protected_resource")
        if Capability.EXECUTION in task.capability_scope or Capability.POLICY_MODIFY in task.capability_scope:
            raise DomainDenied("task_cannot_scope_execution_or_policy_mutation")
        if task.parent_task_id is not None:
            parent = state.tasks.get(task.parent_task_id)
            if parent is None:
                raise DomainDenied("unknown_parent_task")
            if not set(task.capability_scope).issubset(parent.capability_scope):
                raise DomainDenied("child_task_capability_exceeds_parent")
            if not set(task.resource_scope).issubset(parent.resource_scope):
                raise DomainDenied("child_task_resource_exceeds_parent")
        state.tasks[task.task_id] = task
        return MutationOutcome(None, 0, task.state.value, task.version, task.version)

    @staticmethod
    def __transition_task(
        state: _GovernedState,
        command: CommandEnvelope,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, TransitionTaskPayload)
        if payload.task_id != command.task_scope:
            raise DomainDenied("task_payload_scope_mismatch")
        task = state.tasks.get(payload.task_id)
        if task is None:
            raise DomainDenied("unknown_task")
        if task.version != command.expected_state_version:
            raise DomainDenied("expected_state_version_mismatch")
        try:
            target = TaskState(payload.target_state)
        except ValueError as exc:
            raise DomainDenied("unknown_task_state") from exc
        if target not in TASK_TRANSITIONS.get(task.state, frozenset()):
            raise DomainDenied("illegal_task_transition")
        updated = replace(
            task,
            state=target,
            updated_at=now,
            version=task.version + 1,
        )
        state.tasks[task.task_id] = updated
        return MutationOutcome(
            task.state.value,
            task.version,
            updated.state.value,
            updated.version,
            updated.version,
        )

    def __delegate(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, DelegateAuthorityPayload)
        child = payload.grant
        if command.expected_state_version != 0:
            raise DomainDenied("grant_create_requires_expected_version_zero")
        if child.grant_id in state.grants:
            raise DomainDenied("duplicate_grant")
        if child.principal_id not in state.principals:
            raise DomainDenied("unknown_grantee")
        if child.resource_id in PROTECTED_RESOURCES:
            raise DomainDenied("protected_resource_global_deny")
        if child.capability_id in {Capability.EXECUTION, Capability.POLICY_MODIFY}:
            raise DomainDenied("forbidden_capability_delegation")
        if child.issued_at > now:
            raise DomainDenied("grant_issued_in_future")
        if child.parent_grant_id is None:
            raise DomainDenied("untrusted_command_cannot_create_root_grant")
        parent = state.grants.get(child.parent_grant_id)
        if parent is None:
            raise DomainDenied("broken_authority_chain")
        denial = validate_delegation(parent, child, now=now)
        if denial is not None:
            raise DomainDenied(denial)
        state.grants[child.grant_id] = child
        delegation = Delegation(
            delegation_id=self.__ids.new("delegation"),
            parent_grant_id=parent.grant_id,
            child_grant_id=child.grant_id,
            delegator_principal_id=parent.principal_id,
            delegatee_principal_id=child.principal_id,
            issued_at=child.issued_at,
            expires_at=child.expires_at,
        )
        state.delegations[delegation.delegation_id] = delegation
        return MutationOutcome(None, 0, "ACTIVE", 1, 1)

    @staticmethod
    def __revoke_grant(
        state: _GovernedState,
        command: CommandEnvelope,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, RevokeGrantPayload)
        grant = state.grants.get(payload.grant_id)
        if grant is None:
            raise DomainDenied("unknown_grant")
        if grant.revoked_at is not None:
            raise DomainDenied("grant_already_revoked")
        state.grants[grant.grant_id] = replace(grant, revoked_at=now)
        return MutationOutcome("ACTIVE", 1, "REVOKED", 2, 2)

    def __register_artifact(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        session: Session,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, RegisterArtifactPayload)
        item = payload.artifact
        key = artifact_id(item)
        if command.expected_state_version != 0:
            raise DomainDenied("artifact_create_requires_expected_version_zero")
        if key in state.artifacts or key in state.approvals:
            raise DomainDenied("duplicate_artifact")
        if isinstance(item, (VerificationRecord, ContradictionCase, Approval)):
            raise DomainDenied("artifact_requires_specialized_command")
        self.__require_provenance(item, command, session)
        self.__validate_initial_state(item)
        self.__validate_artifact_references(state, item, now)
        state.artifacts[key] = item
        lifecycle = item.lifecycle_state.value
        return MutationOutcome(None, 0, lifecycle, item.version, item.version)

    @staticmethod
    def __validate_initial_state(item: Artifact) -> None:
        expected: tuple[type[object], StrEnum] | None = None
        mapping: tuple[tuple[type[object], StrEnum], ...] = (
            (Source, SourceState.REGISTERED),
            (Evidence, EvidenceState.REGISTERED),
            (Claim, ClaimState.DRAFT),
            (Hypothesis, HypothesisState.PROPOSED),
            (Prediction, PredictionState.PROPOSED),
            (Observation, ObservationState.RECORDED),
            (KnowledgeCandidate, KnowledgeState.SUBMITTED),
            (ResearchMission, ResearchMissionState.PROPOSED),
            (ExperimentPlan, ExperimentState.PLANNED),
            (ExperimentRun, ExperimentState.PLANNED),
            (MemoryRecord, MemoryState.CANDIDATE),
        )
        for kind, state in mapping:
            if isinstance(item, kind):
                expected = (kind, state)
                break
        if expected is None or item.lifecycle_state != expected[1] or item.version != 1:
            raise DomainDenied("artifact_initial_state_invalid")
        if isinstance(item, Evidence):
            if item.verification_status is not VerificationStatus.UNVERIFIED:
                raise DomainDenied("evidence_cannot_self_declare_verified")
            if item.revoked_at is not None:
                raise DomainDenied("new_evidence_cannot_be_revoked")
        if isinstance(item, KnowledgeCandidate):
            if item.verification_ids or item.contradiction_ids:
                raise DomainDenied("candidate_cannot_predeclare_verification_or_contradiction")
        if isinstance(item, (Claim, Observation)) and item.verification_ids:
            raise DomainDenied("artifact_cannot_predeclare_verification")
        if isinstance(item, ContradictionCase) and item.resolution_evidence_ids:
            raise DomainDenied("open_contradiction_cannot_predeclare_resolution")
        if isinstance(item, MemoryRecord) and item.lifecycle_state is MemoryState.PROMOTED:
            raise DomainDenied("memory_cannot_enter_as_truth")

    @staticmethod
    def __require_existing(
        state: _GovernedState, keys: tuple[str, ...], prefix: str
    ) -> None:
        namespace = prefix.rstrip(".-")
        for key in keys:
            if not key.startswith((namespace + ".", namespace + "-")) or key not in state.artifacts:
                raise DomainDenied("invalid_epistemic_reference")

    def __validate_artifact_references(
        self,
        state: _GovernedState,
        item: Artifact,
        now: datetime,
    ) -> None:
        if isinstance(item, Source):
            return
        if isinstance(item, Evidence):
            self.__require_existing(state, (item.source_id,), "source.")
            if item.producer_principal_id not in state.principals:
                raise DomainDenied("unknown_evidence_producer")
            if item.supersedes_evidence_id is not None:
                self.__require_existing(
                    state, (item.supersedes_evidence_id,), "evidence."
                )
            return
        if isinstance(item, Claim):
            self.__require_active_principal(state, item.producer_principal_id)
            self.__require_existing(state, item.evidence_ids, "evidence.")
            return
        if isinstance(item, Hypothesis):
            self.__require_active_principal(state, item.producer_principal_id)
            self.__require_existing(state, item.supporting_claim_ids, "claim.")
            return
        if isinstance(item, Prediction):
            self.__require_existing(state, (item.hypothesis_id,), "hypothesis.")
            return
        if isinstance(item, Observation):
            self.__require_existing(
                state, (item.experiment_run_id,), "experiment-run."
            )
            return
        if isinstance(item, KnowledgeCandidate):
            self.__require_active_principal(state, item.producer_principal_id)
            self.__require_existing(state, item.claim_ids, "claim.")
            self.__require_existing(state, item.evidence_ids, "evidence.")
            return
        if isinstance(item, ResearchMission):
            assigned = state.principals.get(item.assigned_agent_id)
            if not isinstance(assigned, AgentIdentity):
                raise DomainDenied("unknown_research_agent")
            self.__require_active_principal(state, item.assigned_agent_id)
            self.__require_existing(state, item.hypothesis_ids, "hypothesis.")
            if item.parent_mission_id is not None:
                self.__require_existing(
                    state, (item.parent_mission_id,), "mission."
                )
            if item.expires_at <= now:
                raise DomainDenied("research_mission_expired")
            return
        if isinstance(item, ExperimentPlan):
            self.__require_existing(state, (item.hypothesis_id,), "hypothesis.")
            return
        if isinstance(item, ExperimentRun):
            self.__require_existing(
                state, (item.experiment_plan_id,), "experiment-plan."
            )
            return
        if isinstance(item, MemoryRecord):
            self.__require_existing(state, item.evidence_ids, "evidence.")
            if item.supersedes_memory_id is not None:
                self.__require_existing(
                    state, (item.supersedes_memory_id,), "memory."
                )
            return
        raise DomainDenied("unsupported_artifact_type")

    @staticmethod
    def __require_active_principal(
        state: _GovernedState, principal_id: str
    ) -> None:
        principal = state.principals.get(principal_id)
        if (
            principal is None
            or principal.status is not IdentityStatus.ACTIVE
            or principal.revoked_at is not None
        ):
            raise DomainDenied("unknown_or_inactive_artifact_principal")

    def __transition_epistemic(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, TransitionArtifactPayload)
        if command.command_type is not CommandType.TRANSITION_ARTIFACT:
            raise DomainDenied("handler_command_type_mismatch")
        item = state.artifacts.get(payload.artifact_id)
        if item is None:
            raise DomainDenied("unknown_artifact")
        if item.version != command.expected_state_version:
            raise DomainDenied("expected_state_version_mismatch")
        try:
            refuse_generic_knowledge_promotion(item, payload.target_state)
            updated = transition_artifact(item, payload.target_state, now)
        except ValueError as exc:
            raise DomainDenied(str(exc)) from exc
        if isinstance(updated, KnowledgeCandidate) and is_knowledge_promotion_state(
            updated.lifecycle_state
        ):
            raise DomainDenied(KNOWLEDGE_PROMOTION_DENIED_REASON)
        if isinstance(item, MemoryRecord) and payload.target_state is MemoryState.PROMOTED:
            raise DomainDenied("memory_cannot_silently_become_truth")
        if isinstance(item, Evidence) and payload.target_state is EvidenceState.VALID:
            if item.verification_status is not VerificationStatus.PASS:
                raise DomainDenied("evidence_requires_independent_verification")
            if now >= item.expires_at:
                raise DomainDenied("stale_evidence_cannot_become_valid")
        if isinstance(item, Claim) and payload.target_state is ClaimState.VERIFIED:
            self.__require_independent_verification(state, item)
        if (
            isinstance(item, Observation)
            and payload.target_state is ObservationState.VERIFIED
        ):
            self.__require_independent_verification(state, item)
        if (
            isinstance(item, ContradictionCase)
            and payload.target_state is ContradictionState.RESOLVED
        ):
            if not payload.evidence_ids:
                raise DomainDenied("contradiction_resolution_requires_evidence")
            for evidence_id in payload.evidence_ids:
                evidence = state.artifacts.get(evidence_id)
                if not isinstance(evidence, Evidence) or not self.__evidence_eligible(
                    state, evidence, now
                ):
                    raise DomainDenied("contradiction_resolution_evidence_invalid")
            item = replace(item, resolution_evidence_ids=payload.evidence_ids)
            updated = transition_artifact(item, payload.target_state, now)
        if (
            isinstance(item, KnowledgeCandidate)
            and payload.target_state is KnowledgeState.VERIFIED
        ):
            self.__require_candidate_verification(state, item, now)
        state.artifacts[payload.artifact_id] = updated
        return MutationOutcome(
            item.lifecycle_state.value,
            item.version,
            updated.lifecycle_state.value,
            updated.version,
            updated.version,
        )

    def __create_contradiction(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        session: Session,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, CreateContradictionPayload)
        item = payload.contradiction
        self.__require_provenance(item, command, session)
        if item.lifecycle_state is not ContradictionState.OPEN or item.version != 1:
            raise DomainDenied("contradiction_must_start_open")
        if item.resolution_evidence_ids:
            raise DomainDenied("open_contradiction_cannot_predeclare_resolution")
        if artifact_id(item) in state.artifacts:
            raise DomainDenied("duplicate_artifact")
        if (
            item.left_artifact_id not in state.artifacts
            or item.right_artifact_id not in state.artifacts
        ):
            raise DomainDenied("contradiction_target_unknown")
        if len(item.affects_candidate_ids) != 1:
            raise DomainDenied("slice_2b_contradiction_requires_one_candidate")
        candidate = state.artifacts.get(item.affects_candidate_ids[0])
        if not isinstance(candidate, KnowledgeCandidate):
            raise DomainDenied("contradiction_candidate_unknown")
        if candidate.version != command.expected_state_version:
            raise DomainDenied("expected_state_version_mismatch")
        state.artifacts[item.contradiction_id] = item
        updated = replace(
            candidate,
            contradiction_ids=candidate.contradiction_ids + (item.contradiction_id,),
            updated_at=item.updated_at,
            version=candidate.version + 1,
        )
        state.artifacts[candidate.candidate_id] = updated
        return MutationOutcome(
            candidate.lifecycle_state.value,
            candidate.version,
            updated.lifecycle_state.value,
            updated.version,
            updated.version,
        )

    def __create_verification(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        session: Session,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, CreateVerificationPayload)
        verification = payload.verification
        self.__require_provenance(verification, command, session)
        if verification.verification_id in state.artifacts:
            raise DomainDenied("duplicate_verification")
        target = state.artifacts.get(verification.target_artifact_id)
        if target is None:
            raise DomainDenied("fake_verification_target")
        if verification.verifier_principal_id != command.actor_principal_id:
            raise DomainDenied("verifier_identity_mismatch")
        verifier = state.principals.get(verification.verifier_principal_id)
        if (
            verifier is None
            or verifier.status is not IdentityStatus.ACTIVE
            or verifier.revoked_at is not None
        ):
            raise DomainDenied("invalid_verifier")
        producer = self.__producer_of(target)
        if verification.producer_principal_id != producer:
            raise DomainDenied("verification_producer_mismatch")
        self.__require_existing(state, verification.evidence_ids, "evidence.")
        if target.version != command.expected_state_version:
            raise DomainDenied("expected_state_version_mismatch")
        if (
            verification.verification_kind is VerificationKind.INDEPENDENT
            and verification.producer_principal_id
            == verification.verifier_principal_id
        ):
            raise DomainDenied("self_verification_not_independent")
        state.artifacts[verification.verification_id] = verification
        resulting_version = target.version
        if isinstance(target, KnowledgeCandidate):
            updated = replace(
                target,
                verification_ids=target.verification_ids
                + (verification.verification_id,),
                updated_at=now,
                version=target.version + 1,
            )
            state.artifacts[target.candidate_id] = updated
            resulting_version = updated.version
        elif isinstance(target, (Claim, Observation)):
            updated = replace(
                target,
                verification_ids=target.verification_ids
                + (verification.verification_id,),
                updated_at=now,
                version=target.version + 1,
            )
            state.artifacts[artifact_id(target)] = updated
            resulting_version = updated.version
        elif (
            isinstance(target, Evidence)
            and verification.verification_kind is VerificationKind.INDEPENDENT
            and verification.status is VerificationStatus.PASS
        ):
            updated = replace(
                target,
                verification_status=VerificationStatus.PASS,
                updated_at=now,
                version=target.version + 1,
            )
            state.artifacts[target.evidence_id] = updated
            resulting_version = updated.version
        return MutationOutcome(
            target.lifecycle_state.value,
            target.version,
            target.lifecycle_state.value,
            resulting_version,
            resulting_version,
        )

    @staticmethod
    def __producer_of(item: Artifact) -> str:
        producer = getattr(item, "producer_principal_id", None)
        if isinstance(producer, str):
            return producer
        return item.provenance.creator_principal_id

    def __create_approval(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        session: Session,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, CreateApprovalPayload)
        approval = payload.approval
        self.__require_provenance(approval, command, session)
        if approval.approval_id in state.approvals or approval.approval_id in state.artifacts:
            raise DomainDenied("duplicate_approval")
        if not isinstance(state.principals.get(command.actor_principal_id), HumanIdentity):
            raise DomainDenied("approval_requires_human_identity")
        if approval.approver_principal_id != command.actor_principal_id:
            raise DomainDenied("forged_human_approval")
        if approval.task_id != command.task_scope:
            raise DomainDenied("approval_task_scope_mismatch")
        if approval.policy_version != state.policy_version:
            raise DomainDenied("approval_policy_mismatch")
        if approval.resource_id in PROTECTED_RESOURCES:
            raise DomainDenied("approval_cannot_override_global_deny")
        if approval.capability_id in {Capability.EXECUTION, Capability.POLICY_MODIFY}:
            raise DomainDenied("approval_cannot_manufacture_forbidden_capability")
        if approval.lifecycle_state is not ApprovalState.ACTIVE or approval.revoked_at is not None:
            raise DomainDenied("approval_must_start_active")
        if not approval.is_active(now):
            raise DomainDenied("approval_expired")
        if approval.candidate_id is not None:
            bound = state.artifacts.get(approval.candidate_id)
            if not isinstance(bound, KnowledgeCandidate):
                raise DomainDenied("approval_candidate_unknown")
        state.approvals[approval.approval_id] = approval
        state.artifacts[approval.approval_id] = approval
        return MutationOutcome(None, 0, ApprovalState.ACTIVE.value, 1, 1)

    @staticmethod
    def __revoke_approval(
        state: _GovernedState,
        command: CommandEnvelope,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, RevokeApprovalPayload)
        approval = state.approvals.get(payload.approval_id)
        if approval is None:
            raise DomainDenied("unknown_approval")
        if approval.task_id != command.task_scope:
            raise DomainDenied("approval_task_scope_mismatch")
        if approval.version != command.expected_state_version:
            raise DomainDenied("expected_state_version_mismatch")
        if approval.revoked_at is not None:
            raise DomainDenied("approval_already_revoked")
        updated = replace(
            approval,
            lifecycle_state=ApprovalState.REVOKED,
            revoked_at=now,
            updated_at=now,
            version=approval.version + 1,
        )
        state.approvals[approval.approval_id] = updated
        state.artifacts[approval.approval_id] = updated
        return MutationOutcome(
            ApprovalState.ACTIVE.value,
            approval.version,
            ApprovalState.REVOKED.value,
            updated.version,
            updated.version,
        )

    def __promote(
        self,
        state: _GovernedState,
        command: CommandEnvelope,
        now: datetime,
    ) -> MutationOutcome:
        payload = command.payload
        assert isinstance(payload, PromoteKnowledgePayload)
        if command.command_type is not KNOWLEDGE_PROMOTION_COMMAND:
            raise DomainDenied("promotion_command_type_mismatch")
        candidate = state.artifacts.get(payload.candidate_id)
        if not isinstance(candidate, KnowledgeCandidate):
            raise DomainDenied("unknown_knowledge_candidate")
        if candidate.version != command.expected_state_version:
            raise DomainDenied("expected_state_version_mismatch")
        if candidate.lifecycle_state is not KnowledgeState.VERIFIED:
            raise DomainDenied("candidate_not_verified")
        self.__require_candidate_verification(state, candidate, now)
        approval = state.approvals.get(payload.approval_id)
        if approval is None:
            raise DomainDenied("missing_required_approval")
        if not approval.is_active(now):
            raise DomainDenied(
                "approval_revoked"
                if approval.revoked_at is not None
                else "approval_expired"
            )
        if (
            approval.task_id != command.task_scope
            or approval.action != Operation.PROMOTE.value
            or approval.resource_id != command.resource_scope
            or approval.capability_id != command.capability_scope
            or approval.policy_version != command.policy_version
        ):
            raise DomainDenied("approval_scope_mismatch")
        if approval.candidate_id is None:
            raise DomainDenied("approval_missing_candidate_binding")
        if approval.candidate_id != candidate.candidate_id:
            raise DomainDenied("approval_candidate_mismatch")
        updated = replace(
            candidate,
            lifecycle_state=KnowledgeState.PROMOTED,
            updated_at=now,
            version=candidate.version + 1,
        )
        state.artifacts[candidate.candidate_id] = updated
        return MutationOutcome(
            candidate.lifecycle_state.value,
            candidate.version,
            updated.lifecycle_state.value,
            updated.version,
            updated.version,
        )

    def __require_candidate_verification(
        self,
        state: _GovernedState,
        candidate: KnowledgeCandidate,
        now: datetime,
    ) -> None:
        if not candidate.evidence_ids:
            raise DomainDenied("missing_required_evidence")
        for evidence_id in candidate.evidence_ids:
            evidence = state.artifacts.get(evidence_id)
            if not isinstance(evidence, Evidence):
                raise DomainDenied("unknown_evidence_reference")
            if not self.__evidence_eligible(state, evidence, now):
                raise DomainDenied("evidence_not_eligible_for_promotion")
        independent_pass = False
        for verification_id in candidate.verification_ids:
            verification = state.artifacts.get(verification_id)
            verifier = (
                state.principals.get(verification.verifier_principal_id)
                if isinstance(verification, VerificationRecord)
                else None
            )
            if (
                isinstance(verification, VerificationRecord)
                and verification.target_artifact_id == candidate.candidate_id
                and verification.verification_kind is VerificationKind.INDEPENDENT
                and verification.status is VerificationStatus.PASS
                and verification.verifier_principal_id
                != candidate.producer_principal_id
                and verifier is not None
                and verifier.status is IdentityStatus.ACTIVE
                and verifier.revoked_at is None
            ):
                independent_pass = True
        if not independent_pass:
            raise DomainDenied("missing_independent_verification")
        for item in state.artifacts.values():
            if (
                isinstance(item, ContradictionCase)
                and candidate.candidate_id in item.affects_candidate_ids
                and item.lifecycle_state
                in {
                    ContradictionState.OPEN,
                    ContradictionState.UNDER_INVESTIGATION,
                    ContradictionState.RETAINED_UNCERTAIN,
                }
            ):
                raise DomainDenied("unresolved_contradiction")

    @staticmethod
    def __evidence_eligible(
        state: _GovernedState,
        evidence: Evidence,
        now: datetime,
    ) -> bool:
        if not evidence.is_eligible_positive_support(now):
            return False
        return any(
            isinstance(record, VerificationRecord)
            and record.target_artifact_id == evidence.evidence_id
            and record.verification_kind is VerificationKind.INDEPENDENT
            and record.status is VerificationStatus.PASS
            and record.verifier_principal_id != evidence.producer_principal_id
            and record.verifier_principal_id in state.principals
            and state.principals[record.verifier_principal_id].status
            is IdentityStatus.ACTIVE
            and state.principals[record.verifier_principal_id].revoked_at is None
            for record in state.artifacts.values()
        )

    @staticmethod
    def __require_independent_verification(
        state: _GovernedState,
        item: Claim | Observation,
    ) -> None:
        producer = TrustedCommandBoundary.__producer_of(item)
        if not any(
            isinstance(record, VerificationRecord)
            and record.verification_id in item.verification_ids
            and record.target_artifact_id == artifact_id(item)
            and record.verification_kind is VerificationKind.INDEPENDENT
            and record.status is VerificationStatus.PASS
            and record.verifier_principal_id != producer
            and record.verifier_principal_id in state.principals
            and state.principals[record.verifier_principal_id].status
            is IdentityStatus.ACTIVE
            and state.principals[record.verifier_principal_id].revoked_at is None
            for record in state.artifacts.values()
        ):
            raise DomainDenied("missing_independent_verification")


CommandIngress = TrustedCommandBoundary


@dataclass(frozen=True)
class LocalControlPlane:
    tcb: TrustedCommandBoundary
    projections: ReadOnlyProjections
    local_operator_auth: LocalOperatorSessionStub
    operator: HumanIdentity
    system: SystemIdentity


def build_local_control_plane(
    *,
    clock: Clock,
    ids: IdFactory,
    failures: FailureInjector | None = None,
) -> LocalControlPlane:
    """Trusted bootstrap for the non-production local operator TCB."""
    now = clock.now()
    bootstrap_provenance = Provenance(
        creator_principal_id="principal.system-tcb",
        session_id="session.bootstrap",
        command_id="command.bootstrap",
        method="trusted_local_bootstrap",
    )
    system = SystemIdentity(
        principal_id="principal.system-tcb",
        identity_type=IdentityType.SYSTEM,
        display_name="Slice 2B TCB",
        status=IdentityStatus.ACTIVE,
        provenance=bootstrap_provenance,
        created_at=now,
        component="trusted-command-boundary",
    )
    operator = HumanIdentity(
        principal_id="principal.local-operator",
        identity_type=IdentityType.HUMAN,
        display_name="Local Operator Stub",
        status=IdentityStatus.ACTIVE,
        provenance=bootstrap_provenance,
        created_at=now,
        operator_scope="slice-2b-local-only",
    )
    state = _GovernedState(
        principals={
            system.principal_id: system,
            operator.principal_id: operator,
        }
    )
    seen: set[tuple[Capability, Operation, Resource]] = set()
    for command_type, policy in COMMAND_POLICIES.items():
        if command_type is CommandType.UPDATE_POLICY:
            continue
        key = (policy.capability, policy.operation, policy.resource)
        if key in seen:
            continue
        seen.add(key)
        grant = CapabilityGrant(
            grant_id=ids.new("grant"),
            principal_id=operator.principal_id,
            capability_id=policy.capability,
            operation=policy.operation,
            resource_id=policy.resource,
            task_id=None,
            issued_by_principal_id=system.principal_id,
            issued_at=now,
            expires_at=now + timedelta(hours=8),
            policy_version=POLICY_VERSION,
        )
        state.grants[grant.grant_id] = grant
    store, permit = _create_governed_store(state)
    sessions = LocalOperatorSessionStub(operator, clock=clock, ids=ids)
    tcb = TrustedCommandBoundary(
        store=store,
        permit=permit,
        sessions=sessions,
        clock=clock,
        ids=ids,
        failures=failures,
    )
    return LocalControlPlane(
        tcb=tcb,
        projections=ReadOnlyProjections(store.snapshot_for_projection),
        local_operator_auth=sessions,
        operator=operator,
        system=system,
    )
