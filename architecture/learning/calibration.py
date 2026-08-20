#!/usr/bin/env python3
"""AHOS Calibration Harness — does a high score actually mean anything?

WHAT THIS ANSWERS
-----------------
Given predictions recorded by `score_ledger` and outcome labels produced by the
frozen Lane-A labeler (`discovery/outcomes.py`), this module reports:

    "Of the tokens AHOS scored 80-100, what fraction actually hit +50% at 24h,
     and how does that compare to the tokens it scored 0-20?"

That is the only question that can convert "explainable score" into "measurably
useful score", and until predictions were persisted it was not computable at
all.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does NOT tune anything. No weight, threshold, or band is adjusted here, and
nothing in this module writes to the scoring path. Measuring a thing and then
quietly editing it to look better is how a calibration report becomes a lie.
Weight revision is a separate, human-reviewed governance act (the existing
`improvement_proposal_v1` flow) that must cite a report produced here.

HONESTY LAWS
------------
1. PRE-DECLARED BANDS. Score bands and the statistical guards are module-level
   constants, fixed before any data is seen. They are not parameters a caller
   can widen until a result looks significant.

2. NO-PEEKING JOIN. A prediction may only be graded against an outcome whose
   horizon closed AFTER the prediction was made. A score computed at time T is
   never matched to a label describing what already happened before T. This is
   enforced in the join, not left to the caller's discipline.

3. INSUFFICIENT_DATA IS THE DEFAULT. Sample guards are inherited from the
   existing research module (`research/baseline_stats.py`) so this harness
   cannot be more permissive than the project's own pre-registered bar. A young
   cohort returns INSUFFICIENT_DATA, which is the correct, expected, and useful
   answer during Month 1-2 -- not a failure of the tool.

4. MIXED ENGINE VERSIONS ARE REPORTED, NEVER AVERAGED AWAY. Pooling scores from
   different scoring logic produces a number that describes no system that ever
   existed, so the report surfaces the version census and flags mixing.
"""
from __future__ import annotations

import hashlib
import math
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from config.paths import get_discovery_db_path, get_local_db_path
from .score_ledger import CALIBRATION_ELIGIBLE_SOURCES


def _utc(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

# Pre-declared score bands. Fixed before observing any data.
SCORE_BANDS: tuple[tuple[str, float, float], ...] = (
    ("0-20", 0.0, 20.0),
    ("20-40", 20.0, 40.0),
    ("40-60", 40.0, 60.0),
    ("60-80", 60.0, 80.0),
    ("80-100", 80.0, 100.001),   # upper bound inclusive of a perfect 100
)

# Inherited from research/baseline_stats.py -- this harness must never be more
# permissive than the project's own pre-registered statistical bar.
MIN_N_PER_BAND = 200
MIN_POSITIVES = 20

DEFAULT_HORIZON = "24h"
DEFAULT_EVENT_CLASS = "+50%"

# Pre-declared confidence levels (from the scoring contract). Anything not in
# this set is bucketed UNKNOWN and never merged into a real level.
CONFIDENCE_LEVELS: tuple[str, ...] = ("HIGH", "MED", "LOW")

# Minimum pre-prediction observations required to classify a token's price
# regime — matches the MarketRegimeClassifier's own fit minimum. Fewer
# observations => regime stays UNKNOWN (never a fabricated default regime).
MIN_REGIME_OBS = 10


def _token_price_regime(prices: list[float]) -> str | None:
    """Post-hoc token price regime from PRE-prediction observations.

    Uses the existing architecture/intel/regimes.py classifier (its first
    production consumer). Deterministic: quantile-init GMM, no randomness.
    Returns None (-> UNKNOWN bucket) when fewer than MIN_REGIME_OBS prices are
    available — a regime label on a sparse series would be fabrication.
    """
    clean = [float(p) for p in prices if p is not None and float(p) > 0]
    if len(clean) < MIN_REGIME_OBS:
        return None
    returns = [clean[i] / clean[i - 1] - 1.0 for i in range(1, len(clean))]
    if len(returns) < MIN_REGIME_OBS - 1:
        return None
    try:
        import numpy as np
        from ..intel.regimes import MarketRegimeClassifier
        clf = MarketRegimeClassifier()
        clf.fit_returns(np.asarray(returns, dtype=np.float64))
        verdict = clf.predict_regime_probabilities(np.asarray(returns, dtype=np.float64))
        label = str(verdict.get("active_regime") or "")
        return label if label in MarketRegimeClassifier.REGIME_LABELS.values() else None
    except Exception:
        return None


def _mean(values: Iterable[float]) -> float | None:
    vals = [float(v) for v in values]
    return sum(vals) / len(vals) if vals else None


def _median(values: Iterable[float]) -> float | None:
    vals = sorted(float(v) for v in values)
    n = len(vals)
    if n == 0:
        return None
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2.0


def _rank_series(values: list[float]) -> list[float]:
    """Average ranks (ties share the mean rank) — standard Spearman input."""
    indexed = sorted((v, i) for i, v in enumerate(values))
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][0] == indexed[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k][1]] = avg
        i = j + 1
    return ranks


