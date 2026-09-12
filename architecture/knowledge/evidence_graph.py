#!/usr/bin/env python3
"""Read-only Claim/Evidence Graph View — W2 projection only.

Purpose
    Inspectable graph over existing evidence, claims, provenance, and the W1
    token dossier. Analytical/read model. Not a truth, decision, trading,
    council, or world-model engine.

Scope
    Pure composition. No database, network, filesystem, runtime, pipeline,
    Lane A, P5, scoring, security, or decision-authority imports.

Node vocabulary
    TOKEN, EVIDENCE, CLAIM, SOURCE, CONTRADICTION, PROVENANCE, DECISION

Edge vocabulary
    ATTACHED_TO, DERIVED_FROM, SUPPORTED_BY, CONTRADICTS, SOURCED_FROM,
    HAS_PROVENANCE, RELATES_TO

Epistemic rules
    Source status is copied or mapped downward, never upgraded.
    Claims are INFERRED. FACTUAL_PREMISE is a copied label only.
    Evidence provider-VERIFIED maps to DERIVED, never OBSERVED.
    OBSERVED / FACTUAL / FACTUAL_PREMISE authority is never created here.

Identity rules
    Canonical TOKEN nodes require dossier.identity_state == VERIFIED and a
    dossier.canonical_token_id. Symbol, name, operational token_id, and
    aliases never become canonical graph identity.

Contradiction behavior
    Both sides remain. The contradiction is a first-class node plus
    CONTRADICTS edges. No silent winner.

Unknown behavior
    Missing inputs stay missing (UNKNOWN / UNAVAILABLE). Nothing is invented.

Deterministic IDs
    Content/field-derived local IDs. No uuid, hash(), or composition clocks.
    A graph ID is never a canonical token identity.

Immutability
    Frozen nodes/edges. Nested mappings frozen. as_dict() is a safe copy.

Consumer contract
    identity_state, canonical_token_id, security_state, and decision_outcome
    are not sufficient authority. Consumers must also read conflicts,
    unknowns, epistemic_map, and provenance.

Non-goals
    Runtime wiring, claim-store writes, identity fusion, council, calibration,
    automatic promotion, world model, W1 redesign.

Do not import this module from the operational daemon package or the pipeline.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping

try:
    from .dossier import (
        AliasKind,
        EpistemicEntry,
        EpistemicStatus,
        TokenDossier,
        compose_dossier,
    )
except ImportError:  # standalone file load for isolation tests
    from dossier import (  # type: ignore
        AliasKind,
        EpistemicEntry,
        EpistemicStatus,
        TokenDossier,
        compose_dossier,
    )

GRAPH_VERSION = "claim-evidence-graph-v1"

CONSUMER_CONTRACT = (
    "identity_state, canonical_token_id, security_state, and decision_outcome "
    "are not sufficient authority. A graph consumer must also consider "
    "conflicts, unknowns, epistemic_map, and provenance."
)


class NodeType(str, Enum):
    TOKEN = "TOKEN"
    EVIDENCE = "EVIDENCE"
    CLAIM = "CLAIM"
    SOURCE = "SOURCE"
    CONTRADICTION = "CONTRADICTION"
    PROVENANCE = "PROVENANCE"
    DECISION = "DECISION"


class EdgeType(str, Enum):
    ATTACHED_TO = "ATTACHED_TO"
    DERIVED_FROM = "DERIVED_FROM"
    SUPPORTED_BY = "SUPPORTED_BY"
    CONTRADICTS = "CONTRADICTS"
    SOURCED_FROM = "SOURCED_FROM"
    HAS_PROVENANCE = "HAS_PROVENANCE"
    RELATES_TO = "RELATES_TO"


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
            "untrusted_provenance": True,
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
        return str(raw).strip() if raw is not None and str(raw).strip() else None
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


def _local_id(kind: str, *parts: str) -> str:
    cleaned = []
    for part in parts:
        text = _text(part) if not isinstance(part, str) else part.strip()
        if text:
            cleaned.append(text.replace("|", "/"))
    return f"{kind}:" + "|".join(cleaned) if cleaned else f"{kind}:unknown"


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    epistemic_status: EpistemicStatus
    label: str
    metadata: Mapping[str, Any] = MappingProxyType({})

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "epistemic_status": self.epistemic_status.value,
            "label": self.label,
            "metadata": _deep_plain(self.metadata),
        }


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    edge_type: EdgeType
    source_id: str
    target_id: str
    epistemic_status: EpistemicStatus
    metadata: Mapping[str, Any] = MappingProxyType({})

    def as_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "edge_type": self.edge_type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "epistemic_status": self.epistemic_status.value,
            "metadata": _deep_plain(self.metadata),
        }


@dataclass(frozen=True)
class EvidenceGraph:
    """Immutable projection. Not authority."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    identity_state: str | None
    canonical_token_id: str | None
    security_state: str | None
    decision_outcome: str | None
    conflicts: tuple[str, ...]
    unknowns: tuple[str, ...]
    epistemic_map: tuple[EpistemicEntry, ...]
    provenance: tuple[Mapping[str, Any], ...]
    consumer_contract: str = CONSUMER_CONTRACT
    composer_version: str = GRAPH_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.as_dict() for n in self.nodes],
            "edges": [e.as_dict() for e in self.edges],
            "identity_state": self.identity_state,
            "canonical_token_id": self.canonical_token_id,
            "security_state": self.security_state,
            "decision_outcome": self.decision_outcome,
            "conflicts": list(self.conflicts),
            "unknowns": list(self.unknowns),
            "epistemic_map": [e.as_dict() for e in self.epistemic_map],
            "provenance": [_deep_plain(p) for p in self.provenance],
            "consumer_contract": self.consumer_contract,
            "composer_version": self.composer_version,
        }


