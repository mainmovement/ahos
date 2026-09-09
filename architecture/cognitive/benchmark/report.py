"""Write machine-readable and human-readable P4.1 reports."""

from __future__ import annotations

import json
from pathlib import Path

from architecture.cognitive.benchmark.evaluator import BenchmarkReport
from architecture.cognitive.benchmark.metrics import FAIL, NOT_MEASURED, PASS


def write_json(report: BenchmarkReport, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def render_markdown(report: BenchmarkReport) -> str:
    lines = [
        "# P4.1 Cognitive Benchmark Report",
        "",
        f"**Benchmark version:** `{report.benchmark_version}`  ",
        f"**Git SHA:** `{report.git_sha}`  ",
        f"**Data label:** `{report.data_label}`  ",
        f"**Lane-A freeze:** `{report.lane_a_freeze}`  ",
        "",
        "This is **not** an AGI/ACI score. Metrics have numerators and denominators.",
        "Denominator 0 → `NOT_MEASURED`, never `PASS`.",
        "",
        "## Case counts",
        "",
    ]
    for k, v in sorted(report.case_counts.items()):
        lines.append(f"- `{k}`: {v}")
    lines += ["", "## Metrics", "", "| metric | value | n/d | threshold | status | class |", "|---|---:|---:|---:|---|---|"]
    for m in report.metrics:
        val = "—" if m.value is None else f"{m.value:.4f}"
        thr = "—" if m.threshold is None else f"{m.threshold:.4f} {m.threshold_kind}"
        lines.append(
            f"| `{m.metric_id}` | {val} | {m.numerator:.4f}/{m.denominator:.4f} | {thr} | {m.status} | {m.threshold_class} |"
        )
    status_counts = {PASS: 0, FAIL: 0, NOT_MEASURED: 0}
    for m in report.metrics:
        status_counts[m.status] = status_counts.get(m.status, 0) + 1
    lines += [
        "",
        "## Status counts",
        "",
        f"- PASS: {status_counts.get(PASS, 0)}",
        f"- FAIL: {status_counts.get(FAIL, 0)}",
        f"- NOT_MEASURED: {status_counts.get(NOT_MEASURED, 0)}",
        "",
        "## Weaknesses",
        "",
    ]
    if report.weaknesses:
        lines.extend(f"- {w}" for w in report.weaknesses)
    else:
        lines.append("- none recorded")
    lines += ["", "## Improvement candidates (not auto-applied)", ""]
    if report.improvement_candidates:
        lines.extend(f"- {c}" for c in report.improvement_candidates)
    else:
        lines.append("- none recorded")
    lines += ["", "## Soak protection", ""]
    for k, v in report.soak_protection.items():
        lines.append(f"- `{k}`: {v}")
    lines += ["", "## Limitations", ""]
    lines.extend(f"- {x}" for x in report.limitations)
    lines += [
        "",
        "## What this is not",
        "",
        "- Not AGI, not ACI, not a world model, not soak evidence.",
        "- Not a 99.9% intelligence score.",
        "- Not authorization to promote, trade, or execute live.",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_markdown(report: BenchmarkReport, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")
    return path
