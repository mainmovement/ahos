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


def _seed(tmp_path, rows, horizon="24h", event_class="+50%", now=None,
          price_series=None):
    """rows: list of dicts with at least score/hit; optional confidence, chain,
    max_favorable, max_adverse, known_fields, unknown_fields, evidence_sha,
    engine_version, resolved_offset, provider.

    price_series: {row_index: [pre-prediction prices]} — written into a
    discovery_observations table so regime segmentation can be exercised."""
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

    if price_series:
        dconn.execute(
            """CREATE TABLE discovery_observations (
                 obs_id TEXT PRIMARY KEY, token_id TEXT, pair_id TEXT,
                 provider TEXT, capability TEXT, source_ts REAL,
                 retrieved_ts REAL, price_usd REAL, liquidity_usd REAL,
                 fdv REAL, market_cap REAL, volume_5m REAL, volume_1h REAL,
                 volume_6h REAL, volume_24h REAL, txns_5m_buys INTEGER,
                 txns_5m_sells INTEGER, txns_1h_buys INTEGER,
                 txns_1h_sells INTEGER, txns_24h_buys INTEGER,
                 txns_24h_sells INTEGER, price_change_5m REAL,
                 price_change_1h REAL, price_change_6h REAL,
                 price_change_24h REAL, pair_age_minutes REAL,
                 boost_amount REAL, quality_flags TEXT, error_state TEXT,
                 raw_ref TEXT)""")
        for idx, prices in price_series.items():
            tid = f"token{idx:05d}"
            for j, px in enumerate(prices):
                dconn.execute(
                    """INSERT INTO discovery_observations(
                         obs_id, token_id, retrieved_ts, price_usd, error_state)
                       VALUES (?,?,?,?,NULL)""",
                    (f"obs_{idx}_{j}", tid, t0 - 7200 + j * 300.0, float(px)))

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
    assert "computed post-hoc" in da["market_regime"]
    assert "NOT_PERSISTED_AT_PREDICTION_TIME" in da["opportunity_type"]


def test_schema_bumped_to_v8_with_guards_intact(tmp_path):
    report = _seed(tmp_path, [{"score": 90, "hit": 1}]).run()
    d = report.as_dict()
    assert d["schema"] == "ahos.calibration_report.v8"
    assert d["guards"]["min_n_per_band"] == MIN_N_PER_BAND
    assert d["guards"]["min_positives"] == MIN_POSITIVES
    assert "no_peeking" in d["guards"]
    assert "metrics" in d and "dimension_availability" in d
    assert "provider_segments" in d and "regime_segments" in d
    assert "score_drift" in d and "temporal_buckets" in d
    assert "error_analysis" in d
    # outcome provenance must be stated (frozen labeler identity, not a guess)
    assert d["outcome_provenance"]["labeler"].startswith("discovery/outcomes.py")


def test_error_analysis_matrix_and_examples(tmp_path):
    """False-positive/false-negative analysis at the pre-declared 50-point
    threshold: TP/FP/TN/FN counts, rates, precision/recall, and concrete
    highest-FP / lowest-TP examples."""
    rows = [{"score": 90, "hit": 1, "evidence_sha": "a" * 64} for _ in range(150)]
    rows += [{"score": 90, "hit": 0, "evidence_sha": "b" * 64} for _ in range(30)]
    rows += [{"score": 10, "hit": 0, "evidence_sha": "c" * 64} for _ in range(60)]
    rows += [{"score": 10, "hit": 1, "evidence_sha": "d" * 64} for _ in range(10)]
    # a HIGH-score TP (score 70) so the "lowest TP" is a distinct example;
    # score-10 hits are FN (below threshold), not TP.
    rows += [{"score": 70, "hit": 1, "evidence_sha": "e" * 64} for _ in range(5)]
    report = _seed(tmp_path, rows).run()

    ea = report.error_analysis
    assert ea["threshold"] == 50.0
    assert ea["tp"] == 155 and ea["fp"] == 30
    assert ea["tn"] == 60 and ea["fn"] == 10
    assert ea["false_positive_rate"] == pytest.approx(30 / 90, abs=1e-4)
    assert ea["false_negative_rate"] == pytest.approx(10 / 165, abs=1e-4)
    assert ea["precision"] == pytest.approx(155 / 185, abs=1e-4)
    assert ea["recall"] == pytest.approx(155 / 165, abs=1e-4)
    # examples carry evidence provenance
    assert ea["highest_scored_false_positive"]["evidence_sha"] == "b" * 16
    assert ea["lowest_scored_true_positive"]["evidence_sha"] == "e" * 16


