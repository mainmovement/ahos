"""Mode-specific eligibility gates and templates over EvidenceBinding lists.

These are not independent formal reasoning operators. They are distinct
governed eligibility/template transforms (typed inference heuristics).
They do not perform proof, statistical induction, or entailment.
Lexical match is candidate relevance only. Episode-level mixed polarity
is fail-closed independently of CONTRADICTS graph edges.
"""

from __future__ import annotations

from architecture.cognitive.loop.binding import (
    APPLICABLE,
    ROLE_CAUTION,
    ROLE_CONSTRAINT,
    ROLE_EXPLANATION,
    ROLE_FACTUAL_PREMISE,
    ROLE_HISTORY,
    EvidenceBinding,
    addresses_task,
    with_role,
)
from architecture.cognitive.loop.support import SUPPORT_NON, SUPPORT_UNKNOWN
from architecture.cognitive.loop.episode import (
    MIXED_POLARITY,
    MIXED_UNCERTAIN,
    decision_bearing_supporters,
    episode_positive_block_reason,
)
from architecture.cognitive.loop.contracts import (
    Assumption,
    ClaimOrigin,
    CognitiveTask,
    CognitiveVerdict,
    EpistemicAnswer,
)
from architecture.cognitive.loop.inference import CandidateInference
from architecture.cognitive.loop.retrieval import tokens


def _overlap(statement: str, task: CognitiveTask) -> set[str]:
    return tokens(statement) & (tokens(task.question) | tokens(task.objective))


def _relevant(bindings: list[EvidenceBinding], task: CognitiveTask, role: str) -> list[EvidenceBinding]:
    """Lexical candidate relevance. Not evidence support."""
    return [b for b in with_role(bindings, role) if addresses_task(b.statement, task)]


def _supporting(bindings: list[EvidenceBinding], task: CognitiveTask, role: str) -> list[EvidenceBinding]:
    return [b for b in _relevant(bindings, task, role) if b.may_support_task()]


def _contradicting(bindings: list[EvidenceBinding], task: CognitiveTask, role: str) -> list[EvidenceBinding]:
    return [b for b in _relevant(bindings, task, role) if b.contradicts_task()]


def _episode_blocks_positive(
    bindings: list[EvidenceBinding], steps: list[str]
) -> CandidateInference | None:
    """Fail-closed mixed polarity/uncertainty. Graph edges are not required."""
    code = episode_positive_block_reason(bindings)
    if code == MIXED_POLARITY:
        steps.append("episode policy: SUPPORTS + CONTRADICTS; graph edge not required")
        contraries = [b for b in bindings if b.contradicts_task()]
        supporters = decision_bearing_supporters(bindings)
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Episode contested: supporting and contradicting evidence both present.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in supporters],
            supporting_ids=[b.memory_id for b in supporters],
            contradicting_ids=[b.memory_id for b in contraries],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if code == MIXED_UNCERTAIN:
        steps.append("episode policy: SUPPORTS + UNCERTAIN; unresolved")
        uncertain = [
            b
            for b in bindings
            if b.clause_force == "UNCERTAIN" and b.addresses_task_flag
        ]
        supporters = decision_bearing_supporters(bindings)
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.UNCERTAIN.value,
            conclusion="Episode unresolved: supporting evidence coexists with uncertain clauses.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in supporters],
            supporting_ids=[b.memory_id for b in supporters],
            contradicting_ids=[b.memory_id for b in uncertain],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    return None


def _no_support_missing(candidates: list[EvidenceBinding]) -> list[str]:
    if candidates:
        return ["TASK_SUPPORTING_PREMISE"]
    return ["TASK_RELEVANT_PREMISE"]


def _no_support_conclusion(candidates: list[EvidenceBinding]) -> str:
    if any(b.support_class in {SUPPORT_NON, SUPPORT_UNKNOWN} for b in candidates):
        return "Deduction refused: lexical match is not evidence support."
    if candidates:
        return "Deduction refused: retrieved evidence does not support the proposition."
    return "Deduction refused: no task-relevant factual premises."


def _opposes(statement: str) -> bool:
    blob = f" {statement.lower()} "
    return any(w in blob for w in (" is not ", " never ", " contradicts ", " opposite ", " failed "))


def _base_assumption() -> Assumption:
    return Assumption(
        assumption_id="ASM-000001",
        statement="Retrieved memories are the only evidence for this episode",
        basis="P5 loop does not query soak or Lane A",
        confidence=1.0,
        impact="conclusions cannot be stronger than bound evidence",
        origin=ClaimOrigin.ASSUMED.value,
    )


