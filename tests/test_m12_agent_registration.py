"""M12 — agent organisation pins (2026-10-09).

The queue row reads: "37+ agents in config/agent_registry.yaml using the owner
charter template, authority NONE by default, no auto-creation." The vision
(reports/grok/AHOS_AUTONOMOUS_VISION.md §2.3) approved charters 20..37 on
2026-10-03 20:43 and directed their registration in M12.

These tests pin the registration's invariants, not just its size:
- the 18 agents land as AG-26..AG-43, once each, in vision order;
- authority NONE by default is the *machine-checkable* empty allowed list;
- the owner law that only AG-15/AG-16 may DECIDE still holds for the new rows;
- every new agent's evidence resolves to its owner-authored charter;
- no Slice-1 (agent.org.*) agent is created, merged or mapped — the two-taxonomy
  mapping is OWN-AV-56, a human gate this mission must not touch;
- nothing is promoted: all 18 stay PLANNED with operability all-false.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REGISTRY = ROOT / "config" / "agent_registry.yaml"
VISION = ROOT / "reports" / "grok" / "AHOS_AUTONOMOUS_VISION.md"

# vision # -> (AG id, romanised registry name, Persian charter name)
# This table IS the registration mapping; it is pinned here so a renumbering or
# a mis-transcription fails the build instead of shipping silently.
M12_AGENTS = {
    20: ("AG-26", "Kourosh", "کوروش"),
    21: ("AG-27", "Bahram", "بهرام"),
    22: ("AG-28", "Zarrin", "زرین"),
    23: ("AG-29", "Sara", "سارا"),
    24: ("AG-30", "Leila", "لیلا"),
    25: ("AG-31", "Mahsa", "مهسا"),
    26: ("AG-32", "Farhad", "فرهاد"),
    27: ("AG-33", "Negar", "نگار"),
    28: ("AG-34", "Bijan", "بیژن"),
    29: ("AG-35", "Shida", "شیدا"),
    30: ("AG-36", "Siavash", "سیاوش"),
    31: ("AG-37", "Babak", "بابک"),
    32: ("AG-38", "Dariush", "داریوش"),
    33: ("AG-39", "Maryam", "مریم"),
    34: ("AG-40", "Homan", "هومن"),
    35: ("AG-41", "Farzaneh", "فرزانه"),
    36: ("AG-42", "Zhaleh", "ژاله"),
    37: ("AG-43", "Ayda", "آیدا"),
}
NEW_IDS = [v[0] for v in M12_AGENTS.values()]


@pytest.fixture(scope="module")
def reg():
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def by_id(reg):
    return {a["agent_id"]: a for a in reg["agents"]}


@pytest.fixture(scope="module")
def vision():
    return VISION.read_text(encoding="utf-8")


# --- the mapping itself ---------------------------------------------------

def test_the_eighteen_agents_are_registered_once_each_in_vision_order(reg):
    ids = [a["agent_id"] for a in reg["agents"]]
    for ag in NEW_IDS:
        assert ids.count(ag) == 1, f"{ag} must appear exactly once"
    assert ids[-len(NEW_IDS):] == NEW_IDS          # appended, in vision order, no gaps


def test_registry_meets_the_queue_rows_floor(reg):
    assert len(reg["agents"]) >= 37                # "37+ agents" — 25 existing + 18


def test_no_agent_id_collides_with_the_new_block(reg):
    ids = [a["agent_id"] for a in reg["agents"]]
    assert len(set(ids)) == len(ids)               # no duplicate ids anywhere


# --- authority NONE by default, machine-checkable -------------------------

def test_every_new_agent_grants_no_runtime_authority(by_id):
    """'authority NONE by default' is only testable as an empty allowed list.
    A null/omitted field would fail the contract's required-field check, so []
    is the honest encoding — and this is the assertion that keeps it honest."""
    for ag in NEW_IDS:
        assert by_id[ag]["allowed_authority"] == [], f"{ag} grants authority"


def test_owner_decide_law_holds_for_the_new_rows(by_id):
    for ag in NEW_IDS:
        assert "DECIDE" not in by_id[ag]["allowed_authority"]
        assert "PROMOTE" not in by_id[ag]["allowed_authority"]
        assert "DECIDE" in by_id[ag]["forbidden_authority"]
        assert "PROMOTE" in by_id[ag]["forbidden_authority"]


def test_maryams_designed_veto_is_recorded_not_granted_nor_forbidden(by_id):
    """Vision line 113 and her charter give Maryam a veto the CIO cannot cancel.
    Granting it is a governance act (not registration); forbidding it would deny
    an owner-approved charter fact. So it sits in neither list, on the record."""
    m = by_id["AG-39"]
    assert "VETO" not in m["allowed_authority"]
    assert "VETO" not in m["forbidden_authority"]
    assert "VETO" in m["ops"]["notes"]


def test_no_new_agent_holds_a_decide_or_promote_anywhere(reg):
    deciders = {a["agent_id"] for a in reg["agents"] if "DECIDE" in a["allowed_authority"]}
    assert deciders == {"AG-15", "AG-16"}          # unchanged owner law


# --- honesty: nothing is promoted ---------------------------------------

def test_every_new_agent_is_planned_with_no_claimed_runtime(by_id):
    for ag in NEW_IDS:
        a = by_id[ag]
        assert a["status"] == "PLANNED", f"{ag} must stay PLANNED (no artifact exists)"
        o = a["ops"]["operability"]
        assert o == {"implemented": False, "contracted": False,
                     "orchestrated": False, "live": False}, f"{ag} claims runtime"
        assert a["ops"]["runtime"] == "none"


def test_no_new_agent_touches_lane_a(by_id):
    for ag in NEW_IDS:
        assert by_id[ag]["lane"] == "B"             # Lane A stays frozen


def test_new_agents_do_not_inflate_operability_totals(reg):
    t = reg["totals"]["operability_totals"]
    assert t["orchestrated"] == 0                   # still nothing wired to a runtime
    impl = sum(1 for a in reg["agents"] if a["ops"]["operability"]["implemented"])
    live = sum(1 for a in reg["agents"] if a["ops"]["operability"]["live"])
    assert t["implemented"] == impl                 # the 18 add nothing
    assert t["live"] == live


def test_totals_block_is_truthful_after_the_registration(reg):
    from collections import Counter
    c = Counter(a["status"] for a in reg["agents"])
    assert reg["totals"]["agents"] == len(reg["agents"]) == 43
    assert reg["totals"]["PLANNED"] == c["PLANNED"] == 21
    boot = Counter(a["ops"]["boot_class"] for a in reg["agents"])
    assert reg["totals"]["boot_class_totals"]["CRITICAL"] == boot["CRITICAL"]
    assert reg["totals"]["boot_class_totals"]["ADVISORY"] == boot["ADVISORY"]


# --- traceability to the owner-authored charters --------------------------

def test_every_new_agent_evidence_resolves_to_its_charter(by_id, vision):
    for num, (ag, _roman, fa) in M12_AGENTS.items():
        ev = by_id[ag]["evidence"]
        assert "AHOS_AUTONOMOUS_VISION.md" in ev, f"{ag} does not cite the vision"
        assert f"§2.3.3 #{num}" in ev, f"{ag} does not cite its charter number"
        assert fa in ev, f"{ag} evidence does not name its charter agent"
        # the charter it cites must actually be in the owner's document
        assert fa in vision, f"{ag} cites charter name {fa!r} absent from the vision"
        assert VISION.is_file()


# --- the locked boundaries: no auto-creation, no taxonomy merge -----------

def test_no_slice1_agent_was_created(reg):
    """'No auto-creation': the Slice-1 org store is untouched. The registry must
    contain no agent.org.* id, and the canonical Slice-1 set is still 19."""
    from ahos_org.registry import CANONICAL_AGENT_IDS
    ids = {a["agent_id"] for a in reg["agents"]}
    assert not any(i.startswith("agent.") for i in ids), "Slice-1 id leaked into the AG matrix"
    assert len(CANONICAL_AGENT_IDS) == 19, "the Slice-1 anchor set changed under M12"


def test_the_two_taxonomy_mapping_stays_unresolved():
    """OWN-AV-56 is a human gate. The map must still declare reconciliation, not
    a merge — M12 registers agents, it does not bridge the two taxonomies."""
    import json
    m = json.loads((ROOT / "docs" / "governance" / "agent_taxonomy_map.json").read_text(encoding="utf-8"))
    assert m["status"] == "RECONCILED_NOT_MERGED"


def test_new_agent_dependencies_are_known_agent_ids_only(reg, by_id):
    """Registry law: dependencies are agent ids only — and a registration must not
    create a cross-taxonomy edge to a Slice-1 anchor."""
    known = {a["agent_id"] for a in reg["agents"]}
    for ag in NEW_IDS:
        for dep in by_id[ag]["dependencies"]:
            assert dep in known, f"{ag} depends on unknown agent id {dep}"


def test_new_agent_dependency_graph_is_acyclic(by_id):
    seen, stack = set(), []

    def visit(ag):
        if ag in stack:
            raise AssertionError(f"cycle in agent dependencies: {' -> '.join(stack)} -> {ag}")
        if ag in seen:
            return
        seen.add(ag)
        stack.append(ag)
        for dep in by_id[ag]["dependencies"]:
            visit(dep)
        stack.pop()

    for ag in NEW_IDS:
        visit(ag)


# --- non-duplication (vision §2.5) ---------------------------------------

def test_no_new_agent_duplicates_an_existing_one(by_id, reg):
    names = [a["name"] for a in reg["agents"]]
    for ag in NEW_IDS:
        assert names.count(by_id[ag]["name"]) == 1, f"{ag} name duplicates an agent"


def test_the_eighteen_are_disjoint_from_the_nineteen(vision):
    """§2.2 lists the 19 existing Slice-1 agents; §2.3 charters 18 NEW ones.
    A name appearing in both would be a duplicate agent, not a second role."""
    existing = ["آرش", "سامان", "سپهر", "گیتی", "عرفان", "روشا", "دانا", "کامیار",
                "نیما", "تینا", "رامین", "کیمیا", "آریا", "رستم", "پروانه",
                "قاسم", "پریسا", "فرناز", "رضا"]
    for _num, (_ag, _roman, fa) in M12_AGENTS.items():
        assert fa not in existing, f"{fa} is both an existing and a new agent"
        assert fa in vision
