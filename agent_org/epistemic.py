"""Typed epistemic contracts and explicit lifecycle rules.

Stored memory, confidence, recency, and audit inclusion never imply truth.
KnowledgeCandidate.PROMOTED is not a generic lifecycle edge.  The only
authority that may write it is CommandType.PROMOTE_KNOWLEDGE after the TCB
promotion gate succeeds.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from agent_org.contracts import (
    Capability,
    CommandType,
    Operation,
    Provenance,
    Resource,
    require_id,
    require_utc,
)


class SourceState(StrEnum):
    REGISTERED = "REGISTERED"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


class EvidenceState(StrEnum):
    REGISTERED = "REGISTERED"
    VALID = "VALID"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


class VerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerificationKind(StrEnum):
    INDEPENDENT = "INDEPENDENT"
    SELF_CHECK = "SELF_CHECK"


class ClaimState(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    CHALLENGED = "CHALLENGED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class HypothesisState(StrEnum):
    PROPOSED = "PROPOSED"
    TESTING = "TESTING"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SUPERSEDED = "SUPERSEDED"


class PredictionState(StrEnum):
    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    EXPIRED = "EXPIRED"


class ObservationState(StrEnum):
    RECORDED = "RECORDED"
    VERIFIED = "VERIFIED"
    INVALIDATED = "INVALIDATED"


class KnowledgeState(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CHALLENGED = "CHALLENGED"
    VERIFIED = "VERIFIED"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    SUPERSEDED = "SUPERSEDED"


class ContradictionState(StrEnum):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    RESOLVED = "RESOLVED"
    RETAINED_UNCERTAIN = "RETAINED_UNCERTAIN"


class ResearchMissionState(StrEnum):
    PROPOSED = "PROPOSED"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExperimentState(StrEnum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALIDATED = "INVALIDATED"


class ApprovalState(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class MemoryKind(StrEnum):
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    FAILURE = "FAILURE"
    HYPOTHESIS = "HYPOTHESIS"
    CAUSAL = "CAUSAL"
    PERFORMANCE = "PERFORMANCE"
    SELF_MODEL = "SELF_MODEL"


class MemoryState(StrEnum):
    CANDIDATE = "CANDIDATE"
    CHALLENGED = "CHALLENGED"
    PROMOTED = "PROMOTED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


def _validate_common(
    *,
    artifact_id: str,
    prefix: str,
    provenance: Provenance,
    created_at: datetime,
    updated_at: datetime,
    version: int,
    lineage: tuple[str, ...],
) -> None:
    require_id(artifact_id, prefix, "artifact_id")
    require_utc(created_at, "created_at")
    require_utc(updated_at, "updated_at")
    if updated_at < created_at:
        raise ValueError("updated_at cannot precede created_at")
    if version < 1:
        raise ValueError("artifact version must be positive")
    if len(set(lineage)) != len(lineage):
        raise ValueError("lineage cannot contain duplicates")
    if not isinstance(provenance, Provenance):
        raise ValueError("typed provenance is required")


@dataclass(frozen=True)
class Source:
    source_id: str
    source_type: str
    locator: str
    content_hash: str
    provenance: Provenance
    lifecycle_state: SourceState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.source_id,
            prefix="source.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        if not self.source_type or not self.locator or not self.content_hash:
            raise ValueError("source type, locator, and content_hash are required")


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_id: str
    producer_principal_id: str
    retrieval_timestamp: datetime
    observation_timestamp: datetime
    content_hash: str
    content_ref: str
    extraction_method: str
    validity_status: EvidenceState
    freshness_max_age_seconds: int
    expires_at: datetime
    assurance: int
    provenance: Provenance
    lifecycle_state: EvidenceState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    supersedes_evidence_id: str | None = None
    revoked_at: datetime | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.evidence_id,
            prefix="evidence.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.source_id, "source.", "source_id")
        require_id(self.producer_principal_id, "principal.", "producer_principal_id")
        require_utc(self.retrieval_timestamp, "retrieval_timestamp")
        require_utc(self.observation_timestamp, "observation_timestamp")
        require_utc(self.expires_at, "expires_at")
        if self.revoked_at is not None:
            require_utc(self.revoked_at, "revoked_at")
        if self.expires_at <= self.retrieval_timestamp:
            raise ValueError("evidence expiry must follow retrieval")
        if self.freshness_max_age_seconds <= 0:
            raise ValueError("freshness policy must be positive")
        if not 0 <= self.assurance <= 100:
            raise ValueError("assurance must be 0..100")
        if not self.content_hash or not self.content_ref or not self.extraction_method:
            raise ValueError("evidence content and extraction fields are required")
        if self.validity_status != self.lifecycle_state:
            raise ValueError("evidence validity_status and lifecycle_state must agree")
        if self.supersedes_evidence_id is not None:
            require_id(
                self.supersedes_evidence_id,
                "evidence.",
                "supersedes_evidence_id",
            )

    def is_eligible_positive_support(self, now: datetime) -> bool:
        require_utc(now, "now")
        age = (now - self.retrieval_timestamp).total_seconds()
        return (
            self.lifecycle_state is EvidenceState.VALID
            and self.validity_status is EvidenceState.VALID
            and self.revoked_at is None
            and now < self.expires_at
            and 0 <= age <= self.freshness_max_age_seconds
            and self.verification_status is VerificationStatus.PASS
        )


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    evidence_ids: tuple[str, ...]
    producer_principal_id: str
    provenance: Provenance
    lifecycle_state: ClaimState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    verification_ids: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.claim_id,
            prefix="claim.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.producer_principal_id, "principal.", "producer_principal_id")
        if not self.statement.strip() or not self.evidence_ids:
            raise ValueError("claim requires a statement and evidence")
        for value in self.evidence_ids:
            require_id(value, "evidence.", "evidence_id")
        for value in self.verification_ids:
            require_id(value, "verification.", "verification_id")


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str
    supporting_claim_ids: tuple[str, ...]
    falsification_criteria: tuple[str, ...]
    producer_principal_id: str
    provenance: Provenance
    lifecycle_state: HypothesisState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.hypothesis_id,
            prefix="hypothesis.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.producer_principal_id, "principal.", "producer_principal_id")
        if not self.statement or not self.falsification_criteria:
            raise ValueError("hypothesis requires statement and falsification criteria")
        for value in self.supporting_claim_ids:
            require_id(value, "claim.", "claim_id")


@dataclass(frozen=True)
class Prediction:
    prediction_id: str
    hypothesis_id: str
    expected_observation: str
    evaluation_deadline: datetime
    provenance: Provenance
    lifecycle_state: PredictionState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.prediction_id,
            prefix="prediction.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.hypothesis_id, "hypothesis.", "hypothesis_id")
        require_utc(self.evaluation_deadline, "evaluation_deadline")
        if not self.expected_observation:
            raise ValueError("prediction expected_observation is required")


@dataclass(frozen=True)
class Observation:
    """A measured value from an experiment run.

    D-09: carries an explicit producer principal (same pattern as Evidence)
    so an observation transported by the operator on behalf of an agent
    producer can receive a genuinely INDEPENDENT verification.  Without it,
    producer resolved to the registrar and self-verification was the only
    verification a single-session plane could construct.
    """

    observation_id: str
    experiment_run_id: str
    measured_value: str
    observation_method: str
    producer_principal_id: str
    provenance: Provenance
    lifecycle_state: ObservationState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    verification_ids: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.observation_id,
            prefix="observation.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.experiment_run_id, "experiment-run.", "experiment_run_id")
        require_id(self.producer_principal_id, "principal.", "producer_principal_id")
        if not self.measured_value or not self.observation_method:
            raise ValueError("observation value and method are required")
        for value in self.verification_ids:
            require_id(value, "verification.", "verification_id")


@dataclass(frozen=True)
class KnowledgeCandidate:
    candidate_id: str
    proposition: str
    producer_principal_id: str
    claim_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    verification_ids: tuple[str, ...]
    contradiction_ids: tuple[str, ...]
    provenance: Provenance
    lifecycle_state: KnowledgeState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.candidate_id,
            prefix="candidate.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.producer_principal_id, "principal.", "producer_principal_id")
        if not self.proposition or not self.claim_ids or not self.evidence_ids:
            raise ValueError("candidate requires proposition, claims, and evidence")
        for value in self.claim_ids:
            require_id(value, "claim.", "claim_id")
        for value in self.evidence_ids:
            require_id(value, "evidence.", "evidence_id")
        for value in self.verification_ids:
            require_id(value, "verification.", "verification_id")
        for value in self.contradiction_ids:
            require_id(value, "contradiction.", "contradiction_id")


@dataclass(frozen=True)
class ContradictionCase:
    contradiction_id: str
    left_artifact_id: str
    right_artifact_id: str
    rationale: str
    affects_candidate_ids: tuple[str, ...]
    provenance: Provenance
    lifecycle_state: ContradictionState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    resolution_evidence_ids: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.contradiction_id,
            prefix="contradiction.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        if self.left_artifact_id == self.right_artifact_id or not self.rationale:
            raise ValueError("contradiction requires distinct artifacts and rationale")
        for value in self.affects_candidate_ids:
            require_id(value, "candidate.", "candidate_id")
        for value in self.resolution_evidence_ids:
            require_id(value, "evidence.", "evidence_id")


@dataclass(frozen=True)
class ResearchMission:
    mission_id: str
    question: str
    unknowns: tuple[str, ...]
    hypothesis_ids: tuple[str, ...]
    required_evidence: tuple[str, ...]
    constraints: tuple[str, ...]
    allowed_methods: tuple[str, ...]
    assigned_agent_id: str
    authority_capabilities: tuple[Capability, ...]
    authority_resources: tuple[Resource, ...]
    expires_at: datetime
    deliverables: tuple[str, ...]
    verification_required: bool
    success_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    parent_mission_id: str | None
    causal_lineage: tuple[str, ...]
    provenance: Provenance
    lifecycle_state: ResearchMissionState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.mission_id,
            prefix="mission.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.assigned_agent_id, "principal.", "assigned_agent_id")
        require_utc(self.expires_at, "expires_at")
        if not all(
            (
                self.question,
                self.unknowns,
                self.required_evidence,
                self.constraints,
                self.allowed_methods,
                self.authority_capabilities,
                self.authority_resources,
                self.deliverables,
                self.success_criteria,
                self.failure_criteria,
            )
        ):
            raise ValueError("research mission requires explicit bounded fields")
        if self.parent_mission_id is not None:
            require_id(self.parent_mission_id, "mission.", "parent_mission_id")


@dataclass(frozen=True)
class ExperimentPlan:
    experiment_plan_id: str
    hypothesis_id: str
    method: str
    preconditions: tuple[str, ...]
    expected_observations: tuple[str, ...]
    reproducibility_requirements: tuple[str, ...]
    provenance: Provenance
    lifecycle_state: ExperimentState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.experiment_plan_id,
            prefix="experiment-plan.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.hypothesis_id, "hypothesis.", "hypothesis_id")
        if self.lifecycle_state is not ExperimentState.PLANNED:
            raise ValueError("experiment plan starts PLANNED")
        if not self.method or not self.preconditions or not self.expected_observations:
            raise ValueError("experiment plan requires method and expectations")


@dataclass(frozen=True)
class ExperimentRun:
    experiment_run_id: str
    experiment_plan_id: str
    outcome: str
    failure_class: str | None
    provenance: Provenance
    lifecycle_state: ExperimentState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    observation_ids: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.experiment_run_id,
            prefix="experiment-run.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.experiment_plan_id, "experiment-plan.", "experiment_plan_id")
        for value in self.observation_ids:
            require_id(value, "observation.", "observation_id")


@dataclass(frozen=True)
class VerificationRecord:
    verification_id: str
    target_artifact_id: str
    producer_principal_id: str
    verifier_principal_id: str
    verification_kind: VerificationKind
    status: VerificationStatus
    evidence_ids: tuple[str, ...]
    method: str
    provenance: Provenance
    lifecycle_state: VerificationStatus
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.verification_id,
            prefix="verification.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        require_id(self.producer_principal_id, "principal.", "producer_principal_id")
        require_id(self.verifier_principal_id, "principal.", "verifier_principal_id")
        if self.lifecycle_state != self.status:
            raise ValueError("verification lifecycle and status must agree")
        if not self.method or not self.evidence_ids:
            raise ValueError("verification requires method and evidence")
        for value in self.evidence_ids:
            require_id(value, "evidence.", "evidence_id")
        if self.target_artifact_id in self.evidence_ids:
            raise ValueError("verification cannot cite its target as its own support")
        if (
            self.verification_kind is VerificationKind.INDEPENDENT
            and self.producer_principal_id == self.verifier_principal_id
        ):
            raise ValueError("producer cannot independently verify own artifact")


@dataclass(frozen=True)
class Approval:
    """Scoped human approval artifact.

    Knowledge-promotion approvals bind to KnowledgeCandidate.candidate_id.
    Missing candidate_id is not a task-scoped wildcard. Generic
    TRANSITION_ARTIFACT cannot promote regardless of approval.
    """

    approval_id: str
    approver_principal_id: str
    task_id: str | None
    action: str | Operation
    resource_id: Resource
    capability_id: Capability
    policy_version: str
    issued_at: datetime
    expires_at: datetime
    provenance: Provenance
    lifecycle_state: ApprovalState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    candidate_id: str | None = None
    revoked_at: datetime | None = None
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.approval_id,
            prefix="approval.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        # D-20: the action is a typed Operation, not a free-form string.
        # Existing call sites that pass the enum's string value keep working
        # through this coercion; unknown strings fail closed at construction.
        try:
            coerced = Operation(self.action)
        except ValueError as exc:
            raise ValueError(
                f"approval action must be a known Operation, got {self.action!r}"
            ) from exc
        object.__setattr__(self, "action", coerced)
        require_id(self.approver_principal_id, "principal.", "approver_principal_id")
        if self.task_id is not None:
            require_id(self.task_id, "task.", "task_id")
        if self.candidate_id is not None:
            require_id(self.candidate_id, "candidate.", "candidate_id")
        require_utc(self.issued_at, "issued_at")
        require_utc(self.expires_at, "expires_at")
        if self.revoked_at is not None:
            require_utc(self.revoked_at, "revoked_at")
        if self.expires_at <= self.issued_at or not self.policy_version:
            raise ValueError("approval must be bounded and fully scoped")

    def is_active(self, now: datetime) -> bool:
        return (
            self.lifecycle_state is ApprovalState.ACTIVE
            and self.revoked_at is None
            and self.issued_at <= now < self.expires_at
        )


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    memory_kind: MemoryKind
    subject: str
    content_ref: str
    evidence_ids: tuple[str, ...]
    assurance: int
    provenance: Provenance
    lifecycle_state: MemoryState
    created_at: datetime
    updated_at: datetime
    lineage: tuple[str, ...] = ()
    supersedes_memory_id: str | None = None
    failure_outcome: str | None = None
    version: int = 1

    def __post_init__(self) -> None:
        _validate_common(
            artifact_id=self.memory_id,
            prefix="memory.",
            provenance=self.provenance,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            lineage=self.lineage,
        )
        if not self.subject or not self.content_ref or not self.evidence_ids:
            raise ValueError("memory requires subject, content, and evidence")
        if not 0 <= self.assurance <= 100:
            raise ValueError("memory assurance must be 0..100")
        for value in self.evidence_ids:
            require_id(value, "evidence.", "evidence_id")
        if self.supersedes_memory_id is not None:
            require_id(self.supersedes_memory_id, "memory.", "supersedes_memory_id")


Artifact = (
    Source
    | Evidence
    | Claim
    | Hypothesis
    | Prediction
    | Observation
    | KnowledgeCandidate
    | ContradictionCase
    | ResearchMission
    | ExperimentPlan
    | ExperimentRun
    | VerificationRecord
    | Approval
    | MemoryRecord
)


def artifact_id(artifact: Artifact) -> str:
    by_type = (
        (Source, "source_id"),
        (Evidence, "evidence_id"),
        (Claim, "claim_id"),
        (Hypothesis, "hypothesis_id"),
        (Prediction, "prediction_id"),
        (Observation, "observation_id"),
        (KnowledgeCandidate, "candidate_id"),
        (ContradictionCase, "contradiction_id"),
        (ResearchMission, "mission_id"),
        (ExperimentPlan, "experiment_plan_id"),
        (ExperimentRun, "experiment_run_id"),
        (VerificationRecord, "verification_id"),
        (Approval, "approval_id"),
        (MemoryRecord, "memory_id"),
    )
    for kind, field in by_type:
        if isinstance(artifact, kind):
            return getattr(artifact, field)
    raise TypeError(f"unsupported artifact type: {type(artifact)!r}")


_LEGAL_ARTIFACT_TRANSITIONS: dict[type[Any], dict[StrEnum, frozenset[StrEnum]]] = {
    Source: {
        SourceState.REGISTERED: frozenset({SourceState.SUPERSEDED, SourceState.REVOKED}),
        SourceState.SUPERSEDED: frozenset(),
        SourceState.REVOKED: frozenset(),
    },
    Evidence: {
        EvidenceState.REGISTERED: frozenset(
            {
                EvidenceState.VALID,
                EvidenceState.STALE,
                EvidenceState.SUPERSEDED,
                EvidenceState.REVOKED,
            }
        ),
        EvidenceState.VALID: frozenset(
            {EvidenceState.STALE, EvidenceState.SUPERSEDED, EvidenceState.REVOKED}
        ),
        EvidenceState.STALE: frozenset(
            {EvidenceState.SUPERSEDED, EvidenceState.REVOKED}
        ),
        EvidenceState.SUPERSEDED: frozenset(),
        EvidenceState.REVOKED: frozenset(),
    },
    Claim: {
        ClaimState.DRAFT: frozenset({ClaimState.SUBMITTED, ClaimState.REJECTED}),
        # D-05: same discipline as KnowledgeCandidate -- SUBMITTED must be
        # challenged before it can be declared VERIFIED.
        ClaimState.SUBMITTED: frozenset(
            {ClaimState.CHALLENGED, ClaimState.REJECTED}
        ),
        ClaimState.CHALLENGED: frozenset(
            {ClaimState.VERIFIED, ClaimState.REJECTED, ClaimState.SUPERSEDED}
        ),
        ClaimState.VERIFIED: frozenset({ClaimState.SUPERSEDED}),
        ClaimState.REJECTED: frozenset(),
        ClaimState.SUPERSEDED: frozenset(),
    },
    Hypothesis: {
        HypothesisState.PROPOSED: frozenset(
            {HypothesisState.TESTING, HypothesisState.SUPERSEDED}
        ),
        HypothesisState.TESTING: frozenset(
            {
                HypothesisState.SUPPORTED,
                HypothesisState.REFUTED,
                HypothesisState.INCONCLUSIVE,
                HypothesisState.SUPERSEDED,
            }
        ),
        HypothesisState.SUPPORTED: frozenset({HypothesisState.SUPERSEDED}),
        HypothesisState.REFUTED: frozenset({HypothesisState.SUPERSEDED}),
        HypothesisState.INCONCLUSIVE: frozenset(
            {HypothesisState.TESTING, HypothesisState.SUPERSEDED}
        ),
        HypothesisState.SUPERSEDED: frozenset(),
    },
    Prediction: {
        PredictionState.PROPOSED: frozenset(
            {
                PredictionState.CONFIRMED,
                PredictionState.REFUTED,
                PredictionState.EXPIRED,
            }
        ),
        PredictionState.CONFIRMED: frozenset(),
        PredictionState.REFUTED: frozenset(),
        PredictionState.EXPIRED: frozenset(),
    },
    Observation: {
        ObservationState.RECORDED: frozenset(
            {ObservationState.VERIFIED, ObservationState.INVALIDATED}
        ),
        ObservationState.VERIFIED: frozenset({ObservationState.INVALIDATED}),
        ObservationState.INVALIDATED: frozenset(),
    },
    KnowledgeCandidate: {
        KnowledgeState.SUBMITTED: frozenset(
            {KnowledgeState.UNDER_REVIEW, KnowledgeState.REJECTED, KnowledgeState.DEFERRED}
        ),
        KnowledgeState.UNDER_REVIEW: frozenset(
            {
                KnowledgeState.CHALLENGED,
                KnowledgeState.REJECTED,
                KnowledgeState.DEFERRED,
            }
        ),
        KnowledgeState.CHALLENGED: frozenset(
            {
                KnowledgeState.UNDER_REVIEW,
                KnowledgeState.VERIFIED,
                KnowledgeState.REJECTED,
                KnowledgeState.DEFERRED,
            }
        ),
        KnowledgeState.VERIFIED: frozenset(
            {
                KnowledgeState.CHALLENGED,
                KnowledgeState.REJECTED,
                KnowledgeState.DEFERRED,
            }
        ),
        KnowledgeState.PROMOTED: frozenset({KnowledgeState.SUPERSEDED}),
        KnowledgeState.REJECTED: frozenset(),
        KnowledgeState.DEFERRED: frozenset({KnowledgeState.UNDER_REVIEW}),
        KnowledgeState.SUPERSEDED: frozenset(),
    },
    ContradictionCase: {
        ContradictionState.OPEN: frozenset(
            {
                ContradictionState.UNDER_INVESTIGATION,
                ContradictionState.RESOLVED,
                ContradictionState.RETAINED_UNCERTAIN,
            }
        ),
        ContradictionState.UNDER_INVESTIGATION: frozenset(
            {ContradictionState.RESOLVED, ContradictionState.RETAINED_UNCERTAIN}
        ),
        ContradictionState.RESOLVED: frozenset(),
        ContradictionState.RETAINED_UNCERTAIN: frozenset(
            {ContradictionState.UNDER_INVESTIGATION, ContradictionState.RESOLVED}
        ),
    },
    ResearchMission: {
        ResearchMissionState.PROPOSED: frozenset(
            {ResearchMissionState.AUTHORIZED, ResearchMissionState.CANCELLED}
        ),
        ResearchMissionState.AUTHORIZED: frozenset(
            {
                ResearchMissionState.RUNNING,
                ResearchMissionState.BLOCKED,
                ResearchMissionState.CANCELLED,
            }
        ),
        ResearchMissionState.RUNNING: frozenset(
            {
                ResearchMissionState.BLOCKED,
                ResearchMissionState.COMPLETED,
                ResearchMissionState.FAILED,
                ResearchMissionState.CANCELLED,
            }
        ),
        ResearchMissionState.BLOCKED: frozenset(
            {
                ResearchMissionState.AUTHORIZED,
                ResearchMissionState.RUNNING,
                ResearchMissionState.FAILED,
                ResearchMissionState.CANCELLED,
            }
        ),
        ResearchMissionState.COMPLETED: frozenset(),
        ResearchMissionState.FAILED: frozenset(),
        ResearchMissionState.CANCELLED: frozenset(),
    },
    ExperimentRun: {
        ExperimentState.PLANNED: frozenset(
            {ExperimentState.RUNNING, ExperimentState.INVALIDATED}
        ),
        ExperimentState.RUNNING: frozenset(
            {
                ExperimentState.COMPLETED,
                ExperimentState.FAILED,
                ExperimentState.INCONCLUSIVE,
                ExperimentState.INVALIDATED,
            }
        ),
        ExperimentState.COMPLETED: frozenset({ExperimentState.INVALIDATED}),
        ExperimentState.FAILED: frozenset({ExperimentState.INVALIDATED}),
        ExperimentState.INCONCLUSIVE: frozenset({ExperimentState.INVALIDATED}),
        ExperimentState.INVALIDATED: frozenset(),
    },
    MemoryRecord: {
        # D-11: no generic edge may name PROMOTED.  Memory must never
        # automatically become TCB-authoritative knowledge (spec section 26);
        # a table permitting what the TCB denies is policy split-brain.
        # The PROMOTED state remains in the enum (a future dedicated command
        # may govern it) but is unreachable via TRANSITION_ARTIFACT.
        MemoryState.CANDIDATE: frozenset(
            {MemoryState.CHALLENGED, MemoryState.REJECTED}
        ),
        MemoryState.CHALLENGED: frozenset(
            {MemoryState.REJECTED, MemoryState.SUPERSEDED}
        ),
        MemoryState.PROMOTED: frozenset({MemoryState.SUPERSEDED}),
        MemoryState.SUPERSEDED: frozenset(),
        MemoryState.REJECTED: frozenset(),
    },
}


# Authoritative knowledge-promotion policy.  There is exactly one:
# KnowledgeCandidate reaches KnowledgeState.PROMOTED only via
# CommandType.PROMOTE_KNOWLEDGE after the TCB promotion gate.  Generic
# TRANSITION_ARTIFACT is structurally forbidden from writing that state.
KNOWLEDGE_PROMOTION_STATES: frozenset[KnowledgeState] = frozenset(
    {KnowledgeState.PROMOTED}
)
KNOWLEDGE_PROMOTION_COMMAND: CommandType = CommandType.PROMOTE_KNOWLEDGE
KNOWLEDGE_PROMOTION_DENIED_REASON = "knowledge_promotion_requires_dedicated_command"


def is_knowledge_promotion_state(target: object) -> bool:
    """True iff *target* denotes KnowledgeCandidate promotion.

    Membership is taken from the typed KnowledgeState enum, including
    StrEnum string-equality aliases, so a bare ``"PROMOTED"`` value cannot
    bypass the generic-transition prohibition.
    """
    return any(
        state in KNOWLEDGE_PROMOTION_STATES and target == state
        for state in KnowledgeState
    )


def refuse_generic_knowledge_promotion(artifact: Artifact, target: object) -> None:
    """Raise if a generic lifecycle helper would write a promotion state."""
    if isinstance(artifact, KnowledgeCandidate) and is_knowledge_promotion_state(
        target
    ):
        raise ValueError(KNOWLEDGE_PROMOTION_DENIED_REASON)


def _freeze_artifact_transitions(
    table: dict[type[Any], dict[StrEnum, frozenset[StrEnum]]],
) -> Mapping[type[Any], Mapping[StrEnum, frozenset[StrEnum]]]:
    knowledge_rules = table.get(KnowledgeCandidate, {})
    for targets in knowledge_rules.values():
        if any(is_knowledge_promotion_state(target) for target in targets):
            raise RuntimeError(
                "LEGAL_ARTIFACT_TRANSITIONS must not allow KnowledgeCandidate "
                "promotion; only KNOWLEDGE_PROMOTION_COMMAND may write "
                "KNOWLEDGE_PROMOTION_STATES"
            )
    return MappingProxyType(
        {
            artifact_type: MappingProxyType(dict(states))
            for artifact_type, states in table.items()
        }
    )


LEGAL_ARTIFACT_TRANSITIONS = _freeze_artifact_transitions(_LEGAL_ARTIFACT_TRANSITIONS)


def transition_artifact(artifact: Artifact, target: StrEnum, now: datetime) -> Artifact:
    """Pure generic transition; caller must commit through the TCB.

    This helper is not a promotion authority.  KnowledgeCandidate promotion
    states are refused here so a future caller cannot treat the generic
    lifecycle map as a promotion mechanism.
    """
    refuse_generic_knowledge_promotion(artifact, target)
    rules = LEGAL_ARTIFACT_TRANSITIONS.get(type(artifact))
    if rules is None:
        raise ValueError(f"artifact type has no transition lifecycle: {type(artifact).__name__}")
    current = artifact.lifecycle_state
    if target not in rules.get(current, frozenset()):
        raise ValueError(f"illegal epistemic transition {current}->{target}")
    changes: dict[str, Any] = {
        "lifecycle_state": target,
        "updated_at": now,
        "version": artifact.version + 1,
    }
    if isinstance(artifact, Evidence):
        changes["validity_status"] = target
        if target is EvidenceState.REVOKED:
            changes["revoked_at"] = now
    return replace(artifact, **changes)
