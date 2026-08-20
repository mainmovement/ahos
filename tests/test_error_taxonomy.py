#!/usr/bin/env python3
"""Prediction-error taxonomy: never invent an outcome; UNKNOWN security is DATA_PROBLEM."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.error_taxonomy import classify_prediction_error


def test_no_outcome_is_insufficient_evidence():
    c = classify_prediction_error(prediction={"opportunity_score": 80}, outcome=None)
    assert c.error_class == "INSUFFICIENT_EVIDENCE"
    assert c.confidence == "UNKNOWN"


def test_unknown_security_then_trap_is_data_problem_not_security_miss():
    c = classify_prediction_error(
        prediction={"opportunity_score": 80, "is_honeypot": None},
        outcome={"outcome_class": "HONEYPOT"},
    )
    assert c.error_class == "DATA_PROBLEM"


def test_observed_clear_then_honeypot_is_security_miss():
    c = classify_prediction_error(
        prediction={"opportunity_score": 80, "is_honeypot": False},
        outcome={"outcome_class": "HONEYPOT", "is_honeypot": True},
    )
    assert c.error_class == "SECURITY_MISS"
    assert c.confidence == "OBSERVED"


def test_viral_then_dump_is_social_false_positive():
    c = classify_prediction_error(
        prediction={"opportunity_score": 75, "virality_label": "VIRAL", "is_honeypot": False},
        outcome={"outcome_class": "DUMP"},
    )
    assert c.error_class == "SOCIAL_FALSE_POSITIVE"


def test_accumulation_then_dump_is_whale_false_positive():
    c = classify_prediction_error(
        prediction={"whale_label": "ACCUMULATING", "is_honeypot": False},
        outcome={"outcome_class": "LOSS"},
    )
    assert c.error_class == "WHALE_FALSE_POSITIVE"


def test_high_score_adverse_without_specifics_is_calibration_error():
    c = classify_prediction_error(
        prediction={"opportunity_score": 90, "is_honeypot": False, "missing_unknowns": []},
        outcome={"outcome_class": "MISS"},
    )
    assert c.error_class == "CALIBRATION_ERROR"


def test_profitable_outcome_is_not_an_error():
    c = classify_prediction_error(
        prediction={"opportunity_score": 80},
        outcome={"outcome_class": "PROFIT"},
    )
    assert c.error_class == "INSUFFICIENT_EVIDENCE"