def _spearman(xs: Iterable[float], ys: Iterable[float]) -> float | None:
    """Spearman rank correlation. None on <2 points or a constant series."""
    x = [float(v) for v in xs]
    y = [float(v) for v in ys]
    if len(x) != len(y) or len(x) < 2:
        return None
    rx, ry = _rank_series(x), _rank_series(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def _brier(preds: Iterable[float], outcomes: Iterable[float]) -> float | None:
    """Mean squared error between predicted probabilities and 0/1 outcomes.

    AHOS scores are OPPORTUNITY scores, not probabilities; this is a
    diagnostic on the normalized score (score/100), never a claim that the
    score is calibrated probability.
    """
    p = [float(v) for v in preds]
    y = [float(v) for v in outcomes]
    if not p or len(p) != len(y):
        return None
    return sum((a - b) ** 2 for a, b in zip(p, y)) / len(p)


def _wilson_ci(k: int, n: int) -> tuple[float | None, float | None]:
    """Wilson score interval. Reuses the project's existing implementation."""
    try:
        from research.baseline_stats import wilson_ci
        return wilson_ci(k, n)
    except Exception:
        return (None, None)


@dataclass
class BandResult:
    """One score band's measured outcome rate."""
    band: str
    lower: float
    upper: float
    n: int = 0
    positives: int = 0
    rate: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    mean_score: float | None = None
    mean_max_favorable: float | None = None
    median_max_favorable: float | None = None
    mean_max_adverse: float | None = None
    calibration_delta: float | None = None   # rate − mean_score/100 (>0 ⇒ band underperformed its score)
    verdict: str = "INSUFFICIENT_DATA"
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "band": self.band, "lower": self.lower, "upper": self.upper,
            "n": self.n, "positives": self.positives, "rate": self.rate,
            "ci_low": self.ci_low, "ci_high": self.ci_high,
            "mean_score": self.mean_score,
            "mean_max_favorable": self.mean_max_favorable,
            "median_max_favorable": self.median_max_favorable,
            "mean_max_adverse": self.mean_max_adverse,
            "calibration_delta": self.calibration_delta,
            "verdict": self.verdict, "reason": self.reason,
        }


@dataclass
class SegmentResult:
    """One value's measured outcome rate within a segmentation dimension
    (confidence level, chain, ...). Same guards as score bands: never more
    permissive than the pre-registered bar."""
    dimension: str
    value: str
    n: int = 0
    positives: int = 0
    rate: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    verdict: str = "INSUFFICIENT_DATA"
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension, "value": self.value,
            "n": self.n, "positives": self.positives, "rate": self.rate,
            "ci_low": self.ci_low, "ci_high": self.ci_high,
            "verdict": self.verdict, "reason": self.reason,
        }


@dataclass
class CalibrationMetrics:
    """Descriptive diagnostics over ALL joined pairs.

    `guards_met` carries the pre-registered sample bar: these numbers are true
    arithmetic statements about the cohort, but they only support a
    calibration CLAIM when the cohort cleared the bar. Below the bar they are
    reported WITH the warning, never silently upgraded.
    """
    joined_pairs: int = 0
    base_rate: float | None = None
    brier_score: float | None = None
    brier_base_rate: float | None = None
    brier_resolution: float | None = None   # base − model; >0 ⇒ score adds skill
    ece: float | None = None                # expected calibration error (bands)
    spearman_score_vs_hit: float | None = None
    spearman_score_vs_maxfav: float | None = None
    guards_met: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "joined_pairs": self.joined_pairs,
            "base_rate": self.base_rate,
            "brier_score": self.brier_score,
            "brier_base_rate": self.brier_base_rate,
            "brier_resolution": self.brier_resolution,
            "ece": self.ece,
            "spearman_score_vs_hit": self.spearman_score_vs_hit,
            "spearman_score_vs_maxfav": self.spearman_score_vs_maxfav,
            "guards_met": self.guards_met,
            "brier_note": ("Brier is computed on opportunity_score/100 — a "
                           "diagnostic of ranking sharpness, NOT a claim that "
                           "AHOS scores are calibrated probabilities."),
        }


