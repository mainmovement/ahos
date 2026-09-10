"""Typed eligibility + support-class fail-closed + critic-constrained templates.

Modes are distinct governed transformations over EvidenceBinding lists.
They are not formal deduction, statistical induction, or entailment.
Lexical match is candidate relevance only. The critic inspects a candidate
and may ACCEPT, DOWNGRADE, CONTEST, REQUIRE_MORE_EVIDENCE, or REFUSE.
"""

from __future__ import annotations

from architecture.cognitive.loop.binding import (
    NOT_APPLICABLE,
    ROLE_FACTUAL_PREMISE,
    EvidenceBinding,
    addresses_task,
    bind_context,
    cited_unbound_ids,
)
from architecture.cognitive.loop.support import (
    CLAUSE_NEGATED,
    CLAUSE_UNCERTAIN,
    ENTITY_AMBIGUOUS,
    ENTITY_MISMATCH,
)
from architecture.cognitive.loop.contracts import (
    Assumption,
    ClaimOrigin,
    CognitiveContext,
    CognitiveTask,
    CognitiveVerdict,
    Critique,
    EpistemicAnswer,
    ReasoningMode,
    ReasoningTrace,
)
from architecture.cognitive.loop.inference import (
    ACTION_ACCEPT,
    ACTION_CONTEST,
    ACTION_DOWNGRADE,
    ACTION_REFUSE,
    ACTION_REQUIRE_MORE,
    FINDING_APPLICABILITY_VIOLATION,
    FINDING_CONTRADICTION,
    FINDING_EVIDENCE_MISMATCH,
    FINDING_MISSING_PREMISE,
    FINDING_OVERCONFIDENCE,
    FINDING_SCOPE_MISMATCH,
    FINDING_TEMPORAL_VIOLATION,
    FINDING_TYPE_VIOLATION,
    FINDING_UNSUPPORTED_ASSUMPTION,
    CandidateInference,
    apply_constraint,
    to_inference,
)
from architecture.cognitive.loop.modes import MODE_FNS
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import EpistemicKind


IMPLEMENTED_MODES = frozenset(
    {
        ReasoningMode.DEDUCTIVE.value,
        ReasoningMode.INDUCTIVE.value,
        ReasoningMode.ABDUCTIVE.value,
        ReasoningMode.COMPARATIVE.value,
        ReasoningMode.TEMPORAL.value,
        ReasoningMode.ADVERSARIAL.value,
        ReasoningMode.METACOGNITIVE.value,
    }
)

NOT_IMPLEMENTED_MODES = frozenset(
    {
        ReasoningMode.CAUSAL_HYPOTHESIS.value,
        ReasoningMode.COUNTERFACTUAL.value,
    }
)

CRITIC_QUESTIONS = (
    "What evidence contradicts this?",
    "What evidence is missing?",
    "Which assumption is weakest?",
    "Could another explanation fit?",
    "Is the conclusion too strong?",
    "Is retrieved context biased?",
    "Is there stale evidence?",
    "Did we confuse prediction with fact?",
)


