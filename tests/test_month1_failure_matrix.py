#!/usr/bin/env python3
"""Month 1 controlled failure matrix — CI regression pin.

Runs the full injected-failure matrix (scheduler, providers, persistence,
safety) and requires every scenario to stay PASS. This keeps the fail-closed
invariants pinned between explicit matrix runs.
"""
import os
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


def test_execution_surface_scan_needs_no_external_binary(tmp_path, monkeypatch):
    """The static execution-surface scan must not shell out to `grep`.

    M-GAP-041: scenario 28 used to invoke the POSIX `grep` through subprocess,
    which is absent on a default Windows install, so the matrix died with
    FileNotFoundError at the very scenario asserting no execution surface
    exists. The scan is now pure Python, so disabling every subprocess entry
    point must leave it working. If this regresses to a subprocess call the
    soak host fails again for the same reason.
    """
    def _refuse_subprocess(*args, **kwargs):
        raise AssertionError(
            "execution-surface scan must not spawn a subprocess: "
            f"{args[:1] if args else kwargs.get('args')}")

    monkeypatch.setattr(fm.subprocess, "run", _refuse_subprocess)
    monkeypatch.setattr(fm.subprocess, "Popen", _refuse_subprocess)
    monkeypatch.delenv("PATH", raising=False)

    hits = fm.scan_execution_surface()
    assert hits == [], f"execution-surface scan should find no hits: {hits[:2]}"


def test_execution_surface_scan_still_detects_an_order_call(tmp_path):
    """The portable replacement keeps the detection the grep pattern had.

    A scan that silently returned no hits for a real exchange import would
    satisfy its PASS while proving nothing, so the negative case is pinned
    against a planted file. Format stays grep's `path:lineno:line`.
    """
    (tmp_path / "architecture").mkdir()
    (tmp_path / "telegram_ai").mkdir()
    (tmp_path / "architecture" / "broker.py").write_text(
        "import ccxt\n\n\ndef buy():\n    return exchange.create_order(...)\n",
        encoding="utf-8")
    (tmp_path / "telegram_ai" / "benign.py").write_text(
        "def place_order_proxy():\n"
        "    # names an order API in prose only, no SDK or call syntax\n"
        "    return 'no exchange SDK here'\n",
        encoding="utf-8")

    hits = fm.scan_execution_surface(root=tmp_path)
    assert len(hits) == 2, f"expected the import + the call, got {hits}"
    # grep prints paths in the host's native separator form; compare that way.
    normalised = [h.replace(os.sep, "/") for h in hits]
    assert "architecture/broker.py:1:import ccxt" in normalised
    assert "architecture/broker.py:5:return exchange.create_order(...)" in normalised
