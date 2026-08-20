#!/usr/bin/env python3
"""W38 Candidate H: doc <-> code drift detection.

Pins:
  * a synthetic doc referencing a missing file is reported as STALE;
  * `.sqlite` / `.jsonl` extensions are NOT truncated to `.sql` / `.json`
    (the \b boundary fix);
  * intentional references (planned/future artifacts) are ignored with a
    reason and never reported;
  * the full canonical-doc set has ZERO real stale references (the fixes
    applied in W38 are protected from regression).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import doc_drift as dd  # noqa: E402


def _doc(tmp_path, text):
    p = tmp_path / "doc.md"
    p.write_text(text, encoding="utf-8")
    return p


def _scan_in(tmp_path, monkeypatch, p: Path) -> dict:
    """Scan a synthetic doc resolving paths against tmp_path."""
    monkeypatch.setattr(dd, "ROOT", tmp_path)
    return dd.scan_docs([p])


def test_stale_reference_is_reported(tmp_path, monkeypatch):
    p = _doc(tmp_path, "run `scripts/does_not_exist.py` please")
    out = _scan_in(tmp_path, monkeypatch, p)
    assert len(out) == 1
    refs = next(iter(out.values()))
    assert refs[0]["reference"] == "scripts/does_not_exist.py"


def test_sqlite_and_jsonl_are_not_truncated(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "ahos_local.sqlite").write_text("", encoding="utf-8")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "log.jsonl").write_text("", encoding="utf-8")
    p = _doc(tmp_path,
             "stores are data/ahos_local.sqlite and reports/log.jsonl")
    out = _scan_in(tmp_path, monkeypatch, p)
    assert out == {}, f"sqlite/jsonl refs should resolve, got {out}"


def test_existing_paths_are_not_reported(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "doc_drift.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_doc_drift.py").write_text("", encoding="utf-8")
    p = _doc(tmp_path, "see scripts/doc_drift.py and tests/test_doc_drift.py")
    assert _scan_in(tmp_path, monkeypatch, p) == {}


def test_intentional_refs_are_ignored(tmp_path, monkeypatch):
    p = _doc(tmp_path, "write reports/nightly_backup_series.json nightly")
    assert _scan_in(tmp_path, monkeypatch, p) == {}


def test_intentional_reasons_are_substantive():
    for ref, reason in dd.INTENTIONAL_REFS.items():
        assert len(reason) > 20, f"{ref} ignore reason too thin"
        assert not (ROOT / ref).exists(), (
            f"{ref} exists but is listed as intentional — move it to a real fix")


def test_canonical_docs_have_zero_real_stale_refs():
    """The W38 doc-drift fixes are regression-protected: any new canonical-doc
    reference to a missing file fails this test (unless added to
    INTENTIONAL_REFS with a reason)."""
    drift = dd.scan_docs()
    assert drift == {}, (
        f"{sum(len(v) for v in drift.values())} stale reference(s) in "
        f"canonical docs: {drift}")


def test_double_extension_corruption_is_reported(tmp_path, monkeypatch):
    """W38 regression: a `.sql`->`.sqlite` replace inside `.sqlite` produced
    `.sqliteite`, invisible to the path regex — now explicitly detected."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "ahos_knowledge.sqlite").write_text("", encoding="utf-8")
    p = _doc(tmp_path, "store is data/ahos_knowledge.sqliteite")
    out = _scan_in(tmp_path, monkeypatch, p)
    assert len(out) == 1
    refs = next(iter(out.values()))
    assert any(r["reference"] == "sqliteite" for r in refs)


def test_canonical_docs_have_no_double_extension_corruption():
    """The 5 sqliteite corruptions fixed in W38 are regression-protected."""
    from scripts.doc_drift import CORRUPTION_PATTERNS
    drift = dd.scan_docs()
    for doc, refs in drift.items():
        for r in refs:
            assert r["reason"] not in CORRUPTION_PATTERNS.values(), (
                f"{doc}: {r['reference']} ({r['reason']})")
