#!/usr/bin/env python3
"""Month-3 weight-governance acceptance tool: calibration diff tests.

`scripts/calibration_diff.py` is the "any weight change ⇒ calibration diff
report attached to PR" acceptance tool. These tests pin:

  * Two INSUFFICIENT_DATA artifacts → honest NO_COMPARABLE_BANDS (exit 0).
  * Two comparable DESCRIPTIVE_OK artifacts → correct per-band rate deltas.
  * Identical dataset fingerprints → IDENTICAL_DATASETS, no rate deltas.
  * Horizon/event-class mismatch → band comparison refused, provenance only.
  * Deterministic output; missing/unparseable artifact → exit 2.
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

from scripts import calibration_diff as cd  # noqa: E402


def _write_report(path: Path, horizon="24h", event_class="+50%", verdict="INSUFFICIENT_DATA",
                  pairs=0, bands=None, fingerprint="f" * 64, metrics=None,
                  monotonicity=None, versions=None, weights=None):
    default_bands = [
        {"band": name, "n": 0, "positives": 0, "rate": None, "ci_low": None,
         "ci_high": None, "verdict": "INSUFFICIENT_DATA", "reason": "n<200;positives<20"}
        for name in ("0-20", "20-40", "40-60", "60-80", "80-100")
    ]
    payload = {
        "schema": "ahos.calibration_report.v5",
        "horizon": horizon,
        "event_class": event_class,
        "calibration_status": verdict,
        "number_of_eligible_pairs": pairs,
        "dataset_fingerprint": fingerprint,
        "bands": bands if bands is not None else default_bands,
        "monotonicity": monotonicity,
        "metrics": metrics or {},
        "score_engine_versions": versions or {},
        "weight_fingerprints": weights or [],
        "eligible_sources": ["local"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def _ok_band(name, n, hits, rate):
    return {"band": name, "n": n, "positives": hits, "rate": rate,
            "ci_low": 0.1, "ci_high": 0.9, "verdict": "DESCRIPTIVE_OK",
            "reason": None}


# ------------------------------------------------------------ honest answers

def test_two_insufficient_artifacts_is_no_comparable_bands(tmp_path):
    b = _write_report(tmp_path / "b.json", fingerprint="aaa")
    a = _write_report(tmp_path / "a.json", fingerprint="bbb")
    diff = cd.build_diff(tmp_path / "b.json", tmp_path / "a.json")

    assert diff["verdict"] == "NO_COMPARABLE_BANDS"
    assert any("No band is DESCRIPTIVE_OK" in f for f in diff["findings"])
    assert all(row["comparable"] is False for row in diff["bands"])
    assert diff["cohort"]["before"]["dataset_fingerprint"] == "aaa"
    assert diff["cohort"]["after"]["dataset_fingerprint"] == "bbb"


def test_identical_datasets_are_flagged_not_deltad(tmp_path):
    bands = [_ok_band("80-100", 250, 200, 0.8), _ok_band("0-20", 250, 30, 0.12)]
    fp = "same" * 16
    _write_report(tmp_path / "b.json", verdict="DESCRIPTIVE_OK", pairs=500,
                  bands=bands, fingerprint=fp,
                  metrics={"base_rate": 0.46, "guards_met": True})
    _write_report(tmp_path / "a.json", verdict="DESCRIPTIVE_OK", pairs=500,
                  bands=bands, fingerprint=fp,
                  metrics={"base_rate": 0.46, "guards_met": True})

    diff = cd.build_diff(tmp_path / "b.json", tmp_path / "a.json")
    assert "IDENTICAL_DATASETS" in " ".join(diff["findings"])
    assert all(row["comparable"] is False for row in diff["bands"])
    assert all(row["rate_delta"] is None for row in diff["bands"])


def test_horizon_mismatch_refuses_band_comparison(tmp_path):
    _write_report(tmp_path / "b.json", horizon="15m", verdict="DESCRIPTIVE_OK",
                  bands=[_ok_band("80-100", 250, 200, 0.8)])
    _write_report(tmp_path / "a.json", horizon="24h", verdict="DESCRIPTIVE_OK",
                  bands=[_ok_band("80-100", 250, 210, 0.84)])
    diff = cd.build_diff(tmp_path / "b.json", tmp_path / "a.json")

    assert diff["verdict"] == "NO_COMPARABLE_BANDS"
    assert any("COHORT_DEFINITION_MISMATCH" in f for f in diff["findings"])
    assert diff["bands"] == []


def test_missing_artifact_exits_2(tmp_path):
    assert cd.main([str(tmp_path / "nope.json"), str(tmp_path / "nope2.json")]) == 2


def test_non_report_artifact_exits_2(tmp_path):
    p = tmp_path / "junk.json"
    p.write_text(json.dumps({"hello": 1}), encoding="utf-8")
    q = tmp_path / "junk2.json"
    q.write_text(json.dumps({"hello": 2}), encoding="utf-8")
    assert cd.main([str(p), str(q)]) == 2


# ------------------------------------------------------------ comparable diffs

def test_comparable_bands_rate_deltas(tmp_path):
    before = [_ok_band("80-100", 250, 150, 0.60), _ok_band("0-20", 250, 30, 0.12)]
    after = [_ok_band("80-100", 300, 240, 0.80), _ok_band("0-20", 300, 30, 0.10)]
    _write_report(tmp_path / "b.json", verdict="DESCRIPTIVE_OK", pairs=500,
                  bands=before, fingerprint="b" * 64,
                  metrics={"base_rate": 0.36, "brier_score": 0.21,
                           "ece": 0.10, "guards_met": True},
                  monotonicity="MONOTONIC_INCREASING")
    _write_report(tmp_path / "a.json", verdict="DESCRIPTIVE_OK", pairs=600,
                  bands=after, fingerprint="a" * 64,
                  metrics={"base_rate": 0.45, "brier_score": 0.18,
                           "ece": 0.05, "guards_met": True},
                  monotonicity="MONOTONIC_INCREASING")

    diff = cd.build_diff(tmp_path / "b.json", tmp_path / "a.json")
    assert diff["verdict"] == "COMPARABLE"
    top = next(r for r in diff["bands"] if r["band"] == "80-100")
    bottom = next(r for r in diff["bands"] if r["band"] == "0-20")
    assert top["comparable"] is True
    assert top["rate_delta"] == pytest.approx(0.20)
    assert bottom["rate_delta"] == pytest.approx(-0.02)
    assert diff["metrics"]["base_rate"]["delta"] == pytest.approx(0.09)
    assert diff["metrics"]["brier_score"]["delta"] == pytest.approx(-0.03)
    assert diff["metrics"]["ece"]["delta"] == pytest.approx(-0.05)
    assert any("1 band(s) improved, 1 worsened" in f for f in diff["findings"])


def test_diff_is_deterministic(tmp_path):
    bands = [_ok_band("80-100", 250, 200, 0.8), _ok_band("0-20", 250, 30, 0.12)]
    _write_report(tmp_path / "b.json", verdict="DESCRIPTIVE_OK", pairs=500,
                  bands=bands, fingerprint="b" * 64,
                  metrics={"base_rate": 0.46, "guards_met": True})
    _write_report(tmp_path / "a.json", verdict="DESCRIPTIVE_OK", pairs=500,
                  bands=bands, fingerprint="a" * 64,
                  metrics={"base_rate": 0.50, "guards_met": True})

    d1 = cd.build_diff(tmp_path / "b.json", tmp_path / "a.json")
    d2 = cd.build_diff(tmp_path / "b.json", tmp_path / "a.json")
    assert d1 == d2


def test_cli_writes_artifact_and_prints(tmp_path, capsys):
    _write_report(tmp_path / "b.json", verdict="DESCRIPTIVE_OK",
                  bands=[_ok_band("80-100", 250, 200, 0.8)], fingerprint="b" * 64)
    _write_report(tmp_path / "a.json", verdict="DESCRIPTIVE_OK",
                  bands=[_ok_band("80-100", 250, 210, 0.84)], fingerprint="a" * 64)

    out = tmp_path / "diff.json"
    rc = cd.main([str(tmp_path / "b.json"), str(tmp_path / "a.json"), "--out", str(out)])
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "ahos.calibration_diff.v1"
    assert payload["verdict"] == "COMPARABLE"
    assert "git" in payload and "environment" in payload
    printed = capsys.readouterr().out
    assert "calibration_diff verdict : COMPARABLE" in printed
