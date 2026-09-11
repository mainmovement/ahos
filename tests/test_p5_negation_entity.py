"""P5 negation + entity safety — new synthetic cases. Not fixture copies.

Not entailment. Not NER. Isolated SYNTHETIC_TEST_DATA.
"""

from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.hypothesis import HypothesisStore  # noqa: E402
from architecture.cognitive.loop.binding import bind_context  # noqa: E402
from architecture.cognitive.loop.contracts import (  # noqa: E402
    CognitiveContext,
    CognitiveTask,
    CognitiveVerdict,
    ReasoningMode,
    RetrievedItem,
    TaskType,
)
from architecture.cognitive.loop.reason import reason  # noqa: E402
from architecture.cognitive.loop.support import (  # noqa: E402
    CLAUSE_NEGATED,
    CLAUSE_UNCERTAIN,
    ENTITY_AMBIGUOUS,
    ENTITY_MISMATCH,
    POLARITY_CONTRADICTS,
    POLARITY_NEGATED,
    POLARITY_SUPPORTS,
    POLARITY_UNCERTAIN,
    SUPPORT_DIRECT,
    classify_support,
    positive_support_eligible,
)
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402
from tests.observation_test_runtime import (  # noqa: E402
    TestCognitiveOrchestrator,
    bind_with_test_authority,
    reason_with_test_authority,
)
from tests.p5_grant_fixtures import authorize_retrieved_items  # noqa: E402
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType  # noqa: E402

NOW = 1_800_000_000.0
POSITIVE = {
    CognitiveVerdict.SUPPORTED.value,
    CognitiveVerdict.WEAKLY_SUPPORTED.value,
}
PROD_LOOP = ROOT / "architecture" / "cognitive" / "loop"
FORBIDDEN_PROD_TOKENS = (
    "cafeteria",
    "kitchen",
    "lunch",
    "service a",
    "service b",
    "p5-",
    "bm-",
)


