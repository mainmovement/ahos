#!/usr/bin/env python3
"""Automatic regression intelligence (W36 phase 12).

Pins: test-failure deltas, benchmark degradation (direction-aware), schema
drift, UNKNOWN-share increase, storage growth, import-cycle increase,
Lane-A invariant loss — each evidence-backed or NOT_COMPARABLE, never
invented. Deterministic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import regression_report as rr  # noqa: E402


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _test_run(passed=100, failed=0):
    return {"schema": "ahos.test_run.v1",
            "summary": {"passed": passed, "failed": failed}}


def _bench(results, commit="b"):
    return {"schema": "ahos.benchmark_run.v1", "git": {"commit_sha": commit},
            "results": results}


def _health(unknown_share=0.1, total_bytes=1000, schema="ahos.calibration_report.v7",
            cal_status="INSUFFICIENT_DATA"):
    return {
        "schema": "ahos.system_state.v1",
        "lane_a": {"ok": 1},
        "self_observation": {
            "data_completeness": {"unknown_share": unknown_share},
            "storage_growth": {"total_bytes": total_bytes},
            "provider_failure_rates": {"total_failure_events": 0},
            "calibration_state": {"latest_artifact": {"schema": schema,
                                                      "calibration_status": cal_status}},
        },
    }


def test_test_failure_regression_detected(tmp_path):
    _write(tmp_path / "b.json", _test_run(failed=0))
    _write(tmp_path / "a.json", _test_run(failed=3))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    assert report["verdict"] == "REGRESSION_DETECTED"
    f = next(x for x in report["findings"] if x["metric"] == "failed")
    assert f["kind"] == "REGRESSION" and f["delta"] == 3


def test_benchmark_latency_regression_and_throughput_improvement(tmp_path):
    _write(tmp_path / "b.json", _bench({
        "quantstats_tearsheet": {"latency_per_tearsheet_ms": 5.0},
        "vectorized_backtest": {"evaluations_per_sec": 1000.0},
    }))
    _write(tmp_path / "a.json", _bench({
        "quantstats_tearsheet": {"latency_per_tearsheet_ms": 7.0},   # worse
        "vectorized_backtest": {"evaluations_per_sec": 1200.0},      # better
    }))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    latency = next(x for x in report["findings"]
                   if x["metric"] == "quantstats_tearsheet.latency_per_tearsheet_ms")
    throughput = next(x for x in report["findings"]
                      if x["metric"] == "vectorized_backtest.evaluations_per_sec")
    assert latency["kind"] == "REGRESSION"
    assert throughput["kind"] == "INFO"  # improvement is not a regression
    assert report["verdict"] == "REGRESSION_DETECTED"


def test_calibration_schema_drift_is_regression(tmp_path):
    _write(tmp_path / "b.json", _health(schema="ahos.calibration_report.v6"))
    _write(tmp_path / "a.json", _health(schema="ahos.calibration_report.v7"))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    schema = next(x for x in report["findings"] if x["metric"] == "schema")
    assert schema["kind"] == "REGRESSION"
    assert "calibration_report.v6" in schema["evidence"]
    assert "calibration_report.v7" in schema["evidence"]


def test_unknown_share_increase_is_regression(tmp_path):
    _write(tmp_path / "b.json", _health(unknown_share=0.2))
    _write(tmp_path / "a.json", _health(unknown_share=0.6))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    f = next(x for x in report["findings"] if x["metric"] == "unknown_share")
    assert f["kind"] == "REGRESSION"


def test_lane_a_loss_is_regression(tmp_path):
    _write(tmp_path / "b.json", _health())
    a = _health()
    a["lane_a"]["ok"] = 0
    _write(tmp_path / "a.json", a)
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    f = next(x for x in report["findings"] if x["metric"] == "lane_a_ok")
    assert f["kind"] == "REGRESSION"


def test_no_shared_surface_is_not_comparable(tmp_path):
    _write(tmp_path / "b.json", {"unrelated": 1})
    _write(tmp_path / "a.json", {"also_unrelated": 2})
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    assert report["verdict"] == "NO_REGRESSION_DETECTED"
    assert any(f["kind"] == "NOT_COMPARABLE" for f in report["findings"])


def test_identical_states_no_regression(tmp_path):
    payload = _health(unknown_share=0.3, total_bytes=5000)
    _write(tmp_path / "b.json", payload)
    _write(tmp_path / "a.json", dict(payload))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    assert report["verdict"] == "NO_REGRESSION_DETECTED"
    assert all(f["kind"] in ("INFO", "NOT_COMPARABLE")
               for f in report["findings"])


def test_cli_writes_artifact_and_missing_file_exits_2(tmp_path):
    _write(tmp_path / "b.json", _test_run())
    _write(tmp_path / "a.json", _test_run(failed=1))
    out = tmp_path / "report.json"
    assert rr.main([str(tmp_path / "b.json"), str(tmp_path / "a.json"),
                    "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema"] == "ahos.regression_report.v1"
    assert rr.main([str(tmp_path / "nope.json"), str(tmp_path / "a.json")]) == 2


def test_provider_failure_growth_is_regression(tmp_path):
    b = _health()
    a = _health()
    a["self_observation"]["provider_failure_rates"] = {
        "total_failure_events": 5}
    b["self_observation"]["provider_failure_rates"] = {
        "total_failure_events": 0}
    _write(tmp_path / "b.json", b)
    _write(tmp_path / "a.json", a)
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    f = next(x for x in report["findings"] if x["metric"] == "provider_failure_events")
    assert f["kind"] == "REGRESSION" and f["delta"] == 5


def test_calibration_status_change_to_error_is_regression(tmp_path):
    b = _health()
    a = _health()
    a["self_observation"]["calibration_state"]["latest_artifact"][
        "calibration_status"] = "ERROR"
    _write(tmp_path / "b.json", b)
    _write(tmp_path / "a.json", a)
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    f = next(x for x in report["findings"] if x["metric"] == "calibration_status")
    assert f["kind"] == "REGRESSION"


def test_test_count_jump_is_flagged(tmp_path):
    _write(tmp_path / "b.json", _test_run(passed=100))
    _write(tmp_path / "a.json", _test_run(passed=140))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    f = next(x for x in report["findings"] if x["metric"] == "test_count_delta")
    assert f["delta"] == 40
    assert "verify the change was intentional" in f["evidence"]


def test_small_test_count_change_not_flagged(tmp_path):
    _write(tmp_path / "b.json", _test_run(passed=100))
    _write(tmp_path / "a.json", _test_run(passed=103))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    assert not any(x["metric"] == "test_count_delta" for x in report["findings"])


def _graph(nodes, cycles, edges):
    return {"schema": "ahos.architecture_graph.v1",
            "node_count": nodes, "edge_count": edges, "cycles": cycles}


def test_new_architecture_cycle_is_regression(tmp_path):
    _write(tmp_path / "b.json", _graph(100, [], 200))
    _write(tmp_path / "a.json", _graph(100, [["a", "b"]], 200))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    f = next(x for x in report["findings"] if x["metric"] == "cycle_count")
    assert f["kind"] == "REGRESSION" and f["delta"] == 1


def test_cycle_removal_is_not_regression(tmp_path):
    _write(tmp_path / "b.json", _graph(100, [["a", "b"]], 200))
    _write(tmp_path / "a.json", _graph(100, [], 200))
    report = rr.build_regression_report(tmp_path / "b.json", tmp_path / "a.json")
    f = next(x for x in report["findings"] if x["metric"] == "cycle_count")
    assert f["kind"] == "INFO" and f["delta"] == -1