def _empty(task: CognitiveTask, extra: str) -> CandidateInference:
    return CandidateInference(
        verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
        epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
        conclusion=f"{extra} I don't know.",
        conclusion_class="UNKNOWN",
        assumptions=[_base_assumption()],
        steps=["empty or ineligible typed evidence"],
        missing_premises=["no eligible evidence"],
    )


def _lesson_failure_flags(
    bindings: list[EvidenceBinding],
) -> tuple[bool, bool, list[EvidenceBinding], list[EvidenceBinding]]:
    lessons = [
        b
        for b in with_role(bindings, ROLE_CONSTRAINT)
        if b.typed_class == "LESSON" and b.applicability == APPLICABLE
    ]
    fails = [
        b
        for b in with_role(bindings, ROLE_CAUTION)
        if b.typed_class == "FAILURE" and b.applicability != "NOT_APPLICABLE"
    ]
    return bool(lessons), bool(fails), lessons, fails


def reason_deductive(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    steps = [
        "DEDUCTIVE: premises must be typed FACTUAL_PREMISE that support the task",
        "LEXICAL_MATCH != EVIDENCE_SUPPORT",
    ]
    lexical = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
    premises = _supporting(bindings, task, ROLE_FACTUAL_PREMISE)
    contrary = _contradicting(bindings, task, ROLE_FACTUAL_PREMISE)
    requested = [rid for rid in task.requested_evidence if rid]
    present = {b.memory_id for b in lexical}
    missing = [rid for rid in requested if rid not in present]
    if missing:
        steps.append(f"missing requested premises: {missing}")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion="Deduction refused: required premise absent.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in premises],
            missing_premises=missing,
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if contrary and not premises:
        steps.append("direct contrary evidence; no supporting premises")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Deduction contested: evidence contradicts the proposition.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in contrary],
            contradicting_ids=[b.memory_id for b in contrary],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    blocked = _episode_blocks_positive(bindings, steps)
    if blocked:
        return blocked
    if not premises:
        typed_only = with_role(bindings, ROLE_FACTUAL_PREMISE)
        if typed_only:
            steps.append(
                "typed premises exist but none support the proposition "
                "(relevance ≠ entailment; lexical match ≠ support)"
            )
            missing = _no_support_missing(lexical)
            conclusion = _no_support_conclusion(lexical)
        else:
            steps.append("no FACTUAL_PREMISE bindings; lessons/hypotheses/opinions are ineligible")
            missing = ["FACTUAL_PREMISE"]
            conclusion = "Deduction refused: no typed factual premises."
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion=conclusion,
            conclusion_class="INFERENCE",
            missing_premises=missing,
            assumptions=[_base_assumption()],
            steps=steps,
        )
    contested = [b for b in premises if b.contradiction_state == "CONTESTED"]
    if contested:
        steps.append("contradicted factual premises retained")
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Deduction unresolved: contradictory premises.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in premises],
            supporting_ids=[b.memory_id for b in premises if b not in contested],
            contradicting_ids=[b.memory_id for b in contested],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    lesson_on, fail_on, lessons, fails = _lesson_failure_flags(bindings)
    if fail_on:
        steps.append("applicable FAILURE is a caution, not a premise — cannot deduce safety")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Deduction contested by applicable failure caution.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in premises],
            supporting_ids=[b.memory_id for b in premises],
            contradicting_ids=[b.memory_id for b in fails],
            assumptions=[_base_assumption()],
            steps=steps,
            failure_applied=True,
            lesson_applied=lesson_on,
        )
    steps.append(f"{len(premises)} current factual premises identified")
    cand = CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.PROBABLE.value,
        conclusion="Deductive reading: premises hold; conclusion does not exceed them.",
        conclusion_class="INFERENCE",
        premises=[b.memory_id for b in premises],
        supporting_ids=[b.memory_id for b in premises],
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
    )
    if lesson_on:
        cand.epistemic = EpistemicAnswer.UNCERTAIN.value
        cand.steps.append(
            "applicable LESSON constrains deduction; not a universal law"
        )
        cand.supporting_ids = list(cand.supporting_ids)
    return cand


