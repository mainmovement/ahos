"""Enforce the agent taxonomy map against live code.

The map in docs/governance/agent_taxonomy_map.json is governance infrastructure,
not a report. This test pins it to the actual registries so that a silent merge,
an invented agent, or an authority inflation fails the build instead of shipping.
"""

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MAP_PATH = REPO / "docs" / "governance" / "agent_taxonomy_map.json"

TAXONOMY_SOURCES = {
    "slice1_logical": "ahos_org/registry.py",
    "ops_matrix": "config/agent_registry.yaml",
    "runtime_map": "docs/AGENT_MAPPING.md",
    "specialist_blueprint": "docs/agents/PLANNED_19_AGENT_MAP.md",
}


@pytest.fixture(scope="module")
def taxonomy_map():
    assert MAP_PATH.is_file(), f"taxonomy map missing at {MAP_PATH}"
    with MAP_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def canonical_ids():
    from ahos_org.registry import CANONICAL_AGENT_IDS

    return tuple(CANONICAL_AGENT_IDS)


@pytest.fixture(scope="module")
def deny_capabilities():
    from ahos_org.policy import GLOBAL_DENY_CAPABILITIES

    return set(GLOBAL_DENY_CAPABILITIES)


# --- structural integrity -------------------------------------------------


def test_map_declares_reconciliation_not_merge(taxonomy_map):
    assert taxonomy_map["status"] == "RECONCILED_NOT_MERGED"
    assert "SILENT_MERGE_FORBIDDEN" in "".join(taxonomy_map["law"])


def test_every_declared_taxonomy_source_exists(taxonomy_map):
    for entry in taxonomy_map["taxonomies"].values():
        source = entry["source"]
        if source.startswith("M0 "):
            continue
        assert (REPO / source).is_file(), (
            f"taxonomy {entry['namespace']} cites missing source {source}"
        )


def test_map_does_not_invent_agents(taxonomy_map, canonical_ids):
    anchors = {m["anchor"] for m in taxonomy_map["mappings"]}
    assert anchors == set(canonical_ids), (
        "map anchors must be exactly the 19 canonical Slice-1 ids; "
        "adding or removing one is a governance change requiring review"
    )


def test_map_count_matches_registry(taxonomy_map, canonical_ids):
    assert len(taxonomy_map["mappings"]) == len(canonical_ids)


def test_collisions_are_recorded_not_aliased(taxonomy_map):
    """Overlapping ids must be listed as collisions, never absorbed."""
    collisions = taxonomy_map["namespace_collisions"]
    assert collisions, "known collisions must stay explicit"
    for collision in collisions:
        member_taxonomies = [m["taxonomy"] for m in collision["members"]]
        assert len(member_taxonomies) == len(set(member_taxonomies)), (
            f"collision {collision['short_id']} merges two members from one taxonomy"
        )


def test_every_relation_carries_provenance(taxonomy_map):
    for mapping in taxonomy_map["mappings"]:
        for relation in mapping["relations"]:
            assert "taxonomy" in relation, f"{mapping['anchor']} relation lacks taxonomy"
            assert "id" in relation, f"{mapping['anchor']} relation lacks id"
            assert "relation" in relation, f"{mapping['anchor']} relation lacks relation kind"
            assert "provenance" in relation and relation["provenance"], (
                f"{mapping['anchor']} -> {relation['id']} has no provenance "
                "(SILENT_MERGE_FORBIDDEN)"
            )


def test_provenance_cites_a_real_file(taxonomy_map):
    """Cross-taxonomy relations cite the other three taxonomies; the Slice-1
    anchor's own provenance lives in its maturity evidence (a relation never
    points back at its own taxonomy). Both count."""
    cited = set()
    for mapping in taxonomy_map["mappings"]:
        for relation in mapping["relations"]:
            for source in TAXONOMY_SOURCES.values():
                if source in relation["provenance"]:
                    cited.add(source)
                    assert (REPO / source).is_file(), relation["provenance"]
        for source in TAXONOMY_SOURCES.values():
            if source in mapping["maturity"]["evidence"]:
                cited.add(source)
                assert (REPO / source).is_file(), mapping["maturity"]["evidence"]
    assert cited == set(TAXONOMY_SOURCES.values()), (
        "map must keep citing all four taxonomies; dropping one is a silent merge"
    )


# --- authority invariants -------------------------------------------------


def test_no_mapping_grants_decision_authority(taxonomy_map):
    """DECIDE lives only with AG-15 / AG-16 in the ops matrix (INV-DECIDE-HOLDERS)."""
    offenders = [m["anchor"] for m in taxonomy_map["mappings"] if m.get("decision_authority")]
    assert offenders == [], (
        f"Slice-1 anchors must not hold DECIDE: {offenders}. "
        "Only AG-15 Decision Engine and AG-16 Paper-Trading hold allowed_authority [DECIDE]."
    )


