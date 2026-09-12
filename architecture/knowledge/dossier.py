#!/usr/bin/env python3
"""Read-only unified token dossier — composition only.

Lane-B UNDERSTAND/REMEMBER surface. Not a decision, identity, scoring,
security, knowledge-store, cognitive, or trading engine.

Composes caller-supplied objects. Never invents canonical identity,
never upgrades epistemic status, never writes a database, never imports
Lane A, the operational daemon package, grant verifiers, or the P5 loop.

Security state is taken only from an explicit supported `.state` field
(PASS / REJECT / INCOMPLETE / STALE). Object `__str__` is never authority.

Canonical identity is authorized only by a supported IdentityResolution
plus TokenIdentity (type/module match, no import of that package). Arbitrary
caller objects with `state=VERIFIED` are rejected.

Provenance freeze covers mappings, sequences, and deepcopyable values.
Non-deepcopyable objects are replaced with an untrusted marker and are not
epistemic authority.

Do not import this module from the operational daemon package or the pipeline.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping

COMPOSER_VERSION = "token-dossier-composer-v1.2"

# Join path segments so this file does not contain a contiguous forbidden import token.
_IDENTITY_TYPES_MODULE = ".".join(("architecture", "identity", "types"))
_IDENTITY_RESOLUTION_NAME = "IdentityResolution"
_TOKEN_IDENTITY_NAME = "TokenIdentity"

_SUPPORTED_SECURITY_STATES = frozenset({"PASS", "REJECT", "INCOMPLETE", "STALE"})
_SUPPORTED_IDENTITY_STATES = frozenset({
    "VERIFIED", "CONFLICT", "UNRESOLVED", "INVALID", "STALE", "UNSUPPORTED",
})


class AliasKind(str, Enum):
    CANONICAL = "canonical_identity"
    OPERATIONAL = "operational_alias"
    DISPLAY = "display_alias"


class EpistemicStatus(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class JoinKey:
    kind: AliasKind
    scheme: str
    value: str

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind.value, "scheme": self.scheme, "value": self.value}


@dataclass(frozen=True)
class EpistemicEntry:
    field: str
    status: EpistemicStatus
    note: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"field": self.field, "status": self.status.value, "note": self.note}


@dataclass(frozen=True)
class ClaimRecord:
    statement: str
    trust_class: str | None
    category: str | None
    claim_id: str | None
    contradictions: tuple[str, ...]


@dataclass(frozen=True)
class TokenDossier:
    """Immutable composition of existing outputs. Not authority."""

    canonical_token_id: str | None
    join_keys: tuple[JoinKey, ...]
    identity_state: str | None
    security_state: str | None
    decision_outcome: str | None
    opportunity_score: float | None
    epistemic_map: tuple[EpistemicEntry, ...]
    conflicts: tuple[str, ...]
    unknowns: tuple[str, ...]
    provenance: tuple[Mapping[str, Any], ...]
    composed_at: float | None
    claims: tuple[ClaimRecord, ...]
    composer_version: str = COMPOSER_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "canonical_token_id": self.canonical_token_id,
            "join_keys": [k.as_dict() for k in self.join_keys],
            "identity_state": self.identity_state,
            "security_state": self.security_state,
            "decision_outcome": self.decision_outcome,
            "opportunity_score": self.opportunity_score,
            "epistemic_map": [e.as_dict() for e in self.epistemic_map],
            "conflicts": list(self.conflicts),
            "unknowns": list(self.unknowns),
            "provenance": [_deep_plain(p) for p in self.provenance],
            "composed_at": self.composed_at,
            "claims": [
                {
                    "statement": c.statement,
                    "trust_class": c.trust_class,
                    "category": c.category,
                    "claim_id": c.claim_id,
                    "contradictions": list(c.contradictions),
                }
                for c in self.claims
            ],
            "composer_version": self.composer_version,
        }


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        raw = value.value
        return str(raw) if raw is not None else None
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _type_ref(obj: Any) -> tuple[str, str]:
    cls = type(obj)
    return (getattr(cls, "__module__", "") or "", cls.__name__)


def _is_supported_identity_resolution(obj: Any) -> bool:
    module, name = _type_ref(obj)
    return module == _IDENTITY_TYPES_MODULE and name == _IDENTITY_RESOLUTION_NAME


def _is_supported_token_identity(obj: Any) -> bool:
    module, name = _type_ref(obj)
    return module == _IDENTITY_TYPES_MODULE and name == _TOKEN_IDENTITY_NAME


def _enum_or_str(value: Any) -> str | None:
    """Explicit Enum.value or str. Never str(arbitrary object)."""
    if value is None:
        return None
    if isinstance(value, Enum):
        raw = value.value
        if raw is None:
            return None
        text = str(raw).strip()
        return text if text else None
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    return None


def _has_explicit_state_field(obj: Any) -> bool:
    if obj is None or isinstance(obj, (str, bytes, int, float, bool, Enum)):
        return False
    try:
        if isinstance(obj, Mapping):
            return "state" in obj
        return hasattr(obj, "state")
    except (AttributeError, TypeError):
        return False


def _read_overlay_security(security: Any) -> tuple[str | None, str | None]:
    """Return (supported_state, diagnostic). Never uses str(security)."""
    if security is None:
        return None, None
    if not _has_explicit_state_field(security):
        return None, "security_state_field_absent"
    try:
        raw = security["state"] if isinstance(security, Mapping) else getattr(security, "state")
    except (AttributeError, TypeError, KeyError, ValueError):
        return None, "security_state_unreadable"
    if raw is None:
        return None, "security_state_empty"
    if isinstance(raw, str) and not raw.strip():
        return None, "security_state_empty"
    text = _enum_or_str(raw)
    if text is None:
        return None, "security_state_invalid_type"
    if text not in _SUPPORTED_SECURITY_STATES:
        return None, f"security_state_invalid:{text}"
    return text, None


def _read_decision_security(decision: Any) -> tuple[str | None, str | None]:
    if decision is None:
        return None, None
    if isinstance(decision, Mapping):
        present = "security_state" in decision
        raw = decision.get("security_state") if present else None
    else:
        present = hasattr(decision, "security_state")
        raw = getattr(decision, "security_state", None) if present else None
    if not present:
        return None, None
    if raw is None:
        return None, None
    text = _enum_or_str(raw)
    if text is None:
        return None, "decision_security_state_invalid_type"
    if text not in _SUPPORTED_SECURITY_STATES:
        return None, f"decision_security_state_invalid:{text}"
    return text, None


def _freeze_value(value: Any) -> Any:
    """Detach and freeze nested containers so provenance cannot alias caller data."""
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
            "untrusted_provenance": True,
            "value_type": type(value).__name__,
            "note": "non-deepcopyable object discarded; not authoritative",
        })


def _freeze_mapping(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        return None
    return MappingProxyType({str(k): _freeze_value(value[k]) for k in value})


def _deep_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_plain(value[k]) for k in value}
    if isinstance(value, (list, tuple)):
        return [_deep_plain(v) for v in value]
    return value


def _provenance_entry(source: str, payload: Mapping[str, Any] | None = None, **extra: Any) -> Mapping[str, Any]:
    data: dict[str, Any] = {"source": source}
    if payload is not None:
        for key in payload:
            data[str(key)] = payload[key]
    data.update(extra)
    frozen = _freeze_mapping(data)
    assert frozen is not None
    return frozen


def _is_verified_identity(state: str | None) -> bool:
    return state == "VERIFIED"


@dataclass(frozen=True)
class _IdentityIntake:
    present: bool
    accepted: bool
    token: Any | None = None
    identity_state: str | None = None
    conflicts: tuple[Any, ...] = ()
    provenance_blobs: tuple[Any, ...] = ()
    reject_code: str | None = None
    reject_detail: str | None = None


def _extract_identity(identity: Any) -> _IdentityIntake:
    """Accept only a supported IdentityResolution; never crash on caller junk."""
    if identity is None:
        return _IdentityIntake(present=False, accepted=False)
    if not _is_supported_identity_resolution(identity):
        module, name = _type_ref(identity)
        return _IdentityIntake(
            present=True,
            accepted=False,
            reject_code="identity_input_invalid",
            reject_detail=f"unsupported_type:{module}:{name}",
        )
    try:
        token = identity.token
        raw_conflicts = identity.conflicts
        raw_blobs = identity.provenance
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        return _IdentityIntake(
            present=True,
            accepted=False,
            reject_code="identity_resolution_invalid",
            reject_detail=f"unreadable_field:{type(exc).__name__}",
        )
    except Exception as exc:
        return _IdentityIntake(
            present=True,
            accepted=False,
            reject_code="identity_resolution_invalid",
            reject_detail=f"access_error:{type(exc).__name__}",
        )
    if not _is_supported_token_identity(token):
        return _IdentityIntake(
            present=True,
            accepted=False,
            reject_code="identity_resolution_invalid",
            reject_detail="token_not_supported_token_identity",
        )
    try:
        state = _enum_or_str(token.state)
        if state is not None and state not in _SUPPORTED_IDENTITY_STATES:
            state = None
        conflicts = tuple(raw_conflicts) if raw_conflicts is not None else ()
        blobs = tuple(raw_blobs) if raw_blobs is not None else ()
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        return _IdentityIntake(
            present=True,
            accepted=False,
            reject_code="identity_resolution_invalid",
            reject_detail=f"unreadable_token_field:{type(exc).__name__}",
        )
    except Exception as exc:
        return _IdentityIntake(
            present=True,
            accepted=False,
            reject_code="identity_resolution_invalid",
            reject_detail=f"access_error:{type(exc).__name__}",
        )
    return _IdentityIntake(
        present=True,
        accepted=True,
        token=token,
        identity_state=state,
        conflicts=conflicts,
        provenance_blobs=blobs,
    )


def _decision_token_key_alias(chain: str | None, address: str | None) -> str | None:
    """Operational alias of already-present chain+address. Not a canonical ID."""
    c = (chain or "").strip()
    a = (address or "").strip()
    if not c or not a:
        return None
    return f"{c.lower()}:{a.lower()}"


def _symbol_key_alias(chain: str | None, symbol: str | None) -> str | None:
    """Display alias only. Never a canonical identity."""
    c = (chain or "").strip()
    s = (symbol or "").strip()
    if not s:
        return None
    chain_part = c.lower() if c else "unknown"
    return f"{chain_part}:sym:{s.upper()}"


def _append_unique(keys: list[JoinKey], seen: set[tuple[str, str, str]], item: JoinKey) -> None:
    mark = (item.kind.value, item.scheme, item.value)
    if mark in seen:
        return
    seen.add(mark)
    keys.append(item)


def _claim_records(claims: Iterable[Any] | None) -> tuple[ClaimRecord, ...]:
    if not claims:
        return ()
    out: list[ClaimRecord] = []
    for raw in claims:
        statement = _text(_attr(raw, "statement"))
        if statement is None:
            continue
        edges = _attr(raw, "contradiction_edges") or ()
        contra: list[str] = []
        if isinstance(edges, Mapping):
            edges = (edges,)
        for edge in edges:
            if isinstance(edge, Mapping):
                target = _text(edge.get("target_claim_id") or edge.get("reason"))
            else:
                target = _text(_attr(edge, "target_claim_id")) or _text(edge)
            if target:
                contra.append(target)
        ids = _attr(raw, "contradicting_evidence_ids") or ()
        for item in ids:
            t = _text(item)
            if t:
                contra.append(t)
        trust = _attr(raw, "trust_class")
        category = _attr(raw, "category")
        out.append(
            ClaimRecord(
                statement=statement,
                trust_class=_text(trust),
                category=_text(category),
                claim_id=_text(_attr(raw, "claim_id")),
                contradictions=tuple(contra),
            )
        )
    return tuple(out)


def compose_dossier(
    identity: Any = None,
    decision: Any = None,
    score: Any = None,
    security: Any = None,
    claims: Iterable[Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    composed_at: float | None = None,
) -> TokenDossier:
    """Pure composition. Side-effect free. Does not mutate inputs."""
    conflicts: list[str] = []
    unknowns: list[str] = []
    epistemic: list[EpistemicEntry] = []
    provenance: list[Mapping[str, Any]] = []
    join_keys: list[JoinKey] = []
    seen_keys: set[tuple[str, str, str]] = set()

    # Never hash chain+address here. Never invent a replacement identifier.
    intake = _extract_identity(identity)
    token = intake.token if intake.accepted else None
    existing_token_id = _enum_or_str(_attr(token, "token_id")) if token is not None else None
    identity_state = intake.identity_state if intake.accepted else None
    decision_identity_state = _enum_or_str(_attr(decision, "identity_state"))

    if not intake.present:
        unknowns.append("identity_resolution_absent")
        unknowns.append("identity_state")
        epistemic.append(EpistemicEntry(
            "identity_state", EpistemicStatus.UNAVAILABLE,
            "no IdentityResolution supplied; decision identity_state is not primary authority",
        ))
    elif not intake.accepted:
        unknowns.append(intake.reject_code or "identity_input_invalid")
        unknowns.append("identity_state")
        epistemic.append(EpistemicEntry(
            "identity_state", EpistemicStatus.UNAVAILABLE,
            "identity input rejected; not a supported IdentityResolution",
        ))
        provenance.append(_provenance_entry(
            "identity_input_rejected",
            reason=intake.reject_code or "identity_input_invalid",
            detail=intake.reject_detail or "",
            note="malformed or unsupported identity cannot authorize VERIFIED or canonical_token_id",
        ))
    else:
        if identity_state is None:
            unknowns.append("identity_state")
            epistemic.append(EpistemicEntry(
                "identity_state", EpistemicStatus.UNKNOWN, "identity present without state",
            ))
        elif identity_state == "CONFLICT":
            epistemic.append(EpistemicEntry(
                "identity_state", EpistemicStatus.CONFLICTED, "preserved from IdentityResolution",
            ))
        elif identity_state in {"UNRESOLVED", "INVALID", "STALE", "UNSUPPORTED"}:
            epistemic.append(EpistemicEntry(
                "identity_state", EpistemicStatus.UNKNOWN
                if identity_state == "UNRESOLVED" else EpistemicStatus.DERIVED,
                "preserved from IdentityResolution; not upgraded",
            ))
        else:
            epistemic.append(EpistemicEntry(
                "identity_state", EpistemicStatus.DERIVED, "preserved from IdentityResolution",
            ))
        if (
            decision_identity_state is not None
            and identity_state is not None
            and decision_identity_state != identity_state
        ):
            conflicts.append(
                f"identity_state_disagreement:resolution={identity_state}"
                f":decision={decision_identity_state}"
            )
        for item in intake.conflicts:
            text = _enum_or_str(item)
            if text is not None:
                conflicts.append(text)
            elif item is not None:
                conflicts.append(f"identity_conflict_unprintable:{type(item).__name__}")
        for blob in intake.provenance_blobs:
            copied = _freeze_mapping(blob)
            if copied is not None:
                provenance.append(_provenance_entry("identity", copied))

    if not intake.accepted:
        if decision_identity_state is not None:
            unknowns.append(f"decision_identity_state:{decision_identity_state}")
            provenance.append(_provenance_entry(
                "decision_identity_state_diagnostic",
                identity_state=decision_identity_state,
                note="decision-supplied identity_state is diagnostic only; not copied to primary identity_state",
            ))

    if _is_verified_identity(identity_state) and existing_token_id is not None:
        canonical_token_id = existing_token_id
        epistemic.append(EpistemicEntry(
            "canonical_token_id", EpistemicStatus.DERIVED,
            "preserved existing identity.token.token_id under VERIFIED identity; not recomputed",
        ))
        _append_unique(
            join_keys, seen_keys,
            JoinKey(AliasKind.CANONICAL, "token_id", canonical_token_id),
        )
    else:
        canonical_token_id = None
        if existing_token_id is not None:
            _append_unique(
                join_keys, seen_keys,
                JoinKey(AliasKind.OPERATIONAL, "unvalidated_token_id", existing_token_id),
            )
            epistemic.append(EpistemicEntry(
                "canonical_token_id", EpistemicStatus.UNAVAILABLE,
                "caller token_id present but identity is not VERIFIED; not promoted to canonical",
            ))
            epistemic.append(EpistemicEntry(
                "unvalidated_token_id", EpistemicStatus.UNKNOWN,
                "preserved caller token.token_id as a non-canonical operational identifier",
            ))
        else:
            epistemic.append(EpistemicEntry(
                "canonical_token_id", EpistemicStatus.UNAVAILABLE,
                "no VERIFIED identity token_id to preserve; composer does not synthesize one",
            ))
        unknowns.append("canonical_token_id")

    id_chain = _text(_attr(token, "chain")) if token is not None else None
    id_addr = _text(_attr(token, "address_canonical")) if token is not None else None
    if id_addr is None and token is not None:
        id_addr = _text(_attr(token, "address_input"))
    id_symbol = _text(_attr(token, "symbol_alias")) if token is not None else None

    score_chain = _text(_attr(score, "token_chain"))
    score_addr = _text(_attr(score, "token_address"))
    score_symbol = _text(_attr(score, "token_symbol"))

    if id_chain and id_addr:
        _append_unique(
            join_keys, seen_keys,
            JoinKey(AliasKind.OPERATIONAL, "chain_address", f"{id_chain}:{id_addr}"),
        )
        dt = _decision_token_key_alias(id_chain, id_addr)
        if dt is not None:
            _append_unique(
                join_keys, seen_keys,
                JoinKey(AliasKind.OPERATIONAL, "decision_token_key", dt),
            )
    if score_chain and score_addr:
        score_ca = f"{score_chain}:{score_addr}"
        id_ca = f"{id_chain}:{id_addr}" if id_chain and id_addr else None
        _append_unique(
            join_keys, seen_keys,
            JoinKey(AliasKind.OPERATIONAL, "chain_address", score_ca),
        )
        dt_score = _decision_token_key_alias(score_chain, score_addr)
        if dt_score is not None:
            _append_unique(
                join_keys, seen_keys,
                JoinKey(AliasKind.OPERATIONAL, "decision_token_key", dt_score),
            )
        if id_ca is not None and score_ca != id_ca:
            conflicts.append(
                f"alias_chain_address_disagreement:identity={id_ca}:score={score_ca}"
            )
        id_dt = _decision_token_key_alias(id_chain, id_addr) if id_chain and id_addr else None
        if id_dt is not None and dt_score is not None and id_dt != dt_score:
            conflicts.append(
                f"alias_decision_token_key_disagreement:identity={id_dt}:score={dt_score}"
            )

    if id_symbol:
        sk = _symbol_key_alias(id_chain, id_symbol)
        if sk is not None:
            _append_unique(
                join_keys, seen_keys,
                JoinKey(AliasKind.DISPLAY, "symbol_key", sk),
            )
    if score_symbol:
        sk_s = _symbol_key_alias(score_chain or id_chain, score_symbol)
        if sk_s is not None:
            _append_unique(
                join_keys, seen_keys,
                JoinKey(AliasKind.DISPLAY, "symbol_key", sk_s),
            )
        if id_symbol and score_symbol and id_symbol.upper() != score_symbol.upper():
            conflicts.append(
                f"alias_symbol_disagreement:identity={id_symbol}:score={score_symbol}"
            )

    if not any(k.kind is AliasKind.CANONICAL for k in join_keys):
        if any(k.scheme == "symbol_key" for k in join_keys) and canonical_token_id is None:
            unknowns.append("canonical_identity_not_inferable_from_symbol")

    overlay_security_state, overlay_security_diag = _read_overlay_security(security)
    decision_security_state, decision_security_diag = _read_decision_security(decision)
    if overlay_security_diag:
        unknowns.append(overlay_security_diag)
        provenance.append(_provenance_entry(
            "security_overlay_rejected",
            reason=overlay_security_diag,
            note="malformed overlay cannot manufacture security_state; __str__ is not authority",
        ))
    if decision_security_diag:
        unknowns.append(decision_security_diag)
    if overlay_security_state is None:
        security_state = decision_security_state
        if security_state is None:
            unknowns.append("security_state")
            epistemic.append(EpistemicEntry(
                "security_state", EpistemicStatus.UNAVAILABLE, "no security input",
            ))
        else:
            epistemic.append(EpistemicEntry(
                "security_state", EpistemicStatus.DERIVED,
                "copied from decision.security_state; not recomputed",
            ))
    else:
        security_state = overlay_security_state
        epistemic.append(EpistemicEntry(
            "security_state", EpistemicStatus.DERIVED,
            "preserved from overlay/state input; not recomputed",
        ))
        extra_unknown = _attr(security, "unknown_critical") or ()
        for item in extra_unknown:
            t = _text(item)
            if t:
                unknowns.append(f"security_unknown_critical:{t}")
        if security_state == "REJECT":
            for item in (_attr(security, "veto_reasons") or ()):
                t = _text(item)
                if t:
                    conflicts.append(f"security_veto:{t}")
        if (
            decision_security_state is not None
            and decision_security_state != overlay_security_state
        ):
            conflicts.append(
                f"security_state_disagreement:overlay={overlay_security_state}"
                f":decision={decision_security_state}"
            )
            provenance.append(_provenance_entry(
                "security_state_disagreement",
                overlay_security_state=overlay_security_state,
                decision_security_state=decision_security_state,
                effective_security_state=overlay_security_state,
            ))

    decision_outcome = _text(_attr(decision, "outcome"))
    if decision_outcome is None:
        unknowns.append("decision_outcome")
        epistemic.append(EpistemicEntry(
            "decision_outcome", EpistemicStatus.UNAVAILABLE, "no decision input",
        ))
    else:
        epistemic.append(EpistemicEntry(
            "decision_outcome", EpistemicStatus.DERIVED,
            "copied from decision.outcome; not recomputed",
        ))
        for item in (_attr(decision, "unknowns") or ()):
            t = _text(item)
            if t:
                unknowns.append(t)
        for item in (_attr(decision, "hard_vetoes") or ()):
            t = _text(item)
            if t:
                conflicts.append(f"decision_hard_veto:{t}")
        dec_prov = _freeze_mapping(_attr(decision, "provenance"))
        if dec_prov:
            provenance.append(_provenance_entry("decision", dec_prov))

    score_value = _attr(score, "opportunity_score", None) if score is not None else None
    decision_score = _attr(decision, "opportunity_score", None)
    if score is None and decision_score is None:
        opportunity_score = None
        unknowns.append("opportunity_score")
        epistemic.append(EpistemicEntry(
            "opportunity_score", EpistemicStatus.UNAVAILABLE, "no score input",
        ))
    elif score is None:
        opportunity_score = decision_score
        epistemic.append(EpistemicEntry(
            "opportunity_score", EpistemicStatus.DERIVED,
            "copied from decision; score report absent; not recalculated",
        ))
    else:
        opportunity_score = score_value
        epistemic.append(EpistemicEntry(
            "opportunity_score", EpistemicStatus.DERIVED,
            "copied from OpportunityScoreReport; not recalculated",
        ))
        if (
            decision_score is not None
            and score_value is not None
            and float(decision_score) != float(score_value)
        ):
            conflicts.append(
                f"opportunity_score_disagreement:score={score_value}:decision={decision_score}"
            )
        for item in (_attr(score, "missing_unknowns") or ()):
            t = _text(item)
            if t:
                unknowns.append(t)
        sha = _text(_attr(score, "provenance_sha256"))
        if sha:
            provenance.append(_provenance_entry("score", provenance_sha256=sha))

    claim_records = _claim_records(claims)
    for rec in claim_records:
        for c in rec.contradictions:
            conflicts.append(f"claim_contradiction:{c}")
        epistemic.append(EpistemicEntry(
            f"claim:{rec.claim_id or rec.statement[:48]}",
            EpistemicStatus.INFERRED,
            "preserved claim; not promoted to observed fact",
        ))

    if metadata:
        provenance.append(_provenance_entry("metadata", keys=sorted(str(k) for k in metadata)))

    if composed_at is not None:
        epistemic.append(EpistemicEntry(
            "composed_at", EpistemicStatus.DERIVED,
            "composition timestamp only; not an evidence timestamp",
        ))

    return TokenDossier(
        canonical_token_id=canonical_token_id,
        join_keys=tuple(join_keys),
        identity_state=identity_state,
        security_state=security_state,
        decision_outcome=decision_outcome,
        opportunity_score=opportunity_score if opportunity_score is None else float(opportunity_score),
        epistemic_map=tuple(epistemic),
        conflicts=tuple(conflicts),
        unknowns=tuple(unknowns),
        provenance=tuple(provenance),
        composed_at=composed_at,
        claims=claim_records,
    )