def test_error_analysis_empty_and_sample_warning(tmp_path):
    empty = _seed(tmp_path / "e", []).run()
    assert empty.error_analysis["n"] == 0
    assert empty.error_analysis["guards_met"] is False

    tiny = _seed(tmp_path / "t", [{"score": 90, "hit": 1}]).run()
    assert tiny.error_analysis["tp"] == 1
    assert tiny.error_analysis["guards_met"] is False
    assert any("ERROR_ANALYSIS_SAMPLE_WARNING" in f for f in tiny.findings)


def _mk_pair(score, hit, scored_ts, score_id):
    return {"score_id": score_id, "opportunity_score": float(score),
            "scored_ts": float(scored_ts), "hit": hit}


def test_temporal_buckets_split_by_scored_time(tmp_path):
    """Longitudinal view: two well-separated weeks produce two buckets with
    independent rates; a young bucket reports INSUFFICIENT_DATA."""
    from architecture.learning.calibration import CalibrationHarness

    week1 = [_mk_pair(90, 1, 1000.0 + i, f"w1_{i}") for i in range(210)]
    week1 += [_mk_pair(10, 0, 1000.0 + 210 + i, f"w1b_{i}") for i in range(40)]
    week2 = [_mk_pair(90, 0, 1000.0 + 8 * 86400 + i, f"w2_{i}") for i in range(210)]
    week2 += [_mk_pair(10, 1, 1000.0 + 8 * 86400 + 210 + i, f"w2b_{i}") for i in range(40)]

    buckets = CalibrationHarness._temporal_buckets(week1 + week2)
    assert len(buckets) == 2
    assert buckets[0]["verdict"] == "DESCRIPTIVE_OK"
    assert buckets[1]["verdict"] == "DESCRIPTIVE_OK"
    assert buckets[0]["rate"] == pytest.approx(210 / 250)
    assert buckets[1]["rate"] == pytest.approx(40 / 250)
    assert buckets[0]["bucket_start_utc"] != buckets[1]["bucket_start_utc"]


def test_temporal_bucket_guards_small_buckets(tmp_path):
    from architecture.learning.calibration import CalibrationHarness
    small = [_mk_pair(90, 1, 1000.0 + i, f"s_{i}") for i in range(5)]
    buckets = CalibrationHarness._temporal_buckets(small)
    assert buckets[0]["verdict"] == "INSUFFICIENT_DATA"
    assert "pre-registered guards" in (buckets[0]["reason"] or "")


def test_temporal_buckets_detect_degradation(tmp_path):
    """A falling rate across comparable buckets => TEMPORAL_DEGRADATION is
    surfaced by run()'s finding (the finding is appended in run, the bucket
    arithmetic is pure)."""
    from architecture.learning.calibration import CalibrationHarness

    week1 = [_mk_pair(90, 1, 1000.0 + i, f"w1_{i}") for i in range(210)]
    week1 += [_mk_pair(10, 0, 1000.0 + 210 + i, f"w1b_{i}") for i in range(40)]
    week2 = [_mk_pair(90, 0, 1000.0 + 8 * 86400 + i, f"w2_{i}") for i in range(210)]
    week2 += [_mk_pair(10, 1, 1000.0 + 8 * 86400 + 210 + i, f"w2b_{i}") for i in range(40)]

    buckets = CalibrationHarness._temporal_buckets(week1 + week2)
    ok = [b for b in buckets if b["verdict"] == "DESCRIPTIVE_OK"]
    assert len(ok) == 2
    assert ok[0]["rate"] > ok[1]["rate"]  # degradation detectable from buckets


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


# ---------------------------------------------------------------- regime segments

def _noisy_trend(up: bool, n: int = 30) -> list[float]:
    """Deterministic (seeded) trending series with noise, so all three
    variance clusters are non-empty for the classifier."""
    import numpy as np
    rng = np.random.RandomState(42 if up else 7)
    drift = 0.03 if up else -0.03
    p = 1.0
    out = []
    for _ in range(n):
        p *= 1.0 + drift + float(rng.normal(0.0, 0.008))
        out.append(max(p, 1e-9))
    return out


