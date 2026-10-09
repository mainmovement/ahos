"""M34 coherence invariants — the census-consistency lint.

M34.1 found that the agent census had drifted across the docs: the registry
grew from 25 agents to 43 (M12), and the number was stated as present fact in
nine places that M12's grep missed -- including ``config/agent_registry.yaml``'s
own header, which contradicted the file's own ``totals`` block, and
``AHOS_REALITY_MAP_v1.md``, whose entire purpose is to stop census overclaims.
The suite never caught any of it, because nothing asserted that the census
numbers in the world agree with the registry that defines them.

These invariants are the down payment on M34.4 (the coherence lint): they pin
the three relations that actually broke, so a future registration that updates
the rows but not the surrounding census fails here instead of silently leaving
the docs at odds with each other.

The scope is deliberately narrow. A doc that quotes a *different* count is not
wrong merely for that: 19, 10, 15, 8, 6, 100, 16 and 36 are honest counts of
*other* namespaces (Slice-1 logical agents, runtime actors, expert roles, the
M0 evaluation roles, the retired n8n cadences, council personas, mandated
matrix fields, Lane-A frozen paths). The lint only reaches for statements that
must move with the registry: the registry's own header, the taxonomy map's
ops-matrix count, and every ``orchestrated=0/N`` in a live doc, which names the
registry's own operability tally and cannot legitimately refer to anything else.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "agent_registry.yaml"
TAXONOMY_MAP = ROOT / "docs" / "governance" / "agent_taxonomy_map.json"
DOCS = ROOT / "docs"

# A doc is "live" unless it has been archived. The archive is history and is
# allowed to carry the counts it was written with; editing it would falsify the
# record. Reports are the same class of evidence and are out of scope entirely.
ARCHIVE = DOCS / "archive"


def _registry() -> dict:
    with REGISTRY.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _live_docs() -> list[Path]:
    out: list[Path] = []
    for path in DOCS.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".json"}:
            continue
        if ARCHIVE in path.parents or path.parent == ARCHIVE:
            continue
        out.append(path)
    return out


def test_the_registry_header_states_its_own_totals() -> None:
    """The source of truth must not contradict itself.

    ``config/agent_registry.yaml:1`` read "(25-agent matrix; ...)" while its own
    ``totals.agents`` said 43 -- the file that every census quote derives from
    was itself stale, which is why the drift propagated instead of being caught
    at the source.
    """
    header = REGISTRY.read_text(encoding="utf-8").splitlines()[0]
    m = re.search(r"\((\d+)-agent matrix", header)
    assert m, f"the header no longer carries an N-agent matrix count: {header!r}"
    stated = int(m.group(1))
    total = _registry()["totals"]["agents"]
    assert stated == total, (
        f"the registry header states {stated} agents but its totals block says "
        f"{total}; the source of truth disagrees with itself")


def test_the_taxonomy_map_tracks_the_registry() -> None:
    """The cross-taxonomy map's AG-* count must equal the registry it describes.

    M12 had to hand-edit both files; nothing checked they agreed, so the map was
    one forgotten edit away from describing a registry that no longer existed.
    Its status counts must also sum to the same total, or the map is describing
    a population that cannot exist.
    """
    with TAXONOMY_MAP.open(encoding="utf-8") as fh:
        amap = json.load(fh)

    ops = amap["taxonomies"]["ops_matrix"]
    total = _registry()["totals"]["agents"]
    assert ops["count"] == total, (
        f"the taxonomy map's ops_matrix count is {ops['count']} but the registry "
        f"holds {total}")

    counts = ops["status_counts"]
    assert sum(counts.values()) == total, (
        f"the taxonomy map's status_counts sum to {sum(counts.values())}, not "
        f"{total}: {counts}")

    # The map's per-status counts must be the registry's per-status counts, not
    # merely numbers that happen to add up.
    registry_counts = {
        k: _registry()["totals"][k]
        for k in counts
        if k in _registry()["totals"]
    }
    assert registry_counts == counts, (
        f"the taxonomy map's status_counts {counts} do not match the registry's "
        f"own status counts {registry_counts}")


@pytest.mark.parametrize("path", _live_docs())
def test_no_live_doc_states_a_superseded_orchestrated_census(path: Path) -> None:
    """Every ``orchestrated=0/N`` in a live doc must name the registry's tally.

    That expression can only refer to the AG-* registry's operability totals --
    no other namespace reports an orchestrated fraction -- so a doc carrying a
    different N is stale by construction. All four occurrences were 25 while the
    registry had moved to 43; the archived copies are excluded because their
    counts were correct when they were written.
    """
    text = path.read_text(encoding="utf-8")
    found = re.findall(r"orchestrated=0/(\d+)", text)
    if not found:
        return
    total = _registry()["totals"]["agents"]
    bad = {int(n) for n in found if int(n) != total}
    assert not bad, (
        f"{path.relative_to(ROOT)} states orchestrated=0/{sorted(bad)} while the "
        f"registry's operability denominator is {total}")
