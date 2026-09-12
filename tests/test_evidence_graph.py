"""Read-only claim/evidence graph — isolated from runtime, Lane A, and P5."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from architecture.identity.types import (
    ChainIdentity,
    IdentityResolution,
    IdentityState,
    TokenIdentity,
)
from architecture.knowledge.dossier import (
    AliasKind,
    EpistemicStatus,
    compose_dossier,
)
from architecture.knowledge.evidence_graph import (
    CONSUMER_CONTRACT,
    EdgeType,
    NodeType,
    compose_evidence_graph,
)

ROOT = Path(__file__).resolve().parents[1]
GRAPH_SRC = (ROOT / "architecture" / "knowledge" / "evidence_graph.py").read_text(encoding="utf-8")
DOSSIER_SRC = (ROOT / "architecture" / "knowledge" / "dossier.py").read_text(encoding="utf-8")

FORBIDDEN_IMPORT_SNIPPETS = (
    "architecture.runtime",
    "architecture.pipeline",
    "discovery.",
    "paper_trading",
    "architecture.cognitive.memory.observation",
    "architecture.cognitive.loop.orchestrator",
    "import sqlite3",
    "import hashlib",
    "architecture.identity",
    "architecture.decision",
    "architecture.security",
    "architecture.scoring",
    "architecture.intelligence",
)

PRODUCTION_SURFACES = (
    ROOT / "architecture" / "runtime" / "__main__.py",
    ROOT / "architecture" / "runtime" / "__init__.py",
    ROOT / "architecture" / "runtime" / "observation_loop.py",
    ROOT / "architecture" / "pipeline" / "orchestrator.py",
    ROOT / "architecture" / "knowledge" / "__init__.py",
)


def _identity(
    *,
    state: IdentityState,
    chain: str | None = "solana",
    address: str | None = "So11111111111111111111111111111111111111112",
    token_id: str | None = None,
    symbol: str | None = "ABC",
    conflicts: tuple[str, ...] = (),
    provenance: tuple[dict, ...] = (),
) -> IdentityResolution:
    return IdentityResolution(
        chain=ChainIdentity(chain, chain, state, "fixture"),
        token=TokenIdentity(
            chain=chain,
            address_canonical=address,
            address_input=address,
            token_id=token_id,
            symbol_alias=symbol,
            name_alias=None,
            state=state,
            reason="fixture",
        ),
        pool=None,
        dex=None,
        sources=(),
        conflicts=conflicts,
        provenance=provenance,
    )


def _decision(**kwargs):
    defaults = dict(
        outcome="NO_TRADE",
        identity_state=None,
        security_state=None,
        opportunity_score=None,
        unknowns=(),
        hard_vetoes=(),
        provenance={},
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _score(**kwargs):
    defaults = dict(
        opportunity_score=12.0,
        token_chain=None,
        token_address=None,
        token_symbol=None,
        missing_unknowns=(),
        provenance_sha256="",
        evidence_items=(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _security(state: str, **kwargs):
    return SimpleNamespace(state=state, **kwargs)


def _claim(**kwargs):
    defaults = dict(
        statement="token has liquidity",
        trust_class="AI_INTERPRETATION",
        category="RESEARCH",
        claim_id="c1",
        contradiction_edges=(),
        contradicting_evidence_ids=(),
        evidence_links=(),
        author_or_source_id=None,
        provenance_sha256=None,
        review_status="ACTIVE",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _evidence(**kwargs):
    defaults = dict(
        key="liquidity_usd",
        description="pool liquidity",
        value=1000.0,
        provider="gecko",
        timestamp=1.0,
        status="UNKNOWN",
        source_field="liquidity",
        sha256="",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _nodes(graph, ntype: NodeType):
    return [n for n in graph.nodes if n.node_type is ntype]


def _token(graph):
    tokens = _nodes(graph, NodeType.TOKEN)
    assert tokens
    return tokens[0]


def test_empty_input_has_no_canonical_and_records_unknowns():
    graph = compose_evidence_graph()
    assert graph.canonical_token_id is None
    assert graph.identity_state is None
    assert graph.decision_outcome is None
    assert "identity_state" in graph.unknowns
    assert "evidence" in graph.unknowns
    assert "claims" in graph.unknowns
    assert graph.consumer_contract == CONSUMER_CONTRACT
    assert not any(n.metadata.get("canonical") for n in _nodes(graph, NodeType.TOKEN))


def test_one_token_unresolved():
    graph = compose_evidence_graph(identity=_identity(state=IdentityState.UNRESOLVED, token_id=None))
    token = _token(graph)
    assert token.metadata["canonical"] is False
    assert graph.canonical_token_id is None
    assert graph.identity_state == "UNRESOLVED"


def test_verified_identity_creates_canonical_token_node():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"),
    )
    token = _token(graph)
    assert graph.identity_state == "VERIFIED"
    assert graph.canonical_token_id == "abc123canonicalid"
    assert token.metadata["canonical"] is True
    assert token.node_id.startswith("token:canonical")


def test_unresolved_identity_has_no_canonical_token():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id="FORGED_NOT_A_HASH"),
    )
    token = _token(graph)
    assert graph.canonical_token_id is None
    assert token.metadata["canonical"] is False
    assert "canonical" not in token.node_id


def test_conflicting_identity_has_no_canonical_token():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.CONFLICT, token_id="looks", conflicts=("src",)),
    )
    assert graph.identity_state == "CONFLICT"
    assert graph.canonical_token_id is None
    assert _token(graph).epistemic_status is EpistemicStatus.CONFLICTED
    assert "src" in graph.conflicts


def test_invalid_identity_has_no_canonical_token():
    graph = compose_evidence_graph(identity=SimpleNamespace(state="VERIFIED", token_id="FORGED"))
    assert graph.identity_state is None
    assert graph.canonical_token_id is None
    assert _token(graph).metadata["canonical"] is False
    assert "identity_input_invalid" in graph.unknowns


def test_evidence_attached_to_token():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        evidence=(_evidence(key="liq", description="liquidity", status="UNKNOWN"),),
    )
    ev = _nodes(graph, NodeType.EVIDENCE)
    assert ev
    token_id = _token(graph).node_id
    assert any(
        e.edge_type is EdgeType.ATTACHED_TO and e.source_id == ev[0].node_id and e.target_id == token_id
        for e in graph.edges
    )


def test_claim_derived_from_evidence():
    link = SimpleNamespace(
        evidence_id="ev1",
        description="on-chain liquidity",
        source_id="gecko",
        status="DERIVED",
        raw_sha256="abc",
        pointer="row1",
        provider=None,
        sha256=None,
        key=None,
        value=None,
        source_field=None,
    )
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        claims=(_claim(claim_id="c1", evidence_links=(link,)),),
    )
    assert _nodes(graph, NodeType.CLAIM)
    assert _nodes(graph, NodeType.EVIDENCE)
    assert any(e.edge_type is EdgeType.DERIVED_FROM for e in graph.edges)
    assert any(e.edge_type is EdgeType.SUPPORTED_BY for e in graph.edges)


def test_claim_with_provenance():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        claims=(_claim(claim_id="c1", provenance_sha256="provhash1"),),
    )
    assert _nodes(graph, NodeType.PROVENANCE)
    assert any(e.edge_type is EdgeType.HAS_PROVENANCE for e in graph.edges)


def test_contradictory_claims_both_remain():
    a = _claim(claim_id="a", statement="pool is safe", contradiction_edges=({"target_claim_id": "b", "reason": "disagree"},))
    b = _claim(claim_id="b", statement="pool is unsafe", contradiction_edges=({"target_claim_id": "a", "reason": "disagree"},))
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        claims=(a, b),
    )
    claims = {n.metadata.get("claim_id"): n for n in _nodes(graph, NodeType.CLAIM)}
    assert "a" in claims and "b" in claims
    assert _nodes(graph, NodeType.CONTRADICTION)
    assert any(e.edge_type is EdgeType.CONTRADICTS for e in graph.edges)
    assert all(n.epistemic_status is EpistemicStatus.INFERRED for n in claims.values() if n.metadata.get("claim_id") in {"a", "b"})


def test_multiple_evidence_items():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        evidence=(_evidence(key="liq"), _evidence(key="vol", description="volume")),
    )
    keys = {n.metadata.get("evidence_id") for n in _nodes(graph, NodeType.EVIDENCE)}
    assert keys >= {"liq", "vol"}


def test_duplicate_evidence_is_deduplicated():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        evidence=(_evidence(key="liq"), _evidence(key="liq", description="liquidity-dup")),
    )
    ev = [n for n in _nodes(graph, NodeType.EVIDENCE) if n.metadata.get("evidence_id") == "liq"]
    assert len(ev) == 1


def test_duplicate_claims_are_deduplicated():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        claims=(_claim(claim_id="c1", statement="one"), _claim(claim_id="c1", statement="two")),
    )
    assert len([n for n in _nodes(graph, NodeType.CLAIM) if n.metadata.get("claim_id") == "c1"]) == 1


def test_missing_provenance_does_not_invent_provenance_nodes_for_claims():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None, provenance=()),
        claims=(_claim(claim_id="c1", provenance_sha256=None),),
    )
    claim_prov = [
        e for e in graph.edges
        if e.edge_type is EdgeType.HAS_PROVENANCE and e.source_id.startswith("claim:")
    ]
    assert claim_prov == []


def test_unknown_evidence_stays_unknown():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        evidence=(_evidence(key="honeypot", status="UNKNOWN", value=None),),
    )
    ev = next(n for n in _nodes(graph, NodeType.EVIDENCE) if n.metadata.get("evidence_id") == "honeypot")
    assert ev.epistemic_status is EpistemicStatus.UNKNOWN


def test_inferred_claim_is_inferred():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        claims=(_claim(claim_id="c1"),),
    )
    claim = _nodes(graph, NodeType.CLAIM)[0]
    assert claim.epistemic_status is EpistemicStatus.INFERRED
    assert all(n.epistemic_status is not EpistemicStatus.OBSERVED for n in graph.nodes)


def test_factual_premise_label_copied_but_not_promoted():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        claims=(_claim(claim_id="c1", category="FACTUAL_PREMISE", statement="this is verified fact"),),
    )
    claim = _nodes(graph, NodeType.CLAIM)[0]
    assert claim.metadata["category"] == "FACTUAL_PREMISE"
    assert claim.epistemic_status is EpistemicStatus.INFERRED
    assert all(n.epistemic_status is not EpistemicStatus.OBSERVED for n in graph.nodes)
    assert "FACTUAL_PREMISE" not in GRAPH_SRC or "copied" in GRAPH_SRC


def test_decision_buy_with_unresolved_identity():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        decision=_decision(outcome="BUY"),
    )
    assert graph.decision_outcome == "BUY"
    assert graph.identity_state == "UNRESOLVED"
    assert graph.canonical_token_id is None
    assert _nodes(graph, NodeType.DECISION)
    assert CONSUMER_CONTRACT in graph.consumer_contract
    assert _token(graph).metadata["canonical"] is False


def test_security_pass_conflicting_with_decision_reject():
    graph = compose_evidence_graph(
        security=_security("PASS"),
        decision=_decision(outcome="REJECT", security_state="REJECT"),
    )
    assert graph.security_state == "PASS"
    assert graph.decision_outcome == "REJECT"
    assert any("security_state_disagreement" in c for c in graph.conflicts)
    assert graph.consumer_contract == CONSUMER_CONTRACT


def test_canonical_identity_cannot_come_from_symbol():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, address=None, token_id=None, symbol="PEPE"),
        score=_score(token_symbol="PEPE", token_chain="solana"),
    )
    token = _token(graph)
    assert graph.canonical_token_id is None
    assert token.metadata["canonical"] is False
    assert token.metadata.get("identifier_kind") in {"display", "unresolved", "operational"}
    assert not token.node_id.startswith("token:canonical:")


def test_canonical_identity_cannot_come_from_operational_token_id():
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id="FORGED_NOT_A_HASH"),
    )
    token = _token(graph)
    assert graph.canonical_token_id is None
    assert token.metadata["canonical"] is False
    assert token.metadata.get("identifier_kind") in {"unvalidated", "operational"}
    assert token.metadata.get("identifier_value") != "FORGED_NOT_A_HASH" or token.metadata.get("identifier_kind") == "unvalidated"
    assert not token.node_id.startswith("token:canonical")
    dossier = compose_dossier(identity=_identity(state=IdentityState.UNRESOLVED, token_id="FORGED_NOT_A_HASH"))
    assert not any(k.kind is AliasKind.CANONICAL for k in dossier.join_keys)


def test_deterministic_graph_output():
    kwargs = dict(
        identity=_identity(state=IdentityState.VERIFIED, token_id="sameid", symbol="AAA"),
        decision=_decision(outcome="WATCH"),
        claims=(_claim(claim_id="c1"), _claim(claim_id="c2", statement="other")),
        evidence=(_evidence(key="liq"),),
    )
    a = compose_evidence_graph(**kwargs)
    b = compose_evidence_graph(**kwargs)
    assert a == b
    assert a.as_dict() == b.as_dict()


def test_source_objects_remain_unchanged():
    ident = _identity(state=IdentityState.CONFLICT, token_id=None, conflicts=("source_disagreement",))
    claims = [_claim(claim_id="c1")]
    ev = [_evidence(key="liq")]
    compose_evidence_graph(identity=ident, claims=claims, evidence=ev)
    assert ident.conflicts == ("source_disagreement",)
    assert claims[0].claim_id == "c1"
    assert ev[0].key == "liq"


def test_exported_graph_is_mutation_safe():
    nested = {"inner": {"k": "v"}}
    ident = _identity(
        state=IdentityState.VERIFIED,
        token_id="abc123canonicalid",
        provenance=({"provider": "gecko", "nested": nested},),
    )
    graph = compose_evidence_graph(identity=ident)
    exported = graph.as_dict()
    exported["canonical_token_id"] = "forged"
    exported["nodes"][0]["metadata"]["canonical"] = False
    exported["provenance"][0]["nested"]["inner"]["k"] = "mutated"
    nested["inner"]["k"] = "caller"
    assert graph.canonical_token_id == "abc123canonicalid"
    assert _token(graph).metadata["canonical"] is True
    assert graph.provenance[0]["nested"]["inner"]["k"] == "v"


def test_no_runtime_import_in_graph_source():
    for snippet in FORBIDDEN_IMPORT_SNIPPETS:
        assert snippet not in GRAPH_SRC, snippet
    assert "architecture.identity" not in GRAPH_SRC


def test_no_database_network_or_filesystem(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("graph must not touch the filesystem")

    monkeypatch.setattr("builtins.open", _boom)
    compose_evidence_graph(
        identity=_identity(state=IdentityState.UNRESOLVED, token_id=None),
        claims=(_claim(),),
        evidence=(_evidence(),),
    )


def test_production_surfaces_do_not_reference_graph():
    for path in PRODUCTION_SURFACES:
        text = path.read_text(encoding="utf-8")
        assert "evidence_graph" not in text, path
        assert "compose_evidence_graph" not in text, path


def test_knowledge_init_does_not_export_graph():
    import architecture.knowledge as knowledge_pkg
    assert not hasattr(knowledge_pkg, "compose_evidence_graph")
    assert not hasattr(knowledge_pkg, "EvidenceGraph")


def test_isolated_import_does_not_load_lane_a_or_runtime():
    import importlib.util
    import subprocess
    import sys

    code = (
        "import importlib.util, sys\n"
        "from pathlib import Path\n"
        "root = Path(r'''" + str(ROOT) + "''')\n"
        "sys.path.insert(0, str(root / 'architecture' / 'knowledge'))\n"
        "dpath = root / 'architecture' / 'knowledge' / 'dossier.py'\n"
        "gpath = root / 'architecture' / 'knowledge' / 'evidence_graph.py'\n"
        "dspec = importlib.util.spec_from_file_location('dossier', dpath)\n"
        "dmod = importlib.util.module_from_spec(dspec)\n"
        "sys.modules['dossier'] = dmod\n"
        "dspec.loader.exec_module(dmod)\n"
        "gspec = importlib.util.spec_from_file_location('ahos_graph_isolated', gpath)\n"
        "gmod = importlib.util.module_from_spec(gspec)\n"
        "sys.modules[gspec.name] = gmod\n"
        "gspec.loader.exec_module(gmod)\n"
        "banned = [k for k in sys.modules if k == 'discovery' "
        "or k.startswith('discovery.') "
        "or k.startswith('paper_trading') "
        "or k.startswith('architecture.runtime') "
        "or k.startswith('architecture.pipeline') "
        "or k.startswith('architecture.cognitive.loop') "
        "or 'memory.observation' in k "
        "or k == 'architecture.identity' "
        "or k.startswith('architecture.identity.')]\n"
        "assert banned == [], banned\n"
        "assert gmod.GRAPH_VERSION\n"
        "assert gmod.compose_evidence_graph().canonical_token_id is None\n"
    )
    proc = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_consumer_contract_is_explicit_on_graph():
    graph = compose_evidence_graph(decision=_decision(outcome="BUY"))
    assert "not sufficient authority" in graph.consumer_contract
    assert graph.decision_outcome == "BUY"
    assert graph.identity_state is None


def test_w1_dossier_can_be_projected_without_recompose_identity():
    dossier = compose_dossier(identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"))
    graph = compose_evidence_graph(dossier=dossier)
    assert graph.canonical_token_id == "abc123canonicalid"
    assert graph.identity_state == "VERIFIED"