class _Builder:
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, GraphEdge] = {}

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        status: EpistemicStatus,
        label: str,
        **meta: Any,
    ) -> GraphNode:
        existing = self.nodes.get(node_id)
        if existing is not None:
            return existing
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            epistemic_status=status,
            label=label,
            metadata=_freeze_mapping(meta),
        )
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
        status: EpistemicStatus,
        **meta: Any,
    ) -> GraphEdge | None:
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        edge_id = _local_id("edge", edge_type.value, source_id, target_id)
        existing = self.edges.get(edge_id)
        if existing is not None:
            return existing
        edge = GraphEdge(
            edge_id=edge_id,
            edge_type=edge_type,
            source_id=source_id,
            target_id=target_id,
            epistemic_status=status,
            metadata=_freeze_mapping(meta),
        )
        self.edges[edge_id] = edge
        return edge


def _evidence_status(raw: Any) -> EpistemicStatus:
    text = _text(raw)
    if text in {None, "UNKNOWN", "UNAVAILABLE"}:
        return EpistemicStatus.UNKNOWN
    if text in {"CONFLICT", "CONFLICTED"}:
        return EpistemicStatus.CONFLICTED
    # Provider VERIFIED / STALE / DERIVED are copied downward as DERIVED.
    # Never OBSERVED, never FACTUAL.
    if text in {"VERIFIED", "DERIVED", "STALE", "INFERRED"}:
        return EpistemicStatus.DERIVED if text != "INFERRED" else EpistemicStatus.INFERRED
    return EpistemicStatus.UNKNOWN


def _iter_evidence(evidence: Any) -> list[Any]:
    if evidence is None:
        return []
    items = _attr(evidence, "items")
    extra = _attr(evidence, "extra")
    if items is not None or extra is not None:
        out = []
        for seq in (items or (), extra or ()):
            out.extend(list(seq))
        return out
    if isinstance(evidence, (list, tuple)):
        return list(evidence)
    return [evidence]


def _iter_sources(sources: Any) -> list[Any]:
    if sources is None:
        return []
    if isinstance(sources, (list, tuple)):
        return list(sources)
    return [sources]


def _iter_claims(claims: Any) -> list[Any]:
    if claims is None:
        return []
    if isinstance(claims, (list, tuple)):
        return list(claims)
    return [claims]


def _canonical_token_allowed(dossier: TokenDossier) -> bool:
    return (
        dossier.identity_state == "VERIFIED"
        and _text(dossier.canonical_token_id) is not None
    )


