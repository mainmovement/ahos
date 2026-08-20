#!/usr/bin/env python3
"""Month-3 (M-GAP-008): extended calibration harness tests.

Covers the evaluation surface that turns 'explainable score' into 'measured
score': confidence-bucket segmentation, chain segmentation, continuous
outcome statistics (max_favorable/max_adverse), Brier / ECE / rank
correlation diagnostics, evidence-coverage census, extreme-record
provenance, honest dimension-availability, multi-horizon runs, and the
INSUFFICIENT_DATA discipline (no fabricated outcomes, no misleading
statistics on tiny cohorts).

No test touches the network; every fixture is written straight into
temp SQLite stores stamped with the `test` evidence namespace, and the
harness is explicitly pointed at it (the override's necessity is itself the
proof that real calibration cannot silently consume test data).
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.calibration import (  # noqa: E402
    CONFIDENCE_LEVELS,
    MIN_N_PER_BAND,
    MIN_POSITIVES,
    CalibrationHarness,
    SegmentResult,
    _brier,
    _median,
    _spearman,
)
from architecture.learning.score_ledger import (  # noqa: E402
    SCORING_ENGINE_VERSION,
    SOURCE_TEST,
    ScoreLedger,
)

# --------------------------------------------------------------------- helpers


def _seed(tmp_path, rows, horizon="24h", event_class="+50%", now=None):
    """rows: list of dicts with at least score/hit; optional confidence, chain,
    max_favorable, max_adverse, known_fields, unknown_fields, evidence_sha,
    engine_version, resolved_offset."""
    ledger_db = tmp_path / "ledger.sqlite"
    disc_db = tmp_path / "disc.sqlite"
    t0 = (now or time.time()) - 86400
    ScoreLedger(db_path=str(ledger_db))   # creates the ledger schema
    conn = sqlite3.connect(str(ledger_db))
    dconn = sqlite3.connect(str(disc_db))
    dconn.execute(
        """CREATE TABLE outcome_label (
             token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
             hit INTEGER, max_favorable REAL, max_adverse REAL,
             entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
             PRIMARY KEY (token_id, horizon, event_class))""")

    for i, r in enumerate(rows):
        tid = f"token{i:05d}"
        conf = r.get("confidence", "HIGH")
        chain = r.get("chain", "solana")
        engine = r.get("engine_version", SCORING_ENGINE_VERSION)
        resolved_offset = r.get("resolved_offset", 3600.0)
        provider = r.get("provider", "")
        conn.execute(
            """INSERT INTO opportunity_score_ledger(
                 score_id, scored_ts, scored_utc, run_id, source, chain, token_address,
                 token_id, symbol, opportunity_score, confidence_level, risk_level,
                 base_score, total_penalties, engine_version, weights_sha256,
                 evidence_sha256, known_field_count, unknown_field_count,
                 positive_reasons_json, risk_findings_json, missing_unknowns_json,
                 invalidation_json, score_breakdown_json, source_provider)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f"s{i:05d}", t0 + i, "2026-01-01T00:00:00Z", "run", SOURCE_TEST, chain,
             f"addr{i}", tid, "T", float(r["score"]), conf, "LOW", 0.0, 0.0,
             engine, r.get("weights", "a" * 64),
             r.get("evidence_sha", "b" * 64),
             r.get("known_fields", 4), r.get("unknown_fields", 0),
             "[]", "[]", "[]", "[]", "{}", provider))
        dconn.execute(
            """INSERT INTO outcome_label(token_id,horizon,event_class,hit,
                 max_favorable,max_adverse,resolved_ts)
               VALUES (?,?,?,?,?,?,?)""",
            (tid, horizon, event_class, int(r["hit"]),
             r.get("max_favorable"), r.get("max_adverse"), t0 + resolved_offset))

    conn.commit(); conn.close()
    dconn.commit(); dconn.close()
    return CalibrationHarness(ledger_db=str(ledger_db), discovery_db=str(disc_db),
                              eligible_sources={SOURCE_TEST})


def _cohort_rows(score, hits, misses, **kw):
    rows = []
    for _ in range(hits):
        rows.append({"score": score, "hit": 1, **kw})
    for _ in range(misses):
        rows.append({"score": score, "hit": 0, **kw})
    return rows


# ---------------------------------------------------------------- empty/insufficient

