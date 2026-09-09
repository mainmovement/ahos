# MEMORY_ARCHITECTURE_AUDIT (P2)

**UTC date:** 2026-09-09  
**Main baseline:** `1f4febb9b373e01271654515db58dfe72371a0c0`  
**Skills used:** `ahos-governance-context`, `ahos-change-verification` (freeze + validate_imports + pytest). No fake skill integration.

## Classification of what already existed

| Mechanism | Class | Evidence |
|-----------|-------|----------|
| Working memory | MISSING (pre-P2) | process-only evidence bundles |
| Episodic (soak observations) | PARTIAL | Lane-A sqlite — **must not be this store** |
| Semantic claims | PARTIAL | `architecture/knowledge/store.py` VersionedClaimStore + contradiction edges; claims-only, not typed WM/episodic/failure/agent |
| Procedural | PARTIAL | scripts + frozen Lane A; not versioned memory rows |
| Hypothesis memory | PARTIAL | `HypothesisStore` JSONL HYP- ids — **kept, not replaced** |
| Experiment memory | PARTIAL | `ExperimentLedger` JSONL — **kept, not replaced** |
| Failure memory | PARTIAL | experiment ledger failure_reason; paper lessons; no recurrence query API |
| Agent memory | MISSING | passports `memory_bearing=false` |
| Causal / world-model memory | NOT_IMPLEMENTED | `world_model.py` inventory; hindsight is financial oos |
| Self-model | PARTIAL | snapshot self-research, not live observer |
| Provenance | PARTIAL | claims sha, score_ledger evidence_sha256 |
| Contradiction | PARTIAL | claim_contradiction_edges; council disagreement |
| Versioning | PARTIAL | claim versions; hypothesis rewrite JSONL |
| Temporal validity | PARTIAL | STALE in scoring/security; not cognitive TTL |
| Retrieval | PARTIAL | SQL on other stores; no cognitive API |
| Decay | MISSING | no STALE-without-delete cognitive policy |
| Outcome linkage | PARTIAL | score ledger + Lane-A outcomes; joins may be 0 |

## Decision

Do **not** extend `ahos_knowledge.sqlite` or soak DBs. Add dedicated `ahos_cognitive_memory.sqlite` with filename guard. Link HYP-/experiment/prediction IDs as strings. Reuse ExperimentLedger and HypothesisStore.
