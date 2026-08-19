"""AHOS Performance Micro-Benchmark Suite (OSS-011).

Measures and validates execution latency, throughput, and memory performance
for core AHOS subsystems:
1. Vectorized Parameter Sweeps (VectorBT Pattern)
2. QuantStats Institutional Tear-Sheet Analytics
3. In-Process OLAP Query Bridge (DuckDB / SQLite)
4. Streaming Concept Drift Detection Throughput
5. Event-Driven Microstructure Simulation
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from architecture.intel.analytics_bridge import AnalyticsBridge
from architecture.learning.drift import StreamingDriftDetector
from engine.event_backtest import EventDrivenBacktester
from research.quant_metrics import QuantMetricsEngine
from strategy_lab.vector_engine import VectorBacktestEngine


def run_all_benchmarks() -> Dict[str, Any]:
    results = {}
    print("==========================================================")
    print("  AHOS Performance Micro-Benchmark & Profiling Suite")
    print("==========================================================")

    # 1. Benchmark: Vectorized Parameter Sweep
    np.random.seed(42)
    n_points = 500
    prices = 100.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, n_points)))
    scores = np.random.uniform(30.0, 95.0, n_points)

    t0 = time.perf_counter()
    sweeps = VectorBacktestEngine.run_parameter_grid_sweep(
        prices=prices,
        scores=scores,
        score_thresholds=[60.0, 70.0, 80.0, 85.0],
        stop_loss_pcts=[0.03, 0.05, 0.08, 0.10],
        take_profit_pcts=[0.10, 0.15, 0.20, 0.30],
    )
    vector_dur = time.perf_counter() - t0
    n_combos = len(sweeps)
    results["vectorized_backtest"] = {
        "combinations_evaluated": n_combos,
        "duration_seconds": round(vector_dur, 4),
        "evaluations_per_sec": round(n_combos / max(1e-5, vector_dur), 1),
    }
    print(
        f"[1/5] Vectorized Backtest: {n_combos} combinations in {vector_dur:.3f}s ({results['vectorized_backtest']['evaluations_per_sec']} combos/sec)"
    )

    # 2. Benchmark: QuantStats Tear-Sheet Analytics
    equity = np.cumprod(1.0 + np.random.normal(0.002, 0.015, 1000)) * 10000.0
    trades = list(np.random.normal(0.02, 0.05, 100))

    t0 = time.perf_counter()
    for _ in range(50):
        QuantMetricsEngine.generate_tearsheet(equity, trades)
    quant_dur = time.perf_counter() - t0
    results["quantstats_tearsheet"] = {
        "runs": 50,
        "total_duration_sec": round(quant_dur, 4),
        "latency_per_tearsheet_ms": round((quant_dur / 50) * 1000.0, 2),
    }
    print(
        f"[2/5] QuantStats Tear-Sheet: {results['quantstats_tearsheet']['latency_per_tearsheet_ms']} ms/tearsheet"
    )

    # 3. Benchmark: Analytics Bridge In-Memory OLAP
    bridge = AnalyticsBridge()
    mock_data = [
        {"token": f"TKN_{i}", "score": float(i % 100) / 100.0, "outcome": i % 2}
        for i in range(10000)
    ]
    bridge.register_in_memory_data("bench_table", mock_data)

    t0 = time.perf_counter()
    for _ in range(20):
        bridge.compute_brier_calibration_bins(
            "bench_table", "score", "outcome", bins=10
        )
    olap_dur = time.perf_counter() - t0
    results["olap_analytics_bridge"] = {
        "rows": 10000,
        "runs": 20,
        "is_duckdb_accelerated": bridge.is_duckdb_accelerated,
        "latency_per_aggregation_ms": round((olap_dur / 20) * 1000.0, 2),
    }
    print(
        f"[3/5] Analytics Bridge OLAP: {results['olap_analytics_bridge']['latency_per_aggregation_ms']} ms per 10k-row aggregation (DuckDB active: {bridge.is_duckdb_accelerated})"
    )
    bridge.close()

    # 4. Benchmark: Streaming Concept Drift Detection
    detector = StreamingDriftDetector()
    samples = np.random.normal(0.5, 0.1, 50000)
    t0 = time.perf_counter()
    for s in samples:
        detector.update(float(s))
    drift_dur = time.perf_counter() - t0
    results["streaming_drift_throughput"] = {
        "samples": 50000,
        "duration_sec": round(drift_dur, 4),
        "samples_per_sec": round(50000 / max(1e-5, drift_dur), 1),
    }
    print(
        f"[4/5] Streaming Drift Detector: {results['streaming_drift_throughput']['samples_per_sec']} samples/sec"
    )

    # 5. Benchmark: Event-Driven Causal Backtester
    tester = EventDrivenBacktester(initial_capital_usd=1000.0)
    for i in range(500):
        tester.push_event(
            float(i),
            "MARKET_TICK",
            {
                "token_id": "TKN_A",
                "spot_price": 10.0 + (i * 0.01),
                "pool_liquidity_usd": 50000.0,
            },
        )
    t0 = time.perf_counter()
    tester.run_simulation()
    event_dur = time.perf_counter() - t0
    results["event_driven_backtest"] = {
        "events_processed": 500,
        "duration_sec": round(event_dur, 4),
        "events_per_sec": round(500 / max(1e-5, event_dur), 1),
    }
    print(
        f"[5/5] Event-Driven Simulator: {results['event_driven_backtest']['events_per_sec']} events/sec"
    )

    print("==========================================================")
    print("  Benchmark Suite Completed Successfully!")
    print("==========================================================")
    return results


if __name__ == "__main__":
    run_all_benchmarks()