def test_token_price_regime_helper():
    from architecture.learning.calibration import (
        MIN_REGIME_OBS,
        _token_price_regime,
    )

    # fewer than the pre-registered minimum -> UNKNOWN, never a default regime
    assert _token_price_regime([]) is None
    assert _token_price_regime([1.0, 2.0, 3.0]) is None

    # valid label set (the classifier's own); the harness does not re-derive
    from architecture.intel.regimes import MarketRegimeClassifier
    valid = set(MarketRegimeClassifier.REGIME_LABELS.values())

    bull = _noisy_trend(up=True)
    bear = _noisy_trend(up=False)
    assert len(bull) >= MIN_REGIME_OBS and len(bear) >= MIN_REGIME_OBS
    assert _token_price_regime(bull) in valid
    assert _token_price_regime(bear) in valid
    # deterministic across calls (GMM quantile init, no randomness)
    assert _token_price_regime(bull) == _token_price_regime(bull)
    assert _token_price_regime(bear) == _token_price_regime(bear)


def test_regime_segmentation_from_pre_prediction_observations(tmp_path):
    """Regime is computed from PRE-prediction prices only (no peeking) and
    tokens without enough observations land in UNKNOWN. The expected label is
    taken from the helper itself — the harness must not assert the weak
    classifier's label semantics, only that segmentation is coherent."""
    from architecture.learning.calibration import _token_price_regime

    rows = []
    rows += _cohort_rows(90, 200, 50, provider="dexscreener")   # token00000-249
    rows += _cohort_rows(10, 30, 220, provider="dexscreener")   # token00250-499
    series = {i: _noisy_trend(up=True) for i in range(250)}     # one regime
    series.update({i: [1.0, 1.1, 1.2] for i in range(250, 500)})  # sparse
    expected = _token_price_regime(series[0])
    assert expected is not None

    report = _seed(tmp_path, rows, price_series=series).run()
    by = {s.value: s for s in report.regime_segments}
    assert by[expected].n == 250
    assert by[expected].rate == pytest.approx(200 / 250)
    assert by[expected].verdict == "DESCRIPTIVE_OK"
    # sparse tokens land in UNKNOWN (regime not computable), but their
    # outcomes are still real — the bucket carries the honest hit rate
    assert by["UNKNOWN"].n == 250
    assert by["UNKNOWN"].rate == pytest.approx(30 / 250)


def test_regime_memoization_preserves_output_parity():
    """W36 phase 7: the lru_cache wrapper must never change the label for an
    identical series — same input, same output, whether cached or not."""
    from architecture.learning.calibration import (
        _token_price_regime,
        _token_price_regime_cached,
    )

    series = _noisy_trend(up=True)
    # cached core gets the cleaned tuple; wrapper passes the same cleaning
    cleaned = tuple(float(p) for p in series if p is not None and float(p) > 0)
    assert _token_price_regime(series) == _token_price_regime_cached(cleaned)
    # repeated calls (cache hits) return the identical label
    assert _token_price_regime(series) == _token_price_regime(series)
    # a DIFFERENT series still gets its own (potentially different) label
    other = _noisy_trend(up=False)
    other_label = _token_price_regime(other)
    assert other_label in ("BULL_TREND", "BEAR_VOLATILE", "NEUTRAL_CHOP")