@dataclass
class CalibrationReport:
    """Full calibration result. `verdict` is the headline."""
    generated_utc: str
    horizon: str
    event_class: str
    total_predictions: int
    joined_pairs: int
    bands: list[BandResult] = field(default_factory=list)
    engine_versions: dict[str, int] = field(default_factory=dict)
    verdict: str = "INSUFFICIENT_DATA"
    findings: list[str] = field(default_factory=list)
    monotonicity: str | None = None
    # -- Month-3 additions: segmentation + diagnostics -----------------------
    confidence_segments: list[SegmentResult] = field(default_factory=list)
    chain_segments: list[SegmentResult] = field(default_factory=list)
    provider_segments: list[SegmentResult] = field(default_factory=list)
    regime_segments: list[SegmentResult] = field(default_factory=list)
    confidence_ordering: str | None = None
    metrics: CalibrationMetrics = field(default_factory=CalibrationMetrics)
    feature_coverage: dict[str, Any] = field(default_factory=dict)
    extreme_records: list[dict[str, Any]] = field(default_factory=list)
    dimension_availability: dict[str, str] = field(default_factory=dict)
    score_drift: dict[str, Any] = field(default_factory=dict)
    # -- provenance: "this number came from exactly these rows" ---------------
    eligible_sources: list[str] = field(default_factory=list)
    source_census: dict[str, int] = field(default_factory=dict)
    excluded_predictions: int = 0
    exclusion_reasons: dict[str, int] = field(default_factory=dict)
    observation_window: dict[str, Any] = field(default_factory=dict)
    dataset_fingerprint: str = ""
    weight_fingerprints: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "ahos.calibration_report.v6",
            "generated_utc": self.generated_utc,
            "horizon": self.horizon,
            "event_class": self.event_class,
            "calibration_status": self.verdict,
            "number_of_predictions": self.total_predictions,
            "number_of_eligible_pairs": self.joined_pairs,
            "excluded_predictions": self.excluded_predictions,
            "exclusion_reasons": self.exclusion_reasons,
            "eligible_sources": self.eligible_sources,
            "source_census": self.source_census,
            "observation_window": self.observation_window,
            "dataset_fingerprint": self.dataset_fingerprint,
            "score_engine_versions": self.engine_versions,
            "weight_fingerprints": self.weight_fingerprints,
            "bands": [b.as_dict() for b in self.bands],
            "confidence_segments": [s.as_dict() for s in self.confidence_segments],
            "chain_segments": [s.as_dict() for s in self.chain_segments],
            "provider_segments": [s.as_dict() for s in self.provider_segments],
            "regime_segments": [s.as_dict() for s in self.regime_segments],
            "confidence_ordering": self.confidence_ordering,
            "metrics": self.metrics.as_dict(),
            "feature_coverage": self.feature_coverage,
            "extreme_records": self.extreme_records,
            "dimension_availability": self.dimension_availability,
            "score_drift": self.score_drift,
            "monotonicity": self.monotonicity,
            "verdict": self.verdict,
            "findings": self.findings,
            "guards": {
                "min_n_per_band": MIN_N_PER_BAND,
                "min_positives": MIN_POSITIVES,
                "no_peeking": "label.resolved_ts > prediction.scored_ts",
                "source_filter": "prediction.source IN eligible_sources",
                "unresolved_policy": "outcome_label.hit IS NULL => UNRESOLVED, never a failure",
            },
            "outcome_provenance": {
                "labeler": "discovery/outcomes.py (Lane-A frozen, hash-pinned)",
                "horizon_grid": "15m,1h,4h,12h,24h,72h,7d",
                "event_grid": "+25%,+50%,+100%,+200%",
                "entry_rule": "closest observation within 15min of first_seen",
            },
        }


