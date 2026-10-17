"""M49 lessons ledger and M58.1 paper decision scoring."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from architecture.learning.decision_eval import evaluate_paper_decision
from architecture.learning.lessons_ledger import (
    LessonsLedger,
    apply_gate,
)


def _ledger(tmp_path: Path) -> LessonsLedger:
    return LessonsLedger(tmp_path / "lessons.sqlite")


def test_unverified_lesson_has_zero_weight_and_chain_verifies(tmp_path: Path):
    ledger = _ledger(tmp_path)
    ledger.append(
        lesson_id="L1",
        source="trade_loss",
        market="gold",
        taxonomy="exit",
        evidence_refs=("soak:cycle:1",),
        claim="the paper exit was early",
        counterfactual="a later exit was not observed",
        valid_from="2026-10-18T00:00:00Z",
    )
    assert ledger.verify()
    assert ledger.retrieval_weight("L1", as_of="2026-10-18T00:00:00Z") == 0.0
    ledger.close()


def test_lesson_cannot_move_a_gate(tmp_path: Path):
    ledger = _ledger(tmp_path)
    row = ledger.append(
        lesson_id="L2",
        source="code_failure",
        market="gold",
        taxonomy="risk",
        evidence_refs=("fixture",),
        claim="raise the daily loss limit",
        counterfactual="the limit stays",
        valid_from="2026-10-18T00:00:00Z",
    )
    assert apply_gate(3.0, [row]) == 3.0
    ledger.close()


def test_tamper_is_rejected_and_broken_chain_fails_verify(tmp_path: Path):
    ledger = _ledger(tmp_path)
    ledger.append(
        lesson_id="L3",
        source="exam",
        market="gold",
        taxonomy="score",
        evidence_refs=("q1",),
        claim="original",
        counterfactual="none",
        valid_from="2026-10-18T00:00:00Z",
    )
    with pytest.raises(sqlite3.IntegrityError):
        ledger._conn.execute("UPDATE lesson SET claim='tampered'")
    ledger._conn.rollback()
    raw = sqlite3.connect(ledger.path)
    raw.execute("DROP TRIGGER ahos_guard_no_update_lesson")
    raw.execute("UPDATE lesson SET claim='tampered'")
    raw.commit()
    raw.close()
    assert ledger.verify() is False
    ledger.close()


def test_future_lesson_is_invisible(tmp_path: Path):
    ledger = _ledger(tmp_path)
    ledger.append(
        lesson_id="L4",
        source="debug",
        market="gold",
        taxonomy="timing",
        evidence_refs=("later",),
        claim="known only later",
        counterfactual="hidden at decision time",
        valid_from="2026-10-19T00:00:00Z",
    )
    assert ledger.visible("2026-10-18T12:00:00Z") == []
    assert ledger.retrieval_weight("L4", as_of="2026-10-18T12:00:00Z") == 0.0
    ledger.close()


def test_only_reviewer_16_can_give_retrieval_weight(tmp_path: Path):
    ledger = _ledger(tmp_path)
    ledger.append(
        lesson_id="L5",
        source="trade_loss",
        market="gold",
        taxonomy="direction",
        evidence_refs=("e",),
        claim="down",
        counterfactual="up",
        valid_from="2026-10-18T00:00:00Z",
    )
    with pytest.raises(PermissionError):
        ledger.review("L5", reviewer="ai", valid_from="2026-10-18T01:00:00Z")
    ledger.review("L5", reviewer="16", valid_from="2026-10-18T01:00:00Z")
    assert ledger.verify()
    assert ledger.retrieval_weight("L5", as_of="2026-10-18T01:00:00Z") == 1.0
    assert apply_gate(10.0, ledger.visible("2026-10-18T01:00:00Z")) == 10.0
    ledger.close()


def test_decision_eval_refuses_a_leaked_outcome_and_files_unverified(tmp_path: Path):
    ledger = _ledger(tmp_path)
    limit = 3.0
    with pytest.raises(ValueError):
        evaluate_paper_decision(
            ledger,
            lesson_id="D0",
            market="gold",
            decision_ts="2026-10-18T02:00:00Z",
            predicted="up",
            outcome_ts="2026-10-18T02:00:00Z",
            realized="up",
            evidence_ref="fixture-trade",
            gate_limit=limit,
        )
    scored = evaluate_paper_decision(
        ledger,
        lesson_id="D1",
        market="gold",
        decision_ts="2026-10-18T01:00:00Z",
        predicted="up",
        outcome_ts="2026-10-18T02:00:00Z",
        realized="down",
        evidence_ref="fixture-trade",
        gate_limit=limit,
    )
    assert scored.hit is False
    assert scored.retrieval_weight == 0.0
    assert scored.gate_limit == limit
    assert ledger.verify()
    ledger.close()
