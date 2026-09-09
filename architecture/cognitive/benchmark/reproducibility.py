"""Repeated execution must match. Timing and environment are excluded."""

from __future__ import annotations

from pathlib import Path

from architecture.cognitive.benchmark.evaluator import dumps_comparable, run_cognitive_benchmark


def run_twice(workdir: Path | str, *, git_sha: str = "UNKNOWN") -> dict:
    root = Path(workdir)
    a = run_cognitive_benchmark(root / "run_a", git_sha=git_sha)
    b = run_cognitive_benchmark(root / "run_b", git_sha=git_sha)
    pa = dumps_comparable(a)
    pb = dumps_comparable(b)
    equal = pa == pb
    return {
        "equal": equal,
        "bytes_a": len(pa),
        "bytes_b": len(pb),
        "reproducibility_rate": 1.0 if equal else 0.0,
        "report_a": a,
        "report_b": b,
    }
