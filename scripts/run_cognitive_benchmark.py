#!/usr/bin/env python3
"""Run the P4.1 cognitive benchmark offline. Writes reports under reports/agi_aci_evolution/.

Does not open soak DBs. Does not import discovery/paper_trading.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.benchmark.evaluator import run_cognitive_benchmark  # noqa: E402
from architecture.cognitive.benchmark.report import write_json, write_markdown  # noqa: E402
from architecture.cognitive.benchmark.reproducibility import run_twice  # noqa: E402


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(description="P4.1 cognitive benchmark (offline)")
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "reports" / "agi_aci_evolution"),
        help="directory for JSON/MD artifacts",
    )
    parser.add_argument("--lane-a-freeze", default="NOT_MEASURED")
    args = parser.parse_args()
    sha = _git_sha()
    with tempfile.TemporaryDirectory(prefix="ahos-p41-bench-") as tmp:
        report = run_cognitive_benchmark(
            Path(tmp) / "primary", git_sha=sha, lane_a_freeze=args.lane_a_freeze
        )
        twice = run_twice(Path(tmp) / "repro", git_sha=sha)
        report.soak_protection["REPRODUCIBILITY_EQUAL"] = (
            "YES" if twice["equal"] else "NO"
        )
        out = Path(args.out_dir)
        write_json(report, out / "p4_1_cognitive_benchmark_latest.json")
        write_markdown(report, out / "P4_1_COGNITIVE_BENCHMARK_REPORT.md")
        print(f"wrote {out / 'p4_1_cognitive_benchmark_latest.json'}")
        print(f"wrote {out / 'P4_1_COGNITIVE_BENCHMARK_REPORT.md'}")
        print(f"reproducibility_equal={twice['equal']}")
        fails = [m.metric_id for m in report.metrics if m.status == "FAIL"]
        print(f"FAIL metrics: {fails or 'none'}")
        return 0 if twice["equal"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
