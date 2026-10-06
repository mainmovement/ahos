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
    # Uses a still-planned artifact: an INTENTIONAL_REFS entry is only a licence
    # to reference a file that does not exist yet. Once such a file is actually
    # produced its entry must be removed (see
    # test_intentional_reasons_are_substantive), and this example must move to
    # another still-planned artifact.
    p = _doc(tmp_path, "write reports/local_soak_interruptions.json nightly")
    assert _scan_in(tmp_path, monkeypatch, p) == {}


def test_intentional_reasons_are_substantive():
    for ref, reason in dd.INTENTIONAL_REFS.items():
        assert len(reason) > 20, f"{ref} ignore reason too thin"
        # Same existence rule the scanner uses (tracked in git when ROOT is a
        # work tree), so an untracked local copy of a cited artifact cannot make
        # this pass on one machine and fail on another.
        assert not dd._exists(ref), (
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
    """Malformed and doubled extensions are regression-protected."""
    from scripts.doc_drift import CORRUPTION_PATTERNS
    drift = dd.scan_docs()
    for doc, refs in drift.items():
        for r in refs:
            assert r["reason"] not in CORRUPTION_PATTERNS.values(), (
                f"{doc}: {r['reference']} ({r['reason']})")


def test_malformed_jsonl_and_sha256_extensions_are_reported(tmp_path, monkeypatch):
    """Typos that no valid path regex can match must still be surfaced."""
    p = _doc(
        tmp_path,
        "see reports/pilot.jsonll and scripts/freeze_lane_a.pya256",
    )
    out = _scan_in(tmp_path, monkeypatch, p)
    refs = {row["reference"] for row in next(iter(out.values()))}
    assert refs == {"jsonll", "pya256"}


def test_only_tracked_files_satisfy_a_reference(tmp_path, monkeypatch):
    """Blocker A / GM-01 + REDTEAM-19 F5 / QA MAJOR-1: inside a git work tree
    only a TRACKED file counts. A stray untracked copy, and equally a gitignored
    generated/runtime artifact that some earlier run left on disk, must not,
    or the verdict depends on one machine's leftovers or on test order."""
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("data/\n", encoding="utf-8")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "tracked.json").write_text("{}", encoding="utf-8")
    (tmp_path / "reports" / "stray.json").write_text("{}", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "runtime.sqlite").write_text("", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", ".gitignore", "reports/tracked.json"],
                   check=True)
    monkeypatch.setattr(dd, "_TRACKED_CACHE", {})
    p = _doc(tmp_path, "see reports/tracked.json, reports/stray.json and data/runtime.sqlite")
    out = _scan_in(tmp_path, monkeypatch, p)
    refs = sorted(d["reference"] for v in out.values() for d in v)
    assert refs == ["data/runtime.sqlite", "reports/stray.json"]


def test_canonical_docs_verdict_does_not_depend_on_generated_artifacts(tmp_path, monkeypatch):
    """QA MAJOR-1: the canonical-docs verdict is the same with and without the
    gitignored files that tools/tests generate into the checkout (simulated by
    an ignored file appearing on disk mid-session)."""
    gen = dd.ROOT / "reports" / "PRE_SOAK_STATUS.txt"
    before = dd.scan_docs()
    existed = gen.exists()
    saved = gen.read_bytes() if existed else None
    try:
        gen.write_text("pre_soak_entry_ok=False\n", encoding="utf-8")
        with_file = dd.scan_docs()
        gen.unlink()
        without_file = dd.scan_docs()
    finally:
        if existed:
            gen.write_bytes(saved)
        elif gen.exists():
            gen.unlink()
    assert before == with_file == without_file == {}
