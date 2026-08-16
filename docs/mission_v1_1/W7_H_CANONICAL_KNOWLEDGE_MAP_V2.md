# CANONICAL KNOWLEDGE MAP v2 (Deliverable H) — 2026-08-11
# Canonical entry node lives at docs/canonical/KNOWLEDGE_MAP.md (README points there).
# A new agent should understand AHOS from the SMALLEST authoritative set.

## Tier 0 — entry (read first, ~15 min)
1. docs/canonical/KNOWLEDGE_MAP.md — the graph (this file's canonical twin)
2. docs/canonical/MISSION.md — objective, laws, blockers
3. docs/canonical/PROJECT_STATE.md — live truth (supersedes narrative reports)

## Tier 1 — canonical core (docs/canonical/, 12 docs + map)
GOVERNANCE (laws/review chain) · ARCHITECTURE · DATA_MODEL · DISCOVERY (PAL/E-01/lifecycle) ·
SECURITY (veto registry) · RESEARCH (H1–H20 status, baselines) · TELEGRAM · PROVIDERS (probe-backed
matrices) · AGENT_COUNCIL · ROADMAP

## Tier 2 — active code references (B-class, pointers not copies)
discovery/ (pal, identity, observations, lifecycle, feature_store, security_gate, outcomes, ranker,
holders, materialize, collect, providers.yaml) · telegram_ai/ (intent, providers, positions, alerts,
ai_providers.yaml) · research/ (baseline_stats, SEARCH_SPACE_REGISTRY, strategy_lab/) · engine/
(run_all_checks, pal_probe, doc_hygiene, simulators) · tests/ (80 tests) · database/ (schemas pg)

## Tier 3 — historical evidence archive (C/D-class, preserved)
research/experiments/ (exp_*, e01_collection_t*) · research/reports/ · reports/ (wave reports,
probes, integrity audits, cleanups) · docs/mission_v1_1/ (wave-5 A–J, wave-6 A–L, wave-7 W7 A–L) ·
docs/archive/ + uploads/_archive_exact_dups_wave7/ (sha-manifested)

## Rule
Canonical docs reference Tier-2/3 by PATH, never copy content. Duplicate-statements found during
any edit must be collapsed to one canonical statement + pointers (added to council checklist).
