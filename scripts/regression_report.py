#!/usr/bin/env python3
"""Automatic regression intelligence (W36 phase 12).

Beyond "pytest failed": diffs two committed evidence states and emits
machine-readable regression findings across the observability surface:

  * test health anomalies        (pytest_run.json passed/failed/exit delta)
  * benchmark degradation        (reuses scripts/benchmark_performance.compare)
  * schema drift                 (calibration report schema change)
  * unknown-rate increase        (self-observation data_completeness.unknown_share)
  * storage growth               (self-observation storage_growth.total_bytes)
  * import-graph change          (architecture_graph node/edge/cycle counts)
  * safety invariant change      (system_state lane_a.ok)

A finding is REGRESSION only when the deltas are supported by the artifacts;
absent artifacts yield NOT_COMPARABLE (never a fabricated regression).
Deterministic, read-only, stdlib-only.

Usage:
    python scripts/regression_report.py before.json after.json
    # before/after are any of the evidence-state JSON artifacts; each source
    # type present in BOTH is compared.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FINDING_TYPES = ("REGRESSION", "IMPROVEMENT", "INFO", "NOT_COMPARABLE")


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"cannot read artifact {path}: {e}")
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def _classify_delta(before: float, after: float, worse: str) -> str:
    if before == after:
        return "INFO"
    if after > before:
        return "REGRESSION" if worse == "up" else "IMPROVEMENT"
    return "IMPROVEMENT" if worse == "up" else "REGRESSION"


def build_regression_report(before_path: Path, after_path: Path) -> dict[str, Any]:
    before = _load(before_path)
    after = _load(after_path)
    findings: list[dict[str, Any]] = []

    def _num(d: dict, *keys: str) -> float | None:
        cur: Any = d
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        if isinstance(cur, (int, float)):
            return float(cur)
        return None

    def _get(d: dict, *keys: str) -> Any:
        cur: Any = d
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur

    # 1. Test health (record_test_run writes pytest_summary; older/other
    #    artifacts may use summary — accept both)
    def _test_summary(d: dict) -> dict[str, Any]:
        return d.get("pytest_summary") or d.get("summary") or {}

    if before.get("schema") == "ahos.test_run.v1" and \
            after.get("schema") == "ahos.test_run.v1":
        b_fail = _num(_test_summary(before), "failed")
        a_fail = _num(_test_summary(after), "failed")
        b_pass = _num(_test_summary(before), "passed")
        a_pass = _num(_test_summary(after), "passed")
        if b_fail is not None and a_fail is not None:
            findings.append({
                "source": "test_run",
                "metric": "failed",
                "before": b_fail, "after": a_fail,
                "delta": a_fail - b_fail,
                "kind": ("REGRESSION" if a_fail > b_fail
                         else "IMPROVEMENT" if a_fail < b_fail else "INFO"),
                "evidence": f"failed tests {b_fail:.0f} -> {a_fail:.0f}",
            })
        if b_pass is not None and a_pass is not None:
            findings.append({
                "source": "test_run",
                "metric": "passed",
                "before": b_pass, "after": a_pass,
                "delta": a_pass - b_pass,
                "kind": "INFO",
                "evidence": f"passed {b_pass:.0f} -> {a_pass:.0f}",
            })

    # 1b. Test-count anomaly (W37 P13): a large jump in passed-count with no
    #     code change is suspicious (tests added silently OR dropped).
    if before.get("schema") == "ahos.test_run.v1" and \
            after.get("schema") == "ahos.test_run.v1":
        b_pass = _num(_test_summary(before), "passed")
        a_pass = _num(_test_summary(after), "passed")
        if b_pass is not None and a_pass is not None:
            delta = a_pass - b_pass
            if abs(delta) >= 10:
                findings.append({
                    "source": "test_run",
                    "metric": "test_count_delta",
                    "before": b_pass, "after": a_pass,
                    "delta": delta,
                    "kind": "INFO",
                    "evidence": (f"test count moved {b_pass:.0f} -> {a_pass:.0f} "
                                 f"({delta:+.0f}) — verify the change was "
                                 "intentional (no silent test churn)"),
                })

    # 2. Benchmark degradation (headline metrics)
    if before.get("schema") == "ahos.benchmark_run.v1" and \
            after.get("schema") == "ahos.benchmark_run.v1":
        from scripts.benchmark_performance import compare_benchmarks
        diff = compare_benchmarks(before_path, after_path)
        for row in diff["rows"]:
            if not row["comparable"]:
                continue
            dp = row["delta_pct"]
            # direction-aware: latency worse when delta > 0, throughput worse
            # when delta < 0 (benchmark module knows; here we read the note)
            regressed = (row["metric"].startswith("latency") and dp > 0) or \
                        (not row["metric"].startswith("latency") and dp < 0)
            findings.append({
                "source": "benchmark",
                "metric": f"{row['benchmark']}.{row['metric']}",
                "before": row["before"], "after": row["after"],
                "delta": dp,
                "kind": "REGRESSION" if regressed else "INFO",
                "evidence": f"delta {dp:+.2f}%",
            })

    # 3. Calibration schema drift (top-level calibration artifact, or the
    #    nested latest_artifact schema inside a system-state snapshot)
    def _cal_schema(d: dict) -> Any:
        s = d.get("schema")
        if s and str(s).startswith("ahos.calibration_report."):
            return s
        return _get(d, "self_observation", "calibration_state",
                    "latest_artifact", "schema")

    b_schema = _cal_schema(before)
    a_schema = _cal_schema(after)
    if b_schema and a_schema:
        findings.append({
            "source": "calibration",
            "metric": "schema",
            "before": b_schema, "after": a_schema,
            "delta": None,
            "kind": ("INFO" if b_schema == a_schema else "REGRESSION"),
            "evidence": f"calibration schema {b_schema} -> {a_schema}",
        })

    # 4. UNKNOWN-rate increase
    b_share = _num(before, "self_observation", "data_completeness", "unknown_share")
    a_share = _num(after, "self_observation", "data_completeness", "unknown_share")
    if b_share is not None and a_share is not None:
        findings.append({
            "source": "self_observation",
            "metric": "unknown_share",
            "before": b_share, "after": a_share,
            "delta": a_share - b_share,
            "kind": "REGRESSION" if a_share > b_share else "INFO",
            "evidence": f"unknown share {b_share:.1%} -> {a_share:.1%}",
        })

    # 5. Storage growth
    b_bytes = _num(before, "self_observation", "storage_growth", "total_bytes")
    a_bytes = _num(after, "self_observation", "storage_growth", "total_bytes")
    if b_bytes is not None and a_bytes is not None:
        growth = a_bytes - b_bytes
        findings.append({
            "source": "self_observation",
            "metric": "store_bytes",
            "before": b_bytes, "after": a_bytes,
            "delta": growth,
            "kind": "INFO" if growth < 4 * 1024**3 else "REGRESSION",
            "evidence": f"{growth/1024**2:+.1f} MiB store growth",
        })

    # 6. Import-graph change (cycles is a LIST in the graph artifact; use
    #    its length so a new cycle is detected as a regression)
    b_nodes = _num(before, "node_count")
    a_nodes = _num(after, "node_count")
    b_cycles = len(before["cycles"]) if isinstance(before.get("cycles"), list) else None
    a_cycles = len(after["cycles"]) if isinstance(after.get("cycles"), list) else None
    if b_nodes is not None and a_nodes is not None:
        findings.append({
            "source": "architecture_graph",
            "metric": "node_count",
            "before": b_nodes, "after": a_nodes,
            "delta": a_nodes - b_nodes,
            "kind": "INFO",
            "evidence": f"graph nodes {b_nodes:.0f} -> {a_nodes:.0f}",
        })
    if b_cycles is not None and a_cycles is not None:
        findings.append({
            "source": "architecture_graph",
            "metric": "cycle_count",
            "before": b_cycles, "after": a_cycles,
            "delta": a_cycles - b_cycles,
            "kind": "REGRESSION" if a_cycles > b_cycles else "INFO",
            "evidence": f"import cycles {b_cycles:.0f} -> {a_cycles:.0f}",
        })

    # 7. Provider degradation: durable failure-event growth
    b_pf = _num(before, "self_observation", "provider_failure_rates",
                "total_failure_events")
    a_pf = _num(after, "self_observation", "provider_failure_rates",
                "total_failure_events")
    if b_pf is not None and a_pf is not None:
        growth = a_pf - b_pf
        findings.append({
            "source": "self_observation",
            "metric": "provider_failure_events",
            "before": b_pf, "after": a_pf,
            "delta": growth,
            "kind": "REGRESSION" if growth > 0 else "INFO",
            "evidence": f"provider failure events {b_pf:.0f} -> {a_pf:.0f}",
        })

    # 8. Calibration degradation: status change away from expected states
    b_cal = _get(before, "self_observation", "calibration_state",
                 "latest_artifact", "calibration_status")
    a_cal = _get(after, "self_observation", "calibration_state",
                 "latest_artifact", "calibration_status")
    if b_cal and a_cal and b_cal != a_cal:
        findings.append({
            "source": "self_observation",
            "metric": "calibration_status",
            "before": b_cal, "after": a_cal,
            "delta": None,
            "kind": ("REGRESSION" if a_cal in ("ERROR", "FAILED", "CRITICAL")
                     else "INFO"),
            "evidence": f"calibration status {b_cal} -> {a_cal}",
        })

    # 9. Safety invariant
    b_lane = _num(before, "lane_a", "ok")
    a_lane = _num(after, "lane_a", "ok")
    if b_lane is not None and a_lane is not None:
        findings.append({
            "source": "system_state",
            "metric": "lane_a_ok",
            "before": b_lane, "after": a_lane,
            "delta": a_lane - b_lane,
            "kind": "REGRESSION" if a_lane < b_lane else "INFO",
            "evidence": f"Lane-A ok {b_lane:.0f} -> {a_lane:.0f}",
        })

    if not findings:
        findings.append({
            "source": "artifacts",
            "metric": "comparable_surface",
            "before": None, "after": None, "delta": None,
            "kind": "NOT_COMPARABLE",
            "evidence": "no shared comparable surface between artifacts",
        })

    regression_count = sum(1 for f in findings if f["kind"] == "REGRESSION")
    return {
        "schema": "ahos.regression_report.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "before_artifact": str(before_path),
        "after_artifact": str(after_path),
        "regression_count": regression_count,
        "verdict": ("REGRESSION_DETECTED" if regression_count
                    else "NO_REGRESSION_DETECTED"),
        "findings": findings,
        "note": ("machine-readable regression findings; each is evidence-"
                 "backed or NOT_COMPARABLE, never invented"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS regression intelligence")
    ap.add_argument("before", help="before evidence-state artifact")
    ap.add_argument("after", help="after evidence-state artifact")
    ap.add_argument("--out", default=None, help="write the report artifact")
    args = ap.parse_args(argv)

    try:
        report = build_regression_report(Path(args.before), Path(args.after))
    except ValueError as e:
        print(f"ERROR: {e}")
        return 2

    out = Path(args.out) if args.out else (
        ROOT / "reports"
        / f"regression_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"regression verdict : {report['verdict']}")
    for f in report["findings"]:
        print(f"  [{f['kind']:<14}] {f['source']}.{f['metric']}: {f['evidence']}")
    print(f"artifact           : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
