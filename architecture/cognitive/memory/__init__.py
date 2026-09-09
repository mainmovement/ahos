"""Lane-B provenance-bearing cognitive memory substrate (P2).

This is not AGI memory. It is an isolated, tested store with provenance,
contradiction edges, revisions, decay-without-deletion, and agent namespaces.
"""

from architecture.cognitive.memory.consolidation import (
    ConsolidationCandidate,
    ConsolidationGate,
)
from architecture.cognitive.memory.record import (
    EpistemicViolation,
    InvalidProvenanceError,
    MemoryRecord,
    compute_integrity_hash,
)
from architecture.cognitive.memory.store import (
    CognitiveMemoryStore,
    IntegrityError,
    MemoryAuthorizationError,
    MemoryEdge,
    SoakBoundaryError,
    assert_not_soak_db,
)
from architecture.cognitive.memory.types import (
    UNKNOWN,
    ContradictionState,
    DecayState,
    EdgeRelation,
    EpistemicKind,
    MemoryType,
    SourceType,
    WORLD_MODEL_OBJECT_KINDS,
)
from architecture.cognitive.memory.self_query import (
    build_self_research_with_memory,
    memory_query_summary,
)

__all__ = [
    "UNKNOWN",
    "CognitiveMemoryStore",
    "ConsolidationCandidate",
    "ConsolidationGate",
    "ContradictionState",
    "DecayState",
    "EdgeRelation",
    "EpistemicKind",
    "EpistemicViolation",
    "IntegrityError",
    "InvalidProvenanceError",
    "MemoryAuthorizationError",
    "MemoryEdge",
    "MemoryRecord",
    "MemoryType",
    "SoakBoundaryError",
    "SourceType",
    "WORLD_MODEL_OBJECT_KINDS",
    "assert_not_soak_db",
    "build_self_research_with_memory",
    "compute_integrity_hash",
    "memory_query_summary",
]