def test_empty_dataset_is_insufficient_with_no_diagnostics(tmp_path):
    report = _seed(tmp_path, []).run()
    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.joined_pairs == 0
    assert report.metrics.base_rate is None
    assert report.metrics.brier_score is None
    assert report.metrics.ece is None
    assert report.metrics.spearman_score_vs_hit is None
    assert report.metrics.guards_met is False
    assert report.confidence_segments == []
    assert report.chain_segments == []
    assert report.extreme_records == []


def test_tiny_cohort_reports_metrics_with_sample_size_warning(tmp_path):
    """True arithmetic on 3 pairs + an explicit warning — never a claim."""
    report = _seed(tmp_path, [{"score": 90, "hit": 1}, {"score": 10, "hit": 0},
                              {"score": 50, "hit": 1}]).run()
    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.metrics.joined_pairs == 3
    assert report.metrics.base_rate == pytest.approx(2 / 3)
    assert report.metrics.brier_score is not None
    assert report.metrics.guards_met is False
    assert any("SAMPLE_SIZE_WARNING" in f for f in report.findings)


def test_predictions_without_labels_never_produce_rates(tmp_path):
    """No outcome rows -> 0 pairs -> no invented statistics of any kind."""
    harness = _seed(tmp_path, [{"score": 90, "hit": 1}])
    conn = sqlite3.connect(harness.discovery_db)
    conn.execute("DELETE FROM outcome_label")
    conn.commit(); conn.close()

    report = harness.run()
    assert report.joined_pairs == 0
    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.metrics.brier_score is None
    assert report.metrics.spearman_score_vs_hit is None
    assert all(b.n == 0 for b in report.bands)


# ---------------------------------------------------------------- valid cohort

def test_valid_cohort_band_aggregation_with_continuous_outcomes(tmp_path):
    rows = []
    # top band: 150 hits (max_fav 1.0) + 100 misses (max_fav 0.1)
    rows += [{"score": 90, "hit": 1, "max_favorable": 1.0}] * 150
    rows += [{"score": 90, "hit": 0, "max_favorable": 0.1}] * 100
    # bottom band: 30 hits + 220 misses
    rows += [{"score": 10, "hit": 1, "max_favorable": 0.6}] * 30
    rows += [{"score": 10, "hit": 0, "max_favorable": 0.0}] * 220
    report = _seed(tmp_path, rows).run()

    assert report.verdict == "DESCRIPTIVE_OK"
    top = next(b for b in report.bands if b.band == "80-100")
    bottom = next(b for b in report.bands if b.band == "0-20")
    assert top.rate == pytest.approx(0.60, abs=0.01)
    assert bottom.rate == pytest.approx(0.12, abs=0.01)
    # continuous outcomes
    assert top.mean_score == pytest.approx(90.0)
    assert top.mean_max_favorable == pytest.approx((150 * 1.0 + 100 * 0.1) / 250)
    # sorted: 100 x 0.1 (indices 0-99), 150 x 1.0 (indices 100-249);
    # median of 250 = avg of indices 124,125 = 1.0
    assert top.median_max_favorable == pytest.approx(1.0)
    assert bottom.mean_max_favorable == pytest.approx((30 * 0.6) / 250)
    assert report.monotonicity == "MONOTONIC_INCREASING"
    assert report.metrics.guards_met is True
    assert report.metrics.ece is not None


def test_brier_and_spearman_on_hand_computable_cohort(tmp_path):
    rows = [{"score": 100, "hit": 1, "max_favorable": 2.0},
            {"score": 0, "hit": 0, "max_favorable": -0.5}]
    report = _seed(tmp_path, rows).run()

    # brier on normalized scores: (1-1)^2 + (0-0)^2 = 0
    assert report.metrics.brier_score == pytest.approx(0.0)
    # base-rate brier: predict 0.5 for both -> ((0.5-1)^2 + (0.5-0)^2)/2 = 0.25
    assert report.metrics.brier_base_rate == pytest.approx(0.25)
    assert report.metrics.brier_resolution == pytest.approx(0.25)
    # perfect ranking: higher score => hit and higher max_favorable
    assert report.metrics.spearman_score_vs_hit == pytest.approx(1.0)
    assert report.metrics.spearman_score_vs_maxfav == pytest.approx(1.0)


