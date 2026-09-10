"""P5 evidence-support gate — isolated SYNTHETIC_TEST_DATA. Not entailment."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.loop.contracts import CognitiveTask, TaskType  # noqa: E402
from architecture.cognitive.loop.support import (  # noqa: E402
    POLARITY_CONTRADICTS,
    POLARITY_SUPPORTS,
    SUPPORT_CONTEXT,
    SUPPORT_DIRECT,
    SUPPORT_NON,
    SUPPORT_UNKNOWN,
    classify_support,
)

NOW = 1_800_000_000.0
SUPPORT_DIR = ROOT / "architecture" / "cognitive" / "loop"
FORBIDDEN = {"discovery", "paper_trading", "telegram_ai", "engine"}


def _task(question: str) -> CognitiveTask:
    return CognitiveTask(
        task_id="sup-t",
        task_type=TaskType.ANALYZE.value,
        objective="p5",
        question=question,
        domain="software",
        requester="pytest",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
    )


def test_support_package_does_not_import_lane_a() -> None:
    path = SUPPORT_DIR / "support.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in FORBIDDEN
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in FORBIDDEN


def test_exact_support_is_direct() -> None:
    a = classify_support(
        "HTTP retries after timeout reduced request failures.",
        _task("Do retries after timeout help?"),
    )
    assert a.support_class == SUPPORT_DIRECT
    assert a.polarity == POLARITY_SUPPORTS
    assert a.may_support_positive() is True


def test_cafeteria_is_non_supporting_match() -> None:
    a = classify_support(
        "the lunch timeout retries were about cafeteria seating",
        _task("Do retries after timeout help?"),
    )
    assert a.lexical_match is True
    assert a.support_class == SUPPORT_NON
    assert a.may_support_positive() is False
    assert a.blocks_positive() is True


def test_kitchen_http_is_non_supporting_match() -> None:
    a = classify_support(
        "Retry behavior was tested in a kitchen queue system.",
        _task("Do HTTP retries improve reliability?"),
    )
    assert a.lexical_match is True
    assert a.support_class == SUPPORT_NON
    assert a.may_support_positive() is False


def test_generic_recover_is_not_a_lexical_candidate() -> None:
    a = classify_support("The system recovered.", _task("Do retries after timeout help?"))
    assert a.lexical_match is False
    assert a.may_support_positive() is False


def test_timeout_without_retry_outcome_is_context_or_unknown() -> None:
    exact = classify_support(
        "HTTP requests frequently timed out.",
        _task("Do retries after timeout help?"),
    )
    hit = classify_support(
        "HTTP requests frequently hit timeout.",
        _task("Do retries after timeout help?"),
    )
    assert exact.may_support_positive() is False
    assert hit.support_class in {SUPPORT_CONTEXT, SUPPORT_UNKNOWN, SUPPORT_NON}
    assert hit.may_support_positive() is False


def test_increased_failures_is_direct_contrary() -> None:
    a = classify_support(
        "Retries after timeout increased failures.",
        _task("Do retries after timeout help?"),
    )
    assert a.support_class == SUPPORT_DIRECT
    assert a.polarity == POLARITY_CONTRADICTS
    assert a.may_support_positive() is False


def test_adversarial_overlap_is_unknown_not_direct() -> None:
    a = classify_support(
        "HTTP connection timeout retries after the lunch window "
        "improved seating availability for the service team.",
        _task("Do HTTP connection retries after timeout improve service availability?"),
    )
    assert a.lexical_match is True
    assert a.support_class in {SUPPORT_UNKNOWN, SUPPORT_NON}
    assert a.support_class != SUPPORT_DIRECT
    assert a.may_support_positive() is False
    assert set(a.alien_tokens) & {"lunch", "seating", "team", "window"}


def test_did_not_reduce_is_not_positive_support() -> None:
    a = classify_support(
        "Retries after timeout did not reduce failures.",
        _task("Do retries after timeout reduce failures?"),
    )
    assert a.clause_force == "NEGATED"
    assert a.polarity != POLARITY_SUPPORTS
    assert a.may_support_positive() is False
    assert not (a.support_class == SUPPORT_DIRECT and a.polarity == POLARITY_SUPPORTS)


def test_increased_failures_remains_contradictory() -> None:
    a = classify_support(
        "Retries after timeout increased failures.",
        _task("Do retries after timeout reduce failures?"),
    )
    assert a.support_class == SUPPORT_DIRECT
    assert a.polarity == POLARITY_CONTRADICTS
    assert a.may_support_positive() is False


def test_unknown_whether_is_uncertain() -> None:
    a = classify_support(
        "It is unknown whether retries reduce failures.",
        _task("Do retries after timeout reduce failures?"),
    )
    assert a.polarity == "UNCERTAIN" or a.support_class == SUPPORT_UNKNOWN
    assert a.may_support_positive() is False


def test_entity_a_does_not_support_entity_b() -> None:
    a = classify_support(
        "Service A retries reduced failures.",
        _task("Do Service B retries reduce failures?"),
    )
    assert a.entity_state == "MISMATCH"
    assert a.may_support_positive() is False
    assert a.polarity != POLARITY_SUPPORTS or a.support_class != SUPPORT_DIRECT

