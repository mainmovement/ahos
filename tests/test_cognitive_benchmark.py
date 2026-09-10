"""P4.1 cognitive benchmark — isolated SYNTHETIC_TEST_DATA, no soak, no Lane A."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.benchmark.corpus import seed_corpus  # noqa: E402
from architecture.cognitive.benchmark.evaluator import (  # noqa: E402
    dumps_comparable,
    run_cognitive_benchmark,
)
from architecture.cognitive.benchmark.metrics import make_metric  # noqa: E402
from architecture.cognitive.benchmark.reproducibility import run_twice  # noqa: E402
from architecture.cognitive.benchmark.thresholds import BENCHMARK_VERSION  # noqa: E402
from architecture.cognitive.evaluation import refuse_fabricated_score  # noqa: E402
from architecture.cognitive.evaluation import FabricatedScoreError  # noqa: E402
from architecture.cognitive.memory.store import CognitiveMemoryStore, SoakBoundaryError  # noqa: E402

BENCH_DIR = ROOT / "architecture" / "cognitive" / "benchmark"
FORBIDDEN = {"discovery", "paper_trading", "telegram_ai", "engine"}


def test_benchmark_package_does_not_import_lane_a() -> None:
    for path in BENCH_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in FORBIDDEN
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in FORBIDDEN


def test_zero_denominator_is_not_measured() -> None:
    m = make_metric(
        "critic_scope_mismatch",
        name="x",
        definition="none",
        numerator=0.0,
        denominator=0.0,
        population="none",
        limitations="no field",
        n=0,
    )
    assert m.status == "NOT_MEASURED"
    assert m.value is None


def test_refuses_fabricated_intelligence_score() -> None:
    with pytest.raises(FabricatedScoreError):
        refuse_fabricated_score("agi_score", 0.999)


def test_corpus_refuses_soak_filenames(tmp_path: Path) -> None:
    with pytest.raises(SoakBoundaryError):
        CognitiveMemoryStore(tmp_path / "paper_trading.sqlite")
    store = CognitiveMemoryStore(tmp_path / "ahos_cognitive_memory.sqlite")
    idx = seed_corpus(store)
    assert len(idx.ids) >= 30
    assert store.get("BM-SW-TIMEOUT-FACT") is not None
    assert store.get("BM-SW-OLD-FACT") is not None
    assert store.get("BM-A-PRIV") is not None
    stale = store.get("BM-SW-OLD-FACT")
    assert stale is not None
    assert stale.status == "STALE"
    assert stale.observed_at != stale.created_at
    hist = store.history("BM-SW-SUPERSEDED-OLD")
    assert hist[0].statement.startswith("SYNTHETIC_TEST_DATA: service X is on revision 1")


def test_full_benchmark_metrics_and_reproducibility(tmp_path: Path) -> None:
    report = run_cognitive_benchmark(tmp_path / "a", git_sha="TEST")
    assert report.benchmark_version == BENCHMARK_VERSION
    assert report.data_label == "SYNTHETIC_TEST_DATA"
    mmap = report.metric_map()
    required = {
        "retrieval_precision",
        "retrieval_recall",
        "retrieval_f1",
        "recall_at_1",
        "recall_at_3",
        "recall_at_5",
        "recall_at_10",
        "match_reason_correctness",
        "contradiction_detection_rate",
        "contradiction_false_resolution_rate",
        "temporal_classification_accuracy",
        "stale_not_false",
        "unknown_refusal_accuracy",
        "false_certainty_rate",
        "unsupported_claim_rate",
        "failure_recall",
        "false_failure_application_rate",
        "lesson_reuse_rate",
        "correct_lesson_reuse_rate",
        "incorrect_lesson_application_rate",
        "no_memory_lesson_reuse",
        "namespace_isolation_rate",
        "namespace_leakage_rate",
        "cross_domain_consistency",
        "adversarial_resistance",
        "evidence_class_integrity",
        "hypothesis_falsification_present",
        "novelty_not_truth",
        "experiment_analysis_only",
        "critic_detection_rate",
        "typed_evidence_compliance",
        "critic_constraint_rate",
        "mode_specificity",
        "lesson_application_accuracy",
        "false_lesson_application_rate",
        "lexical_match_without_support_rate",
        "unsupported_positive_verdict_rate",
        "direct_support_positive_rate",
        "unknown_support_refusal_rate",
        "negation_positive_leak_rate",
        "negation_safety_rate",
        "entity_mismatch_positive_leak_rate",
        "entity_boundary_safety_rate",
    }
    assert required <= set(mmap)
    for mid in required:
        m = mmap[mid]
        if m.denominator == 0:
            assert m.status == "NOT_MEASURED"
        else:
            assert m.value is not None
            assert m.n >= 1 or m.status == "NOT_MEASURED"
        assert "99.9" not in m.limitations
    # integrity invariants
    assert mmap["namespace_leakage_rate"].numerator == 0
    assert mmap["namespace_isolation_rate"].value == 1.0
    assert mmap["unsupported_claim_rate"].numerator == 0
    assert mmap["contradiction_false_resolution_rate"].numerator == 0
    assert mmap["false_certainty_rate"].numerator == 0
    assert mmap["no_memory_lesson_reuse"].numerator == 0
    assert mmap["adversarial_resistance"].value == 1.0
    assert mmap["stale_not_false"].value == 1.0
    assert mmap["match_reason_correctness"].value == 1.0
    assert mmap["experiment_analysis_only"].value == 1.0
    assert mmap["novelty_not_truth"].value == 1.0
    twice = run_twice(tmp_path / "repro", git_sha="TEST")
    assert twice["equal"] is True
    assert dumps_comparable(twice["report_a"]) == dumps_comparable(twice["report_b"])
    payload = json.loads(json.dumps(report.as_dict(), sort_keys=True))
    assert payload["soak_protection"]["SOAK_DATABASE_TOUCHED"] == "NO"
    assert payload["case_counts"]["corpus_memories"] >= 30


def test_script_is_offline_and_present() -> None:
    text = (ROOT / "scripts" / "run_cognitive_benchmark.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in FORBIDDEN
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in FORBIDDEN
    assert "openai" not in text.lower()
    assert "anthropic" not in text.lower()
