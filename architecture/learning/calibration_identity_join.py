#!/usr/bin/env python3
"""W4 Slice 7 — calibration identity pairing boundary.

Read-only consumer of the existing W4 join classifier. Not an identity
authority and not a resolver.

prediction IdentityResolution
        ↓
classify_canonical_join()  →  CANONICAL_JOIN
        ↓
outcome IdentityResolution
        ↓
classify_canonical_join()  →  CANONICAL_JOIN
        ↓
same canonical token_id + same chain + exact address
        ↓
calibration pair permitted

A stored token_id string, symbol, name, pool, provider ID, fallback,
operational key, or lowercased Solana key is never pairing authority.
Raw `prediction.token_id == outcome.token_id` is not sufficient.

Do not persist, migrate, or rewrite historical prediction/outcome rows.
Do not change calibration mathematics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from architecture.identity.join import JoinClass, classify_canonical_join
from architecture.identity.types import IdentityResolution
from architecture.learning.score_ledger import ledger_canonical_token_id

PAIRING_VERSION = "calibration-identity-join-v1"

CONSUMER_CONTRACT = (
    "A calibration pair requires two legitimate IdentityResolution values "
    "that classify_canonical_join classifies as CANONICAL_JOIN, the same "
    "canonical token_id, the same chain, and the exact same validated "
    "address. token_id string equality, symbols, names, pools, provider "
    "IDs, fallbacks, operational keys, and lowercased Solana keys never "
    "pair. Historical rows are not rewritten."
)

PAIR_PAIRED = "PAIRED"
PAIR_UNMATCHED = "UNMATCHED"
PAIR_REJECTED = "REJECTED"

_TOKEN_SUBJECT = "TOKEN"
_KNOWN_SUBJECTS = frozenset({
    "TOKEN", "POOL", "DEPLOYER", "HOLDER", "CONTRACT",
    "LIQUIDITY_PAIR", "PROVIDER_OBSERVATION",
})


@dataclass(frozen=True)
class CalibrationPairDecision:
    outcome: str
    canonical_token_id: str | None
    reason: str
    prediction_join_class: str | None = None
    outcome_join_class: str | None = None
    observed_chain: str | None = None
    observed_address: str | None = None
    composer_version: str = PAIRING_VERSION

    @property
    def permits_pair(self) -> bool:
        return (
            self.outcome == PAIR_PAIRED
            and isinstance(self.canonical_token_id, str)
            and bool(self.canonical_token_id)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "canonical_token_id": self.canonical_token_id,
            "reason": self.reason,
            "permits_pair": self.permits_pair,
            "prediction_join_class": self.prediction_join_class,
            "outcome_join_class": self.outcome_join_class,
            "observed_chain": self.observed_chain,
            "observed_address": self.observed_address,
            "composer_version": self.composer_version,
            "consumer_contract": CONSUMER_CONTRACT,
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


def _chain_key(chain: Any) -> str | None:
    text = _text(chain)
    return text.lower() if text else None


def _normalize_subject_kind(subject_kind: Any) -> str | None:
    text = _text(subject_kind)
    return text.upper() if text else None


def _is_ambiguous_bundle(value: Any) -> bool:
    return isinstance(value, (list, tuple, set, dict))


def _token_field(identity: Any, name: str) -> Any:
    if not isinstance(identity, IdentityResolution):
        return None
    return getattr(getattr(identity, "token", None), name, None)


def _decision(
    outcome: str,
    reason: str,
    *,
    canonical_token_id: str | None = None,
    prediction_join_class: str | None = None,
    outcome_join_class: str | None = None,
    observed_chain: str | None = None,
    observed_address: str | None = None,
) -> CalibrationPairDecision:
    return CalibrationPairDecision(
        outcome=outcome,
        canonical_token_id=canonical_token_id,
        reason=reason,
        prediction_join_class=prediction_join_class,
        outcome_join_class=outcome_join_class,
        observed_chain=observed_chain,
        observed_address=observed_address,
    )


def pair_calibration_identities(
    prediction_identity: Any = None,
    outcome_identity: Any = None,
    *,
    subject_kind: str | None = _TOKEN_SUBJECT,
) -> CalibrationPairDecision:
    """Classify whether a prediction and an outcome may form a calibration pair.

    Fail closed on missing/unknown subject kind, one-sided identity, ambiguous
    bundles, noncanonical join classes, token_id-only equality, and chain or
    address mismatch. Pure: does not write stores.
    """
    kind = _normalize_subject_kind(subject_kind)
    if kind is None:
        return _decision(PAIR_REJECTED, "missing_subject_kind")
    if kind not in _KNOWN_SUBJECTS:
        return _decision(PAIR_REJECTED, "unknown_subject_kind")
    if kind != _TOKEN_SUBJECT:
        return _decision(PAIR_UNMATCHED, "subject_not_token", observed_chain=None)

    if _is_ambiguous_bundle(prediction_identity) or _is_ambiguous_bundle(outcome_identity):
        return _decision(PAIR_UNMATCHED, "ambiguous_candidates")

    if prediction_identity is None and outcome_identity is None:
        return _decision(PAIR_UNMATCHED, "missing_identity")
    if prediction_identity is None or outcome_identity is None:
        return _decision(PAIR_UNMATCHED, "one_sided_identity")

    pred_join = classify_canonical_join(prediction_identity)
    out_join = classify_canonical_join(outcome_identity)
    pred_cls = pred_join.classification.value
    out_cls = out_join.classification.value

    if (
        pred_join.classification is JoinClass.REJECTED
        or out_join.classification is JoinClass.REJECTED
    ):
        return _decision(
            PAIR_REJECTED,
            pred_join.reason if pred_join.classification is JoinClass.REJECTED
            else out_join.reason,
            prediction_join_class=pred_cls,
            outcome_join_class=out_cls,
        )
    if (
        pred_join.classification is not JoinClass.CANONICAL_JOIN
        or out_join.classification is not JoinClass.CANONICAL_JOIN
    ):
        return _decision(
            PAIR_UNMATCHED,
            "noncanonical_identity",
            prediction_join_class=pred_cls,
            outcome_join_class=out_cls,
        )

    pred_tid = ledger_canonical_token_id(prediction_identity)
    out_tid = ledger_canonical_token_id(outcome_identity)
    if pred_tid is None or out_tid is None:
        return _decision(
            PAIR_UNMATCHED,
            "canonical_token_id_unavailable",
            prediction_join_class=pred_cls,
            outcome_join_class=out_cls,
        )
    if pred_tid != out_tid:
        return _decision(
            PAIR_UNMATCHED,
            "different_canonical_token_id",
            prediction_join_class=pred_cls,
            outcome_join_class=out_cls,
        )

    pred_chain = _chain_key(_token_field(prediction_identity, "chain"))
    out_chain = _chain_key(_token_field(outcome_identity, "chain"))
    if pred_chain is None or out_chain is None or pred_chain != out_chain:
        return _decision(
            PAIR_UNMATCHED,
            "cross_chain_mismatch",
            prediction_join_class=pred_cls,
            outcome_join_class=out_cls,
            observed_chain=pred_chain,
        )

    pred_addr = _text(_token_field(prediction_identity, "address_canonical"))
    out_addr = _text(_token_field(outcome_identity, "address_canonical"))
    if pred_addr is None or out_addr is None or pred_addr != out_addr:
        return _decision(
            PAIR_UNMATCHED,
            "address_mismatch",
            prediction_join_class=pred_cls,
            outcome_join_class=out_cls,
            observed_chain=pred_chain,
            observed_address=pred_addr,
        )

    return _decision(
        PAIR_PAIRED,
        "canonical_join_verified_both_sides",
        canonical_token_id=pred_tid,
        prediction_join_class=pred_cls,
        outcome_join_class=out_cls,
        observed_chain=_text(_token_field(prediction_identity, "chain")),
        observed_address=pred_addr,
    )


def lookup_identity(index: Any, *keys: Any) -> Any:
    """Resolve at most one identity from an operational index. Lists fail closed."""
    if not isinstance(index, dict):
        return None
    for key in keys:
        if key is None:
            continue
        if key not in index:
            continue
        value = index[key]
        if _is_ambiguous_bundle(value) and not isinstance(value, IdentityResolution):
            return ("__ambiguous__", value)
        return value
    return None
