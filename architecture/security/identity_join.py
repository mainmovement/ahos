#!/usr/bin/env python3
"""W4 Slice 6 — security identity attachment boundary.

Read-only consumer of the existing W4 join classifier. Not an identity
authority and not a resolver.

IdentityResolution
        ↓
classify_canonical_join()
        ↓
canonical security attachment (TOKEN subject only)

A security result may be canonically attached to a token only when the
classifier returns CANONICAL_JOIN and the subject kind is TOKEN.
token_id strings, symbols, names, pools, provider IDs, fallbacks,
lowercased Solana keys, and forged wrappers are never authority.

Do not persist, migrate, or rewrite historical security rows from here.
Do not change security veto / eligibility evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from architecture.identity.join import JoinClass, classify_canonical_join
from architecture.identity.types import IdentityResolution, IdentityState

ATTACHMENT_VERSION = "security-identity-join-v1"

CONSUMER_CONTRACT = (
    "Canonical token security attachment requires an existing "
    "IdentityResolution that classify_canonical_join classifies as "
    "CANONICAL_JOIN and an explicit TOKEN subject kind. "
    "Security evaluation (PASS/REJECT/INCOMPLETE/STALE) is independent "
    "of attachment. Identity failure never becomes a positive security "
    "conclusion and never upgrades a veto."
)

_TOKEN_SUBJECT = "TOKEN"


class SecuritySubjectKind(str, Enum):
    TOKEN = "TOKEN"
    POOL = "POOL"
    DEPLOYER = "DEPLOYER"
    HOLDER = "HOLDER"
    CONTRACT = "CONTRACT"
    LIQUIDITY_PAIR = "LIQUIDITY_PAIR"
    PROVIDER_OBSERVATION = "PROVIDER_OBSERVATION"


_KNOWN_SUBJECTS = frozenset(kind.value for kind in SecuritySubjectKind)
_NON_TOKEN_SUBJECTS = _KNOWN_SUBJECTS - {_TOKEN_SUBJECT}


class SecurityAttachmentOutcome(str, Enum):
    CANONICAL = "CANONICAL"
    UNLINKED = "UNLINKED"
    REJECTED = "REJECTED"
    SUBJECT_SCOPED = "SUBJECT_SCOPED"


@dataclass(frozen=True)
class SecurityAttachment:
    outcome: str
    subject_kind: str | None
    canonical_token_id: str | None
    observed_chain: str | None
    observed_address: str | None
    identity_state: str | None
    join_class: str | None
    reason: str
    source_provider: str | None = None
    composer_version: str = ATTACHMENT_VERSION

    @property
    def is_canonical(self) -> bool:
        return (
            self.outcome == SecurityAttachmentOutcome.CANONICAL.value
            and isinstance(self.canonical_token_id, str)
            and bool(self.canonical_token_id)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "subject_kind": self.subject_kind,
            "canonical_token_id": self.canonical_token_id,
            "observed_chain": self.observed_chain,
            "observed_address": self.observed_address,
            "identity_state": self.identity_state,
            "join_class": self.join_class,
            "reason": self.reason,
            "source_provider": self.source_provider,
            "composer_version": self.composer_version,
            "is_canonical": self.is_canonical,
        }


def _text(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Enum):
        raw = value.value
        text = str(raw).strip() if raw is not None else ""
        return text or None
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def _normalize_subject_kind(subject_kind: Any) -> str | None:
    text = _text(subject_kind)
    return text.upper() if text else None


def _identity_state_label(identity: Any) -> str | None:
    if identity is None:
        return None
    if isinstance(identity, IdentityResolution):
        state = getattr(getattr(identity, "token", None), "state", None)
        if isinstance(state, IdentityState):
            return state.value
        return _text(state)
    if isinstance(identity, IdentityState):
        return identity.value
    return None


def _observed_from_identity(identity: Any) -> tuple[str | None, str | None]:
    if not isinstance(identity, IdentityResolution):
        return None, None
    token = identity.token
    return _text(getattr(token, "chain", None)), _text(getattr(token, "address_canonical", None))


def _copy_canonical_token_id(identity: Any) -> str | None:
    if not isinstance(identity, IdentityResolution):
        return None
    tid = _text(getattr(getattr(identity, "token", None), "token_id", None))
    return tid


def _attachment(
    *,
    outcome: SecurityAttachmentOutcome,
    reason: str,
    subject_kind: str | None,
    identity: Any = None,
    observed_chain: str | None = None,
    observed_address: str | None = None,
    join_class: str | None = None,
    source_provider: str | None = None,
    canonical_token_id: str | None = None,
) -> SecurityAttachment:
    return SecurityAttachment(
        outcome=outcome.value,
        subject_kind=subject_kind,
        canonical_token_id=canonical_token_id,
        observed_chain=_text(observed_chain),
        observed_address=_text(observed_address),
        identity_state=_identity_state_label(identity),
        join_class=join_class,
        reason=reason,
        source_provider=_text(source_provider),
    )


def attach_security_identity(
    identity: Any = None,
    *,
    subject_kind: str | None = None,
    observed_chain: str | None = None,
    observed_address: str | None = None,
    source_provider: str | None = None,
) -> SecurityAttachment:
    """Classify whether a security result may attach to a canonical token.

    Fail closed on missing/unknown subject kind. Non-token subjects stay
    scoped and never receive a canonical token id. Historical rows are
    not rewritten; this function is pure.
    """
    kind = _normalize_subject_kind(subject_kind)
    id_chain, id_address = _observed_from_identity(identity)
    chain = id_chain or _text(observed_chain)
    address = id_address or _text(observed_address)
    # Exact Solana mint wins over a folded operational observation.
    if id_address and _text(observed_address) and id_address != _text(observed_address):
        address = id_address

    if kind is None:
        return _attachment(
            outcome=SecurityAttachmentOutcome.REJECTED,
            reason="missing_subject_kind",
            subject_kind=None,
            identity=identity,
            observed_chain=chain,
            observed_address=address,
            source_provider=source_provider,
        )
    if kind not in _KNOWN_SUBJECTS:
        return _attachment(
            outcome=SecurityAttachmentOutcome.REJECTED,
            reason="unknown_subject_kind",
            subject_kind=kind,
            identity=identity,
            observed_chain=chain,
            observed_address=address,
            source_provider=source_provider,
        )
    if kind in _NON_TOKEN_SUBJECTS:
        return _attachment(
            outcome=SecurityAttachmentOutcome.SUBJECT_SCOPED,
            reason="subject_scoped_not_token",
            subject_kind=kind,
            identity=identity,
            observed_chain=_text(observed_chain) or chain,
            observed_address=_text(observed_address) or address,
            source_provider=source_provider,
        )
    if identity is None:
        return _attachment(
            outcome=SecurityAttachmentOutcome.UNLINKED,
            reason="missing_identity",
            subject_kind=kind,
            observed_chain=chain,
            observed_address=address,
            source_provider=source_provider,
        )

    decision = classify_canonical_join(identity)
    join_name = decision.classification.value
    if decision.classification is JoinClass.CANONICAL_JOIN:
        token_id = _copy_canonical_token_id(identity)
        if token_id is None:
            return _attachment(
                outcome=SecurityAttachmentOutcome.REJECTED,
                reason="canonical_join_missing_token_id",
                subject_kind=kind,
                identity=identity,
                observed_chain=chain,
                observed_address=address,
                join_class=join_name,
                source_provider=source_provider,
            )
        return _attachment(
            outcome=SecurityAttachmentOutcome.CANONICAL,
            reason="canonical_join_verified",
            subject_kind=kind,
            identity=identity,
            observed_chain=chain,
            observed_address=address,
            join_class=join_name,
            source_provider=source_provider,
            canonical_token_id=token_id,
        )
    if decision.classification is JoinClass.REJECTED:
        return _attachment(
            outcome=SecurityAttachmentOutcome.REJECTED,
            reason=decision.reason or "rejected_join",
            subject_kind=kind,
            identity=identity,
            observed_chain=chain,
            observed_address=address,
            join_class=join_name,
            source_provider=source_provider,
        )
    return _attachment(
        outcome=SecurityAttachmentOutcome.UNLINKED,
        reason=decision.reason or "noncanonical_join",
        subject_kind=kind,
        identity=identity,
        observed_chain=chain,
        observed_address=address,
        join_class=join_name,
        source_provider=source_provider,
    )


def security_canonical_token_id(
    identity: Any = None,
    *,
    subject_kind: str | None = _TOKEN_SUBJECT,
) -> str | None:
    """Copy token_id only when W4 permits CANONICAL_JOIN for a TOKEN subject."""
    return attach_security_identity(identity, subject_kind=subject_kind).canonical_token_id


def legacy_security_row_is_canonical(row: Any, identity: Any = None) -> bool:
    """A stored token_id / token_key is never canonical authority.

    Legacy rows stay noncanonical unless a live IdentityResolution independently
    permits CANONICAL_JOIN. The row itself is never rewritten.
    """
    if identity is None:
        return False
    return security_canonical_token_id(identity, subject_kind=_TOKEN_SUBJECT) is not None


def overlay_key_is_canonical_authority(key: Any) -> bool:
    """overlay_query tokenKey / token_key is operational only."""
    return False


def overlay_attachment_for_item(
    item: Any = None,
    *,
    identity: Any = None,
    subject_kind: str | None = None,
) -> SecurityAttachment:
    """TS overlay keys never prove canonical attachment."""
    del item
    return attach_security_identity(identity, subject_kind=subject_kind)


def goplus_query_may_attach_as_token_security(
    *,
    subject_kind: str | None,
    identity: Any = None,
    queried_address: str | None = None,
    queried_chain: str | None = None,
) -> bool:
    """GoPlus /token_security is not proof of token subject or canonical identity.

    The adapter still queries an address; this consumer gate refuses token
    attachment unless the subject is explicit TOKEN and W4 permits join.
    queried_address/chain are observational only and never grant authority.
    """
    del queried_address, queried_chain
    if _normalize_subject_kind(subject_kind) != _TOKEN_SUBJECT:
        return False
    return security_canonical_token_id(identity, subject_kind=_TOKEN_SUBJECT) is not None


def rugcheck_query_may_attach_as_token_security(
    *,
    subject_kind: str | None,
    identity: Any = None,
    queried_address: str | None = None,
) -> bool:
    """RugCheck /tokens/{address}/report is not proof the address is a mint.

    Fail closed unless subject is TOKEN, W4 permits CANONICAL_JOIN, and the
    queried address equals the exact validated Solana mint (case-preserving).
    """
    if _normalize_subject_kind(subject_kind) != _TOKEN_SUBJECT:
        return False
    attachment = attach_security_identity(identity, subject_kind=_TOKEN_SUBJECT)
    if not attachment.is_canonical:
        return False
    mint = attachment.observed_address
    queried = _text(queried_address)
    if mint is None or queried is None:
        return False
    return queried == mint
