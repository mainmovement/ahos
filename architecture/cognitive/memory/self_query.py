"""Optional memory-backed fields for self-research. Not a live soak observer."""

from __future__ import annotations

from typing import Any

from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.self_research import SelfResearchReport, build_self_research_report


def memory_query_summary(store: CognitiveMemoryStore) -> dict[str, Any]:
    """Deterministic counts from the Lane-B memory DB only."""
    failures = store.find_failures()
    contradictions = store.find_contradictions()
    return {
        "failure_count": len(failures),
        "open_contradiction_count": sum(
            1 for e in contradictions if e.resolution == "OPEN"
        ),
        "recent_ids": [r.memory_id for r in store.recent(limit=5)],
        "live_observer": False,
        "soak_authority": False,
    }


def build_self_research_with_memory(
    *,
    snapshot: dict[str, Any],
    data_label: str,
    soak_snapshot_is_authoritative: bool,
    store: CognitiveMemoryStore,
) -> tuple[SelfResearchReport, dict[str, Any]]:
    """Same snapshot builder as P1, plus an explicit memory query sidecar.

    The sidecar is not soak evidence.
    """
    summary = memory_query_summary(store)
    extra_unknowns = ()
    extra_gaps = ()
    if summary["failure_count"]:
        extra_gaps = (f"Lane-B memory records {summary['failure_count']} failure memories.",)
    report = build_self_research_report(
        snapshot=snapshot,
        data_label=data_label,
        soak_snapshot_is_authoritative=soak_snapshot_is_authoritative,
        extra_unknowns=extra_unknowns,
        extra_gaps=extra_gaps,
    )
    return report, summary
