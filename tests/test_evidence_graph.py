"""Read-only claim/evidence graph — isolated from runtime, Lane A, and P5."""
from __future__ import annotations

import warnings

import pytest

from pathlib import Path
from types import SimpleNamespace

from architecture.identity.types import (
    ChainIdentity,
    IdentityResolution,
    IdentityState,
    TokenIdentity,
)
from tests._mint_support import _mint_verified_for_tests
from architecture.knowledge.dossier import (
    AliasKind,
    COMPOSER_VERSION,
    EpistemicStatus,
    TokenDossier,
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
    mint: bool | None = None,
) -> IdentityResolution:
    resolution = IdentityResolution(
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
    if mint is None:
        mint = state is IdentityState.VERIFIED
    if mint:
        return _mint_verified_for_tests(resolution)
    return resolution


def _identity_unminted(
    *,
    state: IdentityState = IdentityState.VERIFIED,
    chain: str | None = "solana",
    address: str | None = "So11111111111111111111111111111111111111112",
    token_id: str | None = "abc123canonicalid",
    symbol: str | None = "ABC",
    conflicts: tuple[str, ...] = (),
    provenance: tuple[dict, ...] = (),
) -> IdentityResolution:
    """Hand-built exact-typed VERIFIED without resolver mint (A1/A2)."""
    return _identity(
        state=state,
        chain=chain,
        address=address,
        token_id=token_id,
        symbol=symbol,
        conflicts=conflicts,
        provenance=provenance,
        mint=False,
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
    # Fix B (Agent-19): dossier= alone is not authority — must pass raw identity=.
    dossier = compose_dossier(identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"))
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        ignored = compose_evidence_graph(dossier=dossier)
    assert ignored.canonical_token_id is None
    assert ignored.identity_state is None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        graph = compose_evidence_graph(
            identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"),
        )
    assert not any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert graph.canonical_token_id == "abc123canonicalid"
    assert graph.identity_state == "VERIFIED"


# --- W1.3 Fix B: always-recompose (caller dossier never authority) ---

def _hand_built_verified_dossier(*, token_id: str = "FORGED", version: str = COMPOSER_VERSION):
    return TokenDossier(
        canonical_token_id=token_id,
        join_keys=(),
        identity_state="VERIFIED",
        security_state=None,
        decision_outcome=None,
        opportunity_score=None,
        epistemic_map=(),
        conflicts=(),
        unknowns=(),
        provenance=(),
        composed_at=None,
        claims=(),
        composer_version=version,
    )


def test_w13_t5_hand_built_dossier_no_canonical_token_node():
    """T5: W2 hand-built TokenDossier(VERIFIED, forged id) → no canonical (dossier= discarded)."""
    forged = _hand_built_verified_dossier(token_id="FORGED")
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        graph = compose_evidence_graph(dossier=forged)
    assert graph.canonical_token_id is None
    token = _token(graph)
    assert token.metadata.get("canonical") is False
    assert not token.node_id.startswith("token:canonical")


def test_w13_t6_compose_via_real_verified_identity_still_works():
    """T6: W2 compose via identity=real VERIFIED still works."""
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"),
    )
    assert graph.canonical_token_id == "abc123canonicalid"
    assert _token(graph).metadata["canonical"] is True
    assert _token(graph).node_id.startswith("token:canonical")


def test_w13_t8_hand_built_forged_dossier_fails_b_path_a_alone_insufficient():
    """T8: A-alone is insufficient — hand-built dossier must fail B (always-recompose).

    Fix A only hardens compose_dossier type checks. Without Fix B, a caller can
    hand-build TokenDossier(identity_state='VERIFIED', canonical_token_id=...)
    and pass it to compose_evidence_graph. Fix B always recomposes from raw kwargs
    and discards dossier=.
    """
    forged = _hand_built_verified_dossier(token_id="FORGED_A_ALONE_INSUFFICIENT")
    assert forged.identity_state == "VERIFIED"
    assert forged.canonical_token_id == "FORGED_A_ALONE_INSUFFICIENT"
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        graph = compose_evidence_graph(dossier=forged)
    assert graph.canonical_token_id is None
    assert _token(graph).metadata.get("canonical") is False
    wrong_seal = _hand_built_verified_dossier(token_id="FORGED_WRONG_SEAL")
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        g2 = compose_evidence_graph(dossier=wrong_seal)
    assert g2.canonical_token_id is None


def test_w13_t9_spoofed_identity_via_w2_compose_dossier_path_no_canonical():
    """T9: dynamic IR+TI spoof through W2 identity= kwargs yields no canonical."""
    FakeTI = type(
        "TokenIdentity",
        (),
        {
            "__module__": ".".join(("architecture", "identity", "types")),
            "token_id": "SPOOF_VIA_W2",
            "state": "VERIFIED",
            "chain": "solana",
            "address_canonical": "So111",
            "address_input": "So111",
            "symbol_alias": "FAKE",
        },
    )
    FakeIR = type(
        "IdentityResolution",
        (),
        {
            "__module__": ".".join(("architecture", "identity", "types")),
            "token": FakeTI(),
            "conflicts": (),
            "provenance": (),
        },
    )
    graph = compose_evidence_graph(identity=FakeIR())
    assert graph.canonical_token_id is None
    assert graph.identity_state is None
    assert _token(graph).metadata.get("canonical") is False


def test_w13_t10_combined_a_and_b_both_paths_closed_on_w2():
    """T10: combined A+B — spoofed identity and hand-built dossier both closed on W2."""
    FakeTI = type(
        "TokenIdentity",
        (),
        {
            "__module__": ".".join(("architecture", "identity", "types")),
            "token_id": "COMBINED_SPOOF",
            "state": "VERIFIED",
            "chain": "solana",
            "address_canonical": "x",
            "address_input": "x",
            "symbol_alias": "Z",
        },
    )
    FakeIR = type(
        "IdentityResolution",
        (),
        {
            "__module__": ".".join(("architecture", "identity", "types")),
            "token": FakeTI(),
            "conflicts": (),
            "provenance": (),
        },
    )
    g_spoof = compose_evidence_graph(identity=FakeIR())
    assert g_spoof.canonical_token_id is None

    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        g_hand = compose_evidence_graph(dossier=_hand_built_verified_dossier())
    assert g_hand.canonical_token_id is None

    # Positive control: raw identity= still works (dossier= alone never authorizes).
    g_ok = compose_evidence_graph(
        identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"),
    )
    assert g_ok.canonical_token_id == "abc123canonicalid"


def test_w13_compose_dossier_object_alone_does_not_authorize_canonical():
    """Even a real compose_dossier output is not W2 authority without raw kwargs."""
    dossier = compose_dossier(
        identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid")
    )
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        graph = compose_evidence_graph(dossier=dossier)
    assert graph.canonical_token_id is None
    assert graph.identity_state is None


def test_w13_t11_hand_built_verified_dossier_does_not_authorize_canonical():
    """T11 (Agent-19 / Agent-16): seal symbols absent; hand dossier= discarded → no canonical."""
    dossier_src = (ROOT / "architecture" / "knowledge" / "dossier.py").read_text(encoding="utf-8")
    graph_src = (ROOT / "architecture" / "knowledge" / "evidence_graph.py").read_text(encoding="utf-8")
    for src in (dossier_src, graph_src):
        assert "_COMPOSER_SEAL" not in src
        assert "is_composer_sealed" not in src
        assert "composer_seal" not in src
    # Import surface must not expose seal helpers
    import architecture.knowledge.dossier as dossier_mod
    assert not hasattr(dossier_mod, "_COMPOSER_SEAL")
    assert not hasattr(dossier_mod, "is_composer_sealed")

    forged = _hand_built_verified_dossier(token_id="SEAL_FORGE_BYPASS")
    assert forged.identity_state == "VERIFIED"
    assert forged.canonical_token_id == "SEAL_FORGE_BYPASS"
    try:
        object.__setattr__(forged, "canonical_token_id", "SEAL_FORGE_BYPASS")
    except Exception:
        pass
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        graph = compose_evidence_graph(dossier=forged)
    assert graph.canonical_token_id is None
    assert graph.identity_state is None
    assert _token(graph).metadata.get("canonical") is False

    # dossier= plus spoofed identity= still closed by Fix A
    FakeTI = type(
        "TokenIdentity",
        (),
        {
            "__module__": ".".join(("architecture", "identity", "types")),
            "token_id": "SPOOF_WITH_DISCARDED_DOSSIER",
            "state": "VERIFIED",
            "chain": "solana",
            "address_canonical": "x",
            "address_input": "x",
            "symbol_alias": "Z",
        },
    )
    FakeIR = type(
        "IdentityResolution",
        (),
        {
            "__module__": ".".join(("architecture", "identity", "types")),
            "token": FakeTI(),
            "conflicts": (),
            "provenance": (),
        },
    )
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        g2 = compose_evidence_graph(dossier=forged, identity=FakeIR())
    assert g2.canonical_token_id is None

    g_ok = compose_evidence_graph(
        identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"),
    )
    assert g_ok.canonical_token_id == "abc123canonicalid"


# --- W1.4 resolver-mint marker (graph refuse unminted VERIFIED via identity=) ---


def test_w14_a2_unminted_verified_graph_no_canonical():
    """A2: unminted exact-typed VERIFIED via identity= → no canonical on graph."""
    ident = _identity_unminted(token_id="abc123canonicalid")
    graph = compose_evidence_graph(identity=ident)
    assert graph.canonical_token_id is None
    assert "identity_verified_unminted" in graph.unknowns
    assert graph.identity_state is None
    for node in graph.nodes:
        if node.node_type is NodeType.TOKEN:
            assert node.metadata.get("canonical") is not True
            assert node.metadata.get("canonical_token_id") in (None, "")


def test_w14_a3_minted_graph_canonical():
    """A3 mirror: minted VERIFIED via identity= still authorizes graph canonical."""
    graph = compose_evidence_graph(
        identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid")
    )
    assert graph.canonical_token_id == "abc123canonicalid"
    assert graph.identity_state == "VERIFIED"


def test_dossier_kwarg_emits_deprecation_and_still_discards():
    """dossier= warns and remains non-authority (compat shim)."""
    forged = _hand_built_verified_dossier(token_id="DEPRECATE_FORGE")
    with pytest.warns(DeprecationWarning, match=r"dossier=.*deprecated"):
        graph = compose_evidence_graph(dossier=forged)
    assert graph.canonical_token_id is None
    assert graph.identity_state is None


def test_raw_kwargs_compose_does_not_emit_dossier_deprecation():
    """identity= path must not warn about dossier=."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        graph = compose_evidence_graph(
            identity=_identity(state=IdentityState.VERIFIED, token_id="abc123canonicalid"),
        )
    assert graph.canonical_token_id == "abc123canonicalid"
    assert not any(
        issubclass(w.category, DeprecationWarning) and "dossier=" in str(w.message)
        for w in caught
    )