def _token_node(builder: _Builder, dossier: TokenDossier) -> GraphNode:
    join_meta = [k.as_dict() for k in dossier.join_keys]
    if _canonical_token_allowed(dossier):
        node_id = _local_id("token", "canonical", dossier.canonical_token_id or "")
        return builder.add_node(
            node_id,
            NodeType.TOKEN,
            EpistemicStatus.DERIVED,
            f"canonical token {dossier.canonical_token_id}",
            canonical=True,
            canonical_token_id=dossier.canonical_token_id,
            identity_state=dossier.identity_state,
            join_keys=join_meta,
        )
    operational = next(
        (k.value for k in dossier.join_keys if k.scheme == "chain_address"),
        None,
    )
    unvalidated = next(
        (k.value for k in dossier.join_keys if k.scheme == "unvalidated_token_id"),
        None,
    )
    display = next(
        (k.value for k in dossier.join_keys if k.scheme == "symbol_key"),
        None,
    )
    if operational:
        node_id = _local_id("token", "operational", operational)
        label = f"operational token {operational}"
        kind = "operational"
        value = operational
    elif unvalidated:
        node_id = _local_id("token", "unvalidated", unvalidated)
        label = f"unvalidated token {unvalidated}"
        kind = "unvalidated"
        value = unvalidated
    elif display:
        node_id = _local_id("token", "display", display)
        label = f"display token {display}"
        kind = "display"
        value = display
    else:
        node_id = "token:noncanonical:unresolved"
        label = "unresolved token"
        kind = "unresolved"
        value = None
    return builder.add_node(
        node_id,
        NodeType.TOKEN,
        EpistemicStatus.UNKNOWN if dossier.identity_state in {None, "UNRESOLVED"} else (
            EpistemicStatus.CONFLICTED if dossier.identity_state == "CONFLICT"
            else EpistemicStatus.UNAVAILABLE
        ),
        label,
        canonical=False,
        canonical_token_id=None,
        identity_state=dossier.identity_state,
        identifier_kind=kind,
        identifier_value=value,
        join_keys=join_meta,
    )


def _add_source(builder: _Builder, source_id: str, **meta: Any) -> GraphNode:
    return builder.add_node(
        _local_id("source", source_id),
        NodeType.SOURCE,
        EpistemicStatus.DERIVED,
        f"source {source_id}",
        source_id=source_id,
        **meta,
    )


def _add_evidence_item(builder: _Builder, raw: Any, token_id: str) -> GraphNode | None:
    evidence_id = (
        _text(_attr(raw, "evidence_id"))
        or _text(_attr(raw, "key"))
        or _text(_attr(raw, "pointer"))
    )
    description = _text(_attr(raw, "description")) or evidence_id or "evidence"
    if evidence_id is None and description == "evidence":
        return None
    eid = _local_id("evidence", evidence_id or description)
    status = _evidence_status(_attr(raw, "status"))
    if _attr(raw, "status") is None and _attr(raw, "value") is None and evidence_id:
        if _text(_attr(raw, "description")) is None:
            status = EpistemicStatus.UNKNOWN
    node = builder.add_node(
        eid,
        NodeType.EVIDENCE,
        status,
        description,
        evidence_id=evidence_id,
        provider=_text(_attr(raw, "provider")),
        source_field=_text(_attr(raw, "source_field")),
        copied_status=_text(_attr(raw, "status")),
    )
    builder.add_edge(EdgeType.ATTACHED_TO, eid, token_id, status)
    provider = _text(_attr(raw, "provider")) or _text(_attr(raw, "source_id"))
    if provider:
        src = _add_source(builder, provider)
        builder.add_edge(EdgeType.SOURCED_FROM, eid, src.node_id, EpistemicStatus.DERIVED)
    sha = _text(_attr(raw, "sha256")) or _text(_attr(raw, "raw_sha256"))
    if sha:
        pid = _local_id("provenance", "evidence", sha)
        builder.add_node(
            pid,
            NodeType.PROVENANCE,
            EpistemicStatus.DERIVED,
            "evidence provenance",
            provenance_sha256=sha,
        )
        builder.add_edge(EdgeType.HAS_PROVENANCE, eid, pid, EpistemicStatus.DERIVED)
    return node


