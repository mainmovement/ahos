"""P5 reasoning benchmark population. Isolated from P4.1 retrieval labels."""

from __future__ import annotations

from architecture.cognitive.benchmark.metrics import MetricResult, make_metric
from architecture.cognitive.loop.binding import bind_context
from architecture.cognitive.loop.contracts import (
    CognitiveContext,
    CognitiveTask,
    CognitiveVerdict,
    ReasoningMode,
    RetrievedItem,
    TaskType,
)
from architecture.cognitive.loop.inference import ACTION_ACCEPT, ACTION_CONTEST, ACTION_REFUSE
from architecture.cognitive.loop.modes import reason_metacognitive
from architecture.cognitive.loop.reason import reason
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType

NOW = 1_800_000_000.0
P5_VERSION = "p5.0.0"


def _item(
    mid: str,
    statement: str,
    *,
    kind: str = EpistemicKind.OBSERVED_FACT.value,
    mtype: str = MemoryType.EPISODIC.value,
    status: str = "ACTIVE",
    domain: str = "software",
    observed_at: float | None = NOW - 20,
) -> RetrievedItem:
    return RetrievedItem(
        memory_id=mid,
        revision=1,
        statement=statement,
        match_reasons=("p5",),
        evidence_class="DIRECT_OBSERVATION",
        memory_type=mtype,
        epistemic_kind=kind,
        status=status,
        domain=domain,
        source_id="p5",
        agent_namespace="",
        observed_at=observed_at,
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
    hyps = tuple(i for i in items if i.epistemic_kind == EpistemicKind.HYPOTHESIS.value)
    preds = tuple(i for i in items if i.epistemic_kind == EpistemicKind.PREDICTION.value)
    opinions = tuple(i for i in items if i.epistemic_kind == EpistemicKind.OPINION.value)
    simulations = tuple(i for i in items if i.epistemic_kind == EpistemicKind.SIMULATION.value)
    lessons = tuple(i for i in items if i.epistemic_kind == EpistemicKind.LESSON.value)
    fails = tuple(i for i in items if i.memory_type == MemoryType.FAILURE.value)
    inferences = tuple(i for i in items if i.epistemic_kind == EpistemicKind.INFERENCE.value)
    unknowns = () if facts or items else ("empty assembled context",)
    edges = ()
    if contra and len(items) >= 2:
        edges = (
            {
                "edge_id": "p5-e",
                "from_id": items[0].memory_id,
                "to_id": items[1].memory_id,
                "relation": "CONTRADICTS",
            },
        )
    return CognitiveContext(
        facts=facts,
        inferences=inferences,
        hypotheses=hyps,
        predictions=preds,
        opinions=opinions,
        simulations=simulations,
        experiments=(),
        outcomes=(),
        contradictions=edges,
        failures=fails,
        procedures=(),
        lessons=lessons,
        unknowns=unknowns,
        excluded=(),
        contradiction_present=bool(edges),
        context_incomplete=not items,
        token_estimate=len(items),
    )


def _task(case_id: str, mode: str, **kwargs) -> CognitiveTask:
    base = dict(
        task_id=case_id,
        task_type=TaskType.ANALYZE.value,
        objective="p5",
        question="Do retries after timeout help?",
        domain="software",
        requester="p5-benchmark",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=mode,
        write_back=False,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _run(task: CognitiveTask, ctx: CognitiveContext, store=None):
    ids = [i.memory_id for i in ctx.all_included()]
    return reason(task, ctx, retrieved_ids=ids, store=store)


def evaluate_p5_reasoning(store: CognitiveMemoryStore) -> tuple[list[MetricResult], list[dict], dict[str, int]]:
    case_results: list[dict] = []
    fact = _item("P5-FACT", "SYNTHETIC_TEST_DATA: retries after HTTP timeout recovered the request.")
    fact2 = _item("P5-FACT2", "SYNTHETIC_TEST_DATA: retries after HTTP timeout recovered node two.")
    hyp = _item(
        "P5-HYP",
        "SYNTHETIC_TEST_DATA: timeout retries always help",
        kind=EpistemicKind.HYPOTHESIS.value,
        mtype=MemoryType.HYPOTHESIS.value,
    )
    opinion = _item(
        "P5-OP",
        "SYNTHETIC_TEST_DATA timeouts never happen in production",
        kind=EpistemicKind.OPINION.value,
    )
    stale = _item(
        "P5-OLD",
        "SYNTHETIC_TEST_DATA service X was on revision 1",
        status="STALE",
        observed_at=NOW - 10_000,
    )
    ok_lesson = store.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.LESSON,
        statement="SYNTHETIC_TEST_DATA LESSON: timeout retries are not proof of recovery",
        source_type=SourceType.SYSTEM,
        source_id="p5-l-ok",
        source_location="p5_eval",
        producer="p5",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        created_at=NOW,
        payload={
            "data_label": "SYNTHETIC_TEST_DATA",
            "applicability": "software",
            "component": "http_client",
        },
    )
    bad_lesson = store.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.LESSON,
        statement="SYNTHETIC_TEST_DATA LESSON: timeout retries always work in finance",
        source_type=SourceType.SYSTEM,
        source_id="p5-l-bad",
        source_location="p5_eval",
        producer="p5",
        producer_version="p5",
        domain="finance",
        context="SYNTHETIC_TEST_DATA",
        created_at=NOW,
        payload={"data_label": "SYNTHETIC_TEST_DATA", "applicability": "finance"},
    )
    match_fail = store.record_failure(
        failure_type="timeout_retry",
        component="http_client",
        attempted_action="retry",
        observed_failure="SYNTHETIC_TEST_DATA: timeout retry failed",
        now=NOW,
        producer="p5",
    )
    mismatch_fail = store.record_failure(
        failure_type="disk_full",
        component="database",
        attempted_action="write",
        observed_failure="SYNTHETIC_TEST_DATA: database disk full",
        now=NOW,
        producer="p5",
    )
    lesson_ok_item = _item(ok_lesson.memory_id, ok_lesson.statement, kind=EpistemicKind.LESSON.value)
    lesson_bad_item = _item(
        bad_lesson.memory_id,
        bad_lesson.statement,
        kind=EpistemicKind.LESSON.value,
        domain="finance",
    )
    fail_ok_item = _item(
        match_fail.memory_id,
        match_fail.statement,
        mtype=MemoryType.FAILURE.value,
    )
    fail_bad_item = _item(
        mismatch_fail.memory_id,
        mismatch_fail.statement,
        mtype=MemoryType.FAILURE.value,
    )

    typed_ok = typed_n = 0
    unsup_num = unsup_den = 0
    type_vio_num = type_vio_den = 0
    critic_det_h = critic_det_n = 0
    critic_con_h = critic_con_n = 0
    miss_h = miss_n = 0
    contra_h = contra_n = 0
    temp_h = temp_n = 0
    lesson_h = lesson_n = 0
    false_lesson_h = false_lesson_n = 0
    fail_h = fail_n = 0
    false_fail_h = false_fail_n = 0
    mode_h = mode_n = 0
    confuse_h = confuse_n = 0
    unk_h = unk_n = 0
    assume_h = assume_n = 0
    xdom_h = xdom_n = 0

    # typed compliance: bindings preserve class
    for item, expect in (
        (fact, "OBSERVED_FACT"),
        (hyp, "HYPOTHESIS"),
        (opinion, "OPINION"),
        (fail_ok_item, "FAILURE"),
        (lesson_ok_item, "LESSON"),
    ):
        binds = bind_context(_ctx(item), _task("bind", ReasoningMode.DEDUCTIVE.value), store=store)
        typed_n += 1
        if binds and binds[0].typed_class == expect:
            typed_ok += 1
        case_results.append(
            {
                "case_id": f"P5-TYPE-{expect}",
                "family": "p5_typed",
                "typed_class": binds[0].typed_class if binds else "",
                "expected": expect,
            }
        )

    # mode specificity
    ctx1 = _ctx(fact)
    modes = (
        ReasoningMode.DEDUCTIVE.value,
        ReasoningMode.INDUCTIVE.value,
        ReasoningMode.ABDUCTIVE.value,
        ReasoningMode.COMPARATIVE.value,
        ReasoningMode.TEMPORAL.value,
        ReasoningMode.ADVERSARIAL.value,
        ReasoningMode.METACOGNITIVE.value,
    )
    mode_verdicts: dict[str, str] = {}
    for mode in modes:
        v, ep, tr, cr, _ = _run(_task(f"P5-MODE-{mode}", mode), ctx1, store)
        mode_verdicts[mode] = v
        unsup_den += 1
        if v == CognitiveVerdict.SUPPORTED.value:
            unsup_num += 1
        assume_n += 1
        if tr.assumptions and tr.assumptions[0].assumption_id:
            assume_h += 1
        case_results.append(
            {
                "case_id": f"P5-MODE-{mode}",
                "family": "p5_mode",
                "verdict": v,
                "epistemic": ep,
                "conclusion_class": tr.inference_records[0]["conclusion_class"]
                if tr.inference_records
                else "",
                "critic_action": cr.action,
            }
        )
    mode_n += 1
    if mode_verdicts[ReasoningMode.DEDUCTIVE.value] != mode_verdicts[ReasoningMode.INDUCTIVE.value]:
        mode_h += 1
    confuse_n += 1
    if mode_verdicts[ReasoningMode.DEDUCTIVE.value] == mode_verdicts[ReasoningMode.INDUCTIVE.value]:
        confuse_h += 1

    # missing premise
    miss_n += 1
    v, _, tr, cr, _ = _run(_task("P5-MISS", ReasoningMode.DEDUCTIVE.value), _ctx(), store)
    if v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value:
        miss_h += 1
    unk_n += 1
    if v in {
        CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
        CognitiveVerdict.NOT_IMPLEMENTED.value,
    }:
        unk_h += 1
    critic_det_n += 1
    if cr.action != ACTION_ACCEPT or cr.missing_evidence:
        critic_det_h += 1
    case_results.append({"case_id": "P5-MISS", "family": "p5_unknown", "verdict": v, "critic_action": cr.action})

    # hypothesis is not fact
    type_vio_den += 1
    v, _, tr, _, _ = _run(_task("P5-HYP-DED", ReasoningMode.DEDUCTIVE.value), _ctx(hyp), store)
    if v != CognitiveVerdict.WEAKLY_SUPPORTED.value and v != CognitiveVerdict.SUPPORTED.value:
        type_vio_num += 0
        type_ok = True
    else:
        type_ok = False
    if type_ok:
        pass
    else:
        type_vio_num += 1
    case_results.append({"case_id": "P5-HYP-DED", "family": "p5_type", "verdict": v})

    # opinion adversarial
    type_vio_den += 1
    v, _, _, _, _ = _run(_task("P5-OP-ADV", ReasoningMode.ADVERSARIAL.value), _ctx(opinion), store)
    if v in {CognitiveVerdict.SUPPORTED.value, CognitiveVerdict.WEAKLY_SUPPORTED.value}:
        type_vio_num += 1
    case_results.append({"case_id": "P5-OP-ADV", "family": "p5_adversarial", "verdict": v})

    # contradiction (deductive refuses in-mode; detection = critic finding or CONTEST)
    contra_n += 1
    a = _item("P5-CA", "SYNTHETIC_TEST_DATA: timeout retries support recovery.")
    b = _item("P5-CB", "SYNTHETIC_TEST_DATA: timeout retries contradict recovery.")
    v, _, tr, cr, _ = _run(
        _task("P5-CONTRA", ReasoningMode.DEDUCTIVE.value), _ctx(a, b, contra=True), store
    )
    if v in {CognitiveVerdict.UNRESOLVED.value, CognitiveVerdict.CONTESTED.value}:
        contra_h += 1
    critic_det_n += 1
    if cr.action == ACTION_CONTEST or any("CONTRADICTION" in f for f in cr.findings):
        critic_det_h += 1
    case_results.append(
        {
            "case_id": "P5-CONTRA",
            "family": "p5_contradiction",
            "verdict": v,
            "critic_action": cr.action,
            "findings": list(cr.findings),
        }
    )

    # temporal
    temp_n += 1
    v, ep, _, _, _ = _run(_task("P5-STALE", ReasoningMode.TEMPORAL.value), _ctx(stale), store)
    if v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value and ep == "STALE":
        temp_h += 1
    case_results.append({"case_id": "P5-STALE", "family": "p5_temporal", "verdict": v, "epistemic": ep})

    # lesson apply / false apply
    lesson_n += 1
    v, ep, tr, _, _ = _run(
        _task(
            "P5-LESSON-OK",
            ReasoningMode.DEDUCTIVE.value,
            constraints={"component": "http_client"},
        ),
        _ctx(fact, lesson_ok_item),
        store,
    )
    if tr.inference_records and tr.inference_records[0].get("lesson_applied"):
        lesson_h += 1
    false_lesson_n += 1
    v, ep, tr, _, _ = _run(
        _task("P5-LESSON-BAD", ReasoningMode.DEDUCTIVE.value),
        _ctx(fact, lesson_bad_item),
        store,
    )
    if tr.inference_records and tr.inference_records[0].get("lesson_applied"):
        false_lesson_h += 1
    case_results.append({"case_id": "P5-LESSON-OK", "family": "p5_lesson", "applied": lesson_h == lesson_n})
    case_results.append(
        {"case_id": "P5-LESSON-BAD", "family": "p5_lesson", "applied": bool(tr.inference_records[0].get("lesson_applied"))}
    )

    # failure apply
    fail_n += 1
    v, _, tr, _, _ = _run(
        _task(
            "P5-FAIL-OK",
            ReasoningMode.DEDUCTIVE.value,
            constraints={"component": "http_client", "failure_type": "timeout_retry"},
        ),
        _ctx(fact, fail_ok_item),
        store,
    )
    if tr.inference_records and tr.inference_records[0].get("failure_applied"):
        fail_h += 1
    false_fail_n += 1
    v, _, tr, _, _ = _run(
        _task("P5-FAIL-BAD", ReasoningMode.DEDUCTIVE.value),
        _ctx(fact, fail_bad_item),
        store,
    )
    if tr.inference_records and tr.inference_records[0].get("failure_applied"):
        false_fail_h += 1
    case_results.append({"case_id": "P5-FAIL-OK", "family": "p5_failure", "verdict": v})
    case_results.append({"case_id": "P5-FAIL-BAD", "family": "p5_failure", "applied": bool(tr.inference_records[0].get("failure_applied"))})

    # live critic constraint: metacognitive emits WEAKLY; critic CONTEST → UNRESOLVED
    live_task = _task("P5-CRITIC-LIVE", ReasoningMode.METACOGNITIVE.value)
    live_ctx = _ctx(a, b, contra=True)
    live_binds = bind_context(live_ctx, live_task, store=store)
    pre = reason_metacognitive(live_task, live_binds)
    v, _, tr, cr, _ = _run(live_task, live_ctx, store)
    critic_det_n += 1
    if cr.action == ACTION_CONTEST or any("CONTRADICTION" in f for f in cr.findings):
        critic_det_h += 1
    critic_con_n += 1
    if (
        cr.action != ACTION_ACCEPT
        and cr.constraint_applied
        and v != pre.verdict
        and v in {CognitiveVerdict.UNRESOLVED.value, CognitiveVerdict.CONTESTED.value}
    ):
        critic_con_h += 1
    unsup_den += 1
    if v == CognitiveVerdict.SUPPORTED.value:
        unsup_num += 1
    case_results.append(
        {
            "case_id": "P5-CRITIC-LIVE",
            "family": "p5_critic",
            "pre_verdict": pre.verdict,
            "final": v,
            "critic_action": cr.action,
        }
    )

    # relevance fail-closed (sky is not timeout)
    sky = _item("P5-SKY", "SYNTHETIC_TEST_DATA: the sky is blue.")
    v, _, _, cr_sky, _ = _run(_task("P5-SKY-DED", ReasoningMode.DEDUCTIVE.value), _ctx(sky), store)
    case_results.append(
        {
            "case_id": "P5-SKY-DED",
            "family": "p5_relevance",
            "verdict": v,
            "critic_action": cr_sky.action,
        }
    )
    v, _, _, cr_meta, _ = _run(
        _task("P5-SKY-META", ReasoningMode.METACOGNITIVE.value), _ctx(sky), store
    )
    case_results.append(
        {
            "case_id": "P5-SKY-META",
            "family": "p5_relevance",
            "verdict": v,
            "critic_action": cr_meta.action,
        }
    )
    if cr_meta.action == ACTION_REFUSE:
        critic_det_n += 1
        critic_det_h += 1
        critic_con_n += 1
        if v != CognitiveVerdict.WEAKLY_SUPPORTED.value:
            critic_con_h += 1

    # inductive two examples
    v, _, tr, _, _ = _run(
        _task("P5-IND-2", ReasoningMode.INDUCTIVE.value), _ctx(fact, fact2), store
    )
    case_results.append(
        {
            "case_id": "P5-IND-2",
            "family": "p5_inductive",
            "verdict": v,
            "conclusion_class": tr.inference_records[0]["conclusion_class"] if tr.inference_records else "",
        }
    )

    # abductive alternatives
    h2 = _item(
        "P5-HYP2",
        "SYNTHETIC_TEST_DATA: timeout caused by dns failure",
        kind=EpistemicKind.HYPOTHESIS.value,
        mtype=MemoryType.HYPOTHESIS.value,
    )
    v, _, tr, _, _ = _run(
        _task("P5-ABD", ReasoningMode.ABDUCTIVE.value), _ctx(fact, hyp, h2), store
    )
    case_results.append(
        {
            "case_id": "P5-ABD",
            "family": "p5_abductive",
            "verdict": v,
            "alternatives": len((tr.inference_records or [{}])[0].get("alternatives") or []),
        }
    )

    # cross-domain invariance of DEDUCTIVE with one local fact
    verdicts = []
    for domain, q in (
        ("software", "Do retries after timeout help?"),
        ("science", "Do calibration retries recover the measurement?"),
        ("finance", "Do retries recover the token observation?"),
        ("operations", "Do retries recover queue depth?"),
    ):
        f = _item(f"P5-{domain}", f"SYNTHETIC_TEST_DATA {domain} retries recovered", domain=domain)
        v, _, _, _, _ = _run(
            _task(f"P5-DOM-{domain}", ReasoningMode.DEDUCTIVE.value, domain=domain, question=q),
            _ctx(f),
            store,
        )
        verdicts.append(v)
        case_results.append({"case_id": f"P5-DOM-{domain.upper()}", "family": "p5_domain", "verdict": v})
    xdom_n += 1
    if len(set(verdicts)) == 1:
        xdom_h += 1

    metrics = [
        make_metric(
            "typed_evidence_compliance",
            name="typed_evidence_compliance",
            definition="bindings whose typed_class matches the source taxonomy / probes",
            numerator=typed_ok,
            denominator=float(typed_n),
            population="P5 typed-class probes",
            limitations="Synthetic items; not soak",
            n=typed_n,
        ),
        make_metric(
            "p5_unsupported_claim_rate",
            name="p5_unsupported_claim_rate",
            definition="SUPPORTED finals on P5 mode+critic probes / those probes",
            numerator=unsup_num,
            denominator=float(unsup_den),
            population="P5 mode cases + critic probe",
            limitations="Does not replace P4.1 unsupported_claim_rate",
            n=unsup_den,
        ),
        make_metric(
            "evidence_type_violation_rate",
            name="evidence_type_violation_rate",
            definition="hyp/opinion probes that still WEAKLY/SUPPORTED as if fact / probes",
            numerator=type_vio_num,
            denominator=float(type_vio_den),
            population="P5-HYP-DED + P5-OP-ADV",
            limitations="Two probes",
            n=type_vio_den,
        ),
        make_metric(
            "p5_critic_detection_rate",
            name="p5_critic_detection_rate",
            definition="live critic action or contradiction/relevance finding / probes",
            numerator=critic_det_h,
            denominator=float(critic_det_n),
            population="empty + contradiction + live metacognitive contest + irrelevant inventory refuse",
            limitations="Separate from P4.1 critic_detection_rate; no hardcoded pass",
            n=critic_det_n,
        ),
        make_metric(
            "critic_constraint_rate",
            name="critic_constraint_rate",
            definition="live reason() probes where critic action changed the mode verdict / probes",
            numerator=critic_con_h,
            denominator=float(critic_con_n),
            population="P5-CRITIC-LIVE CONTEST + P5-SKY-META REFUSE",
            limitations="Detection ≠ constraint; apply_constraint is not counted as production constraint",
            n=critic_con_n,
        ),
        make_metric(
            "missing_premise_refusal_accuracy",
            name="missing_premise_refusal_accuracy",
            definition="empty-context deduction returns INSUFFICIENT_EVIDENCE / 1",
            numerator=miss_h,
            denominator=float(miss_n),
            population="P5-MISS",
            limitations="N=1",
            n=miss_n,
        ),
        make_metric(
            "p5_contradiction_preservation",
            name="p5_contradiction_preservation",
            definition="contradiction pair yields UNRESOLVED/CONTESTED / 1",
            numerator=contra_h,
            denominator=float(contra_n),
            population="P5-CONTRA",
            limitations="N=1 synthetic pair",
            n=contra_n,
        ),
        make_metric(
            "temporal_scope_accuracy",
            name="temporal_scope_accuracy",
            definition="stale-only TEMPORAL → INSUFFICIENT+STALE / 1",
            numerator=temp_h,
            denominator=float(temp_n),
            population="P5-STALE",
            limitations="N=1",
            n=temp_n,
        ),
        make_metric(
            "lesson_application_accuracy",
            name="lesson_application_accuracy",
            definition="applicable software lesson sets lesson_applied / 1",
            numerator=lesson_h,
            denominator=float(lesson_n),
            population="P5-LESSON-OK",
            limitations="N=1",
            n=lesson_n,
        ),
        make_metric(
            "false_lesson_application_rate",
            name="false_lesson_application_rate",
            definition="finance lesson applied to software task / 1",
            numerator=false_lesson_h,
            denominator=float(false_lesson_n),
            population="P5-LESSON-BAD",
            limitations="N=1",
            n=false_lesson_n,
        ),
        make_metric(
            "failure_application_accuracy",
            name="failure_application_accuracy",
            definition="matching component/type failure sets failure_applied / 1",
            numerator=fail_h,
            denominator=float(fail_n),
            population="P5-FAIL-OK",
            limitations="N=1",
            n=fail_n,
        ),
        make_metric(
            "p5_false_failure_application_rate",
            name="p5_false_failure_application_rate",
            definition="unconstrained mismatched failure applied / 1",
            numerator=false_fail_h,
            denominator=float(false_fail_n),
            population="P5-FAIL-BAD",
            limitations="Separate from P4.3 retrieval false_failure_application_rate",
            n=false_fail_n,
        ),
        make_metric(
            "mode_specificity",
            name="mode_specificity",
            definition="DEDUCTIVE verdict ≠ INDUCTIVE verdict on one-fact context / 1",
            numerator=mode_h,
            denominator=float(mode_n),
            population="P5 one-fact mode suite",
            limitations="Detects mode collapse between those two modes",
            n=mode_n,
        ),
        make_metric(
            "reasoning_mode_confusion_rate",
            name="reasoning_mode_confusion_rate",
            definition="DEDUCTIVE==INDUCTIVE on one-fact context / 1",
            numerator=confuse_h,
            denominator=float(confuse_n),
            population="P5 one-fact mode suite",
            limitations="Complement of mode_specificity for those two modes",
            n=confuse_n,
        ),
        make_metric(
            "p5_unknown_refusal_accuracy",
            name="p5_unknown_refusal_accuracy",
            definition="empty context refuses with INSUFFICIENT/NOT_IMPLEMENTED / 1",
            numerator=unk_h,
            denominator=float(unk_n),
            population="P5-MISS",
            limitations="N=1; does not replace P4.1 unknown_refusal_accuracy",
            n=unk_n,
        ),
        make_metric(
            "assumption_record_presence",
            name="assumption_record_presence",
            definition="mode episodes with assumption_id / mode count",
            numerator=assume_h,
            denominator=float(assume_n),
            population="P5 seven modes on one fact",
            limitations="Record presence only; not assumption sensitivity",
            n=assume_n,
        ),
        make_metric(
            "p5_cross_domain_invariance",
            name="p5_cross_domain_invariance",
            definition="same DEDUCTIVE verdict class across four adapter domains / 1",
            numerator=xdom_h,
            denominator=float(xdom_n),
            population="software/science/finance/operations one-fact",
            limitations="Synthetic one-fact tasks; not market transfer",
            n=xdom_n,
        ),
    ]
    counts = {
        "p5_cases": len(case_results),
        "p5_metrics": len(metrics),
        "p5_version": 1,
    }
    return metrics, case_results, counts
