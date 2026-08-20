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

import argparse
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


def record_benchmark(results: Dict[str, Any], out_path: Path | str | None = None,
                     commit_sha: str | None = None) -> Path:
    """Persist a benchmark run as a reproducible evidence artifact.

    Carries the git commit, timestamp and environment so a later `compare`
    can attribute a delta to a code change vs. a different machine.
    """
    from scripts.evidence_common import environment_fingerprint, git_meta, utc_now

    payload = {
        "schema": "ahos.benchmark_run.v1",
        "timestamp_utc": utc_now(),
        "git": git_meta(),
        "environment": environment_fingerprint(),
        "results": results,
    }
    if commit_sha:
        payload["git"]["commit_sha"] = commit_sha
    out = Path(out_path) if out_path else (
        ROOT / "reports"
        / f"benchmark_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return out


#: The primary throughput/latency metric per benchmark — the number a
#: before/after comparison should headline. Adding a benchmark must add its
#: headline metric here, or the compare gate cannot see it.
HEADLINE_METRICS: Dict[str, str] = {
    "vectorized_backtest": "evaluations_per_sec",
    "quantstats_tearsheet": "latency_per_tearsheet_ms",
    "olap_analytics_bridge": "latency_per_aggregation_ms",
    "streaming_drift_throughput": "samples_per_sec",
    "event_driven_backtest": "events_per_sec",
}


def compare_benchmarks(before_path: Path, after_path: Path) -> Dict[str, Any]:
    """Deterministic before/after benchmark diff (mission §5 evidence).

    Compares headline metrics for benchmarks present in BOTH artifacts and
    reports the absolute and relative delta (after − before). Benchmarks
    missing from either side are listed as NOT_COMPARABLE — never a fake
    delta. Higher-is-better metrics are flagged so a positive delta is
    readable as an improvement regardless of direction.
    """
    def _load(p: Path) -> Dict[str, Any]:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise ValueError(f"cannot read benchmark artifact {p}: {e}")
        if not isinstance(data.get("results"), dict):
            raise ValueError(f"{p} is not a benchmark_run artifact")
        return data

    before = _load(before_path)
    after = _load(after_path)
    b_res, a_res = before["results"], after["results"]

    rows: list[Dict[str, Any]] = []
    for name, metric in sorted(HEADLINE_METRICS.items()):
        bm, am = b_res.get(name), a_res.get(name)
        bv = (bm or {}).get(metric) if bm else None
        av = (am or {}).get(metric) if am else None
        if bv is None or av is None:
            rows.append({"benchmark": name, "metric": metric,
                         "before": bv, "after": av,
                         "delta_abs": None, "delta_pct": None,
                         "comparable": False})
            continue
        delta_abs = round(av - bv, 4)
        delta_pct = round((delta_abs / bv) * 100.0, 2) if bv else None
        rows.append({"benchmark": name, "metric": metric,
                     "before": bv, "after": av,
                     "delta_abs": delta_abs, "delta_pct": delta_pct,
                     "comparable": True})

    verdict = "COMPARABLE" if any(r["comparable"] for r in rows) else "NO_COMPARABLE_METRICS"
    return {
        "schema": "ahos.benchmark_diff.v1",
        "before_artifact": str(before_path),
        "after_artifact": str(after_path),
        "verdict": verdict,
        "before_commit": (before.get("git") or {}).get("commit_sha"),
        "after_commit": (after.get("git") or {}).get("commit_sha"),
        "rows": rows,
        "note": ("delta = after − before. Higher-is-better metrics "
                 "(evaluations/s, samples/s, events/s) improve when delta > 0; "
                 "latency metrics improve when delta < 0."),
    }


def _print_diff(diff: Dict[str, Any]) -> None:
    print(f"benchmark_diff verdict : {diff['verdict']}")
    print(f"before                 : {diff['before_commit']} ({diff['before_artifact']})")
    print(f"after                  : {diff['after_commit']} ({diff['after_artifact']})")
    for r in diff["rows"]:
        if not r["comparable"]:
            print(f"  {r['benchmark']:<26} NOT_COMPARABLE "
                  f"(before={r['before']}, after={r['after']})")
            continue
        print(f"  {r['benchmark']:<26} {r['before']:>12} -> {r['after']:>12} "
              f"({r['delta_pct']:+.2f}%)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS performance micro-benchmark suite")
    sub = ap.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="run the benchmark suite (default)")
    run_p.add_argument("--out", default=None, help="artifact path for the run")
    run_p.add_argument("--commit-sha", default=None,
                       help="commit sha to stamp (default: git HEAD)")

    cmp_p = sub.add_parser("compare", help="diff two benchmark artifacts")
    cmp_p.add_argument("before", help="before benchmark_run artifact")
    cmp_p.add_argument("after", help="after benchmark_run artifact")
    cmp_p.add_argument("--out", default=None, help="write the diff artifact")

    args = ap.parse_args(argv)

    if args.command == "compare":
        try:
            diff = compare_benchmarks(Path(args.before), Path(args.after))
        except ValueError as e:
            print(f"ERROR: {e}")
            return 2
        _print_diff(diff)
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(diff, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
            print(f"artifact           : {out}")
        return 0

    results = run_all_benchmarks()
    # Always persist: a benchmark run without a recorded artifact cannot be
    # compared later (mission §5: measure -> record -> compare).
    path = record_benchmark(results, out_path=args.out, commit_sha=args.commit_sha)
    print(f"benchmark artifact : {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