def _task(question: str, *, domain: str = "software", **kwargs) -> CognitiveTask:
    base = dict(
        task_id="neg-ent",
        task_type=TaskType.ANALYZE.value,
        objective="p5-safety",
        question=question,
        domain=domain,
        requester="pytest",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=False,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _item(mid: str, statement: str, **kwargs) -> RetrievedItem:
    return RetrievedItem(
        memory_id=mid,
        revision=1,
        statement=statement,
        match_reasons=("test",),
        evidence_class="DIRECT_OBSERVATION",
        memory_type=kwargs.get("memory_type", MemoryType.EPISODIC.value),
        epistemic_kind=kwargs.get("kind", EpistemicKind.OBSERVED_FACT.value),
        status=kwargs.get("status", "ACTIVE"),
        domain=kwargs.get("domain", "software"),
        source_id="pytest",
        agent_namespace="",
        observed_at=kwargs.get("observed_at", NOW - 20),
        created_at=NOW - 10,
    )


def _ctx(*items: RetrievedItem, contra: bool = False) -> CognitiveContext:
    facts = tuple(
        i
        for i in items
        if i.epistemic_kind
        in {EpistemicKind.OBSERVED_FACT.value, EpistemicKind.DERIVED_FACT.value}
        and i.memory_type != MemoryType.FAILURE.value
    )
    edges = ()
    if contra and len(items) >= 2:
        edges = (
            {
                "edge_id": "e",
                "from_id": items[0].memory_id,
                "to_id": items[1].memory_id,
                "relation": "CONTRADICTS",
            },
        )
    return CognitiveContext(
        facts=facts,
        inferences=(),
        hypotheses=(),
        predictions=(),
        opinions=(),
        simulations=(),
        experiments=(),
        outcomes=(),
        contradictions=edges,
        failures=(),
        procedures=(),
        lessons=(),
        unknowns=() if items else ("empty",),
        excluded=(),
        contradiction_present=bool(edges),
        context_incomplete=not items,
        token_estimate=len(items),
    )


def _live(statement: str, question: str, *, domain: str = "software", **item_kw):
    task = _task(question, domain=domain)
    item = _item("m1", statement, domain=domain, **item_kw)
    ctx = _ctx(item)
    store = authorize_retrieved_items(item)
    binds = bind_with_test_authority(ctx, task, store=store, now=NOW)
    v, _, _, _, _ = reason_with_test_authority(
        task, ctx, store=store, retrieved_ids=["m1"], now=NOW
    )
    return classify_support(statement, task), binds[0], v


def _assert_not_positive(assessment, binding, verdict, *, label: str) -> None:
    assert assessment.may_support_positive() is False, label
    assert positive_support_eligible(assessment) is False, label
    assert binding.may_support_task() is False, label
    assert not (
        assessment.support_class == SUPPORT_DIRECT
        and assessment.polarity == POLARITY_SUPPORTS
    ), label
    assert verdict not in POSITIVE, (label, verdict)


# --- 20 negation cases across four domains ---
NEGATION_CASES = [
    ("sw-did-not", "software", "Retries after timeout did not reduce failures.", "Do retries after timeout reduce failures?"),
    ("sw-does-not", "software", "Retry after timeout does not reduce failures.", "Do retries after timeout reduce failures?"),
    ("sw-do-not", "software", "Retries after timeout do not reduce failures.", "Do retries after timeout reduce failures?"),
    ("sw-not-reduced", "software", "Failures were not reduced by retries after timeout.", "Do retries after timeout reduce failures?"),
    ("sw-never", "software", "Retries after timeout never reduced failures.", "Do retries after timeout reduce failures?"),
    ("fin-failed-to", "finance", "Token retries after timeout failed to reduce failures.", "Do retries after timeout reduce failures?"),
    ("fin-cannot", "finance", "Token retries after timeout cannot reduce failures.", "Do retries after timeout reduce failures?"),
    ("fin-unable", "finance", "Token retries after timeout were unable to reduce failures.", "Do retries after timeout reduce failures?"),
    ("fin-without", "finance", "The worker retried after timeout without reducing failures.", "Do retries after timeout reduce failures?"),
    ("fin-no-evidence", "finance", "There is no evidence that retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
    ("sci-unknown", "science", "It is unknown whether calibration retries reduce failures.", "Do retries after timeout reduce failures?"),
    ("sci-unclear", "science", "It is unclear whether retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
    ("sci-not-known", "science", "It is not known whether retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
    ("sci-didnt", "science", "Measurement retries after timeout didn't reduce failures.", "Do retries after timeout reduce failures?"),
    ("sci-dont", "science", "Calibration retries after timeout don't reduce failures.", "Do retries after timeout reduce failures?"),
    ("ops-never", "operations", "Queue retries after timeout never reduced failures.", "Do retries after timeout reduce failures?"),
    ("ops-failed-to", "operations", "Queue retries after timeout failed to reduce failures.", "Do retries after timeout reduce failures?"),
    ("ops-cannot", "operations", "Queue retries after timeout cannot reduce failures.", "Do retries after timeout reduce failures?"),
    ("ops-no-evidence", "operations", "There is no evidence that queue retries reduce failures.", "Do retries after timeout reduce failures?"),
    ("ops-unknown", "operations", "It is unknown whether queue retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
]


# --- 20 entity-boundary cases ---
ENTITY_CASES = [
    ("ent-a-b", "Service A retries after timeout reduced failures.", "Do Service B retries after timeout reduce failures?"),
    ("ent-b-a", "Service B retries after timeout reduced failures.", "Do Service A retries after timeout reduce failures?"),
    ("ent-x-y", "Component X retries after timeout reduced failures.", "Do Component Y retries after timeout reduce failures?"),
    ("ent-y-x", "Node Y retries after timeout reduced failures.", "Do Node X retries after timeout reduce failures?"),
    ("ent-a1-b1", "Replica A1 retries after timeout reduced failures.", "Do Replica B1 retries after timeout reduce failures?"),
    ("ent-b1-a1", "Replica B1 retries after timeout reduced failures.", "Do Replica A1 retries after timeout reduce failures?"),
    ("ent-c2-d2", "Worker C2 retries after timeout reduced failures.", "Do Worker D2 retries after timeout reduce failures?"),
    ("ent-alpha-bravo", "Alpha retries after timeout reduced failures.", "Do Bravo retries after timeout reduce failures?"),
    ("ent-bravo-alpha", "Bravo retries after timeout reduced failures.", "Do Alpha retries after timeout reduce failures?"),
    ("ent-delta-echo", "Delta retries after timeout reduced failures.", "Do Echo retries after timeout reduce failures?"),
    ("ent-hyphen-ab", "Service-A retries after timeout reduced failures.", "Do Service-B retries after timeout reduce failures?"),
    ("ent-hyphen-ba", "Cluster-B retries after timeout reduced failures.", "Do Cluster-A retries after timeout reduce failures?"),
    ("ent-hyphen-xy", "Node-X retries after timeout reduced failures.", "Do Node-Y retries after timeout reduce failures?"),
    ("ent-under-ab", "service_alpha retries after timeout reduced failures.", "Do service_beta retries after timeout reduce failures?"),
    ("ent-under-ba", "service_beta retries after timeout reduced failures.", "Do service_alpha retries after timeout reduce failures?"),
    ("ent-under-xy", "queue_west retries after timeout reduced failures.", "Do queue_east retries after timeout reduce failures?"),
    ("ent-mix-a-alpha", "Service A retries after timeout reduced failures.", "Do Alpha retries after timeout reduce failures?"),
    ("ent-mix-a1-b", "Node A1 retries after timeout reduced failures.", "Do Node B retries after timeout reduce failures?"),
    ("ent-hyphen-under", "Service-A retries after timeout reduced failures.", "Do service_beta retries after timeout reduce failures?"),
    ("ent-named-short", "Orion retries after timeout reduced failures.", "Do Vega retries after timeout reduce failures?"),
]


# --- 10 combined polarity × identity / temporal ---
COMBINED_CASES = [
    (
        "comb-neg-mismatch",
        "Service A retries after timeout did not reduce failures.",
        "Do Service B retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-contra-mismatch",
        "Service A retries after timeout increased failures.",
        "Do Service B retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-uncertain-mismatch",
        "It is unknown whether Service A retries reduce failures.",
        "Do Service B retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-stale-neg",
        "Retries after timeout did not reduce failures.",
        "Do retries after timeout reduce failures?",
        {"status": "STALE"},
    ),
    (
        "comb-unknown-neg",
        "It is unknown whether retries after timeout did not reduce failures.",
        "Do retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-neg-hyphen",
        "Service-A retries after timeout never reduced failures.",
        "Do Service-B retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-contra-alpha",
        "Alpha retries after timeout increased failures.",
        "Do Bravo retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-no-evidence-entity",
        "There is no evidence that Node X retries reduce failures.",
        "Do Node Y retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-unable-underscore",
        "service_alpha retries after timeout were unable to reduce failures.",
        "Do service_beta retries after timeout reduce failures?",
        {},
    ),
    (
        "comb-stale-mismatch",
        "Replica A1 retries after timeout reduced failures.",
        "Do Replica B1 retries after timeout reduce failures?",
        {"status": "STALE"},
    ),
]


# --- 30 adversarial high-overlap non-positives ---
ADVERSARIAL_CASES = [
    ("adv-neg-1", "Retries after timeout did not reduce request failures.", "Do retries after timeout reduce failures?"),
    ("adv-neg-2", "Retries after timeout does not reduce failures.", "Do retries after timeout reduce failures?"),
    ("adv-neg-3", "Retries after timeout do not reduce failures.", "Do retries after timeout reduce failures?"),
    ("adv-neg-4", "Retries after timeout never reduced request failures.", "Do retries after timeout reduce failures?"),
    ("adv-neg-5", "Retries after timeout failed to reduce request failures.", "Do retries after timeout reduce failures?"),
    ("adv-neg-6", "Retries after timeout cannot reduce request failures.", "Do retries after timeout reduce failures?"),
    ("adv-neg-7", "Retries after timeout were unable to reduce failures.", "Do retries after timeout reduce failures?"),
    ("adv-neg-8", "The process retried after timeout without reducing failures.", "Do retries after timeout reduce failures?"),
    ("adv-unc-1", "It is unknown whether retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
    ("adv-unc-2", "There is no evidence that retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
    ("adv-unc-3", "Uncertain whether retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
    ("adv-con-1", "Retries after timeout increased request failures.", "Do retries after timeout reduce failures?"),
    ("adv-con-2", "Retries after timeout worsened request failures.", "Do retries after timeout reduce failures?"),
    ("adv-con-3", "Retries after timeout made failures worse.", "Do retries after timeout reduce failures?"),
    ("adv-ent-1", "Service A retries after timeout reduced request failures.", "Do Service B retries after timeout reduce failures?"),
    ("adv-ent-2", "Cluster X retries after timeout reduced request failures.", "Do Cluster Y retries after timeout reduce failures?"),
    ("adv-ent-3", "Worker A1 retries after timeout reduced request failures.", "Do Worker B1 retries after timeout reduce failures?"),
    ("adv-ent-4", "Helios retries after timeout reduced request failures.", "Do Selene retries after timeout reduce failures?"),
    ("adv-ent-5", "Service-A retries after timeout reduced request failures.", "Do Service-B retries after timeout reduce failures?"),
    ("adv-ent-6", "service_alpha retries after timeout reduced request failures.", "Do service_beta retries after timeout reduce failures?"),
    ("adv-obj-1", "Retries after timeout reduced latency.", "Do retries after timeout reduce failures?"),
    ("adv-obj-2", "Retries after timeout reduced disk errors.", "Do retries after timeout reduce failures?"),
    ("adv-dir-1", "Failures reduced retries after timeout.", "Do retries after timeout reduce failures?"),
    ("adv-dir-2", "Timeout retries increased recovery failures.", "Do retries after timeout reduce failures?"),
    ("adv-out-1", "Retries after timeout reduced logging volume.", "Do retries after timeout reduce failures?"),
    ("adv-out-2", "Retries after timeout reduced queue depth.", "Do retries after timeout reduce failures?"),
    ("adv-mix-1", "Service A retries after timeout did not reduce failures.", "Do Service B retries after timeout reduce failures?"),
    ("adv-mix-2", "Alpha retries after timeout increased failures.", "Do Bravo retries after timeout reduce failures?"),
    ("adv-mix-3", "It is unknown whether Service-A retries reduce failures.", "Do Service-B retries after timeout reduce failures?"),
    ("adv-mix-4", "There is no evidence that Node X retries reduce failures.", "Do Node Y retries after timeout reduce failures?"),
]


WRITE_BACK_CASES = [
    ("wb-neg", "Retries after timeout did not reduce failures.", "Do retries after timeout reduce failures?"),
    ("wb-con", "Retries after timeout increased failures.", "Do retries after timeout reduce failures?"),
    ("wb-unk", "It is unknown whether retries after timeout reduce failures.", "Do retries after timeout reduce failures?"),
    ("wb-ent", "Service A retries after timeout reduced failures.", "Do Service B retries after timeout reduce failures?"),
    ("wb-amb", "Retries after timeout reduced failures on an unspecified replica.", "Do Replica A1 retries after timeout reduce failures?"),
]


def test_positive_control_still_allows_weak_support() -> None:
    a, b, v = _live(
        "Retries after timeout reduced failures.",
        "Do retries after timeout reduce failures?",
    )
    assert a.support_class == SUPPORT_DIRECT
    assert a.polarity == POLARITY_SUPPORTS
    assert a.clause_force not in {CLAUSE_NEGATED, CLAUSE_UNCERTAIN}
    assert a.may_support_positive() is True
    assert b.may_support_task() is True
    assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value


@pytest.mark.parametrize("label,domain,statement,question", NEGATION_CASES, ids=[c[0] for c in NEGATION_CASES])
def test_negation_matrix_never_positive(label, domain, statement, question) -> None:
    a, b, v = _live(statement, question, domain=domain)
    _assert_not_positive(a, b, v, label=label)
    assert a.clause_force in {CLAUSE_NEGATED, CLAUSE_UNCERTAIN} or a.polarity in {
        POLARITY_NEGATED,
        POLARITY_UNCERTAIN,
        POLARITY_CONTRADICTS,
    }


@pytest.mark.parametrize("label,statement,question", ENTITY_CASES, ids=[c[0] for c in ENTITY_CASES])
def test_entity_matrix_never_positive(label, statement, question) -> None:
    a, b, v = _live(statement, question)
    _assert_not_positive(a, b, v, label=label)
    assert a.entity_state in {ENTITY_MISMATCH, ENTITY_AMBIGUOUS} or a.may_support_positive() is False


@pytest.mark.parametrize(
    "label,statement,question,item_kw",
    COMBINED_CASES,
    ids=[c[0] for c in COMBINED_CASES],
)
def test_combined_matrix_never_positive(label, statement, question, item_kw) -> None:
    a, b, v = _live(statement, question, **item_kw)
    _assert_not_positive(a, b, v, label=label)


@pytest.mark.parametrize("label,statement,question", ADVERSARIAL_CASES, ids=[c[0] for c in ADVERSARIAL_CASES])
def test_adversarial_positive_safety(label, statement, question) -> None:
    a, b, v = _live(statement, question)
    _assert_not_positive(a, b, v, label=label)


def test_suite_counts_meet_minimums() -> None:
    assert len(NEGATION_CASES) >= 20
    assert len(ENTITY_CASES) >= 20
    assert len(COMBINED_CASES) >= 10
    assert len(NEGATION_CASES) + len(ENTITY_CASES) + len(COMBINED_CASES) >= 50
    assert len(ADVERSARIAL_CASES) >= 30


def test_polarity_is_load_bearing_before_verdict() -> None:
    statement = "Retries after timeout did not reduce failures."
    question = "Do retries after timeout reduce failures?"
    task = _task(question)
    assessment = classify_support(statement, task)
    assert assessment.clause_force == CLAUSE_NEGATED
    assert assessment.may_support_positive() is False
    binds = bind_context(_ctx(_item("m1", statement)), task)
    assert binds[0].may_support_task() is False
    assert binds[0].clause_force == CLAUSE_NEGATED
    v, _, _, _, _ = reason(task, _ctx(_item("m1", statement)), retrieved_ids=["m1"])
    assert v not in POSITIVE
    assert v in {
        CognitiveVerdict.CONTESTED.value,
        CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
        CognitiveVerdict.UNRESOLVED.value,
    }


def test_entity_mismatch_is_not_treated_as_contradiction_of_other_entity() -> None:
    a, b, v = _live(
        "Service A retries after timeout reduced failures.",
        "Do Service B retries after timeout reduce failures?",
    )
    assert a.entity_state == ENTITY_MISMATCH
    assert b.contradicts_task() is False
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value


def test_negated_same_entity_can_contest_but_not_support() -> None:
    a, b, v = _live(
        "Retries after timeout did not reduce failures.",
        "Do retries after timeout reduce failures?",
    )
    assert a.may_support_positive() is False
    assert v not in POSITIVE
    if a.support_class == SUPPORT_DIRECT and a.polarity == POLARITY_NEGATED:
        assert b.contradicts_task() is True
        assert v == CognitiveVerdict.CONTESTED.value


def test_ambiguous_entity_is_not_positive() -> None:
    a = classify_support(
        "Retries after timeout reduced failures.",
        _task("Do Replica A1 retries after timeout reduce failures?"),
    )
    assert a.entity_state == ENTITY_AMBIGUOUS
    assert a.may_support_positive() is False


@pytest.mark.parametrize("label,statement,question", WRITE_BACK_CASES, ids=[c[0] for c in WRITE_BACK_CASES])
def test_write_back_does_not_mint_reusable_positive(tmp_path: Path, label, statement, question) -> None:
    mem = CognitiveMemoryStore(tmp_path / f"mem-{label}.sqlite")
    hyp = HypothesisStore(tmp_path / f"hyp-{label}.jsonl")
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=tmp_path / f"exp-{label}.jsonl")
    mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=f"SYNTHETIC_TEST_DATA: {statement}",
        source_type=SourceType.SYSTEM,
        source_id=label,
        source_location="tests/test_p5_negation_entity.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 40,
        created_at=NOW - 30,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    result = orch.run(
        _task(
            question,
            task_id=f"wb-{label}",
            write_back=True,
            task_type=TaskType.INVESTIGATE.value,
        ),
        now=NOW,
    )
    assert result.verdict not in POSITIVE, (label, result.verdict)
    assert result.hypothesis_id == ""
    assert result.lesson_memory_id == ""
    assert mem.find_by_type(MemoryType.HYPOTHESIS) == []
    lessons = [
        rec
        for rec in mem.find_by_type(MemoryType.SEMANTIC)
        if rec.epistemic_kind == EpistemicKind.LESSON.value
        and rec.statement.startswith("LESSON ")
    ]
    inferences = [
        rec
        for rec in mem.find_by_type(MemoryType.SEMANTIC)
        if rec.epistemic_kind == EpistemicKind.INFERENCE.value
        and rec.statement.startswith("INFERENCE ")
    ]
    assert lessons == []
    assert inferences == []


def test_unresolved_contested_write_back_is_not_reusable(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem-contested.sqlite")
    hyp = HypothesisStore(tmp_path / "hyp-contested.jsonl")
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=tmp_path / "exp-contested.jsonl")
    a = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="SYNTHETIC_TEST_DATA: retries after timeout reduced failures.",
        source_type=SourceType.SYSTEM,
        source_id="pos",
        source_location="tests/test_p5_negation_entity.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 40,
        created_at=NOW - 30,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    b = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="SYNTHETIC_TEST_DATA: retries after timeout increased failures.",
        source_type=SourceType.SYSTEM,
        source_id="neg",
        source_location="tests/test_p5_negation_entity.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 39,
        created_at=NOW - 29,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    mem.contradict(a.memory_id, b.memory_id, reason="seeded", now=NOW - 1)
    result = orch.run(
        _task(
            "Do retries after timeout reduce failures?",
            task_id="wb-contested",
            write_back=True,
            task_type=TaskType.INVESTIGATE.value,
        ),
        now=NOW,
    )
    assert result.verdict not in POSITIVE
    assert result.hypothesis_id == ""
    assert result.lesson_memory_id == ""


def _code_without_comments(path: Path) -> str:
    src = path.read_bytes()
    out: list[str] = []
    for tok in tokenize.tokenize(io.BytesIO(src).readline):
        if tok.type in {tokenize.COMMENT, tokenize.NL}:
            continue
        if tok.type == tokenize.STRING and tok.start[0] != tok.end[0]:
            continue
        if tok.type == tokenize.STRING and tok.start[1] == 0:
            continue
        out.append(tok.string)
    return " ".join(out).lower()


def test_production_loop_has_no_fixture_specific_rules() -> None:
    hits: list[str] = []
    comment_hits: list[str] = []
    needles = ("cafeteria", "kitchen", "lunch", "service a", "service b")
    for path in sorted(PROD_LOOP.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        executable = _code_without_comments(path)
        for needle in needles:
            if needle in executable:
                hits.append(f"{path.name}:exec:{needle}")
            elif needle in lowered:
                comment_hits.append(f"{path.name}:comment:{needle}")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                dumped = ast.dump(node).lower()
                if "case_id" in dumped and any(x in dumped for x in ("p5-", "bm-")):
                    hits.append(f"{path.name}:case_id_compare")
    assert hits == [], hits
    _ = comment_hits


def test_adversarial_unsupported_positive_rate_is_zero() -> None:
    leaks = 0
    n = 0
    for label, statement, question in ADVERSARIAL_CASES:
        _, _, v = _live(statement, question)
        n += 1
        if v in POSITIVE:
            leaks += 1
            raise AssertionError(f"positive leak {label} verdict={v}")
    rate = leaks / n
    assert n > 0
    assert rate == 0.0
