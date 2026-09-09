"""Governed consolidation. Does not auto-promote model output into semantic truth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from architecture.cognitive.memory.record import EpistemicViolation, MemoryRecord
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType


@dataclass(frozen=True)
class ConsolidationCandidate:
    source_memory_ids: tuple[str, ...]
    statement: str
    proposed_kind: str
    requires_human: bool
    blocked_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_memory_ids": list(self.source_memory_ids),
            "statement": self.statement,
            "proposed_kind": self.proposed_kind,
            "requires_human": self.requires_human,
            "blocked_reason": self.blocked_reason,
        }


class ConsolidationGate:
    """Episodic → candidate semantic. Writes only on explicit accept()."""

    def propose_from_episodes(
        self,
        store: CognitiveMemoryStore,
        episode_ids: Sequence[str],
        *,
        statement: str,
    ) -> ConsolidationCandidate:
        if not episode_ids:
            raise ValueError("episode_ids required")
        kinds: list[str] = []
        sources: list[str] = []
        for mid in episode_ids:
            rec = store.get(mid)
            if rec is None:
                raise KeyError(mid)
            kinds.append(rec.epistemic_kind)
            sources.append(rec.source_type)
        proposed = EpistemicKind.INFERENCE.value
        blocked = ""
        if any(s == SourceType.AI_MODEL.value for s in sources):
            proposed = EpistemicKind.OPINION.value
            blocked = "AI_MODEL episodes cannot become OBSERVED_FACT via consolidation"
        if any(k == EpistemicKind.OPINION.value for k in kinds):
            proposed = EpistemicKind.OPINION.value
        if any(k == EpistemicKind.SIMULATION.value for k in kinds) and proposed != EpistemicKind.OPINION.value:
            proposed = EpistemicKind.SIMULATION.value
        return ConsolidationCandidate(
            source_memory_ids=tuple(episode_ids),
            statement=statement.strip(),
            proposed_kind=proposed,
            requires_human=True,
            blocked_reason=blocked,
        )

    def accept(
        self,
        store: CognitiveMemoryStore,
        candidate: ConsolidationCandidate,
        *,
        actor: str,
        epistemic_kind: EpistemicKind | str,
        producer: str,
    ) -> MemoryRecord:
        kind = EpistemicKind(epistemic_kind)
        if kind in {EpistemicKind.OBSERVED_FACT, EpistemicKind.DERIVED_FACT}:
            raise EpistemicViolation(
                "consolidation cannot write OBSERVED_FACT or DERIVED_FACT"
            )
        if not actor.strip():
            raise ValueError("actor required")
        return store.remember(
            memory_type=MemoryType.SEMANTIC,
            epistemic_kind=kind,
            statement=candidate.statement,
            source_type=SourceType.SYSTEM,
            source_id="consolidation_gate",
            source_location="architecture.cognitive.memory.consolidation",
            producer=producer,
            producer_version="p2-v1",
            domain="COGNITIVE_CORE",
            context=f"accepted_by={actor}",
            derived_from=candidate.source_memory_ids,
            payload={
                "requires_human": candidate.requires_human,
                "proposed_kind": candidate.proposed_kind,
                "accepted_kind": kind.value,
            },
        )