def reason_inductive(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    steps = [
        "INDUCTIVE: examples → pattern → INFERENCE (never OBSERVED_FACT)",
        "LEXICAL_MATCH != EVIDENCE_SUPPORT",
    ]
    examples = _supporting(bindings, task, ROLE_FACTUAL_PREMISE) + [
        b
        for b in with_role(bindings, ROLE_HISTORY)
        if b.typed_class == "FAILURE" and b.may_support_task()
    ]
    contrary = _contradicting(bindings, task, ROLE_FACTUAL_PREMISE)
    # Deduplicate
    seen: set[str] = set()
    uniq: list[EvidenceBinding] = []
    for b in examples:
        if b.memory_id in seen:
            continue
        seen.add(b.memory_id)
        uniq.append(b)
    if contrary and not uniq:
        steps.append("only contrary examples; no supporting pattern")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Inductive pattern contested: examples contradict the proposition.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in contrary],
            contradicting_ids=[b.memory_id for b in contrary],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    blocked = _episode_blocks_positive(bindings, steps)
    if blocked:
        return blocked
    if len(uniq) < 2:
        steps.append(f"insufficient supporting examples n={len(uniq)}")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion="Induction refused: fewer than two supporting examples.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in uniq],
            missing_premises=["additional_examples"],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    opposing = [b for b in uniq if _opposes(b.statement)]
    supporting = [b for b in uniq if b not in opposing]
    if opposing and supporting:
        steps.append("conflicting examples; generalization contested")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Inductive pattern contested by conflicting examples.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in uniq],
            supporting_ids=[b.memory_id for b in supporting],
            contradicting_ids=[b.memory_id for b in opposing],
            assumptions=[_base_assumption()],
            steps=steps,
            failure_applied=any(b.typed_class == "FAILURE" for b in uniq),
        )
    lesson_on, fail_on, _, _ = _lesson_failure_flags(bindings)
    steps.append(f"pattern from {len(uniq)} examples remains an inference")
    return CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.UNCERTAIN.value,
        conclusion=f"Inductive inference from {len(uniq)} examples; not an observed fact.",
        conclusion_class="INFERENCE",
        premises=[b.memory_id for b in uniq],
        supporting_ids=[b.memory_id for b in uniq],
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
        failure_applied=fail_on,
    )


def reason_abductive(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    steps = [
        "ABDUCTIVE: observations + candidates → best explanation, not truth",
        "LEXICAL_MATCH != EVIDENCE_SUPPORT",
    ]
    observations = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
    supporting_obs = _supporting(bindings, task, ROLE_FACTUAL_PREMISE)
    contrary_obs = _contradicting(bindings, task, ROLE_FACTUAL_PREMISE)
    candidates = with_role(bindings, ROLE_EXPLANATION)
    if any(b.contradiction_state == "CONTESTED" for b in observations):
        steps.append("contradictory observations; explanations unresolved")
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Abduction unresolved: observations contradict.",
            conclusion_class="HYPOTHESIS",
            premises=[b.memory_id for b in observations],
            contradicting_ids=[
                b.memory_id for b in observations if b.contradiction_state == "CONTESTED"
            ],
            alternatives=[b.statement for b in candidates],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if not observations:
        steps.append("no observations to explain")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion="Abduction refused: no typed observations.",
            conclusion_class="HYPOTHESIS",
            missing_premises=["OBSERVED_FACT"],
            alternatives=[b.statement for b in candidates],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if contrary_obs and not supporting_obs:
        steps.append("observations contradict the proposition; no supporting observation")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Abduction contested: observations contradict the proposition.",
            conclusion_class="HYPOTHESIS",
            premises=[b.memory_id for b in contrary_obs],
            contradicting_ids=[b.memory_id for b in contrary_obs],
            alternatives=[b.statement for b in candidates],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    blocked = _episode_blocks_positive(bindings, steps)
    if blocked:
        return blocked
    if not supporting_obs:
        steps.append("lexical/context observations are not support for the proposition")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion="Abduction refused: observations do not support the proposition.",
            conclusion_class="HYPOTHESIS",
            premises=[b.memory_id for b in observations],
            missing_premises=["TASK_SUPPORTING_PREMISE"],
            alternatives=[b.statement for b in candidates],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if not candidates:
        steps.append("no hypothesis/inference candidates; explanation unknown")
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion="Abduction unresolved: no candidate explanations.",
            conclusion_class="HYPOTHESIS",
            premises=[b.memory_id for b in observations],
            supporting_ids=[b.memory_id for b in observations],
            alternatives=[],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    scored: list[tuple[int, EvidenceBinding]] = []
    for cand in candidates:
        scored.append((len(_overlap(cand.statement, task)), cand))
    scored.sort(key=lambda t: (-t[0], t[1].memory_id))
    best_n, best = scored[0]
    ties = [c for n, c in scored if n == best_n]
    alts = [c.statement for _, c in scored]
    if len(ties) > 1:
        steps.append("tied explanation scores; unresolved")
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.UNCERTAIN.value,
            conclusion="Abduction unresolved: competing explanations equally supported.",
            conclusion_class="HYPOTHESIS",
            premises=[b.memory_id for b in observations],
            supporting_ids=[b.memory_id for b in observations],
            alternatives=alts,
            assumptions=[_base_assumption()],
            steps=steps,
        )
    steps.append(f"best explanation candidate {best.memory_id}; not promoted to fact")
    lesson_on, fail_on, _, _ = _lesson_failure_flags(bindings)
    return CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.UNCERTAIN.value,
        conclusion=f"Best explanation candidate (not truth): {best.statement}",
        conclusion_class="HYPOTHESIS",
        premises=[b.memory_id for b in supporting_obs],
        supporting_ids=[b.memory_id for b in supporting_obs],
        alternatives=alts,
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
        failure_applied=fail_on,
    )


