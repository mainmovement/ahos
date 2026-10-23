"""M57.T Trend Hunter unit tests (12-point gate, 90-day dedupe, AST zero-install check, Persian digest)."""
from __future__ import annotations

import ast
from pathlib import Path

from architecture.university.trend_hunter import (
    TrendCandidate,
    normalize_and_deduplicate,
    propose_to_idea_shelf,
    render_persian_digest,
    vet_candidate_12_point,
)


def test_12_point_gate_rejects_gpl_paid_and_single_source():
    ok = TrendCandidate("skfolio", "https://github.com/skfolio/skfolio", "0.4.0", "BSD-3-Clause", 0.0, "T8", ("gh", "pypi"), "تست")
    res_ok = vet_candidate_12_point(ok)
    assert res_ok["accepted"] is True
    assert res_ok["state"] == "proposed"
    assert res_ok["installed"] is False

    gpl = TrendCandidate("gpl-pkg", "https://example.org/gpl", "1.0", "GPL-3.0", 0.0, "T8", ("gh", "pypi"), "تست")
    assert vet_candidate_12_point(gpl)["accepted"] is False

    paid = TrendCandidate("paid-pkg", "https://example.org/paid", "1.0", "MIT", 19.0, "T8", ("gh", "pypi"), "تست")
    assert vet_candidate_12_point(paid)["accepted"] is False

    one_src = TrendCandidate("one-src", "https://example.org/one", "1.0", "MIT", 0.0, "T8", ("gh",), "تست")
    assert vet_candidate_12_point(one_src)["accepted"] is False


def test_deduplication_and_90_day_version_bump_resurface():
    seen: dict[str, tuple[str, float]] = {}
    c1 = TrendCandidate("Kronos", "https://github.com/shiyu-coder/Kronos/", "0.1.0", "MIT", 0.0, "T16", ("gh", "hf"), "تست")
    c1_dup = TrendCandidate("kronos", "https://github.com/shiyu-coder/Kronos", "0.1.0", "MIT", 0.0, "T16", ("gh", "hf"), "تست")
    batch1 = normalize_and_deduplicate([c1, c1_dup], seen, now_ts=1_000_000.0)
    assert len(batch1) == 1

    # Same version 10 days later -> suppressed
    batch2 = normalize_and_deduplicate([c1], seen, now_ts=1_000_000.0 + 10 * 86400.0)
    assert len(batch2) == 0

    # Version bump -> resurfaces immediately
    c1_v2 = TrendCandidate("Kronos", "https://github.com/shiyu-coder/Kronos", "0.2.0", "MIT", 0.0, "T16", ("gh", "hf"), "تست")
    batch3 = normalize_and_deduplicate([c1_v2], seen, now_ts=1_000_000.0 + 11 * 86400.0)
    assert len(batch3) == 1


def test_ast_zero_install_or_subprocess_in_trend_hunter(tmp_path: Path):
    src_path = Path(__file__).resolve().parents[1] / "architecture" / "university" / "trend_hunter.py"
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "subprocess" not in imported_names
    assert "pip" not in imported_names

    c = TrendCandidate("Laya", "https://huggingface.co/Laya", "0.1", "MIT", 0.0, "T8", ("hf", "gh"), "مدل سبک")
    prop = propose_to_idea_shelf(c)
    assert prop["status"] == "proposed"
    assert prop["requires_owner_approval"] is True
    digest = render_persian_digest("2026-10-23", [vet_candidate_12_point(c)], tmp_path / "digest.md")
    assert "شکارچی ترند" in digest