def test_batched_regime_query_matches_per_token_semantics(tmp_path):
    """The batched regime query (one connection, one IN-query) must produce
    byte-identical labels to the per-token reference, including the no-peeking
    filter (each token's prices cut at ITS OWN scored_ts)."""
    from architecture.learning.calibration import _token_price_regime

    rows = []
    rows += _cohort_rows(90, 210, 40)                     # token00000-249
    rows += _cohort_rows(10, 30, 220)                     # token00250-499
    series = {i: _noisy_trend(up=True) for i in range(250)}
    series.update({i: _noisy_trend(up=False) for i in range(250, 500)})
    harness = _seed(tmp_path, rows, price_series=series)

    # scored_ts = t0 + i (seed convention), so a price row at t0+250 falls
    # BEFORE the scored_ts of tokens 250-499 (included) and AFTER that of
    # tokens 0-249 (excluded) — exercising the per-token no-peeking cutoff
    # inside the batched query. Recompute t0 with the same convention.
    t0 = time.time() - 86400
    conn = sqlite3.connect(harness.discovery_db)
    for i in range(500):
        conn.execute(
            """INSERT INTO discovery_observations(obs_id, token_id, retrieved_ts,
                 price_usd, error_state) VALUES (?,?,?,?,NULL)""",
            (f"boundary_{i}", f"token{i:05d}", t0 + 250, 3.33))
    conn.commit(); conn.close()
    pairs = harness._load_pairs("24h", "+50%")

    # per-token reference (the pre-batching implementation's semantics)
    def _reference(pairs):
        out = {}
        for p in pairs:
            tid = str(p["token_id"])
            if tid in out:
                continue
            conn2 = harness._connect()
            rows2 = conn2.execute(
                """SELECT price_usd FROM disc.discovery_observations
                    WHERE token_id = ? AND retrieved_ts <= ?
                      AND price_usd IS NOT NULL AND price_usd > 0
                      AND error_state IS NULL ORDER BY retrieved_ts""",
                (tid, float(p["scored_ts"]))).fetchall()
            conn2.close()
            label = _token_price_regime([float(r[0]) for r in rows2])
            out[tid] = label if label else "UNKNOWN"
        return out

    ref = _reference(pairs)
    batched = harness._token_regimes(pairs)
    assert ref == batched, "batched regime query diverged from per-token semantics"


def test_regime_never_uses_post_prediction_observations(tmp_path):
    """Observations after scored_ts must not influence the regime label."""
    from architecture.learning.calibration import _token_price_regime

    rows = _cohort_rows(90, 210, 40)
    series = {i: _noisy_trend(up=True) for i in range(250)}
    expected = _token_price_regime(series[0])
    harness = _seed(tmp_path, rows, price_series=series)

    # inject crashing observations that occur AFTER every prediction — they
    # describe the outcome window, not the regime the scorer operated in
    conn = sqlite3.connect(harness.discovery_db)
    for i in range(5):
        conn.execute(
            """INSERT INTO discovery_observations(obs_id, token_id, retrieved_ts,
                 price_usd, error_state) VALUES (?,?,?,?,NULL)""",
            (f"post_crash_{i}", f"token{i:05d}", 1e18, 0.001))
    conn.commit(); conn.close()

    report = harness.run()
    by = {s.value: s for s in report.regime_segments}
    # the pre-prediction trend still classifies the same regime; crash rows
    # (retrieved_ts after every scored_ts) were ignored by the no-peeking filter
    assert by[expected].n == 250


def test_constants_stay_conservative():
    assert MIN_N_PER_BAND >= 200 and MIN_POSITIVES >= 20
    assert CONFIDENCE_LEVELS == ("HIGH", "MED", "LOW")


# ---------------------------------------------------------------- score drift

def test_score_drift_tiny_cohort_is_insufficient(tmp_path):
    rows = [{"score": 60, "hit": 1} for _ in range(5)]
    report = _seed(tmp_path, rows).run()
    assert report.score_drift["verdict"] == "INSUFFICIENT_DATA"
    assert report.score_drift["drift_detected"] is None


def test_score_drift_stable_series_no_drift(tmp_path):
    rows = [{"score": 50.0, "hit": 1 if i % 3 == 0 else 0}
            for i in range(120)]
    report = _seed(tmp_path, rows).run()
    assert report.score_drift["samples"] == 120
    assert report.score_drift["verdict"] == "NO_DRIFT_DETECTED"
    assert report.score_drift["drift_detected"] is False


def test_score_drift_step_change_is_detected_and_flagged(tmp_path):
    # first 60 scores low, then a step to high — a real distribution shift
    rows = [{"score": 20.0, "hit": 0} for _ in range(60)]
    rows += [{"score": 80.0, "hit": 1} for _ in range(60)]
    report = _seed(tmp_path, rows).run()
    assert report.score_drift["verdict"] == "DRIFT_DETECTED"
    assert report.score_drift["drift_detected"] is True
    assert any("SCORE_DRIFT" in f for f in report.findings)


def test_score_drift_is_deterministic(tmp_path):
    rows = [{"score": 50.0, "hit": 1 if i % 3 == 0 else 0}
            for i in range(120)]
    now = 1755000000.0
    r1 = _seed(tmp_path / "a", rows, now=now).run(now=now)
    r2 = _seed(tmp_path / "b", rows, now=now).run(now=now)
    assert r1.score_drift == r2.score_drift


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
    assert payload["schema"] == "ahos.calibration_report.v8"
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
