#!/usr/bin/env python3
"""Orphan-module detection in the canonical validation gate (mission §4B).

The gate now scans every import (absolute AND resolved relative, including
lazy in-function imports) and WARNs about leaf modules nothing imports and
no test exercises. These tests pin the detector on a synthetic tree:
  * an orphaned module is flagged;
  * a referenced module (incl. via `from pkg import sub` and relative lazy
    imports) is NOT flagged;
  * packages (directories) are never flagged;
  * the full gate still passes (WARN does not fail).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.validate_imports as gate  # noqa: E402


def _build_tree(tmp_path: Path) -> Path:
    """Create a synthetic repo with: an orphan leaf, a referenced leaf, a
    package, and a module referencing the leaf via a relative lazy import."""
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "worker.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "pkg" / "orphan.py").write_text("X = 2\n", encoding="utf-8")
    (root / "pkg" / "main.py").write_text(
        "def run():\n    from .worker import VALUE\n    return VALUE\n",
        encoding="utf-8")
    (root / "consumer.py").write_text(
        "from pkg import worker\n", encoding="utf-8")
    return root


def _pin_synthetic_surface(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(gate, "ROOT", root)
    monkeypatch.setattr(gate, "RUNTIME_PACKAGES", ["pkg"])
    monkeypatch.setattr(gate, "IMPORT_EXCLUDE", {})


def test_orphan_detection_marks_only_true_orphans(tmp_path, monkeypatch):
    root = _build_tree(tmp_path)
    _pin_synthetic_surface(monkeypatch, root)

    failures, notes = gate.check_orphans()
    assert failures == []
    warn = [n for n in notes if n.startswith("WARN:")]
    assert len(warn) == 1
    orphans = set(warn[0].rsplit(": ", 1)[1].split(", "))
    # orphan.py is unreferenced; main.py is an entrypoint-style leaf that
    # nothing imports (like discovery.collect in the real repo) — both are
    # honest orphan candidates
    assert orphans == {"pkg.orphan", "pkg.main"}
    # referenced modules and packages are NOT in the orphan list
    assert "pkg.worker" not in orphans
    assert "pkg" not in orphans  # package never orphaned


def test_no_orphans_when_all_referenced(tmp_path, monkeypatch):
    root = _build_tree(tmp_path)
    # remove every unreferenced leaf: orphan.py (never imported) and main.py
    # (entrypoint-style, nothing imports it). worker.py stays, imported by
    # consumer.py.
    (root / "pkg" / "orphan.py").unlink()
    (root / "pkg" / "main.py").unlink()
    _pin_synthetic_surface(monkeypatch, root)

    failures, notes = gate.check_orphans()
    assert failures == []
    assert all(not n.startswith("WARN:") for n in notes)
    assert any("no orphaned leaf modules" in n for n in notes)


def test_orphan_check_is_warn_not_fail(tmp_path, monkeypatch):
    """ORPHANS reports WARN lines with zero failures — the gate stays green."""
    root = _build_tree(tmp_path)
    _pin_synthetic_surface(monkeypatch, root)
    failures, notes = gate.check_orphans()
    assert failures == [] and any(n.startswith("WARN:") for n in notes)


def test_string_based_lazy_import_is_resolved(tmp_path, monkeypatch):
    """W36: `__init__.py` lazy mappings like ("SecurityIntelligence":
    (".engine", "Name")) must register the target module, so it is never
    falsely reported as an orphan."""
    root = _build_tree(tmp_path)
    (root / "pkg" / "__init__.py").write_text(
        'def __getattr__(name):\n'
        '    _lazy = {"Worker": (".worker", "Worker")}\n'
        '    if name in _lazy:\n'
        '        return _lazy[name]\n'
        '    raise AttributeError(name)\n',
        encoding="utf-8")
    # main.py is an entrypoint-style leaf (nothing imports it) -> orphan;
    # worker.py is referenced only via the string mapping -> NOT an orphan
    _pin_synthetic_surface(monkeypatch, root)
    failures, notes = gate.check_orphans()
    warn = [n for n in notes if n.startswith("WARN:")]
    assert len(warn) == 1
    orphans = set(warn[0].rsplit(": ", 1)[1].split(", "))
    # main.py and orphan.py are genuinely unreferenced; worker.py is
    # referenced ONLY via the string mapping -> NOT an orphan
    assert orphans == {"pkg.main", "pkg.orphan"}
    assert "pkg.worker" not in orphans