def reason_comparative(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    steps = [
        "COMPARATIVE: aligned dimensions; missing is missing, not zero",
        "LEXICAL_MATCH != EVIDENCE_SUPPORT",
    ]
    lexical_facts = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
    facts = _supporting(bindings, task, ROLE_FACTUAL_PREMISE)
    contrary = _contradicting(bindings, task, ROLE_FACTUAL_PREMISE)
    others = [b for b in bindings if b.typed_class != "OBSERVED_FACT"]
    contested = [b for b in bindings if b.contradiction_state == "CONTESTED"]
    dimensions = {
        "typed_current_facts": len(facts),
        "non_fact_items": len(others),
        "contradicted_items": len(contested),
        "unknown_age": len([b for b in bindings if b.temporal_state == "UNKNOWN_AGE"]),
    }
    steps.append(f"dimensions={dimensions}")
    if contested:
        steps.append("both sides of contradiction retained")
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Comparison unresolved: contradictory evidence on aligned ids.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in facts],
            contradicting_ids=[b.memory_id for b in contested],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if contrary and not facts:
        steps.append("only contrary factual dimension; no supporting side")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Comparison contested: evidence contradicts the proposition.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in contrary],
            contradicting_ids=[b.memory_id for b in contrary],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    blocked = _episode_blocks_positive(bindings, steps)
    if blocked:
        return blocked
    if not facts and not others:
        return _empty(task, "Comparison has no bound evidence.")
    if not facts:
        steps.append("no supporting factual side; non-facts are labeled and not treated as zero-facts")
        missing = ["TASK_SUPPORTING_PREMISE"] if lexical_facts else ["FACTUAL_PREMISE"]
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion="Comparison incomplete: missing supporting factual dimension.",
            conclusion_class="INFERENCE",
            missing_premises=missing,
            assumptions=[_base_assumption()],
            steps=steps,
        )
    lesson_on, fail_on, _, fails = _lesson_failure_flags(bindings)
    if fail_on:
        steps.append("applicable failure is a compared caution, not a fact")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Comparison contested: fact vs applicable failure caution.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in facts],
            supporting_ids=[b.memory_id for b in facts],
            contradicting_ids=[b.memory_id for b in fails],
            assumptions=[_base_assumption()],
            steps=steps,
            failure_applied=True,
            lesson_applied=lesson_on,
        )
    return CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.UNCERTAIN.value if lesson_on else EpistemicAnswer.PROBABLE.value,
        conclusion="Comparative reading over typed dimensions; missing fields not scored as zero.",
        conclusion_class="INFERENCE",
        premises=[b.memory_id for b in facts],
        supporting_ids=[b.memory_id for b in facts],
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
        failure_applied=fail_on,
    )


