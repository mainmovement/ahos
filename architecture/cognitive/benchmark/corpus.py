"""Labeled SYNTHETIC_TEST_DATA corpus. Distractors are intentional.

Stable memory_ids (BM-*) so expected sets are reproducible.
Never mixed with soak evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType

NOW = 1_800_000_000.0
DATA_LABEL = "SYNTHETIC_TEST_DATA"
HYP_TIMEOUT = "HYP-BENCH-TIMEOUT"
EXP_TIMEOUT = "EXP-BENCH-TIMEOUT"


@dataclass
class CorpusIndex:
    ids: dict[str, str]
    meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    now: float = NOW

    def id(self, logical: str) -> str:
        return self.ids[logical]


def _remember(
    store: CognitiveMemoryStore,
    *,
    logical: str,
    statement: str,
    domain: str,
    kind: EpistemicKind,
    memory_type: MemoryType = MemoryType.EPISODIC,
    observed_at: float | None = NOW - 100.0,
    created_at: float = NOW - 50.0,
    valid_until: float | None = None,
    agent_id: str = "",
    agent_namespace: str = "",
    hypothesis_id: str = "",
    experiment_id: str = "",
    prediction_id: str = "",
    extra: dict[str, Any] | None = None,
) -> str:
    payload = {"data_label": DATA_LABEL, "logical_id": logical, **(extra or {})}
    rec = store.remember(
        memory_id=logical,
        memory_type=memory_type,
        epistemic_kind=kind,
        statement=statement,
        source_type=SourceType.SYSTEM,
        source_id=f"corpus-{logical}",
        source_location="architecture.cognitive.benchmark.corpus",
        producer="p4.1-benchmark",
        producer_version="p4.1.0",
        domain=domain,
        context=DATA_LABEL,
        observed_at=observed_at,
        created_at=created_at,
        valid_until=valid_until,
        agent_id=agent_id,
        agent_namespace=agent_namespace,
        hypothesis_id=hypothesis_id,
        experiment_id=experiment_id,
        prediction_id=prediction_id,
        payload=payload,
    )
    return rec.memory_id


def seed_corpus(store: CognitiveMemoryStore, *, now: float = NOW) -> CorpusIndex:
    ids: dict[str, str] = {}
    meta: dict[str, dict[str, Any]] = {}

    def add(logical: str, **kwargs: Any) -> None:
        ids[logical] = _remember(store, logical=logical, **kwargs)
        meta[logical] = {"domain": kwargs["domain"], "kind": kwargs["kind"].value}

    add(
        "BM-SW-TIMEOUT-FACT",
        statement="SYNTHETIC_TEST_DATA: HTTP timeout recovered after retries.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        observed_at=now - 80.0,
        created_at=now - 40.0,
    )
    add(
        "BM-SW-TIMEOUT-LESSON",
        statement="SYNTHETIC_TEST_DATA LESSON: retries after HTTP timeout recovered the request.",
        domain="software",
        kind=EpistemicKind.LESSON,
        memory_type=MemoryType.SEMANTIC,
        observed_at=now - 70.0,
        created_at=now - 35.0,
    )
    add(
        "BM-SW-TIMEOUT-FAIL",
        statement="SYNTHETIC_TEST_DATA FAILURE: deploy without timeout retry failed.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        memory_type=MemoryType.FAILURE,
        extra={"failure_type": "timeout_retry", "component": "http_client"},
    )
    add(
        "BM-SW-TIMEOUT-HYP",
        statement="SYNTHETIC_TEST_DATA HYPOTHESIS: retries after timeout reduce error rate.",
        domain="software",
        kind=EpistemicKind.HYPOTHESIS,
        memory_type=MemoryType.HYPOTHESIS,
        hypothesis_id=HYP_TIMEOUT,
    )
    add(
        "BM-SW-TIMEOUT-EXP",
        statement="SYNTHETIC_TEST_DATA EXPERIMENT: timeout retry analysis INSUFFICIENT_DATA.",
        domain="software",
        kind=EpistemicKind.INFERENCE,
        memory_type=MemoryType.EXPERIMENT,
        experiment_id=EXP_TIMEOUT,
        hypothesis_id=HYP_TIMEOUT,
    )
    add(
        "BM-SW-TIMEOUT-INFER",
        statement="SYNTHETIC_TEST_DATA INFERENCE: retries likely helped the timeout path.",
        domain="software",
        kind=EpistemicKind.INFERENCE,
    )
    add(
        "BM-SW-TIMEOUT-PROC",
        statement="SYNTHETIC_TEST_DATA PROCEDURE: on HTTP timeout, retry twice then fail closed.",
        domain="software",
        kind=EpistemicKind.PROCEDURE,
        memory_type=MemoryType.PROCEDURAL,
    )
    add(
        "BM-SW-COMPILE-DIST",
        statement="SYNTHETIC_TEST_DATA: compiler warning unused import in module alpha.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SW-LINT-DIST",
        statement="SYNTHETIC_TEST_DATA: linter flagged line length in module beta.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SW-OPINION",
        statement="SYNTHETIC_TEST_DATA OPINION: timeouts never happen in production.",
        domain="software",
        kind=EpistemicKind.OPINION,
    )
    add(
        "BM-SW-PRED",
        statement="SYNTHETIC_TEST_DATA PREDICTION: timeouts will stop tomorrow.",
        domain="software",
        kind=EpistemicKind.PREDICTION,
        prediction_id="PRED-BENCH-TIMEOUT",
        extra={"confidence_claim": "high"},
    )
    add(
        "BM-SW-SIM",
        statement="SYNTHETIC_TEST_DATA SIMULATION: simulated timeout storm recovered.",
        domain="software",
        kind=EpistemicKind.SIMULATION,
    )
    add(
        "BM-SW-OLD-FACT",
        statement="SYNTHETIC_TEST_DATA historical: timeout rate was 12 percent last quarter.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        observed_at=now - 10_000.0,
        created_at=now - 20.0,
        valid_until=now - 1_000.0,
    )
    add(
        "BM-SW-FRESH-FACT",
        statement="SYNTHETIC_TEST_DATA current: timeout rate is 2 percent this hour.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        observed_at=now - 10.0,
        created_at=now - 5.0,
    )
    add(
        "BM-SW-UNKNOWN-AGE",
        statement="SYNTHETIC_TEST_DATA: timeout note with unknown event time.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        observed_at=None,
        created_at=now - 15.0,
    )
    add(
        "BM-SW-SUPERSEDED-OLD",
        statement="SYNTHETIC_TEST_DATA: service X is on revision 1 (later superseded).",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        observed_at=now - 500.0,
        created_at=now - 400.0,
    )
    add(
        "BM-SW-CONTRA-A",
        statement="SYNTHETIC_TEST_DATA: condition X occurred on node seven.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SW-CONTRA-B",
        statement="SYNTHETIC_TEST_DATA: condition X did not occur on node seven.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        created_at=now - 45.0,
    )
    add(
        "BM-SCI-FACT",
        statement="SYNTHETIC_TEST_DATA: lab measurement recovered after calibration retries.",
        domain="science",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SCI-LESSON",
        statement="SYNTHETIC_TEST_DATA LESSON: calibration retries recovered the measurement.",
        domain="science",
        kind=EpistemicKind.LESSON,
        memory_type=MemoryType.SEMANTIC,
    )
    add(
        "BM-SCI-DIST",
        statement="SYNTHETIC_TEST_DATA: telescope pointing error of 0.2 arcsec.",
        domain="science",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SCI-CONTRA-A",
        statement="SYNTHETIC_TEST_DATA: measurement supports claim X.",
        domain="science",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SCI-CONTRA-B",
        statement="SYNTHETIC_TEST_DATA: measurement contradicts claim X.",
        domain="science",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SCI-HYP",
        statement="SYNTHETIC_TEST_DATA HYPOTHESIS: calibration drift caused the outlier.",
        domain="science",
        kind=EpistemicKind.HYPOTHESIS,
        memory_type=MemoryType.HYPOTHESIS,
        hypothesis_id="HYP-BENCH-SCI",
    )
    add(
        "BM-SCI-PRED",
        statement="SYNTHETIC_TEST_DATA PREDICTION: next run will match the model.",
        domain="science",
        kind=EpistemicKind.PREDICTION,
        prediction_id="PRED-BENCH-SCI",
    )
    add(
        "BM-FIN-FACT",
        statement="SYNTHETIC_TEST_DATA: paper token observation recovered after retries.",
        domain="finance",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-FIN-LESSON",
        statement="SYNTHETIC_TEST_DATA LESSON: paper retries recovered the token observation.",
        domain="finance",
        kind=EpistemicKind.LESSON,
        memory_type=MemoryType.SEMANTIC,
    )
    add(
        "BM-FIN-DIST",
        statement="SYNTHETIC_TEST_DATA: unrelated liquidity note for a different pair.",
        domain="finance",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-FIN-PRED",
        statement="SYNTHETIC_TEST_DATA PREDICTION: paper price will double tomorrow.",
        domain="finance",
        kind=EpistemicKind.PREDICTION,
        prediction_id="PRED-BENCH-FIN",
        extra={"confidence_claim": "high"},
    )
    add(
        "BM-FIN-OPINION",
        statement="SYNTHETIC_TEST_DATA OPINION: this paper token is obviously safe.",
        domain="finance",
        kind=EpistemicKind.OPINION,
    )
    add(
        "BM-OPS-FACT",
        statement="SYNTHETIC_TEST_DATA: queue depth recovered after retries.",
        domain="operations",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-OPS-LESSON",
        statement="SYNTHETIC_TEST_DATA LESSON: retries recovered queue depth.",
        domain="operations",
        kind=EpistemicKind.LESSON,
        memory_type=MemoryType.SEMANTIC,
    )
    add(
        "BM-OPS-FAIL",
        statement="SYNTHETIC_TEST_DATA FAILURE: deploy checklist missing rollback.",
        domain="operations",
        kind=EpistemicKind.OBSERVED_FACT,
        memory_type=MemoryType.FAILURE,
        extra={"failure_type": "deploy_checklist", "component": "ops"},
    )
    add(
        "BM-OPS-DIST",
        statement="SYNTHETIC_TEST_DATA: badge reader firmware version 3.",
        domain="operations",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-OPS-EXP",
        statement="SYNTHETIC_TEST_DATA EXPERIMENT: rollback drill INSUFFICIENT_DATA.",
        domain="operations",
        kind=EpistemicKind.INFERENCE,
        memory_type=MemoryType.EXPERIMENT,
        experiment_id="EXP-BENCH-OPS",
    )
    add(
        "BM-A-PRIV",
        statement="SYNTHETIC_TEST_DATA private A note about timeout retries.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        agent_id="agent_A",
        agent_namespace="agent_A",
    )
    add(
        "BM-B-PRIV",
        statement="SYNTHETIC_TEST_DATA private B note about timeout retries.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        agent_id="agent_B",
        agent_namespace="agent_B",
    )
    add(
        "BM-SHARED",
        statement="SYNTHETIC_TEST_DATA shared note about timeout retries.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
    )
    add(
        "BM-SW-TIMEOUT-LOOKALIKE",
        statement="SYNTHETIC_TEST_DATA: HTTP timeout poster on the office wall.",
        domain="software",
        kind=EpistemicKind.OBSERVED_FACT,
        extra={"distractor": True, "lookalike": True},
    )
    add(
        "BM-GEN-EMPTYISH",
        statement="SYNTHETIC_TEST_DATA: unrelated general remark about weather.",
        domain="general",
        kind=EpistemicKind.OPINION,
    )

    store.contradict(
        "BM-SW-CONTRA-A",
        "BM-SW-CONTRA-B",
        reason="benchmark seeded opposing observations",
        now=now,
    )
    store.contradict(
        "BM-SCI-CONTRA-A",
        "BM-SCI-CONTRA-B",
        reason="benchmark seeded opposing measurements",
        now=now,
    )
    successor = store.supersede(
        "BM-SW-SUPERSEDED-OLD",
        statement="SYNTHETIC_TEST_DATA: service X is on revision 2 (supersedes revision 1).",
        correction_reason="benchmark supersession",
        producer="p4.1-benchmark",
        now=now,
    )
    ids["BM-SW-SUPERSEDED-NEW"] = successor.memory_id
    meta["BM-SW-SUPERSEDED-NEW"] = {"domain": "software", "kind": "OBSERVED_FACT"}
    store.apply_decay(now=now)
    stale = store.get("BM-SW-OLD-FACT")
    meta["BM-SW-OLD-FACT"]["status"] = stale.status if stale else ""
    meta["BM-SW-OLD-FACT"]["stale_is_not_false"] = True
    return CorpusIndex(ids=ids, meta=meta, now=now)


TIMEOUT_RELEVANT = (
    "BM-SW-TIMEOUT-FACT",
    "BM-SW-TIMEOUT-LESSON",
    "BM-SW-TIMEOUT-FAIL",
    "BM-SW-TIMEOUT-HYP",
    "BM-SW-TIMEOUT-EXP",
    "BM-SW-TIMEOUT-INFER",
    "BM-SW-TIMEOUT-PROC",
)
SOFTWARE_DEBUG_LESSONS = ("BM-SW-TIMEOUT-LESSON",)
SOFTWARE_DISTRACTORS = (
    "BM-SW-COMPILE-DIST",
    "BM-SW-LINT-DIST",
    "BM-SW-TIMEOUT-LOOKALIKE",
)
