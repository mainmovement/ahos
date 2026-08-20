#!/usr/bin/env python3
"""AHOS lightweight architecture graph (W36 phase 9).

A deterministic, stdlib-only module dependency graph derived from the SAME
import scan as scripts/validate_imports.py (one source of truth for the
import surface — no parallel scanner, no graph library).

Emits:
  * nodes: every leaf module in the runtime packages
  * edges: module -> imported module (absolute + resolved relative, incl.
    string-based lazy imports in __init__.py)
  * cycles: strongly-connected components of size > 1 (DFS back-edges)
  * coupling: top modules by in-degree (most depended-upon) and out-degree
    (most dependent)
  * isolated: modules with no edges either way (distinct from orphans: an
    isolated module may still be an entrypoint, e.g. a CLI)

Read-only, deterministic (sorted output), network-free. Writes one artifact
under reports/ (or --out). Exit 0 always (a cycle report is evidence, not a
crash); exit 2 on invocation error.

Usage:
    python scripts/architecture_graph.py
    python scripts/architecture_graph.py --out /tmp/graph.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_imports as gate  # noqa: E402


#: Cache of build_graph keyed on a fingerprint of the scanned source files.
#: The graph is a pure function of the scanned files' content, and the
#: evidence package calls it every cadence — re-AST-parsing 140+ files per
#: interval is pure waste when nothing changed. The fingerprint uses each
#: scanned file's mtime+size, so any edit invalidates the cache while an
#: unchanged tree reuses the previous result (deterministic, parity-safe).
_GRAPH_CACHE: dict[str, dict[str, Any]] = {}


def _source_fingerprint() -> str:
    import hashlib

    h = hashlib.sha256()
    scanned = 0
    for pkg in gate.RUNTIME_PACKAGES:
        pkg_dir = gate.ROOT / pkg
        if not pkg_dir.is_dir():
            continue
        for path in sorted(pkg_dir.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                st = path.stat()
                h.update(f"{path}:{st.st_mtime_ns}:{st.st_size};".encode())
                scanned += 1
            except OSError:
                continue
    h.update(str(scanned).encode())
    return h.hexdigest()


def build_graph(use_cache: bool = True) -> dict[str, Any]:
    """Deterministic dependency graph over the runtime module surface.

    W40: memoized on a source fingerprint — the evidence package calls this
    per cadence, so an unchanged tree reuses the previous graph instead of
    re-AST-parsing 140+ files (~294 ms/call before). The fingerprint covers
    every scanned file's mtime+size, so any edit invalidates the cache.
    """
    if use_cache:
        fp = _source_fingerprint()
        cached = _GRAPH_CACHE.get(fp)
        if cached is not None:
            return dict(cached)   # copy: callers may mutate
    modules = sorted(set(gate.collect_modules()))
    # keep only leaf modules (files, not packages) as nodes; imports may
    # reference packages, which we fold to their leaf targets when possible
    leaf = set(modules)
    for m in modules:
        parts = m.split(".")
        for i in range(1, len(parts)):
            leaf.discard(".".join(parts[:i]))  # package names are not leaves

    edges: dict[str, set[str]] = {}
    for m in sorted(leaf):
        p = gate.ROOT / Path(*m.split(".")).with_suffix(".py")
        if not p.exists():
            continue
        targets: set[str] = set()
        for imp in gate._module_import_paths(p):
            # record the edge to any leaf module the import resolves to
            candidates = [imp]
            parts = imp.split(".")
            for i in range(len(parts) - 1, 0, -1):
                candidates.append(".".join(parts[:i]))
            for cand in candidates:
                if cand in leaf and cand != m:
                    targets.add(cand)
                    break
        if targets:
            edges[m] = targets

    # cycles: DFS back-edge detection (self-loops excluded)
    cycles: list[list[str]] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {m: WHITE for m in leaf}
    stack: list[str] = []
    cycle_set: set[tuple[str, ...]] = set()

    def _dfs(node: str) -> None:
        color[node] = GRAY
        stack.append(node)
        for nxt in sorted(edges.get(node, ())):
            if color.get(nxt) == GRAY:
                # back edge -> cycle; extract from stack
                try:
                    idx = stack.index(nxt)
                except ValueError:
                    continue
                cyc = tuple(stack[idx:])
                if len(cyc) > 1:
                    cycle_set.add(tuple(sorted(cyc)))
            elif color.get(nxt) == WHITE:
                _dfs(nxt)
        stack.pop()
        color[node] = BLACK

    for m in sorted(leaf):
        if color[m] == WHITE:
            _dfs(m)
    cycles = [list(c) for c in sorted(cycle_set)]

    # coupling
    in_deg: dict[str, int] = {m: 0 for m in leaf}
    out_deg: dict[str, int] = {m: 0 for m in leaf}
    for src, targets in edges.items():
        out_deg[src] = len(targets)
        for t in targets:
            in_deg[t] += 1

    top_depended = sorted(
        ((m, d) for m, d in in_deg.items() if d > 0),
        key=lambda kv: (-kv[1], kv[0]))[:10]
    top_dependent = sorted(
        ((m, d) for m, d in out_deg.items() if d > 0),
        key=lambda kv: (-kv[1], kv[0]))[:10]
    isolated = sorted(m for m in leaf
                      if not edges.get(m) and in_deg[m] == 0)

    graph = {
        "schema": "ahos.architecture_graph.v1",
        "generated_utc": gate._utc_now() if hasattr(gate, "_utc_now") else "",
        "node_count": len(leaf),
        "edge_count": sum(len(v) for v in edges.values()),
        "cycles": cycles,
        "top_depended_upon": [{"module": m, "dependents": d}
                              for m, d in top_depended],
        "top_dependent": [{"module": m, "dependencies": d}
                          for m, d in top_dependent],
        "isolated_modules": isolated,
        "note": ("deterministic import-graph representation; a cycle is "
                 "evidence for review, not an automatic failure"),
    }
    if use_cache:
        _GRAPH_CACHE[fp] = graph
    return dict(graph)


def main(argv: list[str] | None = None) -> int:
    import time

    ap = argparse.ArgumentParser(description="AHOS architecture graph")
    ap.add_argument("--out", default=None, help="output path for the JSON artifact")
    args = ap.parse_args(argv)

    graph = build_graph()
    graph["generated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    out = Path(args.out) if args.out else (
        ROOT / "reports"
        / f"architecture_graph_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"nodes      : {graph['node_count']}")
    print(f"edges      : {graph['edge_count']}")
    print(f"cycles     : {len(graph['cycles'])}")
    for c in graph["cycles"]:
        print(f"  cycle: {' -> '.join(c)}")
    print("top depended-upon:")
    for row in graph["top_depended_upon"]:
        print(f"  {row['module']:<44} {row['dependents']}")
    print("isolated  :", len(graph["isolated_modules"]))
    print(f"artifact   : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