def reason_temporal(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    steps = [
        "TEMPORAL: stale ≠ false; dated ≠ proven current",
        "LEXICAL_MATCH != EVIDENCE_SUPPORT",
    ]
    usable = _supporting(bindings, task, ROLE_FACTUAL_PREMISE)
    contrary = _contradicting(bindings, task, ROLE_FACTUAL_PREMISE)
    aging = [b for b in usable if b.temporal_state in {"CURRENT", "AGING"}]
    dated = [b for b in usable if b.temporal_state == "DATED"]
    stale = [b for b in bindings if b.temporal_state in {"STALE", "SUPERSEDED", "HISTORICAL"}]
    unknown_age = [b for b in bindings if b.temporal_state == "UNKNOWN_AGE"]
    steps.append(
        f"aging_or_current={len(aging)} dated={len(dated)} "
        f"stale_or_historical={len(stale)} unknown_age={len(unknown_age)}"
    )
    if unknown_age and not aging and not dated and not stale:
        steps.append("only unknown-age evidence")
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion="Temporally unresolved: evidence age unknown.",
            conclusion_class="INFERENCE",
            temporal_scope="UNKNOWN_AGE",
            assumptions=[_base_assumption()],
            steps=steps,
            missing_premises=["observed_at"],
        )
    if stale and not aging and not dated:
        steps.append("historical evidence retained; not used as current")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.STALE.value,
            conclusion="Temporal reading: only stale/historical evidence; stale is not current.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in stale],
            supporting_ids=[b.memory_id for b in stale],
            temporal_scope="HISTORICAL",
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if contrary and not aging and not dated:
        steps.append("dated contrary evidence; no supporting temporal premise")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Temporal reading contested: dated evidence contradicts the proposition.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in contrary],
            contradicting_ids=[b.memory_id for b in contrary],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    blocked = _episode_blocks_positive(bindings, steps)
    if blocked:
        return blocked
    if not aging and not dated:
        return _empty(task, "Temporal reading has no dated supporting facts.")
    lesson_on, fail_on, _, _ = _lesson_failure_flags(bindings)
    if aging:
        scope = "AGING" if not any(b.temporal_state == "CURRENT" for b in aging) else "CURRENT"
        conclusion = "Temporal reading uses decay-aging or current observations; stale retained as history."
        premises = aging
    else:
        scope = "DATED"
        conclusion = (
            "Temporal reading uses dated observations; a timestamp does not prove freshness."
        )
        premises = dated
    return CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.PROBABLE.value,
        conclusion=conclusion,
        conclusion_class="INFERENCE",
        premises=[b.memory_id for b in premises],
        supporting_ids=[b.memory_id for b in premises],
        temporal_scope=scope,
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
        failure_applied=fail_on,
    )


def reason_adversarial(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    steps = [
        "ADVERSARIAL: search contradictions, type misuse, stale-as-current, lookalikes, weak premises"
    ]
    facts = _supporting(bindings, task, ROLE_FACTUAL_PREMISE)
    contrary = _contradicting(bindings, task, ROLE_FACTUAL_PREMISE)
    contested = [b for b in bindings if b.contradiction_state == "CONTESTED"]
    opinions = [b for b in bindings if b.typed_class == "OPINION"]
    hyps = [b for b in bindings if b.typed_class == "HYPOTHESIS"]
    preds = [b for b in bindings if b.typed_class == "PREDICTION"]
    sims = [b for b in bindings if b.typed_class == "SIMULATION"]
    stale_facts = [
        b
        for b in bindings
        if b.typed_class == "OBSERVED_FACT" and b.temporal_state in {"STALE", "SUPERSEDED"}
    ]
    lookalikes = [
        b
        for b in bindings
        if any("LOOKALIKE" in r or "GENERIC" in r for r in b.match_reasons)
    ]
    lesson_on, fail_on, _, fails = _lesson_failure_flags(bindings)
    if contested:
        steps.append("contradiction present — do not pick a side")
        return CandidateInference(
            verdict=CognitiveVerdict.UNRESOLVED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Adversarial: contradiction retained; no silent resolution.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in facts],
            contradicting_ids=[b.memory_id for b in contested],
            assumptions=[_base_assumption()],
            steps=steps,
            lesson_applied=lesson_on,
            failure_applied=fail_on,
        )
    if fail_on:
        steps.append("applicable failure warning prioritized")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Adversarial: applicable prior failure warns against an uncontested success claim.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in facts],
            supporting_ids=[b.memory_id for b in facts],
            contradicting_ids=[b.memory_id for b in fails],
            assumptions=[_base_assumption()],
            steps=steps,
            failure_applied=True,
            lesson_applied=lesson_on,
        )
    if opinions or preds or sims:
        steps.append("non-factual types present; cannot establish fact")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion="Adversarial: opinion/prediction/simulation cannot establish fact.",
            conclusion_class="INFERENCE",
            type_violations=[b.memory_id for b in opinions + preds + sims],
            premises=[b.memory_id for b in facts],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if hyps and not facts:
        steps.append("hypothesis without observations")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion="Adversarial: hypothesis is not a fact.",
            conclusion_class="HYPOTHESIS",
            type_violations=[b.memory_id for b in hyps],
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if lookalikes and not facts:
        steps.append("lookalike-only context")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion="Adversarial: lookalike evidence is not identity.",
            conclusion_class="INFERENCE",
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if stale_facts and not facts:
        steps.append("stale observation must not be treated as current")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.STALE.value,
            conclusion="Adversarial: stale evidence is not current.",
            conclusion_class="INFERENCE",
            temporal_scope="HISTORICAL",
            assumptions=[_base_assumption()],
            steps=steps,
        )
    if contrary and not facts:
        steps.append("contrary evidence only; no supporting factual premise")
        return CandidateInference(
            verdict=CognitiveVerdict.CONTESTED.value,
            epistemic=EpistemicAnswer.CONTESTED.value,
            conclusion="Adversarial: evidence contradicts the proposition.",
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in contrary],
            contradicting_ids=[b.memory_id for b in contrary],
            assumptions=[_base_assumption()],
            steps=steps,
            lesson_applied=lesson_on,
        )
    blocked = _episode_blocks_positive(bindings, steps)
    if blocked:
        return blocked
    if not facts:
        return _empty(task, "Adversarial review found no supporting factual premises.")
    steps.append("supporting facts present; still refuse certainty")
    return CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.UNCERTAIN.value,
        conclusion="Adversarial stance: weakly supported at most; seek falsifiers.",
        conclusion_class="INFERENCE",
        premises=[b.memory_id for b in facts],
        supporting_ids=[b.memory_id for b in facts],
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
    )


