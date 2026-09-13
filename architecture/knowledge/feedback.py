#!/usr/bin/env python3
"""Human Feedback Foundation — W3 signal contract.

Human feedback is evidence about a human judgment of the system.
It is not automatic truth about the market, and it is not authority.

Do not import this module from the operational daemon package or the pipeline.
Do not persist, train, calibrate, or trade from this module.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping

FEEDBACK_VERSION = "human-feedback-contract-v1"
EPISTEMIC_FEEDBACK_SIGNAL = "FEEDBACK_SIGNAL"

CONSUMER_CONTRACT = (
    "Human feedback is a signal, not automatic truth. "
    "Consumers must inspect feedback type, value, subject, epistemic status, "
    "provenance, conflicts, timestamp semantics, actor class, and "
    "canonical-versus-operational identity. "
    "Do not treat value alone as decision authority. "
    "CORRECT is not FACTUAL. INCORRECT is not SYSTEM_INVALID."
)


class FeedbackType(str, Enum):
    CONFIRMATION = "CONFIRMATION"
    CORRECTION = "CORRECTION"
    DISAGREEMENT = "DISAGREEMENT"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    MISSED_SIGNAL = "MISSED_SIGNAL"
    SECURITY_CONCERN = "SECURITY_CONCERN"
    IDENTITY_CORRECTION = "IDENTITY_CORRECTION"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    DECISION_QUALITY = "DECISION_QUALITY"
    ALERT_QUALITY = "ALERT_QUALITY"
    OBSERVATION_QUALITY = "OBSERVATION_QUALITY"
    SYSTEM_BEHAVIOR = "SYSTEM_BEHAVIOR"
    OTHER = "OTHER"


class FeedbackValue(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    UNCERTAIN = "UNCERTAIN"
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    UNKNOWN = "UNKNOWN"


class ActorClass(str, Enum):
    HUMAN = "HUMAN"
    OPERATOR = "OPERATOR"
    REVIEWER = "REVIEWER"
    UNKNOWN = "UNKNOWN"


class SubjectKind(str, Enum):
    CANONICAL_TOKEN = "CANONICAL_TOKEN"
    OPERATIONAL_TOKEN = "OPERATIONAL_TOKEN"
    UNVALIDATED_TOKEN = "UNVALIDATED_TOKEN"
    DISPLAY = "DISPLAY"
    ALIAS = "ALIAS"
    ALERT = "ALERT"
    DECISION = "DECISION"
    OBSERVATION = "OBSERVATION"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    SYSTEM = "SYSTEM"
    UNKNOWN = "UNKNOWN"


class CorrectionClass(str, Enum):
    CONFIRMATION = "CONFIRMATION"
    CORRECTION = "CORRECTION"
    DISAGREEMENT = "DISAGREEMENT"
    NONE = "NONE"


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_value(value[k]) for k in value})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(v) for v in value)
    try:
        return deepcopy(value)
    except Exception:
        return MappingProxyType({
            "untrusted": True,
            "value_type": type(value).__name__,
            "note": "non-deepcopyable object discarded; not authoritative",
        })


def _freeze_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_value(value[k]) for k in value})
    return MappingProxyType({})


def _deep_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_plain(value[k]) for k in value}
    if isinstance(value, (list, tuple)):
        return [_deep_plain(v) for v in value]
    return value


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        raw = value.value
        text = str(raw).strip() if raw is not None else ""
        return text or None
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def _enum_member(enum_cls: type[Enum], value: Any, default: Enum) -> Enum:
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    text = _text(value)
    if text is None:
        return default
    try:
        return enum_cls(text)
    except ValueError:
        return default


def _local_id(*parts: str | None) -> str:
    cleaned = []
    for part in parts:
        text = part.strip() if isinstance(part, str) else _text(part)
        if text:
            cleaned.append(text.replace("|", "/"))
    return "feedback:" + "|".join(cleaned) if cleaned else "feedback:empty"


def _correction_class(feedback_type: FeedbackType, supplied: Any) -> CorrectionClass:
    if supplied is not None:
        return _enum_member(CorrectionClass, supplied, CorrectionClass.NONE)  # type: ignore[return-value]
    if feedback_type is FeedbackType.CONFIRMATION:
        return CorrectionClass.CONFIRMATION
    if feedback_type in {FeedbackType.CORRECTION, FeedbackType.IDENTITY_CORRECTION}:
        return CorrectionClass.CORRECTION
    if feedback_type in {
        FeedbackType.DISAGREEMENT,
        FeedbackType.FALSE_POSITIVE,
        FeedbackType.FALSE_NEGATIVE,
    }:
        return CorrectionClass.DISAGREEMENT
    return CorrectionClass.NONE


@dataclass(frozen=True)
class SubjectRef:
    kind: SubjectKind
    value: str | None
    identity_state: str | None
    canonical: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "value": self.value,
            "identity_state": self.identity_state,
            "canonical": self.canonical,
        }


def _subject(
    subject_id: Any,
    subject_kind: Any,
    identity_state: Any,
) -> tuple[SubjectRef, tuple[str, ...]]:
    unknowns: list[str] = []
    raw_id = _text(subject_id)
    raw_kind = _enum_member(SubjectKind, subject_kind, SubjectKind.UNKNOWN)
    ident = _text(identity_state)
    requested_canonical = raw_kind is SubjectKind.CANONICAL_TOKEN
    allowed = (
        requested_canonical
        and ident == "VERIFIED"
        and raw_id is not None
        and raw_kind is SubjectKind.CANONICAL_TOKEN
    )
    if requested_canonical and not allowed:
        kind = SubjectKind.UNVALIDATED_TOKEN if raw_id else SubjectKind.UNKNOWN
        if ident is None:
            unknowns.append("identity_state")
        if ident not in {None, "VERIFIED"}:
            unknowns.append("canonical_identity_not_authorized")
        if raw_id is None:
            unknowns.append("subject_id")
        return SubjectRef(kind=kind, value=raw_id, identity_state=ident, canonical=False), tuple(unknowns)
    if raw_kind in {SubjectKind.DISPLAY, SubjectKind.ALIAS, SubjectKind.UNVALIDATED_TOKEN, SubjectKind.OPERATIONAL_TOKEN}:
        return SubjectRef(kind=raw_kind, value=raw_id, identity_state=ident, canonical=False), tuple(unknowns)
    if raw_id is None and raw_kind is SubjectKind.UNKNOWN:
        unknowns.append("subject")
        return SubjectRef(kind=SubjectKind.UNKNOWN, value=None, identity_state=ident, canonical=False), tuple(unknowns)
    return SubjectRef(kind=raw_kind, value=raw_id, identity_state=ident, canonical=allowed), tuple(unknowns)


@dataclass(frozen=True)
class FeedbackSignal:
    """Immutable human-feedback signal. Not authority and not world truth."""

    feedback_id: str
    feedback_type: FeedbackType
    value: FeedbackValue
    epistemic_status: str
    subject: SubjectRef
    rationale: str | None
    actor_class: ActorClass
    actor_id: str | None
    timestamp: float | None
    referenced_ids: Mapping[str, Any]
    provenance: Mapping[str, Any] | None
    confidence: float | None
    correction_class: CorrectionClass
    expected_outcome: str | None
    observed_outcome: str | None
    authoritative_state: Mapping[str, Any]
    unknowns: tuple[str, ...]
    conflicts: tuple[str, ...]
    metadata: Mapping[str, Any]
    consumer_contract: str = CONSUMER_CONTRACT
    composer_version: str = FEEDBACK_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "feedback_type": self.feedback_type.value,
            "value": self.value.value,
            "epistemic_status": self.epistemic_status,
            "subject": self.subject.as_dict(),
            "rationale": self.rationale,
            "actor_class": self.actor_class.value,
            "actor_id": self.actor_id,
            "timestamp": self.timestamp,
            "referenced_ids": _deep_plain(self.referenced_ids),
            "provenance": _deep_plain(self.provenance) if self.provenance is not None else None,
            "confidence": self.confidence,
            "correction_class": self.correction_class.value,
            "expected_outcome": self.expected_outcome,
            "observed_outcome": self.observed_outcome,
            "authoritative_state": _deep_plain(self.authoritative_state),
            "unknowns": list(self.unknowns),
            "conflicts": list(self.conflicts),
            "metadata": _deep_plain(self.metadata),
            "consumer_contract": self.consumer_contract,
            "composer_version": self.composer_version,
        }


def compose_feedback_signal(
    feedback_type: Any = None,
    value: Any = None,
    *,
    subject_id: Any = None,
    subject_kind: Any = None,
    identity_state: Any = None,
    rationale: Any = None,
    actor_class: Any = None,
    actor_id: Any = None,
    timestamp: Any = None,
    referenced_ids: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    confidence: Any = None,
    correction_class: Any = None,
    expected_outcome: Any = None,
    observed_outcome: Any = None,
    metadata: Mapping[str, Any] | None = None,
    authoritative_state: Mapping[str, Any] | None = None,
) -> FeedbackSignal:
    """Compose an immutable feedback signal. Does not invent time, IDs, or truth."""
    ftype = _enum_member(FeedbackType, feedback_type, FeedbackType.OTHER)
    fvalue = _enum_member(FeedbackValue, value, FeedbackValue.UNKNOWN)
    actor = _enum_member(ActorClass, actor_class, ActorClass.UNKNOWN)
    subject, subject_unknowns = _subject(subject_id, subject_kind, identity_state)
    unknowns = list(subject_unknowns)
    if feedback_type is None:
        unknowns.append("feedback_type")
    if value is None:
        unknowns.append("value")
    if timestamp is None:
        unknowns.append("timestamp")
    if provenance is None:
        unknowns.append("provenance")

    ts: float | None
    if timestamp is None:
        ts = None
    elif isinstance(timestamp, bool):
        ts = None
        unknowns.append("timestamp_invalid")
    elif isinstance(timestamp, (int, float)):
        ts = float(timestamp)
    else:
        ts = None
        unknowns.append("timestamp_invalid")

    conf: float | None
    if confidence is None:
        conf = None
    elif isinstance(confidence, bool):
        conf = None
        unknowns.append("confidence_invalid")
    elif isinstance(confidence, (int, float)):
        conf = float(confidence)
    else:
        conf = None
        unknowns.append("confidence_invalid")

    auth = _freeze_mapping(authoritative_state or {})
    conflicts: list[str] = []
    decision = _text(auth.get("decision_outcome")) if auth else None
    security = _text(auth.get("security_state")) if auth else None
    ident_auth = _text(auth.get("identity_state")) if auth else None
    if decision is not None and ftype in {FeedbackType.DISAGREEMENT, FeedbackType.FALSE_POSITIVE, FeedbackType.CORRECTION}:
        conflicts.append(f"feedback_disagrees_with_authoritative:decision={decision}")
    if security is not None and ftype is FeedbackType.SECURITY_CONCERN:
        conflicts.append(f"feedback_security_concern_against:security={security}")
    if ident_auth is not None and ftype is FeedbackType.IDENTITY_CORRECTION:
        conflicts.append(f"feedback_identity_correction_against:identity={ident_auth}")

    refs = _freeze_mapping(referenced_ids or {})
    prov = _freeze_mapping(provenance) if provenance is not None else None
    meta = _freeze_mapping(metadata or {})
    fid = _local_id(
        ftype.value,
        fvalue.value,
        subject.kind.value,
        subject.value,
        actor.value,
        _text(actor_id),
        _text(rationale),
        None if ts is None else str(ts),
    )
    return FeedbackSignal(
        feedback_id=fid,
        feedback_type=ftype,
        value=fvalue,
        epistemic_status=EPISTEMIC_FEEDBACK_SIGNAL,
        subject=subject,
        rationale=_text(rationale),
        actor_class=actor,
        actor_id=_text(actor_id),
        timestamp=ts,
        referenced_ids=refs,
        provenance=prov,
        confidence=conf,
        correction_class=_correction_class(ftype, correction_class),
        expected_outcome=_text(expected_outcome),
        observed_outcome=_text(observed_outcome),
        authoritative_state=auth,
        unknowns=tuple(unknowns),
        conflicts=tuple(conflicts),
        metadata=meta,
    )


create_feedback = compose_feedback_signal


@dataclass(frozen=True)
class FeedbackAggregate:
    count: int
    by_type: Mapping[str, int]
    by_value: Mapping[str, int]
    by_subject: Mapping[str, int]
    disagreements: tuple[str, ...]
    repeated_corrections: tuple[str, ...]
    unknowns: tuple[str, ...]
    consumer_contract: str = CONSUMER_CONTRACT
    composer_version: str = FEEDBACK_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "by_type": dict(self.by_type),
            "by_value": dict(self.by_value),
            "by_subject": dict(self.by_subject),
            "disagreements": list(self.disagreements),
            "repeated_corrections": list(self.repeated_corrections),
            "unknowns": list(self.unknowns),
            "consumer_contract": self.consumer_contract,
            "composer_version": self.composer_version,
        }


def _subject_key(signal: FeedbackSignal) -> str:
    return f"{signal.subject.kind.value}:{signal.subject.value or 'unknown'}"


def aggregate_feedback(signals: Iterable[FeedbackSignal] | None) -> FeedbackAggregate:
    """Analytical summary only. Does not score, weigh, train, or decide."""
    items = tuple(signals or ())
    type_counts = Counter(s.feedback_type.value for s in items)
    value_counts = Counter(s.value.value for s in items)
    subject_counts = Counter(_subject_key(s) for s in items)
    by_subject_values: dict[str, set[str]] = {}
    correction_subjects: Counter[str] = Counter()
    for signal in items:
        key = _subject_key(signal)
        by_subject_values.setdefault(key, set()).add(signal.value.value)
        if signal.correction_class is CorrectionClass.CORRECTION:
            correction_subjects[key] += 1
    disagreements = tuple(
        sorted(
            f"subject_feedback_disagreement:{key}:values={','.join(sorted(vals))}"
            for key, vals in by_subject_values.items()
            if len(vals) > 1
        )
    )
    repeated = tuple(
        sorted(f"repeated_correction:{key}:count={n}" for key, n in correction_subjects.items() if n > 1)
    )
    unknowns = ("feedback" if not items else ())
    return FeedbackAggregate(
        count=len(items),
        by_type=_freeze_mapping(dict(sorted(type_counts.items()))),
        by_value=_freeze_mapping(dict(sorted(value_counts.items()))),
        by_subject=_freeze_mapping(dict(sorted(subject_counts.items()))),
        disagreements=disagreements,
        repeated_corrections=repeated,
        unknowns=unknowns,
    )
