"""Cognitive memory vocabularies. Not a world model and not AGI."""

from __future__ import annotations

from enum import Enum


UNKNOWN = "UNKNOWN"

# Dedicated Lane-B filename. Must never collide with soak / Lane-A stores.
COGNITIVE_MEMORY_DB_NAME = "ahos_cognitive_memory.sqlite"
FORBIDDEN_DB_NAMES = frozenset(
    {
        "e01_discovery.sqlite",
        "paper_trading.sqlite",
        "ahos_local.sqlite",
        "ahos_knowledge.sqlite",
    }
)

SCHEMA_VERSION = 1


class MemoryType(str, Enum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    HYPOTHESIS = "HYPOTHESIS"
    EXPERIMENT = "EXPERIMENT"
    FAILURE = "FAILURE"
    AGENT = "AGENT"
    WORLD_MODEL = "WORLD_MODEL"
    SELF_MODEL = "SELF_MODEL"


class EpistemicKind(str, Enum):
    OBSERVED_FACT = "OBSERVED_FACT"
    DERIVED_FACT = "DERIVED_FACT"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    PREDICTION = "PREDICTION"
    SIMULATION = "SIMULATION"
    OPINION = "OPINION"
    PROCEDURE = "PROCEDURE"
    LESSON = "LESSON"


class ContradictionState(str, Enum):
    UNCONTESTED = "UNCONTESTED"
    SUPPORTED = "SUPPORTED"
    CONTESTED = "CONTESTED"
    CONTRADICTED = "CONTRADICTED"
    SUPERSEDED = "SUPERSEDED"
    RESOLVED = "RESOLVED"
    UNKNOWN = "UNKNOWN"


class DecayState(str, Enum):
    ACTIVE = "ACTIVE"
    AGING = "AGING"
    STALE = "STALE"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"


class SourceType(str, Enum):
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"
    SENSOR = "SENSOR"
    DATABASE = "DATABASE"
    HYPOTHESIS_STORE = "HYPOTHESIS_STORE"
    EXPERIMENT_LEDGER = "EXPERIMENT_LEDGER"
    SCORE_LEDGER = "SCORE_LEDGER"
    AI_MODEL = "AI_MODEL"
    AGENT = "AGENT"
    UNKNOWN = "UNKNOWN"


class EdgeRelation(str, Enum):
    CONTRADICTS = "CONTRADICTS"
    SUPPORTS = "SUPPORTS"
    SUPERSEDES = "SUPERSEDES"
    DERIVED_FROM = "DERIVED_FROM"
    RELATED = "RELATED"
    OUTCOME_OF = "OUTCOME_OF"


class EdgeResolution(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    UNKNOWN = "UNKNOWN"


# World-model payload keys that MAY be stored. Storing them is not a world model.
WORLD_MODEL_OBJECT_KINDS = frozenset(
    {
        "ENTITY",
        "RELATION",
        "EVENT",
        "STATE",
        "CAUSE",
        "EFFECT",
        "UNCERTAINTY",
        "TIME",
        "OBSERVATION",
        "COUNTERFACTUAL",
    }
)

AI_SOURCE_TYPES = frozenset({SourceType.AI_MODEL, SourceType.AGENT})
FACT_KINDS = frozenset({EpistemicKind.OBSERVED_FACT, EpistemicKind.DERIVED_FACT})
