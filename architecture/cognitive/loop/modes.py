"""Mode-specific reasoners over EvidenceBinding lists. LLM-free."""

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
    return [b for b in with_role(bindings, role) if addresses_task(b.statement, task)]


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
    steps = ["DEDUCTIVE: premises must be typed FACTUAL_PREMISE that address the task"]
    premises = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
    requested = [rid for rid in task.requested_evidence if rid]
    present = {b.memory_id for b in premises}
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
    if not premises:
        typed_only = with_role(bindings, ROLE_FACTUAL_PREMISE)
        if typed_only:
            steps.append("typed premises exist but none address the task (valid type ≠ relevant content)")
            missing = ["TASK_RELEVANT_PREMISE"]
            conclusion = "Deduction refused: no task-relevant factual premises."
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
    steps = ["INDUCTIVE: examples → pattern → INFERENCE (never OBSERVED_FACT)"]
    examples = _relevant(bindings, task, ROLE_FACTUAL_PREMISE) + [
        b
        for b in with_role(bindings, ROLE_HISTORY)
        if b.typed_class == "FAILURE" and addresses_task(b.statement, task)
    ]
    # Deduplicate
    seen: set[str] = set()
    uniq: list[EvidenceBinding] = []
    for b in examples:
        if b.memory_id in seen:
            continue
        seen.add(b.memory_id)
        uniq.append(b)
    if len(uniq) < 2:
        steps.append(f"insufficient examples n={len(uniq)}")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion="Induction refused: fewer than two typed examples.",
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
    steps = ["ABDUCTIVE: observations + candidates → best explanation, not truth"]
    observations = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
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
        premises=[b.memory_id for b in observations],
        supporting_ids=[best.memory_id] + [b.memory_id for b in observations],
        alternatives=alts,
        assumptions=[_base_assumption()],
        steps=steps,
        lesson_applied=lesson_on,
        failure_applied=fail_on,
    )


def reason_comparative(
    task: CognitiveTask, bindings: list[EvidenceBinding]
) -> CandidateInference:
    steps = ["COMPARATIVE: aligned dimensions; missing is missing, not zero"]
    facts = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
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
    if not facts and not others:
        return _empty(task, "Comparison has no bound evidence.")
    if not facts:
        steps.append("no factual side; non-facts are labeled and not treated as zero-facts")
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.INSUFFICIENT_EVIDENCE.value,
            conclusion="Comparison incomplete: missing factual dimension.",
            conclusion_class="INFERENCE",
            missing_premises=["FACTUAL_PREMISE"],
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
    steps = ["TEMPORAL: stale ≠ false; dated ≠ proven current"]
    usable = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
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
    if not aging and not dated:
        return _empty(task, "Temporal reading has no dated task-relevant facts.")
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
    facts = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
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
    if not facts:
        return _empty(task, "Adversarial review found no factual premises.")
    steps.append("facts present; still refuse certainty")
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
    facts = with_role(bindings, ROLE_FACTUAL_PREMISE)
    relevant = _relevant(bindings, task, ROLE_FACTUAL_PREMISE)
    inferred = [b for b in bindings if b.typed_class in {"INFERENCE", "DERIVED_FACT"}]
    unknown_n = [b for b in bindings if b.typed_class == "UNKNOWN"]
    steps = [
        "METACOGNITIVE: inventory known / inferred / unknown; not self-awareness",
        f"known_facts={len(facts)} task_relevant={len(relevant)} "
        f"inferred={len(inferred)} typed_unknown={len(unknown_n)}",
        "capability limitation: no causal or counterfactual engine",
    ]
    lesson_on, fail_on, _, _ = _lesson_failure_flags(bindings)
    if not facts:
        return CandidateInference(
            verdict=CognitiveVerdict.INSUFFICIENT_EVIDENCE.value,
            epistemic=EpistemicAnswer.UNKNOWN.value,
            conclusion=(
                f"Known observations: 0. Inferred: {len(inferred)}. "
                "Unknowns remain unknown. Capability limitation: no world model."
            ),
            conclusion_class="INFERENCE",
            missing_premises=["FACTUAL_PREMISE"],
            assumptions=[_base_assumption()],
            steps=steps,
            lesson_applied=lesson_on,
            failure_applied=fail_on,
        )
    if not relevant:
        steps.append("inventory includes observations that do not address the task")
        return CandidateInference(
            verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
            epistemic=EpistemicAnswer.UNCERTAIN.value,
            conclusion=(
                f"Known observations: {len(facts)} (0 address the task). "
                "Inventory is not an answer. Capability limitation: no world model."
            ),
            conclusion_class="INFERENCE",
            premises=[b.memory_id for b in facts],
            supporting_ids=[b.memory_id for b in facts],
            assumptions=[_base_assumption()],
            steps=steps,
            lesson_applied=lesson_on,
            failure_applied=fail_on,
        )
    return CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic=EpistemicAnswer.UNCERTAIN.value,
        conclusion=(
            f"Known observations: {len(facts)} ({len(relevant)} address the task). "
            "Verdict remains uncertain; no claim of self-awareness. "
            "Capability limitation: no world model."
        ),
        conclusion_class="INFERENCE",
        premises=[b.memory_id for b in relevant],
        supporting_ids=[b.memory_id for b in relevant],
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
