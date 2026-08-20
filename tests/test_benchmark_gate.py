#!/usr/bin/env python3
"""Benchmark persistence + before/after compare gate (evolution mission §5).

Pins:
  * A run persists a `ahos.benchmark_run.v1` artifact carrying git/env.
  * compare_benchmarks reports per-benchmark absolute + relative deltas with
    a COMPARABLE verdict; benchmarks missing from either side are
    NOT_COMPARABLE (never a fake delta).
  * Deterministic output; missing/unparseable artifact exits 2.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import benchmark_performance as bench  # noqa: E402


def _artifact(path: Path, results, commit="a" * 40):
    payload = {
        "schema": "ahos.benchmark_run.v1",
        "timestamp_utc": "2026-08-20T00:00:00Z",
        "git": {"commit_sha": commit},
        "environment": {"fingerprint_sha256": "x" * 64},
        "results": results,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _results(**kw):
    base = {
        "vectorized_backtest": {"combinations_evaluated": 64, "duration_seconds": 0.05,
                                "evaluations_per_sec": 1300.0},
        "quantstats_tearsheet": {"runs": 50, "total_duration_sec": 0.5,
                                 "latency_per_tearsheet_ms": 10.0},
        "olap_analytics_bridge": {"latency_per_aggregation_ms": 4.0},
        "streaming_drift_throughput": {"samples_per_sec": 400000.0},
        "event_driven_backtest": {"events_per_sec": 700000.0},
    }
    for k, v in kw.items():
        if k in base and isinstance(v, dict):
            base[k].update(v)
        else:
            raise KeyError(f"unknown benchmark override: {k}")
    return base


def test_run_persists_benchmark_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "run_all_benchmarks",
                        lambda: _results(vectorized_backtest={"evaluations_per_sec": 1310.0}))
    out = tmp_path / "bench.json"
    rc = bench.main(["run", "--out", str(out), "--commit-sha", "c" * 40])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema"] == "ahos.benchmark_run.v1"
    assert data["git"]["commit_sha"] == "c" * 40
    assert data["results"]["vectorized_backtest"]["evaluations_per_sec"] == 1310.0


def test_compare_reports_headline_deltas(tmp_path):
    before = _results(vectorized_backtest={"evaluations_per_sec": 1000.0},
                      quantstats_tearsheet={"latency_per_tearsheet_ms": 10.0},
                      streaming_drift_throughput={"samples_per_sec": 400000.0},
                      event_driven_backtest={"events_per_sec": 700000.0})
    after = _results(vectorized_backtest={"evaluations_per_sec": 1200.0},
                     quantstats_tearsheet={"latency_per_tearsheet_ms": 8.0},
                     streaming_drift_throughput={"samples_per_sec": 400000.0},
                     event_driven_backtest={"events_per_sec": 700000.0})
    _artifact(tmp_path / "b.json", before, commit="b" * 40)
    _artifact(tmp_path / "a.json", after, commit="a" * 40)

    diff = bench.compare_benchmarks(tmp_path / "b.json", tmp_path / "a.json")
    assert diff["verdict"] == "COMPARABLE"
    assert diff["before_commit"] == "b" * 40
    rows = {r["benchmark"]: r for r in diff["rows"]}

    # higher-is-better improved +20%
    assert rows["vectorized_backtest"]["delta_pct"] == pytest.approx(20.0)
    assert rows["vectorized_backtest"]["comparable"] is True
    # latency improved (delta negative is good)
    assert rows["quantstats_tearsheet"]["delta_pct"] == pytest.approx(-20.0)
    # unchanged
    assert rows["streaming_drift_throughput"]["delta_pct"] == pytest.approx(0.0)


def test_compare_missing_benchmark_is_not_comparable(tmp_path):
    before = _results()
    after = _results()
    after.pop("event_driven_backtest")
    _artifact(tmp_path / "b.json", before)
    _artifact(tmp_path / "a.json", after)

    diff = bench.compare_benchmarks(tmp_path / "b.json", tmp_path / "a.json")
    row = next(r for r in diff["rows"] if r["benchmark"] == "event_driven_backtest")
    assert row["comparable"] is False
    assert row["delta_pct"] is None
    # others still comparable
    assert any(r["comparable"] for r in diff["rows"])
    assert diff["verdict"] == "COMPARABLE"


def test_compare_is_deterministic(tmp_path):
    _artifact(tmp_path / "b.json",
              _results(vectorized_backtest={"evaluations_per_sec": 1000.0}))
    _artifact(tmp_path / "a.json",
              _results(vectorized_backtest={"evaluations_per_sec": 1100.0}))
    d1 = bench.compare_benchmarks(tmp_path / "b.json", tmp_path / "a.json")
    d2 = bench.compare_benchmarks(tmp_path / "b.json", tmp_path / "a.json")
    assert d1 == d2


def test_compare_missing_artifact_exits_2(tmp_path):
    assert bench.main(["compare", str(tmp_path / "nope.json"),
                       str(tmp_path / "nope2.json")]) == 2


def test_compare_cli_writes_artifact(tmp_path, capsys):
    _artifact(tmp_path / "b.json",
              _results(vectorized_backtest={"evaluations_per_sec": 1000.0}))
    _artifact(tmp_path / "a.json",
              _results(vectorized_backtest={"evaluations_per_sec": 1100.0}))
    out = tmp_path / "diff.json"
    rc = bench.main(["compare", str(tmp_path / "b.json"), str(tmp_path / "a.json"),
                     "--out", str(out)])
    assert rc == 0
    diff = json.loads(out.read_text(encoding="utf-8"))
    assert diff["schema"] == "ahos.benchmark_diff.v1"
    printed = capsys.readouterr().out
    assert "benchmark_diff verdict : COMPARABLE" in printed