def test_no_mapping_allows_a_globally_denied_capability(taxonomy_map, deny_capabilities):
    denied = set(deny_capabilities)
    for mapping in taxonomy_map["mappings"]:
        allowed = set(mapping.get("slice1_allowed", ()))
        overlap = allowed & denied
        assert not overlap, f"{mapping['anchor']} allows denied capability {sorted(overlap)}"


def test_every_allowed_capability_is_in_the_real_catalog(taxonomy_map):
    """The map must cite tokens the governance engine actually knows.

    Unknown tokens are denied by GovernanceEngine, so a fabricated capability
    token would be silently un-enforceable. Pin the map to the real catalog.
    """
    from ahos_org.policy import INTERNAL_CAPABILITIES

    known = set(INTERNAL_CAPABILITIES)
    for mapping in taxonomy_map["mappings"]:
        allowed = set(mapping.get("slice1_allowed", ()))
        assert allowed, f"{mapping['anchor']} declares no slice1_allowed capabilities"
        unknown = allowed - known
        assert not unknown, (
            f"{mapping['anchor']} cites capabilities absent from "
            f"ahos_org/policy.py INTERNAL_CAPABILITIES: {sorted(unknown)}"
        )


def test_no_mapping_allows_execution(taxonomy_map, deny_capabilities):
    """Real trading is disabled; no mapped role may carry execution authority."""
    for mapping in taxonomy_map["mappings"]:
        for cap in mapping.get("slice1_allowed", ()):
            assert not cap.startswith("trading.live"), mapping["anchor"]
            assert "execution" not in cap, f"{mapping['anchor']} allows execution"


def test_all_anchors_registered_and_blocked_from_execution(taxonomy_map):
    """INV-NO-SLICE1-EXECUTION: maturity 0 < MINIMUM_MATURITY_FOR_ALLOW 2."""
    from ahos_org.policy import MINIMUM_MATURITY_FOR_ALLOW

    for mapping in taxonomy_map["mappings"]:
        maturity = mapping["maturity"]
        assert maturity["level"] == 0, f"{mapping['anchor']} maturity must stay REGISTERED (0)"
        assert maturity["name"] == "REGISTERED"
        assert 0 < MINIMUM_MATURITY_FOR_ALLOW, "minimum maturity floor must be positive"


def test_global_deny_law_still_covered(taxonomy_map, deny_capabilities):
    """The map must keep naming the deny tokens that keep trading closed."""
    blob = json.dumps(taxonomy_map)
    assert "trading.live" in deny_capabilities
    assert "INV-NO-SLICE1-EXECUTION" in blob
    assert "INV-GLOBAL-DENY" in blob


# --- non-claims ------------------------------------------------------------


POSITIVE_READINESS_LABELS = (
    "OPERATIONAL",
    "OPERATIONALLY_TRUSTED",
    "OPERATOR_READY",
    "PRODUCTION_READY",
    "VERIFIED_READY",
    "COMPLETE",
)


def _labels_found(text):
    return [label for label in POSITIVE_READINESS_LABELS if label in text]


def test_map_makes_no_positive_readiness_claim(taxonomy_map):
    """Ban readiness labels from the fields where a claim would live.

    A bare substring ban over the whole map is wrong: the map deliberately
    *writes* the negation "NO_AGENT_IS_OPERATIONAL_BY_VIRTUE_OF_BEING_MAPPED".
    So the positive labels are banned from claim-bearing fields instead, and
    the negations themselves are required to survive (below), so a future edit
    cannot quietly delete the disclaimer either.
    """
    assert not _labels_found(taxonomy_map["status"]), taxonomy_map["status"]

    for entry in taxonomy_map["taxonomies"].values():
        assert not _labels_found(entry["honest_class"]), entry["namespace"]

    for mapping in taxonomy_map["mappings"]:
        assert not _labels_found(mapping["maturity"]["name"]), mapping["anchor"]
        # A gap is a finding of absence, so it may quote a status token while
        # explicitly negating it ("OPERATOR_READY = NOT_VERIFIED"). A bare
        # positive label with no negator beside it is still a claim.
        gap = mapping.get("gap", "")
        for label in _labels_found(gap):
            assert any(neg in gap for neg in ("NOT_VERIFIED", "not ", "no ", "never ")), (
                mapping["anchor"],
                label,
            )
        for relation in mapping["relations"]:
            assert not _labels_found(relation["relation"]), (
                mapping["anchor"],
                relation["id"],
            )

    for invariant in taxonomy_map["authority_invariants"]:
        assert not _labels_found(invariant["claim"]), invariant["id"]


