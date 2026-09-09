"""Deterministic reasoning modes + critic. LLM-free. Unimplemented modes say so."""

from __future__ import annotations

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
from architecture.cognitive.loop.retrieval import tokens
from architecture.cognitive.memory.types import DecayState, EpistemicKind


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


def _keyword_hits(ctx: CognitiveContext, task: CognitiveTask) -> tuple[list[str], list[str]]:
    q = tokens(task.question) | tokens(task.objective)
    supporting: list[str] = []
    opposing: list[str] = []
    for item in ctx.all_included():
        overlap = tokens(item.statement) & q
        if not overlap:
            continue
        if item.epistemic_kind in {
            EpistemicKind.PREDICTION.value,
            EpistemicKind.OPINION.value,
            EpistemicKind.SIMULATION.value,
        }:
            continue
        if any(
            w in f" {item.statement.lower()} "
            for w in (" is not ", " never ", " contradicts ", " opposite ")
        ):
            opposing.append(item.memory_id)
        else:
            supporting.append(item.memory_id)
    return supporting, opposing


def _verdict_from_context(ctx: CognitiveContext, task: CognitiveTask) -> tuple[str, str, list[str]]:
    steps: list[str] = []
    if ctx.contradiction_present:
        steps.append("CONTRADICTION_PRESENT: both sides retained")
        return CognitiveVerdict.UNRESOLVED.value, EpistemicAnswer.CONTESTED.value, steps
    facts = [i for i in ctx.facts if i.status != DecayState.STALE.value]
    stale_facts = [i for i in ctx.facts if i.status == DecayState.STALE.value]
    if stale_facts and not facts:
        steps.append("only STALE observations; STALE is not current")
        return CognitiveVerdict.INSUFFICIENT_EVIDENCE.value, EpistemicAnswer.STALE.value, steps
    supporting, opposing = _keyword_hits(ctx, task)
    if opposing and supporting:
        steps.append("keyword-level support and opposition without formal edge")
        return CognitiveVerdict.CONTESTED.value, EpistemicAnswer.CONTESTED.value, steps
    if facts and supporting:
        steps.append("non-stale observations overlap the question")
        if len(supporting) == 1:
            return CognitiveVerdict.WEAKLY_SUPPORTED.value, EpistemicAnswer.PROBABLE.value, steps
        return CognitiveVerdict.WEAKLY_SUPPORTED.value, EpistemicAnswer.PROBABLE.value, steps
    if ctx.lessons:
        steps.append("lessons present but not treated as OBSERVED_FACT")
        return CognitiveVerdict.WEAKLY_SUPPORTED.value, EpistemicAnswer.UNCERTAIN.value, steps
    if ctx.predictions and not facts:
        steps.append("predictions are not facts")
        return CognitiveVerdict.INSUFFICIENT_EVIDENCE.value, EpistemicAnswer.UNKNOWN.value, steps
    steps.append("insufficient evidence")
    return (
        CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
        EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
        steps,
    )


def critique_result(
    *,
    task: CognitiveTask,
    ctx: CognitiveContext,
    verdict: str,
    assumptions: list[Assumption],
) -> Critique:
    questions = (
        "What evidence contradicts this?",
        "What evidence is missing?",
        "Which assumption is weakest?",
        "Could another explanation fit?",
        "Is the conclusion too strong?",
        "Is retrieved context biased?",
        "Is there stale evidence?",
        "Did we confuse prediction with fact?",
    )
    pred_as_fact = any(
        i.epistemic_kind == EpistemicKind.PREDICTION.value for i in ctx.facts
    )
    stale_current = any(i.status == DecayState.STALE.value for i in ctx.facts)
    too_strong = verdict == CognitiveVerdict.SUPPORTED.value
    weakest = assumptions[0].statement if assumptions else "none recorded"
    missing = ctx.unknowns
    alt = "An unrecorded cause could explain the same observations."
    if ctx.contradiction_present:
        alt = "The opposing memory remains a live alternative; do not discard it."
    return Critique(
        questions=questions,
        weakest_assumption=weakest,
        alternative_explanation=alt,
        too_strong=too_strong,
        prediction_confused_with_fact=pred_as_fact,
        stale_used_as_current=stale_current,
        missing_evidence=missing,
    )