class CalibrationHarness:
    """Joins persisted predictions to frozen outcome labels and measures lift."""

    def __init__(self, ledger_db: str | None = None,
                 discovery_db: str | None = None,
                 eligible_sources: frozenset[str] | set[str] | None = None):
        self.ledger_db = ledger_db or get_local_db_path()
        self.discovery_db = discovery_db or get_discovery_db_path()
        # Overridable ONLY so the test suite can prove the filter works on its
        # own fixtures. Production callers take the default, which admits real
        # operator evidence and nothing else.
        self.eligible_sources = frozenset(
            eligible_sources if eligible_sources is not None
            else CALIBRATION_ELIGIBLE_SOURCES)

    # ------------------------------------------------------------- the join --

    def _connect(self) -> sqlite3.Connection:
        """Read-only handle over the ledger with the Lane-A store attached.

        Both stores are opened `mode=ro`: a calibration run must be incapable
        of writing to either, and Lane-A especially is never mutated.
        """
        conn = sqlite3.connect(f"file:{self.ledger_db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("ATTACH DATABASE ? AS disc", (f"file:{self.discovery_db}?mode=ro",))
        return conn

    def _load_pairs(self, horizon: str, event_class: str) -> list[dict[str, Any]]:
        """Prediction ⋈ outcome label, with the no-peeking rule enforced in SQL.

        Three filters carry the integrity of this join and none of them may be
        relaxed by a caller:
          * `s.source IN (eligible)`  — test/sandbox/synthetic rows can never
            become calibration evidence, even when they share a store.
          * `o.resolved_ts > s.scored_ts` — no-peeking: a label that closed
            before the prediction existed cannot grade it.
          * `o.hit IS NOT NULL` — an unresolved outcome stays UNRESOLVED and is
            never silently read as a failure.
        """
        placeholders = ",".join("?" for _ in self.eligible_sources)
        try:
            conn = self._connect()
            rows = [dict(r) for r in conn.execute(
                f"""SELECT s.score_id, s.token_id, s.opportunity_score, s.scored_ts,
                          s.engine_version, s.weights_sha256, s.confidence_level,
                          s.chain, s.known_field_count, s.unknown_field_count,
                          s.evidence_sha256, s.source, s.source_provider,
                          o.hit, o.resolved_ts, o.max_favorable, o.max_adverse
                     FROM opportunity_score_ledger s
                     JOIN disc.outcome_label o
                       ON o.token_id = s.token_id
                    WHERE o.horizon = ?
                      AND o.event_class = ?
                      AND o.hit IS NOT NULL
                      AND s.token_id IS NOT NULL
                      AND s.source IN ({placeholders})
                      AND o.resolved_ts > s.scored_ts""",
                (horizon, event_class, *sorted(self.eligible_sources)),
            ).fetchall()]
            conn.close()
            return rows
        except sqlite3.Error:
            return []

    def _exclusion_census(self, horizon: str, event_class: str) -> dict[str, int]:
        """Why predictions did NOT make it into the cohort.

        A calibration number without an exclusion account is unauditable: the
        reader cannot tell a genuinely small cohort from a large one that was
        quietly filtered down.
        """
        placeholders = ",".join("?" for _ in self.eligible_sources)
        eligible = sorted(self.eligible_sources)
        census: dict[str, int] = {}
        try:
            conn = self._connect()

            def scalar(sql: str, params: tuple = ()) -> int:
                row = conn.execute(sql, params).fetchone()
                return int(row[0]) if row else 0

            total = scalar("SELECT COUNT(*) FROM opportunity_score_ledger")
            census["ineligible_source"] = scalar(
                f"SELECT COUNT(*) FROM opportunity_score_ledger "
                f"WHERE source NOT IN ({placeholders})", tuple(eligible))
            census["missing_token_id"] = scalar(
                f"SELECT COUNT(*) FROM opportunity_score_ledger "
                f"WHERE token_id IS NULL AND source IN ({placeholders})", tuple(eligible))
            census["no_matching_label"] = scalar(
                f"""SELECT COUNT(*) FROM opportunity_score_ledger s
                     WHERE s.source IN ({placeholders})
                       AND s.token_id IS NOT NULL
                       AND NOT EXISTS (
                         SELECT 1 FROM disc.outcome_label o
                          WHERE o.token_id = s.token_id
                            AND o.horizon = ? AND o.event_class = ?)""",
                (*eligible, horizon, event_class))
            census["label_predates_prediction"] = scalar(
                f"""SELECT COUNT(*) FROM opportunity_score_ledger s
                     JOIN disc.outcome_label o ON o.token_id = s.token_id
                    WHERE s.source IN ({placeholders})
                      AND o.horizon = ? AND o.event_class = ?
                      AND o.resolved_ts <= s.scored_ts""",
                (*eligible, horizon, event_class))
            census["unresolved_outcome"] = scalar(
                f"""SELECT COUNT(*) FROM opportunity_score_ledger s
                     JOIN disc.outcome_label o ON o.token_id = s.token_id
                    WHERE s.source IN ({placeholders})
                      AND o.horizon = ? AND o.event_class = ?
                      AND o.hit IS NULL""",
                (*eligible, horizon, event_class))
            census["_total_predictions"] = total
            conn.close()
        except sqlite3.Error:
            return {}
        return census

    def _dataset_fingerprint(self, pairs: list[dict[str, Any]]) -> str:
        """Deterministic digest of the exact cohort behind a report.

        Two reports with the same fingerprint were computed from the same rows;
        a changed number with an unchanged fingerprint means the CODE changed,
        not the data. That distinction is what makes a result replayable.
        """
        h = hashlib.sha256()
        for p in sorted(pairs, key=lambda r: str(r["score_id"])):
            h.update(f"{p['score_id']}|{p['opportunity_score']}|"
                     f"{p['hit']}|{p['resolved_ts']}|{p['scored_ts']}".encode())
        return h.hexdigest()

    def _observation_window(self, pairs: list[dict[str, Any]]) -> dict[str, Any]:
        if not pairs:
            return {"first_scored_utc": None, "last_scored_utc": None,
                    "first_resolved_utc": None, "last_resolved_utc": None}
        scored = [float(p["scored_ts"]) for p in pairs]
        resolved = [float(p["resolved_ts"]) for p in pairs]
        return {
            "first_scored_utc": _utc(min(scored)),
            "last_scored_utc": _utc(max(scored)),
            "first_resolved_utc": _utc(min(resolved)),
            "last_resolved_utc": _utc(max(resolved)),
        }

    def _pre_prediction_prices(self, token_id: str, scored_ts: float) -> list[float]:
        """Price observations BEFORE the prediction was made (no-peeking).

        Only observations with retrieved_ts <= scored_ts may describe the
        regime the scorer was operating in; anything after would leak the
        outcome window into the segmentation.
        """
        try:
            conn = self._connect()
            rows = conn.execute(
                """SELECT price_usd FROM disc.discovery_observations
                    WHERE token_id = ? AND retrieved_ts <= ?
                      AND price_usd IS NOT NULL AND price_usd > 0
                      AND error_state IS NULL
                 ORDER BY retrieved_ts""",
                (token_id, float(scored_ts)),
            ).fetchall()
            conn.close()
            return [float(r[0]) for r in rows if r[0] is not None]
        except sqlite3.Error:
            return []

    def _token_regimes(self, pairs: list[dict[str, Any]]) -> dict[str, str]:
        """token_id -> regime label (or UNKNOWN). Memoized; deterministic."""
        out: dict[str, str] = {}
        for p in pairs:
            tid = str(p["token_id"])
            if tid in out:
                continue
            prices = self._pre_prediction_prices(tid, float(p["scored_ts"]))
            label = _token_price_regime(prices)
            out[tid] = label if label else "UNKNOWN"
        return out

    def _source_census(self) -> dict[str, int]:
        try:
            conn = sqlite3.connect(f"file:{self.ledger_db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT source, COUNT(*) AS n FROM opportunity_score_ledger "
                "GROUP BY source ORDER BY source").fetchall()
            conn.close()
            return {r["source"]: r["n"] for r in rows}
        except sqlite3.Error:
            return {}

    def _total_predictions(self) -> int:
        try:
            conn = sqlite3.connect(f"file:{self.ledger_db}?mode=ro", uri=True)
            n = conn.execute("SELECT COUNT(*) FROM opportunity_score_ledger").fetchone()[0]
            conn.close()
            return int(n)
        except sqlite3.Error:
            return 0

    # ------------------------------------------------- segmentation helpers --

    @staticmethod
    def _segment_table(pairs: list[dict[str, Any]], dimension: str,
                       key_fn: Callable[[dict[str, Any]], str],
                       allowed: tuple[str, ...] | None = None) -> list[SegmentResult]:
        """Rate table per value of a dimension, with the SAME guards as score
        bands. Values outside `allowed` (when given) bucket to UNKNOWN and are
        never merged into a real level."""
        by_value: dict[str, list[dict[str, Any]]] = {}
        for p in pairs:
            raw = str(key_fn(p) or "").strip()
            value = raw if raw else "UNKNOWN"
            if allowed is not None and value.upper() not in allowed:
                value = "UNKNOWN"
            by_value.setdefault(value, []).append(p)

        rows: list[SegmentResult] = []
        for value in sorted(by_value):
            seg = by_value[value]
            n = len(seg)
            positives = sum(1 for p in seg if int(p["hit"]) == 1)
            guards: list[str] = []
            if n < MIN_N_PER_BAND:
                guards.append(f"n<{MIN_N_PER_BAND}")
            if positives < MIN_POSITIVES:
                guards.append(f"positives<{MIN_POSITIVES}")
            row = SegmentResult(dimension=dimension, value=value, n=n,
                                positives=positives)
            if n > 0:
                row.rate = positives / n
                row.ci_low, row.ci_high = _wilson_ci(positives, n)
            if guards:
                row.verdict = "INSUFFICIENT_DATA"
                row.reason = ";".join(guards)
            else:
                row.verdict = "DESCRIPTIVE_OK"
            rows.append(row)
        return rows

    @staticmethod
    def _confidence_ordering(segments: list[SegmentResult]) -> str | None:
        """HIGH ≥ MED ≥ LOW hit rates ⇒ confidence is ordered (higher stated
        confidence corresponds to higher realized success). An inversion
        between HIGH and LOW is reported even when MED has no data yet — the
        strongest failure mode must never hide behind a missing middle."""
        rates = {s.value: s.rate for s in segments
                 if s.verdict == "DESCRIPTIVE_OK" and s.rate is not None}
        hi = rates.get("HIGH")
        lo = rates.get("LOW")
        if hi is not None and lo is not None and lo > hi:
            return "CONFIDENCE_INVERTED"
        med = rates.get("MED")
        if hi is not None and med is not None and lo is not None:
            if hi >= med >= lo:
                return "CONFIDENCE_ORDERED"
            return "CONFIDENCE_NOT_ORDERED"
        return None

    # ------------------------------------------------------------- drift --

    @staticmethod
    def _score_drift_report(pairs: list[dict[str, Any]]) -> dict[str, Any]:
        """ADWIN-style score-stream drift diagnostic over the joined cohort.

        First production consumer of architecture/learning/drift.py: feeds the
        opportunity scores in scored_ts order through StreamingDriftDetector
        and reports whether the score distribution shifted during the
        observation window. Honesty: fewer than the detector's min_window
        samples => INSUFFICIENT_DATA (never a fabricated stability claim);
        the verdict is a fact about the cohort, not a claim about live data.
        """
        ordered = sorted(pairs, key=lambda p: (float(p["scored_ts"]),
                                               str(p["score_id"])))
        if len(ordered) < 10:   # StreamingDriftDetector.min_window
            return {
                "detector": "StreamingDriftDetector (ADWIN pattern)",
                "samples": len(ordered),
                "verdict": "INSUFFICIENT_DATA",
                "reason": f"fewer than {10} score samples in cohort",
                "drift_detected": None,
            }
        try:
            from ..learning.drift import StreamingDriftDetector
        except Exception as e:
            return {"detector": "StreamingDriftDetector", "samples": len(ordered),
                    "verdict": "UNKNOWN", "reason": f"{type(e).__name__}: {e}",
                    "drift_detected": None}
        detector = StreamingDriftDetector()
        triggered_at: int | None = None
        for idx, p in enumerate(ordered, start=1):
            if detector.update(float(p["opportunity_score"])):
                triggered_at = idx
        return {
            "detector": "StreamingDriftDetector (ADWIN pattern)",
            "samples": len(ordered),
            "verdict": ("DRIFT_DETECTED" if triggered_at is not None
                        else "NO_DRIFT_DETECTED"),
            "drift_detected": triggered_at is not None,
            "first_trigger_at_sample": triggered_at,
            "final_window_mean": round(detector.current_mean, 4),
        }

    # ------------------------------------------------------------- metrics --

    def _compute_metrics(self, report: CalibrationReport,
                         pairs: list[dict[str, Any]]) -> CalibrationMetrics:
        m = CalibrationMetrics(joined_pairs=len(pairs))
        if not pairs:
            return m

        scores = [float(p["opportunity_score"]) for p in pairs]
        hits = [float(p["hit"]) for p in pairs]
        m.base_rate = sum(hits) / len(hits)

        norm = [s / 100.0 for s in scores]
        m.brier_score = _brier(norm, hits)
        m.brier_base_rate = _brier([m.base_rate] * len(hits), hits)
        if m.brier_score is not None and m.brier_base_rate is not None:
            m.brier_resolution = m.brier_base_rate - m.brier_score

        m.spearman_score_vs_hit = _spearman(scores, hits)

        fav = [(float(p["opportunity_score"]), float(p["max_favorable"]))
               for p in pairs if p.get("max_favorable") is not None]
        if fav:
            m.spearman_score_vs_maxfav = _spearman(
                [s for s, _ in fav], [f for _, f in fav])

        populated = [b for b in report.bands
                     if b.n > 0 and b.rate is not None and b.mean_score is not None]
        if populated:
            total = sum(b.n for b in populated)
            m.ece = sum(b.n / total * abs(b.rate - b.mean_score / 100.0)
                        for b in populated)

        positives = sum(1 for h in hits if h == 1.0)
        m.guards_met = (len(pairs) >= MIN_N_PER_BAND
                        and positives >= MIN_POSITIVES)
        return m

    @staticmethod
    def _feature_coverage(pairs: list[dict[str, Any]]) -> dict[str, Any]:
        if not pairs:
            return {"mean_known_fields": None, "mean_unknown_fields": None,
                    "records_with_evidence_sha": 0, "total_records": 0}
        known = [float(p["known_field_count"]) for p in pairs
                 if p.get("known_field_count") is not None]
        unknown = [float(p["unknown_field_count"]) for p in pairs
                   if p.get("unknown_field_count") is not None]
        with_evidence = sum(1 for p in pairs if str(p.get("evidence_sha256") or ""))
        return {
            "mean_known_fields": _mean(known),
            "mean_unknown_fields": _mean(unknown),
            "records_with_evidence_sha": with_evidence,
            "total_records": len(pairs),
        }

    @staticmethod
    def _extreme_records(pairs: list[dict[str, Any]], k: int = 3) -> list[dict[str, Any]]:
        """Highest- and lowest-scored predictions with their outcome — the
        concrete answer to 'what did the system say about the extremes, and
        what happened to them?' Deterministic (score, then score_id)."""
        if not pairs:
            return []
        ordered = sorted(pairs, key=lambda p: (float(p["opportunity_score"]),
                                               str(p["score_id"])))
        selected = ordered[:k] + ordered[-k:]
        out = []
        for p in selected:
            out.append({
                "score_id": p["score_id"],
                "opportunity_score": float(p["opportunity_score"]),
                "confidence_level": str(p.get("confidence_level") or "UNKNOWN"),
                "chain": str(p.get("chain") or "UNKNOWN"),
                "hit": int(p["hit"]),
                "max_favorable": p.get("max_favorable"),
                "known_field_count": p.get("known_field_count"),
                "unknown_field_count": p.get("unknown_field_count"),
                "evidence_sha256": str(p.get("evidence_sha256") or "")[:16] or None,
            })
        return out

    @staticmethod
    def _dimension_availability() -> dict[str, str]:
        """Which segmentation dimensions are persisted at prediction time.
        Absent dimensions are honest UNKNOWNs — wiring them is writer-side
        work, not something a calibration report may invent."""
        return {
            "score": "persisted (opportunity_score_ledger.opportunity_score)",
            "confidence_level": "persisted (opportunity_score_ledger.confidence_level)",
            "chain": "persisted (opportunity_score_ledger.chain)",
            "horizon": "run parameter (outcome_label.horizon)",
            "event_class": "run parameter (outcome_label.event_class)",
            "evidence": ("persisted (evidence_sha256, positive_reasons_json, "
                         "known/unknown field counts)"),
            "provider": ("persisted (opportunity_score_ledger.source_provider, "
                         "stamped from the candidate at scoring time)"),
            "market_regime": ("computed post-hoc at evaluation time from "
                              "PRE-prediction observations per token "
                              "(token_price_regime via "
                              "architecture/intel/regimes.py, first production "
                              "consumer; <10 obs -> UNKNOWN); not stamped on "
                              "predictions"),
            "opportunity_type": "NOT_PERSISTED_AT_PREDICTION_TIME — no "
                                "opportunity-type concept exists in the scoring "
                                "contract; not invented by the harness",
        }

    # ------------------------------------------------------------- multi-run --

    def run_many(self, horizons: Iterable[str],
                 event_class: str = DEFAULT_EVENT_CLASS,
                 now: float | None = None) -> list[CalibrationReport]:
        """Run the harness per horizon. Each report keeps its own provenance;
        pooling horizons into one number would describe a system that never
        existed."""
        ts = time.time() if now is None else now
        return [self.run(horizon=h, event_class=event_class, now=ts)
                for h in horizons]

    # ----------------------------------------------------------- the report --

    def run(self, horizon: str = DEFAULT_HORIZON,
            event_class: str = DEFAULT_EVENT_CLASS,
            now: float | None = None) -> CalibrationReport:
        ts = time.time() if now is None else now
        pairs = self._load_pairs(horizon, event_class)

        exclusions = self._exclusion_census(horizon, event_class)
        total = exclusions.pop("_total_predictions", self._total_predictions())

        report = CalibrationReport(
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
            horizon=horizon,
            event_class=event_class,
            total_predictions=total,
            joined_pairs=len(pairs),
            eligible_sources=sorted(self.eligible_sources),
            source_census=self._source_census(),
            excluded_predictions=max(0, total - len(pairs)),
            exclusion_reasons=exclusions,
            observation_window=self._observation_window(pairs),
            dataset_fingerprint=self._dataset_fingerprint(pairs),
        )

        # Version census first: a mixed cohort must be visible before any rate.
        versions: dict[str, int] = {}
        for p in pairs:
            key = f"{p['engine_version']}:{str(p['weights_sha256'])[:12]}"
            versions[key] = versions.get(key, 0) + 1
        report.engine_versions = versions
        report.weight_fingerprints = sorted(
            {str(p["weights_sha256"]) for p in pairs})

        # Contamination is a headline finding, not a footnote.
        contaminating = {s: n for s, n in report.source_census.items()
                         if s not in self.eligible_sources}
        if contaminating:
            report.findings.append(
                f"NON_ELIGIBLE_ROWS_PRESENT: {contaminating} — these are excluded "
                "from every rate below (test/sandbox/synthetic data is never "
                "calibration evidence).")
        if len(versions) > 1:
            report.findings.append(
                f"MIXED_ENGINE_VERSIONS: {len(versions)} scoring versions in cohort — "
                "rates below pool distinct systems and must not be read as one curve.")

        for name, low, high in SCORE_BANDS:
            band = BandResult(band=name, lower=low, upper=high)
            in_band = [p for p in pairs
                       if low <= float(p["opportunity_score"]) < high]
            band.n = len(in_band)
            band.positives = sum(1 for p in in_band if int(p["hit"]) == 1)

            guards: list[str] = []
            if band.n < MIN_N_PER_BAND:
                guards.append(f"n<{MIN_N_PER_BAND}")
            if band.positives < MIN_POSITIVES:
                guards.append(f"positives<{MIN_POSITIVES}")

            if band.n > 0:
                band.rate = band.positives / band.n
                band.ci_low, band.ci_high = _wilson_ci(band.positives, band.n)
                band.mean_score = _mean(
                    float(p["opportunity_score"]) for p in in_band)
                band.mean_max_favorable = _mean(
                    float(p["max_favorable"]) for p in in_band
                    if p.get("max_favorable") is not None)
                band.median_max_favorable = _median(
                    float(p["max_favorable"]) for p in in_band
                    if p.get("max_favorable") is not None)
                band.mean_max_adverse = _mean(
                    float(p["max_adverse"]) for p in in_band
                    if p.get("max_adverse") is not None)
                if band.rate is not None and band.mean_score is not None:
                    band.calibration_delta = band.rate - band.mean_score / 100.0

            if guards:
                band.verdict = "INSUFFICIENT_DATA"
                band.reason = ";".join(guards)
            else:
                band.verdict = "DESCRIPTIVE_OK"
            report.bands.append(band)

        # Month-3: segmentation + diagnostics (descriptive over the cohort;
        # guards travel with every table, verdict stays the headline).
        report.confidence_segments = self._segment_table(
            pairs, "confidence_level",
            lambda p: str(p.get("confidence_level") or ""),
            allowed=CONFIDENCE_LEVELS)
        report.chain_segments = self._segment_table(
            pairs, "chain", lambda p: str(p.get("chain") or ""))
        report.provider_segments = self._segment_table(
            pairs, "provider", lambda p: str(p.get("source_provider") or ""))
        regimes = self._token_regimes(pairs)
        report.regime_segments = self._segment_table(
            pairs, "token_price_regime", lambda p: regimes.get(str(p["token_id"]), "UNKNOWN"))
        report.confidence_ordering = self._confidence_ordering(
            report.confidence_segments)
        report.metrics = self._compute_metrics(report, pairs)
        report.feature_coverage = self._feature_coverage(pairs)
        report.extreme_records = self._extreme_records(pairs)
        report.dimension_availability = self._dimension_availability()
        report.score_drift = self._score_drift_report(pairs)
        if report.score_drift.get("verdict") == "DRIFT_DETECTED":
            report.findings.append(
                "SCORE_DRIFT: the prediction score stream shifted during the "
                "observation window (ADWIN trigger at sample "
                f"{report.score_drift.get('first_trigger_at_sample')}) — "
                "rates pool distinct score regimes; segment by time before "
                "reading them as one curve.")

        # Sample-size warnings travel with the descriptive metrics.
        if pairs and not report.metrics.guards_met:
            report.findings.append(
                f"SAMPLE_SIZE_WARNING: {len(pairs)} joined pairs "
                f"({sum(1 for p in pairs if int(p['hit']) == 1)} positives) below "
                f"the pre-registered bar (n>={MIN_N_PER_BAND}, "
                f"positives>={MIN_POSITIVES}) — descriptive metrics are arithmetic "
                "facts about this cohort but support NO calibration claim.")

        if report.confidence_ordering == "CONFIDENCE_INVERTED":
            report.findings.append(
                "CONFIDENCE_INVERTED: LOW-confidence predictions succeeded at a "
                "HIGHER rate than HIGH-confidence ones — the confidence signal "
                "is inverted (systematically mislabeled).")
        elif report.confidence_ordering == "CONFIDENCE_NOT_ORDERED":
            report.findings.append(
                "CONFIDENCE_NOT_ORDERED: HIGH≥MED≥LOW hit-rate ordering did not "
                "hold — confidence is not a reliable success signal in this cohort.")

        usable = [b for b in report.bands if b.verdict == "DESCRIPTIVE_OK"]
        if not usable:
            report.verdict = "INSUFFICIENT_DATA"
            report.findings.append(
                f"No score band met the pre-registered guards "
                f"(n>={MIN_N_PER_BAND}, positives>={MIN_POSITIVES}). "
                f"{len(pairs)} prediction/outcome pairs available. "
                "This is the expected honest result until enough real "
                "observation history has accumulated.")
            return report

        report.verdict = "DESCRIPTIVE_OK"
        rates = [(b.band, b.rate) for b in usable if b.rate is not None]
        if len(rates) >= 2:
            ordered = all(rates[i][1] <= rates[i + 1][1] for i in range(len(rates) - 1))
            report.monotonicity = "MONOTONIC_INCREASING" if ordered else "NOT_MONOTONIC"
            report.findings.append(
                "Score bands rank outcomes in the expected order."
                if ordered else
                "Score bands do NOT rank outcomes monotonically — higher scores "
                "did not produce higher hit rates in this cohort.")
        else:
            report.monotonicity = "UNDETERMINED"
            report.findings.append(
                "Only one band cleared the guards — a calibration CURVE needs at "
                "least two comparable bands.")
        return report
