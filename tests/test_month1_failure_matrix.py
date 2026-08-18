#!/usr/bin/env python3
"""Month 1 controlled failure matrix — CI regression pin.

Runs the full injected-failure matrix (scheduler, providers, persistence,
safety) and requires every scenario to stay PASS. This keeps the fail-closed
invariants pinned between explicit matrix runs.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest  # noqa: E402

from scripts import month1_failure_matrix as fm  # noqa: E402


def test_full_failure_matrix_all_pass(tmp_path):
    results = fm.run_all(workdir=tmp_path)
    assert len(results) >= 27, f"matrix shrank: {len(results)}"
    failed = [r for r in results if r["verdict"] != "PASS"]
    assert not failed, "FAIL scenarios: " + "; ".join(
        f"{r['category']}/{r['scenario']}: {r['evidence']}" for r in failed)


@pytest.mark.parametrize("category,minimum", [
    ("SCHEDULER", 10), ("PROVIDERS", 8), ("PERSISTENCE", 5), ("SAFETY", 5),
])
def test_matrix_category_coverage(tmp_path, category, minimum):
    results = fm.run_all(workdir=tmp_path)
    n = sum(1 for r in results if r["category"] == category)
    assert n >= minimum, f"{category}: {n} < {minimum}"
