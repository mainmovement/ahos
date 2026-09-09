# AHOS Cognitive Memory Architecture v1.0

**Status:** Lane-B substrate IMPLEMENTED_AND_VERIFIED (unit tests). **Not AGI memory.**  
**Code:** `architecture/cognitive/memory/`  
**DB:** `data/ahos_cognitive_memory.sqlite` (gitignored; never soak DBs)  
**Tests:** `tests/test_cognitive_memory.py`  
**Base:** main `1f4febb9b373e01271654515db58dfe72371a0c0` (post PR #87)

## Architecture

Isolated SQLite, schema version 1, append-only `(memory_id, revision)` rows, relation `memory_edges`, failure fingerprints in `failure_stats`.

```text
Lane A / Soak DBs (e01_discovery, paper_trading, ahos_local)
        X  no open, no write, filename guard
ahos_knowledge.sqlite (VersionedClaimStore) — not replaced; not opened by this store
        X
Lane B CognitiveMemoryStore (ahos_cognitive_memory.sqlite)
```

`config.paths.get_cognitive_memory_db_path()` is the default path helper. Tests pass an explicit tmp path.

## Memory classes

| Type | Role | Notes |
|------|------|-------|
| WORKING | TTL + session/task | Cannot omit TTL; expiry → STALE, not delete |
| EPISODIC | What happened | Event time `observed_at` vs ingestion `created_at` |
| SEMANTIC | Beliefs | Consolidation cannot write OBSERVED_FACT |
| PROCEDURAL | How-to | Version via revisions |
| HYPOTHESIS / EXPERIMENT | Links | Does not replace HypothesisStore / ExperimentLedger |
| FAILURE | Errors | Recurrence via fingerprint |
| AGENT | Per-namespace lessons | Default queries do not leak other namespaces |
| WORLD_MODEL | Payload kinds only | Not a causal graph |
| SELF_MODEL | Reserved type | No live soak observer |

## Epistemic kinds

`OBSERVED_FACT` · `DERIVED_FACT` · `INFERENCE` · `HYPOTHESIS` · `PREDICTION` · `SIMULATION` · `OPINION` · `PROCEDURE` · `LESSON`

AI_MODEL / AGENT sources cannot be stored as OBSERVED_FACT or DERIVED_FACT.

## Provenance

Required tokens (use `UNKNOWN` if unknown; empty string rejected): `source_id`, `source_location`, `producer`, `producer_version`, `domain`, `context`. Also: `source_type`, `created_at`, `observed_at` (nullable = unknown event time), `confidence` (nullable), `valid_from`/`valid_until`, `integrity_hash`.

## Contradiction

Edges `CONTRADICTS` / `SUPPORTS` / `SUPERSEDES` / `DERIVED_FROM` / `RELATED`. Both records kept. Newer claim does not delete older observation. Resolve marks edge RESOLVED and appends revisions.

## Temporal / decay

`created_at` = when AHOS ingested this revision. `observed_at` = when the event happened. `apply_decay` sets AGING/STALE/ARCHIVED/SUPERSEDED. **STALE ≠ FALSE.**

## Retrieval

`get`, `history`, `find_by_type/source/domain/time_range/hypothesis/experiment/agent`, `find_failures`, `find_contradictions`, `find_supporting_memories`, `find_related_memories`, `recent`, `relevant_context` (deterministic rank, not embeddings).

## Agent namespaces

`find_by_agent(id)` returns `agent_namespace == id` only. `relevant_context(agent_id=)` excludes other namespaces; empty namespace is shared.

## Security

`authorize_execution` / `authorize_trading` / `elevate_autonomy` always raise. PAPER_ONLY and L1_ANALYZE unchanged. Memory cannot promote itself.

## Future vector extension

Not implemented. A later adapter may index `memory_id` → embedding without replacing this schema.

## Future world-model integration

`record_world_model_object` stores ENTITY/RELATION/EVENT/… payloads. That is storage prep, not a world model (ACI-GAP-002 remains OPEN).

## Current limitations

- Runtime/soak events are not auto-ingested.
- VersionedClaimStore is not dual-written.
- `relevant_context` is heuristic rank, not intelligence.
- No vector search, no GPU, no cloud DB.
- ACI-GAP-001 remains PARTIAL until production wiring exists without touching soak writes.
