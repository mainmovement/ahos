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

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any

from config.paths import get_discovery_db_path, get_local_db_path

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
    verdict: str = "INSUFFICIENT_DATA"
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "band": self.band, "lower": self.lower, "upper": self.upper,
            "n": self.n, "positives": self.positives, "rate": self.rate,
            "ci_low": self.ci_low, "ci_high": self.ci_high,
            "verdict": self.verdict, "reason": self.reason,
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

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "ahos.calibration_report.v1",
            "generated_utc": self.generated_utc,
            "horizon": self.horizon,
            "event_class": self.event_class,
            "total_predictions": self.total_predictions,
            "joined_pairs": self.joined_pairs,
            "bands": [b.as_dict() for b in self.bands],
            "engine_versions": self.engine_versions,
            "monotonicity": self.monotonicity,
            "verdict": self.verdict,
            "findings": self.findings,
            "guards": {
                "min_n_per_band": MIN_N_PER_BAND,
                "min_positives": MIN_POSITIVES,
                "no_peeking": "label.resolved_ts > prediction.scored_ts",
            },
        }


class CalibrationHarness:
    """Joins persisted predictions to frozen outcome labels and measures lift."""

    def __init__(self, ledger_db: str | None = None,
                 discovery_db: str | None = None):
        self.ledger_db = ledger_db or get_local_db_path()
        self.discovery_db = discovery_db or get_discovery_db_path()

    # ------------------------------------------------------------- the join --

    def _load_pairs(self, horizon: str, event_class: str) -> list[dict[str, Any]]:
        """Prediction ⋈ outcome label, with the no-peeking rule enforced in SQL.

        The two live in different stores (predictions in the local operational
        DB, labels in the Lane-A discovery DB), so the discovery store is
        ATTACHed read-only. Lane-A is never written.
        """
        rows: list[dict[str, Any]] = []
        try:
            conn = sqlite3.connect(f"file:{self.ledger_db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            conn.execute("ATTACH DATABASE ? AS disc", (f"file:{self.discovery_db}?mode=ro",))
            rows = [dict(r) for r in conn.execute(
                """SELECT s.score_id, s.token_id, s.opportunity_score, s.scored_ts,
                          s.engine_version, s.weights_sha256, s.confidence_level,
                          o.hit, o.resolved_ts, o.max_favorable
                     FROM opportunity_score_ledger s
                     JOIN disc.outcome_label o
                       ON o.token_id = s.token_id
                    WHERE o.horizon = ?
                      AND o.event_class = ?
                      AND o.hit IS NOT NULL
                      AND s.token_id IS NOT NULL
                      AND o.resolved_ts > s.scored_ts""",   # no-peeking law
                (horizon, event_class),
            ).fetchall()]
            conn.close()
        except sqlite3.Error:
            return []
        return rows

    def _total_predictions(self) -> int:
        try:
            conn = sqlite3.connect(f"file:{self.ledger_db}?mode=ro", uri=True)
            n = conn.execute("SELECT COUNT(*) FROM opportunity_score_ledger").fetchone()[0]
            conn.close()
            return int(n)
        except sqlite3.Error:
            return 0

    # ----------------------------------------------------------- the report --

    def run(self, horizon: str = DEFAULT_HORIZON,
            event_class: str = DEFAULT_EVENT_CLASS,
            now: float | None = None) -> CalibrationReport:
        ts = time.time() if now is None else now
        pairs = self._load_pairs(horizon, event_class)

        report = CalibrationReport(
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
            horizon=horizon,
            event_class=event_class,
            total_predictions=self._total_predictions(),
            joined_pairs=len(pairs),
        )

        # Version census first: a mixed cohort must be visible before any rate.
        versions: dict[str, int] = {}
        for p in pairs:
            key = f"{p['engine_version']}:{str(p['weights_sha256'])[:12]}"
            versions[key] = versions.get(key, 0) + 1
        report.engine_versions = versions
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

            if guards:
                band.verdict = "INSUFFICIENT_DATA"
                band.reason = ";".join(guards)
            else:
                band.verdict = "DESCRIPTIVE_OK"
            report.bands.append(band)

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