def _add_claim(builder: _Builder, raw: Any, token_id: str, dossier_claim: bool = False) -> GraphNode | None:
    statement = _text(_attr(raw, "statement"))
    if statement is None:
        return None
    claim_id = _text(_attr(raw, "claim_id")) or statement[:64]
    nid = _local_id("claim", claim_id)
    category = _text(_attr(raw, "category"))
    trust = _text(_attr(raw, "trust_class"))
    node = builder.add_node(
        nid,
        NodeType.CLAIM,
        EpistemicStatus.INFERRED,
        statement,
        claim_id=claim_id,
        category=category,
        trust_class=trust,
        review_status=_text(_attr(raw, "review_status")),
        label_copied_not_promoted=True,
    )
    builder.add_edge(EdgeType.ATTACHED_TO, nid, token_id, EpistemicStatus.INFERRED)
    for link in _attr(raw, "evidence_links") or ():
        ev = _add_evidence_item(builder, link, token_id)
        if ev is not None:
            builder.add_edge(EdgeType.DERIVED_FROM, nid, ev.node_id, EpistemicStatus.INFERRED)
            builder.add_edge(EdgeType.SUPPORTED_BY, nid, ev.node_id, EpistemicStatus.INFERRED)
    for ev_id in _attr(raw, "contradicting_evidence_ids") or ():
        text = _text(ev_id)
        if not text:
            continue
        ev_node = builder.add_node(
            _local_id("evidence", text),
            NodeType.EVIDENCE,
            EpistemicStatus.UNKNOWN,
            text,
            evidence_id=text,
        )
        builder.add_edge(EdgeType.RELATES_TO, nid, ev_node.node_id, EpistemicStatus.CONFLICTED)
    sha = _text(_attr(raw, "provenance_sha256"))
    if sha:
        pid = _local_id("provenance", "claim", sha)
        builder.add_node(
            pid,
            NodeType.PROVENANCE,
            EpistemicStatus.DERIVED,
            "claim provenance",
            provenance_sha256=sha,
        )
        builder.add_edge(EdgeType.HAS_PROVENANCE, nid, pid, EpistemicStatus.DERIVED)
    author = _text(_attr(raw, "author_or_source_id"))
    if author:
        src = _add_source(builder, author)
        builder.add_edge(EdgeType.SOURCED_FROM, nid, src.node_id, EpistemicStatus.INFERRED)
    _ = dossier_claim
    return node


def _add_contradictions(builder: _Builder, claims: Iterable[Any]) -> None:
    pairs: list[tuple[str, str, str | None]] = []
    for raw in claims:
        source_claim = _text(_attr(raw, "claim_id")) or _text(_attr(raw, "statement"))
        if source_claim is None:
            continue
        src_id = _local_id("claim", source_claim[:64] if _text(_attr(raw, "claim_id")) is None else source_claim)
        for edge in _attr(raw, "contradiction_edges") or ():
            if isinstance(edge, Mapping):
                target = _text(edge.get("target_claim_id") or edge.get("reason"))
                reason = _text(edge.get("reason"))
            else:
                target = _text(_attr(edge, "target_claim_id")) or _text(edge)
                reason = _text(_attr(edge, "reason"))
            if target:
                pairs.append((src_id, _local_id("claim", target), reason))
        for target in _attr(raw, "contradictions") or ():
            text = _text(target)
            if text:
                # ClaimRecord.contradictions may be target ids or reasons.
                target_id = _local_id("claim", text)
                pairs.append((src_id, target_id, text))
    for src_id, dst_id, reason in pairs:
        if dst_id not in builder.nodes:
            builder.add_node(
                dst_id,
                NodeType.CLAIM,
                EpistemicStatus.INFERRED,
                reason or dst_id,
                referenced_only=True,
            )
        contra_id = _local_id("contradiction", *sorted((src_id, dst_id)))
        builder.add_node(
            contra_id,
            NodeType.CONTRADICTION,
            EpistemicStatus.CONFLICTED,
            reason or "contradiction",
            reason=reason,
            sides=(src_id, dst_id),
        )
        builder.add_edge(EdgeType.CONTRADICTS, src_id, dst_id, EpistemicStatus.CONFLICTED, reason=reason)
        builder.add_edge(EdgeType.CONTRADICTS, src_id, contra_id, EpistemicStatus.CONFLICTED, reason=reason)
        builder.add_edge(EdgeType.CONTRADICTS, dst_id, contra_id, EpistemicStatus.CONFLICTED, reason=reason)
        builder.add_edge(EdgeType.RELATES_TO, contra_id, src_id, EpistemicStatus.CONFLICTED)
        builder.add_edge(EdgeType.RELATES_TO, contra_id, dst_id, EpistemicStatus.CONFLICTED)