def reason_metacognitive(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    """Inventory transform. Decision-bearing evidence is may_support_task() only.

    Lexical `_relevant` items are counted, never cited as support. Non-supporting
    lexical matches cannot upgrade an episode because a real supporter is also present.
    """
    facts = with_role(bindings, ROLE_FACTUAL_PREMISE)
    relevant = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
    supporters = decision_bearing_supporters(bindings)
    inferred = [b for b in bindings if b.typed_class in {"INFERENCE", "DERIVED_FACT"}]
    unknown_n = [b for b in bindings if b.typed_class == "UNKNOWN"]
    steps = [
        "METACOGNITIVE: inventory known / inferred / unknown; not self-awareness",
        "decision-bearing = may_support_task(); lexical inventory is not support",
        f"known_facts={len(facts)} task_relevant={len(relevant)} "
        f"decision_bearing={len(supporters)} inferred={len(inferred)} "
        f"typed_unknown={len(unknown_n)}",
        "capability limitation: no causal or counterfactual engine",
    ]
    lesson_on, fail_on, _, _ = _lesson_failure_flags(bindings)
    blocked = _episode_blocks_positive(bindings, steps)
    if blocked:
        blocked.conclusion = (
            f"Known observations: {len(facts)} ({len(supporters)} decision-bearing). "
            f"{blocked.conclusion} Capability limitation: no world model."
        )
        blocked.lesson_applied = lesson_on
        blocked.failure_applied = fail_on
        return blocked
    if not supporters:
        steps.append("inventory is not an answer; no decision-bearing supporter")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion=(
                f"Known observations: {len(facts)} ({len(relevant)} address the task "
                "lexically; 0 decision-bearing). Inventory is not an answer. "
                "Capability limitation: no world model."
            ),
            conclusion_class="INFERENCE",
            missing_premises=["TASK_SUPPORTING_PREMISE"] if facts else ["FACTUAL_PREMISE"],
            assumptions=[_base_assumption()],
            steps=steps,
            lesson_applied=lesson_on,
            failure_applied=fail_on,
        )
    steps.append(f"{len(supporters)} decision-bearing supporters; lexical inventory not cited")
    return CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.UNCERTAIN.value,
        conclusion=(
            f"Known observations: {len(facts)} ({len(supporters)} decision-bearing). "
            "Verdict remains uncertain; no claim of self-awareness. "
            "Capability limitation: no world model."
        ),
        conclusion_class="INFERENCE",
        premises=[b.memory_id for b in supporters],
        supporting_ids=[b.memory_id for b in supporters],
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
        failure_applied=fail_on,
    )


MODE_FNS = {
    "DEDUCTIVE": reason_deductive,
    "INDUCTIVE": reason_inductive,
    "ABDUCTIVE": reason_abductive,
    "COMPARATIVE": reason_comparative,
    "TEMPORAL": reason_temporal,
    "ADVERSARIAL": reason_adversarial,
    "METACOGNITIVE": reason_metacognitive,
}