def reason(
    task: CognitiveTask,
    ctx: CognitiveContext,
    *,
    retrieved_ids: list[str],
) -> tuple[str, str, ReasoningTrace, Critique, list[Assumption]]:
    mode = task.reasoning_mode
    assumptions = [
        Assumption(
            assumption_id="ASM-000001",
            statement="Retrieved memories are the only evidence for this episode",
            basis="P3 loop does not query soak or Lane A",
            confidence=1.0,
            impact="conclusions cannot be stronger than assembled context",
            origin=ClaimOrigin.ASSUMED.value,
        )
    ]
    if mode in NOT_IMPLEMENTED_MODES:
        verdict, epistemic = (
            CognitiveVerdict.NOT_IMPLEMENTED.value,
            EpistemicAnswer.UNKNOWN.value,
        )
        steps = [f"mode {mode} is NOT_IMPLEMENTED; refusing pretended inference"]
        mode_status = "NOT_IMPLEMENTED"
        conclusion = f"Mode {mode} is not implemented; I don't know."
    else:
        mode_status = "IMPLEMENTED"
        verdict, epistemic, steps = _verdict_from_context(ctx, task)
        if mode == ReasoningMode.METACOGNITIVE.value:
            steps.append(
                f"know={len(ctx.facts)} facts; unknown={list(ctx.unknowns)}; "
                f"failures={len(ctx.failures)}; lessons={len(ctx.lessons)}"
            )
            conclusion = (
                f"Known observations: {len(ctx.facts)}. "
                f"Unknowns: {'; '.join(ctx.unknowns) or 'none listed'}. "
                f"Verdict remains {verdict}."
            )
        elif mode == ReasoningMode.TEMPORAL.value:
            steps.append("event time (observed_at) is distinct from ingestion (created_at)")
            conclusion = f"Temporal reading: {verdict} (stale not treated as current)."
        elif mode == ReasoningMode.INDUCTIVE.value:
            n = len(ctx.failures) + len(ctx.lessons)
            steps.append(f"inductive count of failures+lessons={n}")
            conclusion = f"Pattern strength from {n} prior lessons/failures: {verdict}."
        elif mode == ReasoningMode.ABDUCTIVE.value:
            steps.append("abduction proposes an explanation; not a fact")
            conclusion = f"Best explanation candidate under {verdict}: {task.question}"
        elif mode == ReasoningMode.ADVERSARIAL.value:
            steps.append("adversarial mode defers to critic before any upgrade")
            conclusion = f"Adversarial stance: {verdict}"
        else:
            conclusion = f"{mode} verdict {verdict} for: {task.question}"
        if verdict == CognitiveVerdict.SUPPORTED.value:
            verdict = CognitiveVerdict.WEAKLY_SUPPORTED.value
            epistemic = EpistemicAnswer.PROBABLE.value
            steps.append("downgraded SUPPORTED→WEAKLY_SUPPORTED: P3 never upgrades to certainty")

    if ctx.context_incomplete:
        steps.append("CONTEXT_INCOMPLETE")
        if verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value:
            epistemic = EpistemicAnswer.UNCERTAIN.value

    critique = critique_result(
        task=task, ctx=ctx, verdict=verdict, assumptions=assumptions
    )
    if critique.too_strong:
        verdict = CognitiveVerdict.WEAKLY_SUPPORTED.value
    selected = [i.memory_id for i in ctx.all_included()]
    trace = ReasoningTrace(
        task_id=task.task_id,
        mode=mode,
        mode_status=mode_status,
        retrieved_ids=tuple(retrieved_ids),
        selected_ids=tuple(selected),
        excluded=ctx.excluded,
        assumptions=tuple(assumptions),
        inferences=tuple(steps),
        contradictions=ctx.contradictions,
        steps=tuple(steps),
        uncertainty=epistemic,
        conclusion=conclusion,
        open_questions=critique.questions[:4],
        verdict=verdict,
    )
    return verdict, epistemic, trace, critique, assumptions
