"""AHOS Learning Lane — prediction persistence and calibration infrastructure.

This package exists to close a structural hole in the intelligence loop:

    Observation → Prediction → Outcome → Label → Lesson → Evidence threshold

Everything in that chain existed EXCEPT `Prediction`. The scoring engine
produced a complete, explainable `OpportunityScoreReport` on every cycle and
then discarded it when the function returned. Outcome labels are recorded
(frozen Lane-A `discovery/outcomes.py`), but nothing recorded *what the system
predicted before the outcome happened*, so the two could never be joined and no
calibration statement was even computable.

Two modules close that:

  * `score_ledger`  — append-only persistence of every score the engine emits,
                      with engine version + weight fingerprint + provenance.
  * `calibration`   — joins persisted predictions to frozen outcome labels and
                      reports score-vs-outcome rates with Wilson intervals.

LAWS (inherited, enforced here):
  * This package NEVER changes a weight, threshold, or score. It only records
    and measures. Recording must never alter what is recorded.
  * Lane-A is read-only from here. Outcome labels are consumed, never written.
  * INSUFFICIENT_DATA is a first-class verdict. A calibration report on a young
    cohort must say so rather than produce a comfortable number.
  * Persistence is best-effort and fail-open with respect to the pipeline: a
    ledger write failure must never take down an observation cycle, but it is
    always visible (logged + counted), never silently swallowed.
"""

from .score_ledger import (
    SCHEMA_SCORE_LEDGER,
    SCORING_ENGINE_VERSION,
    ScoreLedger,
    ScoreRecord,
    weights_fingerprint,
)

__all__ = [
    "SCHEMA_SCORE_LEDGER",
    "SCORING_ENGINE_VERSION",
    "ScoreLedger",
    "ScoreRecord",
    "weights_fingerprint",
]
