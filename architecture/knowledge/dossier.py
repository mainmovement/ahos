#!/usr/bin/env python3
"""Read-only unified token dossier — composition only.

Lane-B UNDERSTAND/REMEMBER surface. Not a decision, identity, scoring,
security, knowledge-store, cognitive, or trading engine.

Composes caller-supplied objects. Never invents canonical identity,
never upgrades epistemic status, never writes a database, never imports
Lane A, the operational daemon package, grant verifiers, or the P5 loop.

Do not import this module from the operational daemon package or the pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

COMPOSER_VERSION = "token-dossier-composer-v1"


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
    provenance: tuple[dict[str, Any], ...]
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
            "provenance": [dict(p) for p in self.provenance],
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
    text = str(value).strip()
    return text if text else None


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _state_text(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, str):
        return _text(obj)
    return _text(_attr(obj, "state", obj))


def _copy_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return {str(k): value[k] for k in value}
    return None


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
    provenance: list[dict[str, Any]] = []
    join_keys: list[JoinKey] = []
    seen_keys: set[tuple[str, str, str]] = set()

    token = identity.token if identity is not None else None
    existing_token_id = _text(_attr(token, "token_id")) if token is not None else None
    # Preserve only. Never hash chain+address here.
    canonical_token_id = existing_token_id

    identity_state = _text(_attr(token, "state")) if token is not None else None
    if identity_state is None and identity is not None:
        identity_state = _text(_attr(identity, "state"))
    decision_identity_state = _text(_attr(decision, "identity_state"))
    if identity is None:
        if decision_identity_state is not None:
            identity_state = decision_identity_state
            unknowns.append("identity_resolution_absent")
            epistemic.append(EpistemicEntry(
                "identity_state", EpistemicStatus.UNAVAILABLE,
                "copied from decision; no IdentityResolution supplied",
            ))
        else:
            unknowns.append("identity_state")
            epistemic.append(EpistemicEntry(
                "identity_state", EpistemicStatus.UNAVAILABLE, "no identity input",
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

    if identity is not None:
        for item in identity.conflicts:
            conflicts.append(str(item))
        for blob in identity.provenance:
            copied = _copy_mapping(blob)
            if copied is not None:
                provenance.append({"source": "identity", **copied})

    if canonical_token_id is None:
        epistemic.append(EpistemicEntry(
            "canonical_token_id", EpistemicStatus.UNAVAILABLE,
            "no existing token_id on identity; composer does not synthesize one",
        ))
        unknowns.append("canonical_token_id")
    else:
        epistemic.append(EpistemicEntry(
            "canonical_token_id", EpistemicStatus.DERIVED,
            "preserved existing identity.token.token_id; not recomputed",
        ))
        _append_unique(
            join_keys, seen_keys,
            JoinKey(AliasKind.CANONICAL, "token_id", canonical_token_id),
        )

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

    security_state = _state_text(security)
    if security_state is None:
        security_state = _text(_attr(decision, "security_state"))
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
        dec_prov = _copy_mapping(_attr(decision, "provenance"))
        if dec_prov:
            provenance.append({"source": "decision", **dec_prov})

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
            provenance.append({"source": "score", "provenance_sha256": sha})

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
        provenance.append({"source": "metadata", "keys": sorted(str(k) for k in metadata)})

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