def compose_evidence_graph(
    dossier: TokenDossier | None = None,
    *,
    identity: Any = None,
    decision: Any = None,
    score: Any = None,
    security: Any = None,
    claims: Iterable[Any] | None = None,
    evidence: Any = None,
    sources: Any = None,
    metadata: Mapping[str, Any] | None = None,
) -> EvidenceGraph:
    """Project existing objects into a read-only evidence graph.

    This is a view. It does not decide, verify identity, or mint facts.
    Scalars alone are not sufficient authority; see CONSUMER_CONTRACT.
    """
    if dossier is None:
        dossier = compose_dossier(
            identity=identity,
            decision=decision,
            score=score,
            security=security,
            claims=claims,
            metadata=metadata,
        )

    builder = _Builder()
    token = _token_node(builder, dossier)

    if dossier.decision_outcome is not None:
        did = _local_id("decision", dossier.decision_outcome)
        builder.add_node(
            did,
            NodeType.DECISION,
            EpistemicStatus.DERIVED,
            f"copied decision {dossier.decision_outcome}",
            decision_outcome=dossier.decision_outcome,
            security_state=dossier.security_state,
            identity_state=dossier.identity_state,
            copied_not_evidence=True,
            consumer_contract=CONSUMER_CONTRACT,
        )
        builder.add_edge(EdgeType.RELATES_TO, did, token.node_id, EpistemicStatus.DERIVED)

    for raw in _iter_evidence(evidence):
        _add_evidence_item(builder, raw, token.node_id)
    score_items = _attr(score, "evidence_items") if score is not None else None
    for raw in score_items or ():
        _add_evidence_item(builder, raw, token.node_id)

    rich_claims = _iter_claims(claims)
    if rich_claims:
        for raw in rich_claims:
            _add_claim(builder, raw, token.node_id)
        _add_contradictions(builder, rich_claims)
    else:
        for raw in dossier.claims:
            _add_claim(builder, raw, token.node_id, dossier_claim=True)
        _add_contradictions(builder, dossier.claims)

    for raw in _iter_sources(sources):
        sid = _text(_attr(raw, "source_id")) or _text(_attr(raw, "source_name"))
        if sid:
            _add_source(
                builder,
                sid,
                source_name=_text(_attr(raw, "source_name")),
                source_type=_text(_attr(raw, "source_type")),
            )

    for index, blob in enumerate(dossier.provenance):
        source = _text(_attr(blob, "source")) or str(index)
        pid = _local_id("provenance", "dossier", source, str(index))
        builder.add_node(
            pid,
            NodeType.PROVENANCE,
            EpistemicStatus.DERIVED,
            f"dossier provenance {source}",
            payload=_deep_plain(blob),
        )
        builder.add_edge(EdgeType.HAS_PROVENANCE, token.node_id, pid, EpistemicStatus.DERIVED)

    unknowns = list(dossier.unknowns)
    if not any(n.node_type is NodeType.EVIDENCE for n in builder.nodes.values()):
        unknowns.append("evidence")
    if not any(n.node_type is NodeType.CLAIM for n in builder.nodes.values()):
        unknowns.append("claims")

    nodes = tuple(sorted(builder.nodes.values(), key=lambda n: n.node_id))
    edges = tuple(sorted(builder.edges.values(), key=lambda e: e.edge_id))
    return EvidenceGraph(
        nodes=nodes,
        edges=edges,
        identity_state=dossier.identity_state,
        canonical_token_id=dossier.canonical_token_id if _canonical_token_allowed(dossier) else None,
        security_state=dossier.security_state,
        decision_outcome=dossier.decision_outcome,
        conflicts=tuple(dossier.conflicts),
        unknowns=tuple(unknowns),
        epistemic_map=dossier.epistemic_map,
        provenance=tuple(_freeze_mapping(p) for p in dossier.provenance),
    )
