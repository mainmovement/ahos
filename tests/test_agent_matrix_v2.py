"""Agent Matrix v2 pins (W12 PART J/PART M):
freshness (doc == generator output) · full coverage · 16-field completeness ·
owner law (AG-23 human) · no invented IO (empty state_tables ⇒ explicit DEFINED marker) ·
authority law re-asserted (only AG-15/AG-16 may DECIDE).
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "architecture" / "agent_matrix_v2.md"

sys.path.insert(0, str(ROOT / "engine"))
import agent_matrix_v2 as gen  # noqa: E402


def _reg():
    return yaml.safe_load((ROOT / "config" / "agent_registry.yaml").read_text())


def test_matrix_v2_doc_is_fresh():
    """Hand-drift protection: the file must equal a fresh regeneration, byte-identically."""
    assert DOC.read_text() == gen.render(_reg())


def test_matrix_v2_covers_every_agent_exactly_once():
    agents = _reg()["agents"]
    text = DOC.read_text()
    for a in agents:
        assert text.count(f"### {a['agent_id']} ·") == 1, a["agent_id"]


def test_matrix_v2_sixteen_fields_present_per_agent():
    text = DOC.read_text()
    blocks = [b for b in text.split("### ")[1:]]
    assert len(blocks) == len(_reg()["agents"]) == 25
    for b in blocks:
        for f in gen.FIELDS[1:]:            # identity is the block header
            assert f"**{f}**:" in b, f"missing field {f} in block {b.splitlines()[0]}"


def test_matrix_v2_owner_and_authority_laws():
    text = DOC.read_text()
    ag23 = next(b for b in text.split("### ")[1:] if b.startswith("AG-23"))
    assert "human operator" in ag23
    reg = _reg()
    for a in reg["agents"]:
        if a["agent_id"] not in ("AG-15", "AG-16"):
            assert "DECIDE" not in (a.get("allowed_authority") or [])
        if a["agent_id"] == "AG-25":
            assert "PROMOTE" not in (a.get("allowed_authority") or [])
            assert "DECIDE" in (a.get("forbidden_authority") or [])


def test_matrix_v2_never_invents_io():
    """Agents without declared state_tables must show the DEFINED marker, not ad-hoc output."""
    for a in _reg()["agents"]:
        if not (a["ops"].get("state_tables") or []):
            blk = next(b for b in DOC.read_text().split("### ")[1:] if b.startswith(a["agent_id"]))
            assert "**outputs**: — DEFINED" in blk
