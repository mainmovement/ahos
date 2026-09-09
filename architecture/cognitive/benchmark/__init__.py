"""P4.1 Lane-B cognitive benchmark. Deterministic, offline, non-authoritative.

Measures the P3 loop. Does not claim AGI/ACI. Does not write soak/Lane-A DBs.
Reuses architecture.cognitive.loop — does not replace it.
"""

from architecture.cognitive.benchmark.evaluator import run_cognitive_benchmark
from architecture.cognitive.benchmark.metrics import MetricResult
from architecture.cognitive.benchmark.thresholds import BENCHMARK_VERSION

__all__ = [
    "BENCHMARK_VERSION",
    "MetricResult",
    "run_cognitive_benchmark",
]
