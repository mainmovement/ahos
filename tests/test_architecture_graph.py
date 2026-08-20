#!/usr/bin/env python3
"""Architecture graph (W36 phase 9): deterministic stdlib-only module graph.

Pins:
  * graph building on a synthetic tree: nodes/edges/cycles/coupling/isolated
    are computed correctly and deterministically;
  * cycles are detected (DFS back-edge) and reported as evidence, not errors;
  * the real repo graph is well-formed (schema, counts, sorted output) and
    the known intelligence cycle is reported (evidence, not a failure).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import architecture_graph as ag  # noqa: E402
from scripts import validate_imports as gate  # noqa: E402


def _build_tree(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "a.py").write_text(
        "from .b import B\n", encoding="utf-8")          # a -> b
    (root / "pkg" / "b.py").write_text(
        "from .a import A\n", encoding="utf-8")          # b -> a  (cycle)
    (root / "pkg" / "c.py").write_text(
        "from .a import A\n", encoding="utf-8")          # c -> a
    (root / "pkg" / "d.py").write_text("X = 1\n", encoding="utf-8")  # isolated
    return root


def test_graph_on_synthetic_tree(tmp_path, monkeypatch):
    root = _build_tree(tmp_path)
    monkeypatch.setattr(gate, "ROOT", root)
    monkeypatch.setattr(gate, "RUNTIME_PACKAGES", ["pkg"])
    monkeypatch.setattr(gate, "IMPORT_EXCLUDE", {})

    graph = ag.build_graph()
    assert graph["schema"] == "ahos.architecture_graph.v1"
    assert graph["node_count"] == 4  # a, b, c, d
    # the a<->b cycle is detected
    assert len(graph["cycles"]) == 1
    assert set(graph["cycles"][0]) == {"pkg.a", "pkg.b"}
    # coupling: a is depended upon by b and c
    top = {row["module"]: row["dependents"] for row in graph["top_depended_upon"]}
    assert top["pkg.a"] == 2
    # d is isolated
    assert graph["isolated_modules"] == ["pkg.d"]


def test_graph_is_deterministic(tmp_path, monkeypatch):
    root = _build_tree(tmp_path)
    monkeypatch.setattr(gate, "ROOT", root)
    monkeypatch.setattr(gate, "RUNTIME_PACKAGES", ["pkg"])
    monkeypatch.setattr(gate, "IMPORT_EXCLUDE", {})
    g1 = ag.build_graph()
    g2 = ag.build_graph()
    assert g1 == g2


def test_real_repo_graph_is_well_formed_and_reports_cycle():
    graph = ag.build_graph()
    assert graph["node_count"] > 100
    assert graph["edge_count"] > graph["node_count"]
    # the intelligence cycle is known and reported as evidence
    cycle_nodes = {m for c in graph["cycles"] for m in c}
    assert "architecture.intelligence.engine" in cycle_nodes
    assert "architecture.scoring.engine" in cycle_nodes
    assert "architecture.explanations.engine" in cycle_nodes
    # deterministic
    assert ag.build_graph()["cycles"] == graph["cycles"]


def test_cli_writes_artifact(tmp_path):
    out = tmp_path / "graph.json"
    rc = ag.main(["--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema"] == "ahos.architecture_graph.v1"
    assert data["generated_utc"]


def test_graph_cache_reuses_result_and_invalidates_on_edit(tmp_path, monkeypatch):
    """W40: build_graph is cached on a source fingerprint — repeated calls
    reuse the graph (parity), and editing a scanned file invalidates it."""
    import os
    from scripts.architecture_graph import build_graph, _source_fingerprint

    g1 = build_graph()
    g2 = build_graph()
    assert g1 == g2, "cached graph must equal the first build (parity)"

    # fingerprint changes when a scanned file is touched
    fp1 = _source_fingerprint()
    p = tmp_path / "x.py"
    p.write_text("X = 1\n", encoding="utf-8")
    # fingerprint covers RUNTIME_PACKAGES dirs under gate.ROOT — for the
    # synthetic tree we verify the mechanism via a mtime change
    from scripts import validate_imports as gate
    root = gate.ROOT
    probe = next((f for f in (root / "architecture").rglob("*.py")
                  if "__pycache__" not in f.parts), None)
    assert probe is not None
    st = probe.stat()
    os.utime(probe, (st.st_atime, st.st_mtime + 3))
    try:
        fp2 = _source_fingerprint()
        assert fp1 != fp2, "source fingerprint must change on file edit"
    finally:
        os.utime(probe, (st.st_atime, st.st_mtime))