def _inspect(
    *,
    task: CognitiveTask,
    ctx: CognitiveContext,
    bindings: list[EvidenceBinding],
    candidate: CandidateInference,
    assumptions: list[Assumption],
) -> tuple[str, list[str]]:
    findings: list[str] = []
    accepted = candidate.verdict in {
        CognitiveVerdict.SUPPORTED.value,
        CognitiveVerdict.WEAKLY_SUPPORTED.value,
    }
    already_refused = candidate.verdict in {
        CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
        CognitiveVerdict.UNRESOLVED.value,
        CognitiveVerdict.CONTESTED.value,
        CognitiveVerdict.NOT_IMPLEMENTED.value,
    }
    cited = list(candidate.supporting_ids) + list(candidate.premises)
    unbound = cited_unbound_ids(cited, bindings)
    if unbound:
        findings.append(f"{FINDING_EVIDENCE_MISMATCH}:unbound_citation:{','.join(unbound)}")
    cited_set = {i for i in cited if i}
    relevant_cited = any(
        addresses_task(b.statement, task)
        and b.may(ROLE_FACTUAL_PREMISE)
        and b.memory_id in cited_set
        for b in bindings
    )
    supporting_cited = any(
        b.may_support_task() and b.may(ROLE_FACTUAL_PREMISE) and b.memory_id in cited_set
        for b in bindings
    )
    if accepted and cited_set and not relevant_cited:
        findings.append(f"{FINDING_EVIDENCE_MISMATCH}:irrelevant_citation")
    if accepted and cited_set and relevant_cited and not supporting_cited:
        findings.append(f"{FINDING_EVIDENCE_MISMATCH}:lexical_match_without_support")
    if accepted and not any(b.may_support_task() for b in bindings):
        findings.append(f"{FINDING_EVIDENCE_MISMATCH}:no_direct_support")
    if candidate.missing_premises:
        findings.append(f"{FINDING_MISSING_PREMISE}:{','.join(candidate.missing_premises)}")
    if candidate.type_violations:
        findings.append(f"{FINDING_TYPE_VIOLATION}:{','.join(candidate.type_violations)}")
    if any(b.typed_class in {"OPINION", "PREDICTION", "SIMULATION"} for b in bindings) and (
        accepted
        and not any(b.may(ROLE_FACTUAL_PREMISE) for b in bindings)
        and candidate.conclusion_class not in {"HYPOTHESIS", "INFERENCE"}
    ):
        findings.append(f"{FINDING_TYPE_VIOLATION}:non_fact_used_as_fact")
    if candidate.verdict == CognitiveVerdict.SUPPORTED.value:
        findings.append(f"{FINDING_OVERCONFIDENCE}:candidate_supported")
    stale_as_current = any(
        b.typed_class == "OBSERVED_FACT"
        and b.temporal_state in {"STALE", "SUPERSEDED"}
        and b.memory_id in candidate.premises
        and b.may(ROLE_FACTUAL_PREMISE)
        for b in bindings
    )
    if stale_as_current:
        findings.append(f"{FINDING_TEMPORAL_VIOLATION}:stale_premise")
    if ctx.contradiction_present:
        findings.append(f"{FINDING_CONTRADICTION}:present")
        if accepted:
            findings.append(f"{FINDING_CONTRADICTION}:ignored_or_underweighted")
    inapplicable_lessons = [
        b
        for b in bindings
        if b.typed_class == "LESSON"
        and b.applicability == NOT_APPLICABLE
        and b.memory_id in candidate.supporting_ids
    ]
    if inapplicable_lessons:
        findings.append(
            f"{FINDING_APPLICABILITY_VIOLATION}:{inapplicable_lessons[0].memory_id}"
        )
    inapplicable_fails = [
        b
        for b in bindings
        if b.typed_class == "FAILURE"
        and b.applicability == NOT_APPLICABLE
        and candidate.failure_applied
    ]
    if inapplicable_fails:
        findings.append(f"{FINDING_APPLICABILITY_VIOLATION}:failure")
    scope = [
        b
        for b in bindings
        if b.domain
        and task.domain
        and b.domain not in {task.domain, "COGNITIVE_CORE"}
        and b.memory_id in candidate.premises
    ]
    if scope:
        findings.append(f"{FINDING_SCOPE_MISMATCH}:{scope[0].memory_id}")
    if candidate.verdict in {
        CognitiveVerdict.SUPPORTED.value,
        CognitiveVerdict.WEAKLY_SUPPORTED.value,
    } and not candidate.supporting_ids and not candidate.premises:
        findings.append(f"{FINDING_EVIDENCE_MISMATCH}:conclusion_without_support")
    if assumptions and candidate.verdict == CognitiveVerdict.SUPPORTED.value:
        findings.append(f"{FINDING_UNSUPPORTED_ASSUMPTION}:{assumptions[0].assumption_id}")

    codes = {f.split(":")[0] for f in findings}
    if candidate.verdict == CognitiveVerdict.NOT_IMPLEMENTED.value:
        return ACTION_ACCEPT, findings
    if not bindings:
        return ACTION_REQUIRE_MORE, findings or [f"{FINDING_MISSING_PREMISE}:empty_context"]
    if accepted and unbound:
        return ACTION_REFUSE, findings
    if accepted and not relevant_cited and cited_set:
        return ACTION_REFUSE, findings
    if accepted and not supporting_cited:
        return ACTION_REFUSE, findings
    if already_refused:
        return ACTION_ACCEPT, findings
    if FINDING_MISSING_PREMISE in codes:
        return ACTION_REQUIRE_MORE, findings
    if FINDING_EVIDENCE_MISMATCH in codes and "unbound_citation" not in " ".join(findings):
        return ACTION_REQUIRE_MORE, findings
    if FINDING_CONTRADICTION in codes:
        return ACTION_CONTEST, findings
    if FINDING_TYPE_VIOLATION in codes:
        return ACTION_DOWNGRADE, findings
    if FINDING_TEMPORAL_VIOLATION in codes or FINDING_SCOPE_MISMATCH in codes:
        return ACTION_DOWNGRADE, findings
    if FINDING_APPLICABILITY_VIOLATION in codes:
        return ACTION_DOWNGRADE, findings
    if FINDING_OVERCONFIDENCE in codes or FINDING_UNSUPPORTED_ASSUMPTION in codes:
        return ACTION_DOWNGRADE, findings
    return ACTION_ACCEPT, findings