def test_spearman_handles_ties_and_constant_series():
    assert _spearman([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
    assert _spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert _spearman([5, 5, 5], [1, 2, 3]) is None       # constant xs
    assert _spearman([1, 2], [1, 1]) is None              # constant ys
    assert _spearman([1], [1]) is None                    # too few points
    # tie in ys: ranks [1,2,3] vs [2.5,2.5,1] -> rho = -sqrt(3)/2
    assert _spearman([1, 2, 3], [3, 3, 1]) == pytest.approx(-0.8660254)


# ---------------------------------------------------------------- confidence buckets

def test_confidence_segments_ordered(tmp_path):
    rows = []
    rows += _cohort_rows(90, 200, 50, confidence="HIGH")
    rows += _cohort_rows(60, 125, 125, confidence="MED")
    rows += _cohort_rows(20, 25, 225, confidence="LOW")
    report = _seed(tmp_path, rows).run()

    by = {s.value: s for s in report.confidence_segments}
    assert by["HIGH"].rate == pytest.approx(200 / 250)
    assert by["MED"].rate == pytest.approx(0.5)
    assert by["LOW"].rate == pytest.approx(25 / 250)
    assert all(s.verdict == "DESCRIPTIVE_OK" for s in report.confidence_segments)
    assert report.confidence_ordering == "CONFIDENCE_ORDERED"


def test_confidence_segments_inverted_are_flagged(tmp_path):
    rows = []
    rows += _cohort_rows(90, 25, 225, confidence="HIGH")   # HIGH does WORSE
    rows += _cohort_rows(20, 200, 50, confidence="LOW")
    report = _seed(tmp_path, rows).run()

    assert report.confidence_ordering == "CONFIDENCE_INVERTED"
    assert any("CONFIDENCE_INVERTED" in f for f in report.findings)


def test_unknown_confidence_level_is_bucketed_never_merged(tmp_path):
    rows = []
    rows += _cohort_rows(90, 200, 50, confidence="HIGH")
    rows += _cohort_rows(90, 20, 30, confidence="BOGUS")   # not a real level
    rows += _cohort_rows(90, 20, 30, confidence="")
    report = _seed(tmp_path, rows).run()

    values = {s.value for s in report.confidence_segments}
    assert "BOGUS" not in values and "" not in values
    assert "UNKNOWN" in values
    unknown = next(s for s in report.confidence_segments if s.value == "UNKNOWN")
    assert unknown.n == 100  # 50 BOGUS + 50 empty
    high = next(s for s in report.confidence_segments if s.value == "HIGH")
    assert high.n == 250  # UNKNOWN rows never merged into HIGH


# ---------------------------------------------------------------- chain segments

def test_chain_segmentation(tmp_path):
    rows = []
    rows += _cohort_rows(90, 200, 50, chain="solana")
    rows += _cohort_rows(90, 30, 220, chain="ethereum")
    rows += _cohort_rows(90, 20, 30, chain="")           # missing -> UNKNOWN
    report = _seed(tmp_path, rows).run()

    by = {s.value: s for s in report.chain_segments}
    assert by["solana"].rate == pytest.approx(0.8)
    assert by["ethereum"].rate == pytest.approx(30 / 250)
    assert by["UNKNOWN"].n == 50


# ---------------------------------------------------------------- missing fields

def test_missing_continuous_fields_stay_unknown(tmp_path):
    # two score values so rank diagnostics are computable; NO max_favorable /
    # max_adverse anywhere in the cohort
    rows = _cohort_rows(90, 210, 40) + _cohort_rows(10, 0, 200)
    report = _seed(tmp_path, rows).run()

    top = next(b for b in report.bands if b.band == "80-100")
    assert top.mean_max_favorable is None
    assert top.median_max_favorable is None
    assert top.mean_max_adverse is None
    # diagnostics that don't need the missing field still exist
    assert report.metrics.spearman_score_vs_hit is not None
    assert report.metrics.spearman_score_vs_maxfav is None
    assert report.metrics.brier_score is not None


# ---------------------------------------------------------------- versions & horizons

def test_multiple_engine_versions_flagged_metrics_still_descriptive(tmp_path):
    rows = _cohort_rows(90, 210, 40, engine_version="AHOS-SCORE-v2")
    rows += _cohort_rows(10, 30, 220)   # default v1
    report = _seed(tmp_path, rows).run()

    assert len(report.engine_versions) >= 2
    assert any("MIXED_ENGINE_VERSIONS" in f for f in report.findings)
    # rates still computed, but the mixing finding forbids reading them as one curve
    assert report.verdict == "DESCRIPTIVE_OK"


def test_multiple_horizons_run_independently(tmp_path):
    rows = []
    rows += _cohort_rows(90, 210, 40)   # 250 rows, all written as 15m below
    rows += _cohort_rows(10, 30, 220)
    harness = _seed(tmp_path, rows, horizon="15m")
    # add a DIFFERENT 24h label set for the same tokens (independent cohort):
    # at 24h the score-90 tokens mostly FAIL (25/250 hits) while the score-10
    # tokens mostly SUCCEED (225/250 hits) — an inversion that only exists at
    # 24h and still clears the per-band guard (positives >= 20).
    now = time.time()
    conn = sqlite3.connect(harness.discovery_db)
    for i in range(500):
        hit_24h = 1 if (i < 25 or 250 <= i < 475) else 0
        conn.execute(
            "INSERT INTO outcome_label(token_id,horizon,event_class,hit,resolved_ts) "
            "VALUES (?,?,?,?,?)",
            (f"token{i:05d}", "24h", "+50%", hit_24h, now))
    conn.commit(); conn.close()

    reports = harness.run_many(["15m", "24h"])
    assert len(reports) == 2
    r15, r24 = reports
    assert r15.horizon == "15m" and r24.horizon == "24h"
    assert r15.joined_pairs == 500
    assert r24.joined_pairs == 500
    # independent band rates per horizon
    top15 = next(b for b in r15.bands if b.band == "80-100")
    bottom15 = next(b for b in r15.bands if b.band == "0-20")
    top24 = next(b for b in r24.bands if b.band == "80-100")
    bottom24 = next(b for b in r24.bands if b.band == "0-20")
    assert top15.rate == pytest.approx(210 / 250)
    assert bottom15.rate == pytest.approx(30 / 250)
    assert top24.rate == pytest.approx(25 / 250)
    assert bottom24.rate == pytest.approx(225 / 250)
    assert r15.monotonicity == "MONOTONIC_INCREASING"
    assert r24.monotonicity == "NOT_MONOTONIC"


# ---------------------------------------------------------------- determinism

def test_deterministic_output_across_runs(tmp_path):
    rows = [{"score": 90, "hit": 1, "confidence": "HIGH", "max_favorable": 1.0}
            for _ in range(150)] + \
           [{"score": 90, "hit": 0, "confidence": "HIGH", "max_favorable": 0.1}
            for _ in range(100)] + \
           [{"score": 10, "hit": 1, "confidence": "LOW", "max_favorable": 0.6}
            for _ in range(30)] + \
           [{"score": 10, "hit": 0, "confidence": "LOW", "max_favorable": 0.0}
            for _ in range(220)]
    now = 1755000000.0
    r1 = _seed(tmp_path / "a", rows, now=now).run(now=now)
    r2 = _seed(tmp_path / "b", rows, now=now).run(now=now)

    assert r1.dataset_fingerprint == r2.dataset_fingerprint
    assert r1.metrics.as_dict() == r2.metrics.as_dict()
    assert [b.as_dict() for b in r1.bands] == [b.as_dict() for b in r2.bands]
    assert [s.as_dict() for s in r1.confidence_segments] == \
           [s.as_dict() for s in r2.confidence_segments]
    assert r1.extreme_records == r2.extreme_records


# ---------------------------------------------------------------- provenance surface

def test_extreme_records_are_deterministic_and_evidence_linked(tmp_path):
    rows = _cohort_rows(95, 5, 0, max_favorable=2.0, evidence_sha="c" * 64)
    rows += _cohort_rows(5, 0, 5, max_favorable=-0.9, evidence_sha="")
    report = _seed(tmp_path, rows).run()

    recs = report.extreme_records
    assert len(recs) == 6
    # lowest-scored records first, highest-scored last (deterministic order)
    assert all(r["opportunity_score"] == 5.0 for r in recs[:3])
    assert all(r["opportunity_score"] == 95.0 for r in recs[3:])
    assert recs[0]["evidence_sha256"] is None  # absent evidence stays absent
    assert recs[3]["evidence_sha256"] == "c" * 16
    assert recs[0]["hit"] == 0 and recs[3]["hit"] == 1


def test_feature_coverage_census(tmp_path):
    rows = _cohort_rows(90, 210, 40, known_fields=7, unknown_fields=2,
                        evidence_sha="d" * 64)
    report = _seed(tmp_path, rows).run()

    fc = report.feature_coverage
    assert fc["mean_known_fields"] == pytest.approx(7.0)
    assert fc["mean_unknown_fields"] == pytest.approx(2.0)
    assert fc["records_with_evidence_sha"] == 250
    assert fc["total_records"] == 250


def test_dimension_availability_is_honest(tmp_path):
    report = _seed(tmp_path, [{"score": 90, "hit": 1}]).run()
    da = report.dimension_availability
    assert da["score"].startswith("persisted")
    assert da["confidence_level"].startswith("persisted")
    assert da["chain"].startswith("persisted")
    assert da["provider"].startswith("persisted")  # now stamped at scoring time
    assert "NOT_PERSISTED_AT_PREDICTION_TIME" in da["market_regime"]
    assert "NOT_PERSISTED_AT_PREDICTION_TIME" in da["opportunity_type"]


def test_schema_bumped_to_v4_with_guards_intact(tmp_path):
    report = _seed(tmp_path, [{"score": 90, "hit": 1}]).run()
    d = report.as_dict()
    assert d["schema"] == "ahos.calibration_report.v4"
    assert d["guards"]["min_n_per_band"] == MIN_N_PER_BAND
    assert d["guards"]["min_positives"] == MIN_POSITIVES
    assert "no_peeking" in d["guards"]
    assert "metrics" in d and "dimension_availability" in d
    assert "provider_segments" in d
    # outcome provenance must be stated (frozen labeler identity, not a guess)
    assert d["outcome_provenance"]["labeler"].startswith("discovery/outcomes.py")


# ---------------------------------------------------------------- provider segments

def test_provider_segmentation(tmp_path):
    rows = []
    rows += _cohort_rows(90, 200, 50, provider="dexscreener")
    rows += _cohort_rows(90, 30, 220, provider="geckoterminal")
    rows += _cohort_rows(90, 20, 30)                     # no provider -> UNKNOWN
    report = _seed(tmp_path, rows).run()

    by = {s.value: s for s in report.provider_segments}
    assert by["dexscreener"].rate == pytest.approx(0.8)
    assert by["geckoterminal"].rate == pytest.approx(30 / 250)
    assert by["UNKNOWN"].n == 50
    assert by["dexscreener"].verdict == "DESCRIPTIVE_OK"


def test_provider_segments_follow_the_same_guards(tmp_path):
    rows = _cohort_rows(90, 5, 5, provider="dexscreener")  # n=10 < 200
    report = _seed(tmp_path, rows).run()
    seg = next(s for s in report.provider_segments if s.value == "dexscreener")
    assert seg.verdict == "INSUFFICIENT_DATA"
    assert "n<200" in (seg.reason or "")


def test_constants_stay_conservative():
    assert MIN_N_PER_BAND >= 200 and MIN_POSITIVES >= 20
    assert CONFIDENCE_LEVELS == ("HIGH", "MED", "LOW")


# ---------------------------------------------------------------- CLI surface

def test_cli_writes_artifact_and_reports_insufficient_data(tmp_path, monkeypatch):
    """The operator-facing command must work on an empty laptop store and
    produce an honest INSUFFICIENT_DATA artifact (exit 0)."""
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path / "empty_data"))
    from scripts import calibration_report as cr

    out = tmp_path / "cal.json"
    rc = cr.main(["--out", str(out), "--horizon", "24h"])
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "ahos.calibration_report.v4"
    assert payload["calibration_status"] == "INSUFFICIENT_DATA"
    assert payload["number_of_eligible_pairs"] == 0
    assert "metrics" in payload and payload["metrics"]["brier_score"] is None
    assert "dimension_availability" in payload


def test_cli_all_horizons_writes_combined_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path / "empty_data"))
    from scripts import calibration_report as cr

    out = tmp_path / "cal_all.json"
    rc = cr.main(["--all-horizons", "--out", str(out)])
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "ahos.calibration_multi.v1"
    horizons = [r["horizon"] for r in payload["horizons"]]
    assert horizons == ["15m", "1h", "4h", "12h", "24h", "72h", "7d"]
    assert all(r["calibration_status"] == "INSUFFICIENT_DATA"
               for r in payload["horizons"])
