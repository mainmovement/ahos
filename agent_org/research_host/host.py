"""Trusted mediator: research facade -> validated CommandEnvelope -> TCB.submit.

The agent receives only the facade. It does not receive sessions, grants,
approvals, TCB internals, or a general identity API.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import Any, Callable

from agent_org.commands import (
    CommandEnvelope,
    CreateContradictionPayload,
    CreateTaskPayload,
    DelegateAuthorityPayload,
    RegisterAgentPayload,
    RegisterArtifactPayload,
    TransitionArtifactPayload,
    TransitionTaskPayload,
)
from agent_org.contracts import (
    Capability,
    CommandType,
    DERIVE_AUTHORITY_AT_TCB,
    GovernedTask,
    IdentityStatus,
    IdentityType,
    POLICY_VERSION,
    PROTECTED_RESOURCES,
    Provenance,
    Resource,
    TaskState,
)
from agent_org.epistemic import (
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
    Observation,
    ObservationState,
    Prediction,
    PredictionState,
    ResearchMission,
    ResearchMissionState,
    Source,
    SourceState,
    artifact_id,
)
from agent_org.governance import COMMAND_POLICIES
from agent_org.identity import AgentIdentity, Session
from agent_org.research_host.contracts import (
    ALLOWED_MISSION_INTENT_RESOURCES,
    ALLOWED_RESEARCH_CAPABILITIES,
    API_BOUNDARY,
    FORBIDDEN_RESEARCH_CAPABILITIES,
    NETWORK_LOCATOR_PREFIXES,
    PROCESS_ISOLATION_PROVIDED,
    RESEARCH_PRINCIPAL_ID,
    RESEARCH_PRINCIPAL_ROLE,
    SAME_PROCESS_RESIDUAL,
    SAME_PROCESS_RUNTIME,
    HostAuditRecord,
    HostDecision,
    HostResult,
    OperationClass,
    ResearchAgentContext,
    RuntimeClassification,
    allow,
    deny,
)
from agent_org.research_host.workspace import (
    ResearchWorkspace,
    WorkspaceDenied,
    research_sandbox_root,
)
from agent_org.tcb import LocalControlPlane


_RESEARCH_ARTIFACT_TYPES = (
    Source,
    Evidence,
    Claim,
    Hypothesis,
    Prediction,
    Observation,
    KnowledgeCandidate,
    ContradictionCase,
    ResearchMission,
    ExperimentPlan,
    ExperimentRun,
)


def _locator_denied(locator: str) -> str | None:
    lowered = locator.strip().lower()
    for prefix in NETWORK_LOCATOR_PREFIXES:
        if lowered.startswith(prefix):
            return "network_locator_denied"
    if lowered.startswith(("socket:", "dns:", "mailto:")):
        return "network_locator_denied"
    return None


def _hash_ok(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())


class _Mediator:
    def __init__(
        self,
        *,
        plane: LocalControlPlane,
        session: Session,
        workspace: ResearchWorkspace,
        context: ResearchAgentContext,
        research_task_id: str,
        clock: Callable[[], datetime],
        ids: Callable[[str], str],
    ) -> None:
        self.__plane = plane
        self.__session = session
        self.__workspace = workspace
        self.__context = context
        self.__research_task_id = research_task_id
        self.__clock = clock
        self.__ids = ids
        self.__audit: list[HostAuditRecord] = []
        self.__lock = RLock()

    @property
    def context(self) -> ResearchAgentContext:
        return self.__context

    def audit_records(self) -> tuple[HostAuditRecord, ...]:
        with self.__lock:
            return tuple(self.__audit)

    def runtime_classification(self) -> RuntimeClassification:
        return RuntimeClassification(
            api_boundary=API_BOUNDARY,
            process_isolation=PROCESS_ISOLATION_PROVIDED,
            same_process_runtime=SAME_PROCESS_RUNTIME,
            same_process_residual=SAME_PROCESS_RESIDUAL,
            agent_one_implemented=False,
            network_provided=False,
            ahos_connected=False,
        )

    def operator_expose_file(self, relative_path: str, content: str) -> str:
        return self.__workspace.operator_write(relative_path, content)

    def _record(
        self,
        result: HostResult,
        *,
        correlation_id: str,
        command: str = "N/A",
    ) -> HostResult:
        record = HostAuditRecord(
            research_agent_context=self.__context.context_id,
            operation=result.operation,
            resource=result.resource,
            command=command if result.command_id is None else result.command_id,
            result=result.decision.value,
            timestamp=self.__clock(),
            correlation_id=correlation_id,
            reason=result.reason,
            classification=result.classification.value,
        )
        self.__audit.append(record)
        if result.correlation_id is None:
            result = replace(result, correlation_id=correlation_id)
        return result

    def _closed(self, operation: str, classification: OperationClass, reason: str) -> HostResult:
        correlation_id = self.__ids("correlation")
        return self._record(
            deny(operation, classification, reason, correlation_id=correlation_id),
            correlation_id=correlation_id,
        )

    def _submit_artifact(self, operation: str, factory: Callable[[str, Provenance], Any]) -> HostResult:
        correlation_id = self.__ids("correlation")
        with self.__lock:
            command_id = self.__ids("command")
            now = self.__clock()
            provenance = Provenance(
                creator_principal_id=self.__plane.operator.principal_id,
                session_id=self.__session.session_id,
                command_id=command_id,
                method="research-host-mediated",
            )
            try:
                artifact = factory(command_id, provenance)
            except (ValueError, TypeError) as exc:
                return self._record(
                    deny(
                        operation,
                        OperationClass.RESEARCH_WRITE,
                        f"artifact_construction_rejected:{exc}",
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                )
            envelope = self._envelope(
                CommandType.REGISTER_ARTIFACT,
                RegisterArtifactPayload(artifact),
                command_id=command_id,
                correlation_id=correlation_id,
                task_scope=self.__research_task_id,
                issued_at=now,
            )
            tcb_result = self.__plane.tcb.submit(envelope, self.__session)
            if not tcb_result.accepted:
                return self._record(
                    deny(
                        operation,
                        OperationClass.RESEARCH_WRITE,
                        tcb_result.reason,
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                    command=command_id,
                )
            copied = deepcopy(self.__plane.projections.artifact(artifact_id(artifact)))
            return self._record(
                allow(
                    operation,
                    OperationClass.RESEARCH_WRITE,
                    "research_write_accepted",
                    resource="EPISTEMIC_STORE",
                    command_id=command_id,
                    correlation_id=correlation_id,
                    artifact_id=artifact_id(artifact),
                    payload=copied,
                ),
                correlation_id=correlation_id,
                command=command_id,
            )

    def _envelope(
        self,
        command_type: CommandType,
        payload: Any,
        *,
        command_id: str,
        correlation_id: str,
        task_scope: str | None,
        issued_at: datetime,
        expected_state_version: int = 0,
        evidence_lineage: tuple[str, ...] = (),
    ) -> CommandEnvelope:
        policy = COMMAND_POLICIES[command_type]
        return CommandEnvelope(
            command_id=command_id,
            command_type=command_type,
            actor_principal_id=self.__plane.operator.principal_id,
            session_id=self.__session.session_id,
            authority_context_ref=DERIVE_AUTHORITY_AT_TCB,
            task_scope=task_scope,
            resource_scope=policy.resource,
            capability_scope=policy.capability,
            requested_operation=policy.operation,
            policy_version=POLICY_VERSION,
            causation_id=None,
            correlation_id=correlation_id,
            parent_command_id=None,
            evidence_lineage=evidence_lineage,
            expected_state_version=expected_state_version,
            payload=payload,
            issued_at=issued_at,
        )

    def read_context(self) -> HostResult:
        correlation_id = self.__ids("correlation")
        payload = {
            "research_agent_context": deepcopy(self.__context),
            "runtime": self.runtime_classification(),
            "allowed_capabilities": tuple(sorted(c.value for c in ALLOWED_RESEARCH_CAPABILITIES)),
            "forbidden_capabilities": tuple(
                sorted(c.value for c in FORBIDDEN_RESEARCH_CAPABILITIES)
            ),
            "workspace_artifacts": self.__workspace.list_supplied(),
            "mission_authority_note": "RESEARCH_MISSION_IS_NOT_AN_AUTHORITY_GRANT",
            "identity_note": "RESEARCH_AGENT_CONTEXT_IS_NOT_HUMAN_IDENTITY",
        }
        return self._record(
            allow(
                "read_context",
                OperationClass.READ,
                "projection_copy",
                resource="RESEARCH_CONTEXT",
                correlation_id=correlation_id,
                payload=payload,
            ),
            correlation_id=correlation_id,
        )

    def read_epistemic_state(self) -> HostResult:
        correlation_id = self.__ids("correlation")
        items = tuple(
            deepcopy(item)
            for item in self.__plane.projections.epistemic_objects()
            if isinstance(item, _RESEARCH_ARTIFACT_TYPES)
        )
        missions = tuple(
            deepcopy(item) for item in self.__plane.projections.research_missions()
        )
        payload = {
            "artifacts": items,
            "missions": missions,
            "mutable": False,
            "authoritative": False,
        }
        return self._record(
            allow(
                "read_epistemic_state",
                OperationClass.READ,
                "projection_copy",
                resource="EPISTEMIC_STORE",
                correlation_id=correlation_id,
                payload=payload,
            ),
            correlation_id=correlation_id,
        )

    def read_supplied_artifact(self, relative_path: str) -> HostResult:
        correlation_id = self.__ids("correlation")
        try:
            content = self.__workspace.read_supplied(relative_path)
        except WorkspaceDenied as exc:
            return self._record(
                deny(
                    "read_supplied_artifact",
                    OperationClass.READ,
                    str(exc),
                    resource="RESEARCH_WORKSPACE",
                    correlation_id=correlation_id,
                ),
                correlation_id=correlation_id,
            )
        return self._record(
            allow(
                "read_supplied_artifact",
                OperationClass.READ,
                "workspace_read",
                resource="RESEARCH_WORKSPACE",
                correlation_id=correlation_id,
                payload=content,
            ),
            correlation_id=correlation_id,
        )

    def create_mission(
        self,
        *,
        question: str,
        unknowns: tuple[str, ...],
        hypothesis_ids: tuple[str, ...],
        required_evidence: tuple[str, ...],
        constraints: tuple[str, ...],
        allowed_methods: tuple[str, ...],
        authority_capabilities: tuple[Capability, ...] = (Capability.EPISTEMIC_WRITE,),
        authority_resources: tuple[Resource, ...] = (Resource.EPISTEMIC_STORE,),
        deliverables: tuple[str, ...],
        success_criteria: tuple[str, ...],
        failure_criteria: tuple[str, ...],
        expires_in_seconds: int = 3600,
        parent_mission_id: str | None = None,
        causal_lineage: tuple[str, ...] = ("cause.research-host",),
    ) -> HostResult:
        if set(authority_capabilities) & FORBIDDEN_RESEARCH_CAPABILITIES:
            return self._closed(
                "create_mission",
                OperationClass.RESEARCH_WRITE,
                "research_mission_forbidden_capability_intent",
            )
        if set(authority_resources) & PROTECTED_RESOURCES:
            return self._closed(
                "create_mission",
                OperationClass.RESEARCH_WRITE,
                "protected_resource_declaration_denied",
            )
        if not set(authority_capabilities).issubset(ALLOWED_RESEARCH_CAPABILITIES):
            return self._closed(
                "create_mission",
                OperationClass.RESEARCH_WRITE,
                "research_mission_unknown_capability_intent",
            )
        if not set(authority_resources).issubset(ALLOWED_MISSION_INTENT_RESOURCES):
            return self._closed(
                "create_mission",
                OperationClass.RESEARCH_WRITE,
                "research_mission_resource_is_not_authority",
            )

        def factory(command_id: str, provenance: Provenance) -> ResearchMission:
            now = self.__clock()
            return ResearchMission(
                mission_id=self.__ids("mission"),
                question=question,
                unknowns=unknowns,
                hypothesis_ids=hypothesis_ids,
                required_evidence=required_evidence,
                constraints=constraints,
                allowed_methods=allowed_methods,
                assigned_agent_id=self.__context.principal_id,
                authority_capabilities=authority_capabilities,
                authority_resources=authority_resources,
                expires_at=now + timedelta(seconds=expires_in_seconds),
                deliverables=deliverables,
                verification_required=True,
                success_criteria=success_criteria,
                failure_criteria=failure_criteria,
                parent_mission_id=parent_mission_id,
                causal_lineage=causal_lineage,
                provenance=provenance,
                lifecycle_state=ResearchMissionState.PROPOSED,
                created_at=now,
                updated_at=now,
            )

        grants = self.__plane.projections.capability_status(self.__context.principal_id)
        if grants.grants or grants.delegations:
            return self._closed(
                "create_mission",
                OperationClass.GOVERNANCE,
                "mission_must_not_create_grants",
            )
        return self._submit_artifact("create_mission", factory)

    def record_source(self, *, source_type: str, locator: str, content_hash: str) -> HostResult:
        blocked = _locator_denied(locator)
        if blocked:
            return self._closed("record_source", OperationClass.EXECUTION, blocked)
        if not _hash_ok(content_hash):
            return self._closed(
                "record_source", OperationClass.RESEARCH_WRITE, "content_hash_invalid"
            )

        def factory(command_id: str, provenance: Provenance) -> Source:
            now = self.__clock()
            return Source(
                source_id=self.__ids("source"),
                source_type=source_type,
                locator=locator,
                content_hash=content_hash.lower(),
                provenance=provenance,
                lifecycle_state=SourceState.REGISTERED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("record_source", factory)

    def record_evidence(
        self,
        *,
        source_id: str,
        content_hash: str,
        content_ref: str,
        extraction_method: str = "host-supplied-artifact",
        assurance: int = 50,
        freshness_max_age_seconds: int = 600,
    ) -> HostResult:
        blocked = _locator_denied(content_ref)
        if blocked:
            return self._closed("record_evidence", OperationClass.EXECUTION, blocked)
        if not _hash_ok(content_hash):
            return self._closed(
                "record_evidence", OperationClass.RESEARCH_WRITE, "content_hash_invalid"
            )

        def factory(command_id: str, provenance: Provenance) -> Evidence:
            now = self.__clock()
            return Evidence(
                evidence_id=self.__ids("evidence"),
                source_id=source_id,
                producer_principal_id=self.__context.principal_id,
                retrieval_timestamp=now,
                observation_timestamp=now,
                content_hash=content_hash.lower(),
                content_ref=content_ref,
                extraction_method=extraction_method,
                validity_status=EvidenceState.REGISTERED,
                freshness_max_age_seconds=freshness_max_age_seconds,
                expires_at=now + timedelta(seconds=freshness_max_age_seconds),
                assurance=assurance,
                provenance=provenance,
                lifecycle_state=EvidenceState.REGISTERED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("record_evidence", factory)

    def create_claim(self, *, statement: str, evidence_ids: tuple[str, ...]) -> HostResult:
        def factory(command_id: str, provenance: Provenance) -> Claim:
            now = self.__clock()
            return Claim(
                claim_id=self.__ids("claim"),
                statement=statement,
                evidence_ids=evidence_ids,
                producer_principal_id=self.__context.principal_id,
                provenance=provenance,
                lifecycle_state=ClaimState.DRAFT,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("create_claim", factory)

    def create_hypothesis(
        self,
        *,
        statement: str,
        falsification_criteria: tuple[str, ...],
        supporting_claim_ids: tuple[str, ...] = (),
    ) -> HostResult:
        def factory(command_id: str, provenance: Provenance) -> Hypothesis:
            now = self.__clock()
            return Hypothesis(
                hypothesis_id=self.__ids("hypothesis"),
                statement=statement,
                supporting_claim_ids=supporting_claim_ids,
                falsification_criteria=falsification_criteria,
                producer_principal_id=self.__context.principal_id,
                provenance=provenance,
                lifecycle_state=HypothesisState.PROPOSED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("create_hypothesis", factory)

    def create_prediction(
        self,
        *,
        hypothesis_id: str,
        expected_observation: str,
        evaluation_deadline_seconds: int = 3600,
    ) -> HostResult:
        def factory(command_id: str, provenance: Provenance) -> Prediction:
            now = self.__clock()
            return Prediction(
                prediction_id=self.__ids("prediction"),
                hypothesis_id=hypothesis_id,
                expected_observation=expected_observation,
                evaluation_deadline=now + timedelta(seconds=evaluation_deadline_seconds),
                provenance=provenance,
                lifecycle_state=PredictionState.PROPOSED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("create_prediction", factory)

    def propose_experiment(
        self,
        *,
        hypothesis_id: str,
        method: str,
        preconditions: tuple[str, ...],
        expected_observations: tuple[str, ...],
        reproducibility_requirements: tuple[str, ...] = ("offline deterministic replay",),
    ) -> HostResult:
        def factory(command_id: str, provenance: Provenance) -> ExperimentPlan:
            now = self.__clock()
            return ExperimentPlan(
                experiment_plan_id=self.__ids("experiment-plan"),
                hypothesis_id=hypothesis_id,
                method=method,
                preconditions=preconditions,
                expected_observations=expected_observations,
                reproducibility_requirements=reproducibility_requirements,
                provenance=provenance,
                lifecycle_state=ExperimentState.PLANNED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("propose_experiment", factory)

    def record_experiment_result(
        self,
        *,
        experiment_plan_id: str,
        outcome: str,
        failure_class: str | None = None,
    ) -> HostResult:
        def factory(command_id: str, provenance: Provenance) -> ExperimentRun:
            now = self.__clock()
            return ExperimentRun(
                experiment_run_id=self.__ids("experiment-run"),
                experiment_plan_id=experiment_plan_id,
                outcome=outcome,
                failure_class=failure_class,
                provenance=provenance,
                lifecycle_state=ExperimentState.PLANNED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("record_experiment_result", factory)

    def record_observation(
        self,
        *,
        experiment_run_id: str,
        measured_value: str,
        observation_method: str,
    ) -> HostResult:
        def factory(command_id: str, provenance: Provenance) -> Observation:
            now = self.__clock()
            return Observation(
                observation_id=self.__ids("observation"),
                experiment_run_id=experiment_run_id,
                measured_value=measured_value,
                observation_method=observation_method,
                provenance=provenance,
                lifecycle_state=ObservationState.RECORDED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("record_observation", factory)

    def create_candidate(
        self,
        *,
        proposition: str,
        claim_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
    ) -> HostResult:
        def factory(command_id: str, provenance: Provenance) -> KnowledgeCandidate:
            now = self.__clock()
            return KnowledgeCandidate(
                candidate_id=self.__ids("candidate"),
                proposition=proposition,
                producer_principal_id=self.__context.principal_id,
                claim_ids=claim_ids,
                evidence_ids=evidence_ids,
                verification_ids=(),
                contradiction_ids=(),
                provenance=provenance,
                lifecycle_state=KnowledgeState.SUBMITTED,
                created_at=now,
                updated_at=now,
            )

        return self._submit_artifact("create_candidate", factory)

    def record_contradiction(
        self,
        *,
        left_artifact_id: str,
        right_artifact_id: str,
        rationale: str,
        candidate_id: str,
    ) -> HostResult:
        correlation_id = self.__ids("correlation")
        with self.__lock:
            candidate = self.__plane.projections.artifact(candidate_id)
            if not isinstance(candidate, KnowledgeCandidate):
                return self._record(
                    deny(
                        "record_contradiction",
                        OperationClass.RESEARCH_WRITE,
                        "contradiction_candidate_unknown",
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                )
            command_id = self.__ids("command")
            now = self.__clock()
            provenance = Provenance(
                creator_principal_id=self.__plane.operator.principal_id,
                session_id=self.__session.session_id,
                command_id=command_id,
                method="research-host-mediated",
            )
            try:
                contradiction = ContradictionCase(
                    contradiction_id=self.__ids("contradiction"),
                    left_artifact_id=left_artifact_id,
                    right_artifact_id=right_artifact_id,
                    rationale=rationale,
                    affects_candidate_ids=(candidate_id,),
                    provenance=provenance,
                    lifecycle_state=ContradictionState.OPEN,
                    created_at=now,
                    updated_at=now,
                )
            except ValueError as exc:
                return self._record(
                    deny(
                        "record_contradiction",
                        OperationClass.RESEARCH_WRITE,
                        f"artifact_construction_rejected:{exc}",
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                )
            envelope = self._envelope(
                CommandType.CREATE_CONTRADICTION,
                CreateContradictionPayload(contradiction),
                command_id=command_id,
                correlation_id=correlation_id,
                task_scope=self.__research_task_id,
                issued_at=now,
                expected_state_version=candidate.version,
            )
            tcb_result = self.__plane.tcb.submit(envelope, self.__session)
            if not tcb_result.accepted:
                return self._record(
                    deny(
                        "record_contradiction",
                        OperationClass.RESEARCH_WRITE,
                        tcb_result.reason,
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                    command=command_id,
                )
            copied = deepcopy(
                self.__plane.projections.artifact(contradiction.contradiction_id)
            )
            return self._record(
                allow(
                    "record_contradiction",
                    OperationClass.RESEARCH_WRITE,
                    "research_write_accepted",
                    resource="EPISTEMIC_STORE",
                    command_id=command_id,
                    correlation_id=correlation_id,
                    artifact_id=contradiction.contradiction_id,
                    payload=copied,
                ),
                correlation_id=correlation_id,
                command=command_id,
            )

    def request_review(self, *, candidate_id: str) -> HostResult:
        correlation_id = self.__ids("correlation")
        with self.__lock:
            item = self.__plane.projections.artifact(candidate_id)
            if not isinstance(item, KnowledgeCandidate):
                return self._record(
                    deny(
                        "request_review",
                        OperationClass.RESEARCH_WRITE,
                        "unknown_candidate",
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                )
            if item.lifecycle_state is KnowledgeState.PROMOTED:
                return self._record(
                    deny(
                        "request_review",
                        OperationClass.GOVERNANCE,
                        "promotion_is_not_review",
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                )
            command_id = self.__ids("command")
            envelope = self._envelope(
                CommandType.TRANSITION_ARTIFACT,
                TransitionArtifactPayload(
                    artifact_id=candidate_id,
                    target_state=KnowledgeState.UNDER_REVIEW,
                ),
                command_id=command_id,
                correlation_id=correlation_id,
                task_scope=self.__research_task_id,
                issued_at=self.__clock(),
                expected_state_version=item.version,
            )
            tcb_result = self.__plane.tcb.submit(envelope, self.__session)
            if not tcb_result.accepted:
                return self._record(
                    deny(
                        "request_review",
                        OperationClass.RESEARCH_WRITE,
                        tcb_result.reason,
                        resource="EPISTEMIC_STORE",
                        correlation_id=correlation_id,
                    ),
                    correlation_id=correlation_id,
                    command=command_id,
                )
            copied = deepcopy(self.__plane.projections.artifact(candidate_id))
            return self._record(
                allow(
                    "request_review",
                    OperationClass.RESEARCH_WRITE,
                    "review_requested_not_promoted",
                    resource="EPISTEMIC_STORE",
                    command_id=command_id,
                    correlation_id=correlation_id,
                    artifact_id=candidate_id,
                    payload=copied,
                ),
                correlation_id=correlation_id,
                command=command_id,
            )

    def promote_knowledge(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "promote_knowledge", OperationClass.GOVERNANCE, "promotion_firewall_denied"
        )

    def issue_approval(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "issue_approval", OperationClass.GOVERNANCE, "approval_issuance_denied"
        )

    def record_independent_verification(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "record_independent_verification",
            OperationClass.GOVERNANCE,
            "verification_firewall_denied",
        )

    def create_principal(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "create_principal", OperationClass.GOVERNANCE, "identity_creation_denied"
        )

    def create_session(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "create_session", OperationClass.GOVERNANCE, "agent_session_issuance_denied"
        )

    def delegate_authority(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "delegate_authority", OperationClass.GOVERNANCE, "authority_delegation_denied"
        )

    def update_policy(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "update_policy", OperationClass.GOVERNANCE, "policy_modification_denied"
        )

    def request_execution(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_execution", OperationClass.EXECUTION, "execution_capability_denied"
        )

    def request_network(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_network", OperationClass.EXECUTION, "network_denied"
        )

    def request_ahos_access(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_ahos_access", OperationClass.EXECUTION, "ahos_firewall_denied"
        )

    def request_credential_access(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_credential_access",
            OperationClass.EXECUTION,
            "credential_access_denied",
        )

    def request_environment_secret(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_environment_secret",
            OperationClass.EXECUTION,
            "environment_secret_denied",
        )

    def request_eval(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_eval", OperationClass.EXECUTION, "dynamic_code_denied"
        )

    def request_exec(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_exec", OperationClass.EXECUTION, "dynamic_code_denied"
        )

    def request_compile(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_compile", OperationClass.EXECUTION, "dynamic_code_denied"
        )

    def request_importlib(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_importlib", OperationClass.EXECUTION, "dynamic_code_denied"
        )

    def request_subprocess(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_subprocess", OperationClass.EXECUTION, "subprocess_denied"
        )

    def request_powershell(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_powershell", OperationClass.EXECUTION, "shell_execution_denied"
        )

    def request_cmd(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_cmd", OperationClass.EXECUTION, "shell_execution_denied"
        )

    def request_tcb_submit(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_tcb_submit", OperationClass.GOVERNANCE, "tcb_internals_denied"
        )

    def request_store_access(self, *_args: Any, **_kwargs: Any) -> HostResult:
        return self._closed(
            "request_store_access", OperationClass.GOVERNANCE, "internal_store_denied"
        )


def _make_facade(mediator: _Mediator) -> Any:
    class ResearchFacade:
        __slots__ = ()

        def __getattribute__(self, name: str) -> Any:
            if name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
                raise AttributeError("private_attribute_denied")
            return object.__getattribute__(self, name)

        def __setattr__(self, name: str, value: Any) -> None:
            raise AttributeError("research_facade_is_immutable")

        def __delattr__(self, name: str) -> None:
            raise AttributeError("research_facade_is_immutable")

        def read_context(self) -> HostResult:
            return mediator.read_context()

        def read_epistemic_state(self) -> HostResult:
            return mediator.read_epistemic_state()

        def read_supplied_artifact(self, relative_path: str) -> HostResult:
            return mediator.read_supplied_artifact(relative_path)

        def create_mission(self, **kwargs: Any) -> HostResult:
            return mediator.create_mission(**kwargs)

        def record_source(self, **kwargs: Any) -> HostResult:
            return mediator.record_source(**kwargs)

        def record_evidence(self, **kwargs: Any) -> HostResult:
            return mediator.record_evidence(**kwargs)

        def create_claim(self, **kwargs: Any) -> HostResult:
            return mediator.create_claim(**kwargs)

        def create_hypothesis(self, **kwargs: Any) -> HostResult:
            return mediator.create_hypothesis(**kwargs)

        def create_prediction(self, **kwargs: Any) -> HostResult:
            return mediator.create_prediction(**kwargs)

        def record_observation(self, **kwargs: Any) -> HostResult:
            return mediator.record_observation(**kwargs)

        def record_contradiction(self, **kwargs: Any) -> HostResult:
            return mediator.record_contradiction(**kwargs)

        def propose_experiment(self, **kwargs: Any) -> HostResult:
            return mediator.propose_experiment(**kwargs)

        def record_experiment_result(self, **kwargs: Any) -> HostResult:
            return mediator.record_experiment_result(**kwargs)

        def create_candidate(self, **kwargs: Any) -> HostResult:
            return mediator.create_candidate(**kwargs)

        def request_review(self, **kwargs: Any) -> HostResult:
            return mediator.request_review(**kwargs)

        def promote_knowledge(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.promote_knowledge(*args, **kwargs)

        def issue_approval(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.issue_approval(*args, **kwargs)

        def record_independent_verification(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.record_independent_verification(*args, **kwargs)

        def create_principal(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.create_principal(*args, **kwargs)

        def create_session(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.create_session(*args, **kwargs)

        def delegate_authority(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.delegate_authority(*args, **kwargs)

        def update_policy(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.update_policy(*args, **kwargs)

        def request_execution(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_execution(*args, **kwargs)

        def request_network(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_network(*args, **kwargs)

        def request_ahos_access(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_ahos_access(*args, **kwargs)

        def request_credential_access(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_credential_access(*args, **kwargs)

        def request_environment_secret(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_environment_secret(*args, **kwargs)

        def request_eval(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_eval(*args, **kwargs)

        def request_exec(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_exec(*args, **kwargs)

        def request_compile(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_compile(*args, **kwargs)

        def request_importlib(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_importlib(*args, **kwargs)

        def request_subprocess(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_subprocess(*args, **kwargs)

        def request_powershell(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_powershell(*args, **kwargs)

        def request_cmd(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_cmd(*args, **kwargs)

        def request_tcb_submit(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_tcb_submit(*args, **kwargs)

        def request_store_access(self, *args: Any, **kwargs: Any) -> HostResult:
            return mediator.request_store_access(*args, **kwargs)

    return ResearchFacade()


def _bootstrap_research_identity(
    plane: LocalControlPlane,
    session: Session,
    ids: Callable[[str], str],
    clock: Callable[[], datetime],
) -> None:
    command_id = ids("command")
    now = clock()
    identity = AgentIdentity(
        principal_id=RESEARCH_PRINCIPAL_ID,
        identity_type=IdentityType.AGENT,
        display_name=(
            "RESEARCH_AGENT_CONTEXT (not human identity, not production authority)"
        ),
        status=IdentityStatus.ACTIVE,
        provenance=Provenance(
            creator_principal_id=plane.operator.principal_id,
            session_id=session.session_id,
            command_id=command_id,
            method="research-host-bootstrap",
        ),
        created_at=now,
        role=RESEARCH_PRINCIPAL_ROLE,
    )
    envelope = CommandEnvelope(
        command_id=command_id,
        command_type=CommandType.REGISTER_AGENT,
        actor_principal_id=plane.operator.principal_id,
        session_id=session.session_id,
        authority_context_ref=DERIVE_AUTHORITY_AT_TCB,
        task_scope=None,
        resource_scope=COMMAND_POLICIES[CommandType.REGISTER_AGENT].resource,
        capability_scope=COMMAND_POLICIES[CommandType.REGISTER_AGENT].capability,
        requested_operation=COMMAND_POLICIES[CommandType.REGISTER_AGENT].operation,
        policy_version=POLICY_VERSION,
        causation_id=None,
        correlation_id=ids("correlation"),
        parent_command_id=None,
        evidence_lineage=(),
        expected_state_version=0,
        payload=RegisterAgentPayload(identity),
        issued_at=now,
    )
    result = plane.tcb.submit(envelope, session)
    if not result.accepted:
        raise RuntimeError(f"research host bootstrap identity failed: {result.reason}")


def _operator_command(
    plane: LocalControlPlane,
    session: Session,
    ids: Callable[[str], str],
    clock: Callable[[], datetime],
    command_type: CommandType,
    payload: Any,
    *,
    task_scope: str | None = None,
    expected_state_version: int = 0,
) -> None:
    policy = COMMAND_POLICIES[command_type]
    envelope = CommandEnvelope(
        command_id=ids("command"),
        command_type=command_type,
        actor_principal_id=plane.operator.principal_id,
        session_id=session.session_id,
        authority_context_ref=DERIVE_AUTHORITY_AT_TCB,
        task_scope=task_scope,
        resource_scope=policy.resource,
        capability_scope=policy.capability,
        requested_operation=policy.operation,
        policy_version=POLICY_VERSION,
        causation_id=None,
        correlation_id=ids("correlation"),
        parent_command_id=None,
        evidence_lineage=(),
        expected_state_version=expected_state_version,
        payload=payload,
        issued_at=clock(),
    )
    result = plane.tcb.submit(envelope, session)
    if not result.accepted:
        raise RuntimeError(f"research host bootstrap failed ({command_type}): {result.reason}")


def _bootstrap_research_task(
    plane: LocalControlPlane,
    session: Session,
    ids: Callable[[str], str],
    clock: Callable[[], datetime],
) -> str:
    now = clock()
    task = GovernedTask(
        task_id=ids("task"),
        owner_principal_id=plane.operator.principal_id,
        state=TaskState.PROPOSED,
        capability_scope=(
            Capability.TASK_MANAGE,
            Capability.EPISTEMIC_WRITE,
            Capability.EPISTEMIC_CHALLENGE,
        ),
        resource_scope=(Resource.TASK_STORE, Resource.EPISTEMIC_STORE),
        created_at=now,
        updated_at=now,
    )
    _operator_command(
        plane, session, ids, clock, CommandType.CREATE_TASK, CreateTaskPayload(task)
    )
    parent = next(
        grant
        for grant in plane.projections.capability_status(plane.operator.principal_id).grants
        if grant.task_id is None
        and grant.capability_id is Capability.TASK_MANAGE
        and grant.operation is COMMAND_POLICIES[CommandType.TRANSITION_TASK].operation
        and grant.resource_id is Resource.TASK_STORE
        and grant.revoked_at is None
    )
    child = replace(
        parent,
        grant_id=ids("grant"),
        task_id=task.task_id,
        issued_by_principal_id=plane.operator.principal_id,
        issued_at=now,
        parent_grant_id=parent.grant_id,
        delegation_depth=1,
    )
    _operator_command(
        plane,
        session,
        ids,
        clock,
        CommandType.DELEGATE_AUTHORITY,
        DelegateAuthorityPayload(child),
    )
    _operator_command(
        plane,
        session,
        ids,
        clock,
        CommandType.TRANSITION_TASK,
        TransitionTaskPayload(task_id=task.task_id, target_state=TaskState.AUTHORIZED.value),
        task_scope=task.task_id,
        expected_state_version=task.version,
    )
    for command_type in (
        CommandType.REGISTER_ARTIFACT,
        CommandType.TRANSITION_ARTIFACT,
        CommandType.CREATE_CONTRADICTION,
    ):
        policy = COMMAND_POLICIES[command_type]
        root = next(
            grant
            for grant in plane.projections.capability_status(
                plane.operator.principal_id
            ).grants
            if grant.task_id is None
            and grant.capability_id is policy.capability
            and grant.operation is policy.operation
            and grant.resource_id is policy.resource
            and grant.revoked_at is None
        )
        delegated = replace(
            root,
            grant_id=ids("grant"),
            task_id=task.task_id,
            issued_by_principal_id=plane.operator.principal_id,
            issued_at=clock(),
            parent_grant_id=root.grant_id,
            delegation_depth=1,
        )
        _operator_command(
            plane,
            session,
            ids,
            clock,
            CommandType.DELEGATE_AUTHORITY,
            DelegateAuthorityPayload(delegated),
        )
    research_grants = plane.projections.capability_status(RESEARCH_PRINCIPAL_ID)
    if research_grants.grants or research_grants.delegations:
        raise RuntimeError("research principal must not receive capability grants")
    return task.task_id


class ResearchAgentHost:
    """Operator-held host. Give cognitive code only facade(), never this object."""

    __slots__ = ("__mediator", "__facade")

    def __init__(self, mediator: _Mediator) -> None:
        object.__setattr__(self, "_ResearchAgentHost__mediator", mediator)
        object.__setattr__(self, "_ResearchAgentHost__facade", _make_facade(mediator))

    def facade(self) -> Any:
        return self.__facade

    def invoke(self, cognitive_fn: Callable[[Any], Any]) -> Any:
        if isinstance(cognitive_fn, str) or not callable(cognitive_fn):
            raise TypeError("SAME_PROCESS_RUNTIME does not execute generated code strings")
        return cognitive_fn(self.__facade)

    def audit_records(self) -> tuple[HostAuditRecord, ...]:
        return self.__mediator.audit_records()

    def runtime_classification(self) -> RuntimeClassification:
        return self.__mediator.runtime_classification()

    def expose_supplied_artifact(self, relative_path: str, content: str) -> str:
        return self.__mediator.operator_expose_file(relative_path, content)

    def context(self) -> ResearchAgentContext:
        return self.__mediator.context


def build_research_agent_host(
    *,
    plane: LocalControlPlane,
    session: Session,
    clock: Callable[[], datetime],
    ids: Callable[[str], str],
    workspace_root: Path | None = None,
) -> ResearchAgentHost:
    _bootstrap_research_identity(plane, session, ids, clock)
    task_id = _bootstrap_research_task(plane, session, ids, clock)
    root = workspace_root or research_sandbox_root(Path(__file__))
    mediator = _Mediator(
        plane=plane,
        session=session,
        workspace=ResearchWorkspace(root),
        context=ResearchAgentContext(
            context_id="research-context.local-cognitive",
            principal_id=RESEARCH_PRINCIPAL_ID,
        ),
        research_task_id=task_id,
        clock=clock,
        ids=ids,
    )
    return ResearchAgentHost(mediator)