def critique_result(
    *,
    task: CognitiveTask,
    ctx: CognitiveContext,
    verdict: str,
    assumptions: list[Assumption],
    bindings: list[EvidenceBinding] | None = None,
    candidate: CandidateInference | None = None,
) -> Critique:
    pred_as_fact = any(
        i.epistemic_kind == EpistemicKind.PREDICTION.value for i in ctx.facts
    )
    stale_current = any(
        i.status == "STALE" and i.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
        for i in ctx.facts
    )
    too_strong = verdict == CognitiveVerdict.SUPPORTED.value
    weakest = assumptions[0].statement if assumptions else "none recorded"
    missing = list(ctx.unknowns)
    if candidate and candidate.missing_premises:
        missing = list(dict.fromkeys(list(missing) + list(candidate.missing_premises)))
    alt = "An unrecorded cause could explain the same observations."
    if ctx.contradiction_present:
        alt = "The opposing memory remains a live alternative; do not discard it."
    action = ACTION_ACCEPT
    findings: list[str] = []
    if candidate is not None:
        action, findings = _inspect(
            task=task,
            ctx=ctx,
            bindings=bindings or [],
            candidate=candidate,
            assumptions=assumptions,
        )
    elif not ctx.all_included():
        action = ACTION_REQUIRE_MORE
        findings = [f"{FINDING_MISSING_PREMISE}:empty_context"]
    return Critique(
        questions=CRITIC_QUESTIONS,
        weakest_assumption=weakest,
        alternative_explanation=alt,
        too_strong=too_strong,
        prediction_confused_with_fact=pred_as_fact,
        stale_used_as_current=stale_current,
        missing_evidence=tuple(missing),
        action=action,
        findings=tuple(findings),
        constraint_applied=action != ACTION_ACCEPT,
    )


