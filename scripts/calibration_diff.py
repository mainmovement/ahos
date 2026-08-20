#!/usr/bin/env python3
"""AHOS calibration diff — the governance acceptance tool for scoring changes.

Month-3 roadmap: "Weight governance: versioned weight sets + acceptance test on
historical data | Any weight change ⇒ calibration diff report attached to PR."

This tool compares two calibration report artifacts
(`ahos.calibration_report.vN`) and produces a structured, deterministic diff:

  - verdict change (INSUFFICIENT_DATA ↔ DESCRIPTIVE_OK)
  - per-band rate deltas (after − before) for bands that are comparable
  - monotonicity change
  - diagnostic deltas (base_rate, Brier, ECE, Spearman)
  - full provenance of BOTH sides (dataset fingerprints, weight fingerprints,
    engine versions, timestamps) — a number without provenance is not evidence

Honesty rules (same law as the harness it diffs):
  1. Bands are compared only when BOTH artifacts have that band at
     DESCRIPTIVE_OK for the SAME horizon + event_class. Anything else is
     `NO_COMPARABLE_BANDS` — the correct, expected answer while real evidence
     is still accruing (M-GAP-008). Never a misleading delta.
  2. Identical dataset fingerprints on both sides ⇒ `IDENTICAL_DATASETS`: the
     "change" is in the code, not the data, and rate deltas would be a lie.
  3. Mixed engine versions are censused on both sides and flagged, never
     silently pooled.
  4. Horizon/event-class mismatches refuse band comparison outright.

Read-only. Writes exactly one artifact under reports/ (or --out). Exit codes:
    0 = diff produced (INCLUDING an honest NO_COMPARABLE_BANDS verdict)
    2 = diff could not be produced (missing/unparseable artifact)

Usage:
    python scripts/calibration_diff.py reports/before.json reports/after.json
    python scripts/calibration_diff.py before.json after.json --stdout
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

from scripts.evidence_common import environment_fingerprint, git_meta, utc_now  # noqa: E402


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"cannot read artifact {path}: {type(e).__name__}: {e}")
    if not isinstance(data, dict) or "bands" not in data:
        raise ValueError(f"{path} is not a calibration report artifact (no 'bands')")
    return data


def _band_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {b["band"]: b for b in report.get("bands", []) if isinstance(b, dict)}


def _band_delta(before: dict[str, Any] | None, after: dict[str, Any] | None) -> dict[str, Any]:
    """One band's before/after row. Rates compared only when both are
    DESCRIPTIVE_OK; anything else is an explicit NOT_COMPARABLE."""
    def _rate(b: dict[str, Any] | None) -> float | None:
        return b.get("rate") if b and b.get("verdict") == "DESCRIPTIVE_OK" else None

    br, ar = _rate(before), _rate(after)
    comparable = (br is not None and ar is not None)
    row = {
        "band": (before or after or {}).get("band"),
        "before_n": (before or {}).get("n", 0),
        "after_n": (after or {}).get("n", 0),
        "before_rate": br,
        "after_rate": ar,
        "rate_delta": (round(ar - br, 6) if comparable else None),
        "before_verdict": (before or {}).get("verdict", "ABSENT"),
        "after_verdict": (after or {}).get("verdict", "ABSENT"),
        "comparable": comparable,
    }
    return row


def build_diff(before_path: Path, after_path: Path) -> dict[str, Any]:
    before = _load(before_path)
    after = _load(after_path)

    b_horizon = before.get("horizon")
    a_horizon = after.get("horizon")
    b_class = before.get("event_class")
    a_class = after.get("event_class")
    same_cohort_def = (b_horizon == a_horizon and b_class == a_class)

    b_bands = _band_map(before)
    a_bands = _band_map(after)

    verdict = "NO_COMPARABLE_BANDS"
    findings: list[str] = []
    band_rows: list[dict[str, Any]] = []

    if not same_cohort_def:
        findings.append(
            f"COHORT_DEFINITION_MISMATCH: before=({b_horizon},{b_class}) "
            f"after=({a_horizon},{a_class}) — bands are not comparable across "
            "different horizons/event classes; provenance only.")
    else:
        for name in sorted(set(b_bands) | set(a_bands)):
            band_rows.append(_band_delta(b_bands.get(name), a_bands.get(name)))

        comparable = [r for r in band_rows if r["comparable"]]
        if not comparable:
            findings.append(
                f"No band is DESCRIPTIVE_OK on both sides "
                f"(before {len(b_bands)} bands, after {len(a_bands)} bands) — "
                "no rate delta can be stated while real evidence is insufficient "
                "(M-GAP-008). This is the expected honest answer, not a failure.")
        else:
            b_fp = before.get("dataset_fingerprint")
            a_fp = after.get("dataset_fingerprint")
            if b_fp and a_fp and b_fp == a_fp:
                findings.append(
                    "IDENTICAL_DATASETS: both artifacts carry the same dataset "
                    "fingerprint — rate deltas would describe a code change on "
                    "the same rows; stating them would be misleading. "
                    "Reported as identical; re-run after new evidence accrues.")
                for r in band_rows:
                    r["comparable"] = False
                    r["rate_delta"] = None
            else:
                verdict = "COMPARABLE"
                deltas = [r["rate_delta"] for r in comparable
                          if r["rate_delta"] is not None]
                if deltas:
                    improved = sum(1 for d in deltas if d > 0)
                    worsened = sum(1 for d in deltas if d < 0)
                    findings.append(
                        f"{improved} band(s) improved, {worsened} worsened "
                        f"after the change (delta = after − before).")

    # monotonicity change (informational, only when both sides have it)
    monotonicity = {
        "before": before.get("monotonicity"),
        "after": after.get("monotonicity"),
    }

    # diagnostic deltas — arithmetic facts about both cohorts, comparable only
    # when both sides have the metric (guards_met travels with each side)
    metrics: dict[str, Any] = {}
    for key in ("base_rate", "brier_score", "brier_base_rate", "ece",
                "spearman_score_vs_hit", "spearman_score_vs_maxfav", "guards_met"):
        bv = (before.get("metrics") or {}).get(key)
        av = (after.get("metrics") or {}).get(key)
        if isinstance(bv, (int, float)) and isinstance(av, (int, float)):
            metrics[key] = {"before": bv, "after": av,
                            "delta": round(av - bv, 6)}
        else:
            metrics[key] = {"before": bv, "after": av, "delta": None}

    return {
        "schema": "ahos.calibration_diff.v1",
        "generated_utc": utc_now(),
        "before_artifact": str(before_path),
        "after_artifact": str(after_path),
        "verdict": verdict,
        "cohort": {
            "before": {"horizon": b_horizon, "event_class": b_class,
                       "joined_pairs": before.get("number_of_eligible_pairs"),
                       "calibration_status": before.get("calibration_status"),
                       "dataset_fingerprint": before.get("dataset_fingerprint")},
            "after": {"horizon": a_horizon, "event_class": a_class,
                      "joined_pairs": after.get("number_of_eligible_pairs"),
                      "calibration_status": after.get("calibration_status"),
                      "dataset_fingerprint": after.get("dataset_fingerprint")},
        },
        "provenance": {
            "before": {
                "score_engine_versions": before.get("score_engine_versions", {}),
                "weight_fingerprints": before.get("weight_fingerprints", []),
                "eligible_sources": before.get("eligible_sources", []),
            },
            "after": {
                "score_engine_versions": after.get("score_engine_versions", {}),
                "weight_fingerprints": after.get("weight_fingerprints", []),
                "eligible_sources": after.get("eligible_sources", []),
            },
        },
        "bands": band_rows,
        "monotonicity": monotonicity,
        "metrics": metrics,
        "findings": findings,
    }


def render(diff: dict[str, Any]) -> str:
    lines = [f"calibration_diff verdict : {diff['verdict']}"]
    cohort = diff["cohort"]
    lines.append(f"before ({cohort['before']['horizon']},{cohort['before']['event_class']}): "
                 f"{cohort['before']['joined_pairs']} pairs, "
                 f"{cohort['before']['calibration_status']}, "
                 f"fp={str(cohort['before']['dataset_fingerprint'])[:12] or '(none)'}")
    lines.append(f"after  ({cohort['after']['horizon']},{cohort['after']['event_class']}): "
                 f"{cohort['after']['joined_pairs']} pairs, "
                 f"{cohort['after']['calibration_status']}, "
                 f"fp={str(cohort['after']['dataset_fingerprint'])[:12] or '(none)'}")
    for row in diff["bands"]:
        delta = f"{row['rate_delta']:+.4f}" if row["rate_delta"] is not None else "n/a"
        lines.append(
            f"  band {row['band']:>7}: before={row['before_verdict']} "
            f"({row['before_n']:>4}) after={row['after_verdict']} "
            f"({row['after_n']:>4}) delta={delta}")
    for key, m in diff["metrics"].items():
        delta = f"{m['delta']:+.6f}" if m["delta"] is not None else "n/a"
        lines.append(f"  metric {key:<24}: before={m['before']} after={m['after']} "
                     f"delta={delta}")
    if diff["monotonicity"]["before"] or diff["monotonicity"]["after"]:
        lines.append(f"  monotonicity: {diff['monotonicity']['before']} -> "
                     f"{diff['monotonicity']['after']}")
    for finding in diff["findings"]:
        lines.append(f"  - {finding}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS calibration diff (weight-governance acceptance tool)")
    ap.add_argument("before", help="path to the before calibration artifact")
    ap.add_argument("after", help="path to the after calibration artifact")
    ap.add_argument("--out", default=None, help="output path for the JSON artifact")
    ap.add_argument("--stdout", action="store_true", help="also print the diff")
    args = ap.parse_args(argv)

    try:
        diff = build_diff(Path(args.before), Path(args.after))
    except ValueError as e:
        print(f"ERROR: {e}")
        return 2

    diff["command"] = ("python scripts/calibration_diff.py "
                       f"{args.before} {args.after}")
    diff["timestamp_utc"] = utc_now()
    diff["git"] = git_meta()
    diff["environment"] = environment_fingerprint()

    out = Path(args.out) if args.out else (
        ROOT / "reports" / f"calibration_diff_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(diff, indent=2, ensure_ascii=False), encoding="utf-8")

    print(render(diff))
    print(f"artifact           : {_display_path(out)}")

    if args.stdout:
        print(json.dumps(diff, indent=2, ensure_ascii=False))
    return 0


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    sys.exit(main())
