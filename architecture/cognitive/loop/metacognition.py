"""Structured metacognitive state from a P3 episode. Not a metacognitive agent."""

from __future__ import annotations

from typing import Any

from architecture.cognitive.loop.contracts import CognitiveContext, CognitiveResult


def metacognitive_state(
    result: CognitiveResult,
    ctx: CognitiveContext | None = None,
) -> dict[str, Any]:
    assembled = ctx or result.context
    facts = [] if assembled is None else [i.memory_id for i in assembled.facts]
    unknowns = () if assembled is None else assembled.unknowns
    contradictions = () if assembled is None else assembled.contradictions
    failures = [] if assembled is None else [i.memory_id for i in assembled.failures]
    assumptions = [a.as_dict() for a in result.trace.assumptions]
    return {
        "what_i_know": facts,
        "what_i_dont_know": list(unknowns),
        "why_i_believe_it": list(result.trace.steps),
        "what_evidence_supports_it": list(result.trace.selected_ids),
        "what_contradicts_it": list(contradictions),
        "what_assumptions_i_made": assumptions,
        "what_failed_before": failures,
        "what_experiment_should_resolve_uncertainty": result.experiment_id or "",
        "verdict": result.verdict,
        "epistemic": result.epistemic,
    }