def reason(
    task: CognitiveTask,
    ctx: CognitiveContext,
    *,
    retrieved_ids: list[str],
    store: CognitiveMemoryStore | None = None,
) -> tuple[str, str, ReasoningTrace, Critique, list[Assumption]]:
    mode = task.reasoning_mode
    assumptions = [
        Assumption(
            assumption_id="ASM-000001",
            statement="Retrieved memories are the only evidence for this episode",
            basis="P5 loop does not query soak or Lane A",
            confidence=1.0,
            impact="conclusions cannot be stronger than bound evidence",
            origin=ClaimOrigin.ASSUMED.value,
        )
    ]
    bindings = bind_context(ctx, task, store=store)

    if mode in NOT_IMPLEMENTED_MODES:
        candidate = CandidateInference(
            verdict=CognitiveVerdict.NOT_IMPLEMENTED.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion=f"Mode {mode} is not implemented; I don't know.",
            conclusion_class="UNKNOWN",
            assumptions=assumptions,
            steps=[f"mode {mode} is NOT_IMPLEMENTED; refusing pretended inference"],
        )
        mode_status = "NOT_IMPLEMENTED"
    elif mode not in IMPLEMENTED_MODES:
        candidate = CandidateInference(
            verdict=CognitiveVerdict.NOT_IMPLEMENTED.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion=f"Mode {mode} is unknown; I don't know.",
            conclusion_class="UNKNOWN",
            assumptions=assumptions,
            steps=[f"mode {mode} is not in the implemented set"],
        )
        mode_status = "NOT_IMPLEMENTED"
    else:
        mode_status = "IMPLEMENTED"
        candidate = MODE_FNS[mode](task, bindings)
        if not candidate.assumptions:
            candidate.assumptions = list(assumptions)
        assumptions = list(candidate.assumptions)

    pre_verdict = candidate.verdict
    critique = critique_result(
        task=task,
        ctx=ctx,
        verdict=candidate.verdict,
        assumptions=assumptions,
        bindings=bindings,
        candidate=candidate,
    )
    constrained = apply_constraint(
        candidate, action=critique.action, findings=list(critique.findings)
    )
    leftover = cited_unbound_ids(
        list(constrained.supporting_ids) + list(constrained.premises), bindings
    )
    if leftover and constrained.verdict in {
        CognitiveVerdict.SUPPORTED.value,
        CognitiveVerdict.WEAKLY_SUPPORTED.value,
    }:
        extra = [f"{FINDING_EVIDENCE_MISMATCH}:unbound_citation:{','.join(leftover)}"]
        constrained = apply_constraint(
            constrained, action=ACTION_REFUSE, findings=extra
        )
        critique.action = ACTION_REFUSE
        critique.findings = tuple(list(critique.findings) + extra)
        critique.constraint_applied = True
    if constrained.verdict in {
        CognitiveVerdict.SUPPORTED.value,
        CognitiveVerdict.WEAKLY_SUPPORTED.value,
    } and not any(b.may_support_task() for b in bindings):
        extra = [f"{FINDING_EVIDENCE_MISMATCH}:no_direct_support"]
        constrained = apply_constraint(
            constrained, action=ACTION_REFUSE, findings=extra
        )
        critique.action = ACTION_REFUSE
        critique.findings = tuple(list(critique.findings) + extra)
        critique.constraint_applied = True
    cited_support = {
        i for i in (list(constrained.supporting_ids) + list(constrained.premises)) if i
    }
    polarity_unsafe = [
        b
        for b in bindings
        if b.memory_id in cited_support
        and (
            b.clause_force in {CLAUSE_NEGATED, CLAUSE_UNCERTAIN}
            or b.entity_state in {ENTITY_MISMATCH, ENTITY_AMBIGUOUS}
        )
    ]
    if constrained.verdict in {
        CognitiveVerdict.SUPPORTED.value,
        CognitiveVerdict.WEAKLY_SUPPORTED.value,
    } and polarity_unsafe:
        extra = [f"{FINDING_EVIDENCE_MISMATCH}:polarity_or_entity_blocks_positive"]
        constrained = apply_constraint(
            constrained, action=ACTION_REFUSE, findings=extra
        )
        critique.action = ACTION_REFUSE
        critique.findings = tuple(list(critique.findings) + extra)
        critique.constraint_applied = True
    if ctx.context_incomplete:
        constrained.steps.append("CONTEXT_INCOMPLETE")
        if constrained.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value:
            constrained.epistemic = EpistemicAnswer.UNCERTAIN.value
    if constrained.verdict == CognitiveVerdict.SUPPORTED.value:
        constrained.verdict = CognitiveVerdict.WEAKLY_SUPPORTED.value
        constrained.epistemic = EpistemicAnswer.PROBABLE.value
        constrained.steps.append("governance: never emit SUPPORTED certainty from P5")

    inference = to_inference(
        constrained,
        mode=mode,
        action=critique.action,
        findings=list(critique.findings),
    )
    selected = [i.memory_id for i in ctx.all_included()]
    trace = ReasoningTrace(
        task_id=task.task_id,
        mode=mode,
        mode_status=mode_status,
        retrieved_ids=tuple(retrieved_ids),
        selected_ids=tuple(selected),
        excluded=ctx.excluded,
        assumptions=tuple(assumptions),
        inferences=tuple(constrained.steps),
        contradictions=ctx.contradictions,
        steps=tuple(constrained.steps),
        uncertainty=constrained.epistemic,
        conclusion=constrained.conclusion,
        open_questions=critique.questions[:4],
        verdict=constrained.verdict,
        inference_records=(inference.as_dict(),),
        critic_findings=tuple(critique.findings),
        constraint_actions=(critique.action,),
        evidence_classes=tuple(b.typed_class for b in bindings),
        premises=tuple(constrained.premises),
    )
    # Preserve critic flags after constraint (too_strong refers to candidate).
    critique.too_strong = pre_verdict == CognitiveVerdict.SUPPORTED.value
    critique.constraint_applied = (
        critique.action != ACTION_ACCEPT or constrained.verdict != pre_verdict
    )
    return constrained.verdict, constrained.epistemic, trace, critique, assumptions
