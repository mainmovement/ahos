#!/usr/bin/env python3
"""Prediction-error taxonomy (learning loop).

Closes the gap between "we stored a score" and "we know WHY it was wrong".

    Prediction → Outcome → Error class → Lesson

This module NEVER invents an outcome. If the outcome is missing, the class
is INSUFFICIENT_EVIDENCE. A high score that later rugs is not proof of a
security miss unless a security atom was observed-clear at prediction time
(UNKNOWN security is DATA_PROBLEM, not SECURITY_MISS).

Classes (fixed vocabulary):
  SECURITY_MISS          observed-clear security, later honeypot/rug/trap
  LIQUIDITY_ERROR        observed liquidity, later unexitability / collapse
  TIMING_ERROR           peak existed then faded (outcome path observed)
  SOCIAL_FALSE_POSITIVE  virality VIRAL then dump; social was a positive
  WHALE_FALSE_POSITIVE   whale-accumulation label then distribution/dump
  DATA_PROBLEM           prediction made with material UNKNOWNs
  REGIME_SHIFT           regime at prediction ≠ regime at outcome (both known)
  CALIBRATION_ERROR      score high, outcome miss, no more specific class
  INSUFFICIENT_EVIDENCE  no outcome, or both sides unknown
  UNKNOWN                observed error, but no class fits without guessing
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

ERROR_CLASSES = (
    "SECURITY_MISS",
    "LIQUIDITY_ERROR",
    "TIMING_ERROR",
    "SOCIAL_FALSE_POSITIVE",
    "WHALE_FALSE_POSITIVE",
    "DATA_PROBLEM",
    "REGIME_SHIFT",
    "CALIBRATION_ERROR",
    "INSUFFICIENT_EVIDENCE",
    "UNKNOWN",
)

BAD_OUTCOMES = {
    "RUG", "HONEYPOT", "TRAPPED", "TOTAL_LOSS", "LOSS", "DUMP", "MISS",
}


@dataclass(frozen=True)
class ErrorClassification:
    error_class: str
    confidence: str                 # OBSERVED | DERIVED | UNKNOWN
    rationale: str
    evidence_refs: tuple[str, ...]
    unknowns: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _s(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def classify_prediction_error(*, prediction: dict[str, Any],
                              outcome: dict[str, Any] | None) -> ErrorClassification:
    """Pure function. `prediction` and `outcome` are plain dicts of observed
    fields (None = UNKNOWN). Never fabricates an outcome."""
    if not outcome:
        return ErrorClassification(
            "INSUFFICIENT_EVIDENCE", "UNKNOWN",
            "no outcome observed — cannot classify an error",
            (), ("outcome",),
        )

    outcome_class = str(_s(outcome, "outcome_class", "label", "result") or "").upper()
    if not outcome_class:
        return ErrorClassification(
            "INSUFFICIENT_EVIDENCE", "UNKNOWN",
            "outcome present but unlabeled",
            (), ("outcome_class",),
        )

    score = _s(prediction, "opportunity_score", "score")
    honeypot_at_pred = _s(prediction, "is_honeypot")
    liq_at_pred = _s(prediction, "liquidity_usd")
    virality = str(_s(prediction, "virality_label") or "").upper()
    whale = str(_s(prediction, "whale_label") or "").upper()
    unknowns_at_pred = list(_s(prediction, "missing_unknowns") or [])
    regime_pred = _s(prediction, "regime")
    regime_out = _s(outcome, "regime")
    honeypot_later = _s(outcome, "is_honeypot")
    trapped = outcome_class in {"TRAPPED", "TOTAL_LOSS", "HONEYPOT", "RUG"}
    dumped = outcome_class in {"DUMP", "LOSS", "MISS"}
    peak = _s(outcome, "peak_multiple", "max_favorable")

    refs: list[str] = []
    if trapped and honeypot_at_pred is False and (
            honeypot_later is True or outcome_class in {"HONEYPOT", "RUG", "TRAPPED"}):
        return ErrorClassification(
            "SECURITY_MISS", "OBSERVED",
            "security was observed-clear at prediction; later trap/honeypot/rug",
            ("is_honeypot", "outcome_class"), (),
        )
    if trapped and honeypot_at_pred is None:
        return ErrorClassification(
            "DATA_PROBLEM", "OBSERVED",
            "security was UNKNOWN at prediction — this is missing data, not a miss",
            ("outcome_class",), ("is_honeypot",),
        )
    if trapped and liq_at_pred is not None:
        return ErrorClassification(
            "LIQUIDITY_ERROR", "DERIVED",
            "position became unexitable; liquidity was observed at prediction",
            ("liquidity_usd", "outcome_class"), (),
        )
    if dumped and virality in {"VIRAL", "BUILDING"}:
        return ErrorClassification(
            "SOCIAL_FALSE_POSITIVE", "DERIVED",
            "virality was treated as attention; outcome dumped — attention ≠ demand",
            ("virality_label", "outcome_class"), (),
        )
    if dumped and whale in {"ACCUMULATING"}:
        return ErrorClassification(
            "WHALE_FALSE_POSITIVE", "DERIVED",
            "accumulation label then dump — concentration is not smart-money proof",
            ("whale_label", "outcome_class"), (),
        )
    if peak is not None:
        try:
            if float(peak) >= 1.5 and outcome_class in BAD_OUTCOMES:
                return ErrorClassification(
                    "TIMING_ERROR", "OBSERVED",
                    "a favorable excursion existed then was not captured",
                    ("peak_multiple", "outcome_class"), (),
                )
        except (TypeError, ValueError):
            pass
    if regime_pred and regime_out and regime_pred != regime_out and outcome_class in BAD_OUTCOMES:
        return ErrorClassification(
            "REGIME_SHIFT", "OBSERVED",
            f"regime {regime_pred} → {regime_out} across the horizon",
            ("regime",), (),
        )
    if unknowns_at_pred and len(unknowns_at_pred) >= 3 and outcome_class in BAD_OUTCOMES:
        return ErrorClassification(
            "DATA_PROBLEM", "OBSERVED",
            f"{len(unknowns_at_pred)} canonical unknowns at prediction time",
            ("missing_unknowns",), tuple(unknowns_at_pred[:4]),
        )
    try:
        if score is not None and float(score) >= 70 and outcome_class in BAD_OUTCOMES:
            return ErrorClassification(
                "CALIBRATION_ERROR", "DERIVED",
                "high score, adverse outcome, no more specific class evidenced",
                ("opportunity_score", "outcome_class"), (),
            )
    except (TypeError, ValueError):
        pass
    if outcome_class in BAD_OUTCOMES:
        return ErrorClassification(
            "UNKNOWN", "UNKNOWN",
            "adverse outcome observed but no class can be assigned without guessing",
            ("outcome_class",), refs or ("cause",),
        )
    return ErrorClassification(
        "INSUFFICIENT_EVIDENCE", "UNKNOWN",
        f"outcome {outcome_class} is not an error class (or is not adverse)",
        ("outcome_class",), (),
    )