def test_map_keeps_its_denials_of_readiness(taxonomy_map):
    """The guard above is only meaningful while the disclaimer survives."""
    assert "NO_AGENT_IS_OPERATIONAL_BY_VIRTUE_OF_BEING_MAPPED" in "".join(
        taxonomy_map["law"]
    )
    blob = " ".join(taxonomy_map["explicit_non_claims"])
    assert "does not grant" in blob
    assert "not evidence that the role is implemented" in blob
    assert "All 19 Slice-1 anchors remain at maturity REGISTERED (0)" in blob


def test_explicit_non_claims_present(taxonomy_map):
    claims = taxonomy_map["explicit_non_claims"]
    assert len(claims) >= 5
    blob = " ".join(claims)
    assert "does not merge" in blob
    assert "does not grant" in blob
    assert "not evidence that the role is implemented" in blob


def test_m0_roles_without_anchor_are_recorded(taxonomy_map):
    """Each entry must state that it has no Slice-1 logical anchor.

    F is the subtle case: it has real implemented substance (research_worker +
    research_host) but still no Slice-1 *logical* anchor, so it is phrased as
    "not as a Slice-1 logical agent" rather than "NO Slice-1 anchor exists."
    """
    for entry in taxonomy_map["m0_roles_without_slice1_anchor"]:
        assert entry["m0_role"] in set("ABCDEFGH"), entry["m0_role"]
        lower = entry["finding"].lower()
        assert "slice-1" in lower, entry["m0_role"]
        assert "no slice-1" in lower or "not as a slice-1" in lower, entry["m0_role"]
        assert entry["gap"], entry["m0_role"]


def test_inv_paper_only_and_no_upgrade_invariants_named(taxonomy_map):
    ids = {inv["id"] for inv in taxonomy_map["authority_invariants"]}
    for required in (
        "INV-DECIDE-HOLDERS",
        "INV-VETO-DETERMINISTIC",
        "INV-PROMOTE-HUMAN-ONLY",
        "INV-NO-SLICE1-EXECUTION",
        "INV-MATURITY-ADVANCE-GOVERNED",
        "INV-GLOBAL-DENY",
        "INV-RESEARCH-FORBIDDEN",
        "INV-AI-NO-UPGRADE",
        "INV-PAPER-ONLY",
    ):
        assert required in ids, f"authority invariant {required} was dropped"


def test_advance_maturity_is_the_governed_exit_ramp(taxonomy_map):
    """The map claims INV-MATURITY-ADVANCE-GOVERNED; the code must make it true.

    All 19 anchors must still seed at REGISTERED (the map's blocking finding),
    while the fail-closed advance path exists and refuses to over-claim.
    """
    from ahos_org.clock import FrozenClock
    from ahos_org.ids import SequentialIdFactory
    from ahos_org.models import MaturityLevel
    from ahos_org.organization import AgentOrganization

    org = AgentOrganization(clock=FrozenClock(), ids=SequentialIdFactory())
    org.agents.seed_canonical_agents()

    # Blocking finding still holds: nothing was auto-promoted.
    assert all(
        a.maturity_level is MaturityLevel.REGISTERED for a in org.agents.list_agents()
    )

    anchor = "agent.chief-orchestrator"
    from ahos_org.errors import ValidationError

    # The governed ramp refuses every shortcut and logs the attempt.
    for bad_target in (MaturityLevel.VERIFIED, MaturityLevel.OPERATIONALLY_TRUSTED):
        with pytest.raises(ValidationError):
            org.agents.advance_maturity(
                anchor, actor="self", evidence="shortcut", target=bad_target
            )
    with pytest.raises(ValidationError):
        org.agents.advance_maturity(
            anchor, actor="self", evidence="", target=MaturityLevel.IMPLEMENTED
        )
    assert org.agents.get(anchor).maturity_level is MaturityLevel.REGISTERED

    # A lawful advance clears the seed default and is audit-logged.
    org.agents.advance_maturity(
        anchor,
        actor="human-governance",
        evidence="governed review under M-GAP-028",
        target=MaturityLevel.IMPLEMENTED,
    )
    assert org.agents.get(anchor).maturity_level is MaturityLevel.IMPLEMENTED
    events = [e for e in org.audit.events() if e.action == "advance_maturity"]
    assert any(e.decision == "ALLOW" for e in events)
    assert any(e.decision == "DENY" for e in events), "refused attempts must be logged too"

def test_paper_only_still_disabled_in_live_code():
    """The map says trading is disabled; the code must still say so."""
    from agent_org.contracts import PROTECTED_RESOURCES, Resource
    from ahos_org.resources import PROTECTED_AHOS_RESOURCE_IDS

    assert Resource.AHOS_LIVE_TRADING in PROTECTED_RESOURCES, (
        "AHOS_LIVE_TRADING must remain a protected resource in the control plane"
    )
    assert "AHOS_LIVE_TRADING" in PROTECTED_AHOS_RESOURCE_IDS, (
        "AHOS_LIVE_TRADING must remain a protected resource in the organization model"
    )
