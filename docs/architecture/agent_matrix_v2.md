# AHOS — AGENT MATRIX v2 (W12 PART J, machine-generated review)
Generator: engine/agent_matrix_v2.py · source of truth: config/agent_registry.yaml ·
freshness pinned by tests/test_agent_matrix_v2.py (doc == generator output, byte-identical).
Laws honored: no agent exists by declaration alone (PART J) — MISSING/PARTIAL/PLANNED never
promoted without executable evidence; no filler agents; every field is either registry-derived
or an explicit DEFINED marker; typed payload-level IO is queued for contract v2 (F3), and
until then inputs/outputs are declared at dependency/state-table granularity — never invented.
Census (computed, not asserted): 25 agents — EXISTS 9 / PARTIAL 12 / PLANNED 3 / MISSING 1

Each block below carries exactly the 16 PART J fields: identity, version, status, capabilities,
owner, dependencies, inputs, outputs, authority, evidence_requirements, probes, health,
circuit, failure_mode, fallback, runtime, cadence.

### AG-01 · Master Orchestrator · form=n8n_workflow · lane=B
- **version**: design-W9
- **status**: MISSING · criticality=CRITICAL · operability impl/contract/orch/live = False/False/False/False
- **capabilities**: orchestration, lifecycle
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-22, AG-23
- **inputs**: agent deps [AG-22, AG-23] + probe feeds [REPLAY_PROBE, DETERMINISM_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: data/control_plane_ledger.sqlite (future run-ledger)
- **authority**: allowed: OBSERVE · forbidden: DECIDE, PROMOTE, VETO
- **evidence_requirements**: no artifact exists (MISSING) — build only via improvement_proposal_v1 with human approval
- **probes**: required: REPLAY_PROBE, DETERMINISM_PROBE · refs: W10A-07 (graph analysis)
- **health**: none → none
- **circuit**: CLOSED (failures=0)
- **failure_mode**: SAFE HALT on critical dep failure; DEGRADED otherwise
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: none
- **cadence**: continuous

### AG-02 · Data Intelligence · form=lib · lane=A
- **version**: e01-t11
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: collection, normalization, provenance
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [PROVENANCE_PROBE, ADVERSARIAL_INPUT] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: tokens, pairs, discovery_observations, raw_payloads, observation_state, lifecycle_events, gap_register, gate_summary, feature_definitions, feature_vector, outcome_label, security_verdicts, opportunity_rank, holder_snapshot, wallet_observation
- **authority**: allowed: OBSERVE · forbidden: DECIDE, PROMOTE, VETO, ADVISE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): discovery/collect.py + discovery/observations.py; data/e01_discovery.sqlite (569 tok/716 obs @t11)
- **probes**: required: PROVENANCE_PROBE, ADVERSARIAL_INPUT · refs: W10A-01, W10A-03, PRB-20260813-001..011 (chain probes)
- **health**: probe → pal_probe collectors
- **circuit**: CLOSED (failures=0)
- **failure_mode**: provider failure ⇒ circuit + gap_register row
- **fallback**: on_failure=DEGRADE, retries=2, backoff_s=60 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_lib
- **cadence**: periodic

### AG-03 · Research Agent · form=lib · lane=A
- **version**: b2-prereg
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: statistics, evaluation, registry
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-02
- **inputs**: agent deps [AG-02] + probe feeds [STATISTICAL_SUFFICIENCY, OVERFIT_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: research/data/* (manifested files); reads e01 RO
- **authority**: allowed: OBSERVE, ANALYZE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): research/baseline_stats.py (incl. evaluate_conjunction); research/SEARCH_SPACE_REGISTRY.json (9 cells)
- **probes**: required: STATISTICAL_SUFFICIENCY, OVERFIT_CHECK · refs: tests/test_baseline_stats.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: INSUFFICIENT_SAMPLE verdicts; never force
- **fallback**: on_failure=DEGRADE, retries=1, backoff_s=0 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_lib
- **cadence**: event_driven

### AG-04 · Market Intelligence · form=lib · lane=A
- **version**: ranker-v0
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: ranking, regimes
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-02
- **inputs**: agent deps [AG-02] + probe feeds [STATISTICAL_SUFFICIENCY] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: opportunity_rank
- **authority**: allowed: OBSERVE, ANALYZE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: STATISTICAL_SUFFICIENCY · refs: tests/test_discovery.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: UNKNOWN if inputs missing
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_lib
- **cadence**: periodic

### AG-05 · Trend Intelligence · form=lib · lane=A
- **version**: mom-classes-v1
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: momentum, decay
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-02
- **inputs**: agent deps [AG-02] + probe feeds [MODEL_ASSUMPTION_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: OBSERVE, ANALYZE · forbidden: DECIDE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: MODEL_ASSUMPTION_CHECK · refs: tests/test_paper_trading_v3.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: momentum UNKNOWN without 2 obs
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_lib
- **cadence**: periodic

### AG-06 · On-Chain Intelligence · form=service · lane=A
- **version**: holders-refuted
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: holders, deployers
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [SOURCE_DISAGREEMENT_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: holder_snapshot, wallet_observation
- **authority**: allowed: OBSERVE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: SOURCE_DISAGREEMENT_PROBE · refs: PRB-20260813-012..016
- **health**: probe → pal_probe rpc tier
- **circuit**: OPEN (failures=3)
- **failure_mode**: source-refuted ⇒ UNKNOWN rows (R-15 stands)
- **fallback**: on_failure=SKIP, retries=1, backoff_s=300 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_service
- **cadence**: periodic

### AG-07 · Liquidity/Exitability · form=lib · lane=A
- **version**: PT-REALIZABLE-v1
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: realizable, impact, exitability
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [LIQUIDITY_ILLUSION_CHECK, NUMERIC_TRACE_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: realizable_snapshot
- **authority**: allowed: OBSERVE, ANALYZE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): paper_trading/realizable.py + live sweep (disp 17.8759 vs realizable 14.5329; 11/11 EXECUTABLE_FULL)
- **probes**: required: LIQUIDITY_ILLUSION_CHECK, NUMERIC_TRACE_CHECK · refs: W10A-05, tests/test_paper_trading_v3.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: UNKNOWN liq ⇒ UNEXITABLE status, never guessed
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_lib
- **cadence**: per_decision

### AG-08 · Risk Agent · form=lib · lane=A
- **version**: risk-v2
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: classification, escalation, trapped
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-09
- **inputs**: agent deps [AG-09] + probe feeds [MODEL_ASSUMPTION_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: position_state_event
- **authority**: allowed: OBSERVE, ANALYZE · forbidden: DECIDE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): paper_trading/risk.py; MEANINGFUL_RECOVERY_FRAC 0.10 locked (line 14)
- **probes**: required: MODEL_ASSUMPTION_CHECK · refs: tests/test_paper_trading_v2.py, tests/test_paper_trading_v3.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: worst-case-first; TRAPPED not guessed from UNKNOWN
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_lib
- **cadence**: per_decision

### AG-09 · Security/Scam Defense · form=service · lane=A
- **version**: sec-multi-v2
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: veto, taxes, honeypot, lp-lock
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [PROVIDER_COMPROMISE, ADVERSARIAL_INPUT] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: scam_assessment, security_verdicts
- **authority**: allowed: OBSERVE, ANALYZE, VETO · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): paper_trading/security_multi.py; honeypots_avoided=3 live (W10A-14); single-source-per-chain KNOWN RISK
- **probes**: required: PROVIDER_COMPROMISE, ADVERSARIAL_INPUT · refs: W10A-14, PRB-20260813-00x tiers (rugcheck/goplus)
- **health**: probe → pal_probe security providers
- **circuit**: CLOSED (failures=0)
- **failure_mode**: UNKNOWN ≠ PASS; insufficient coverage ⇒ NO ENTRY
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_service
- **cadence**: per_decision

### AG-10 · Narrative Intelligence · form=service · lane=A
- **version**: rss-only
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/False/False/False
- **capabilities**: rss, narrative_streams
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [SOURCE_DISAGREEMENT_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: OBSERVE, ANALYZE · forbidden: DECIDE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: SOURCE_DISAGREEMENT_PROBE · refs: PRB-20260813-017
- **health**: probe → pal_probe rss tier
- **circuit**: CLOSED (failures=0)
- **failure_mode**: no feed ⇒ UNAVAILABLE_NO_FEED (never fabricated)
- **fallback**: on_failure=SKIP, retries=1, backoff_s=300 · boot_class=ADVISORY ⇒ SYSTEM_DEGRADED; DETERMINISTIC_ONLY floor continues unimpaired
- **runtime**: python_service
- **cadence**: periodic

### AG-11 · Multi-Mind Council · form=service · lane=B
- **version**: contract-W11
- **status**: PLANNED · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/True/False/False
- **capabilities**: advisory_review, lenses, AI
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-12, AG-13
- **inputs**: agent deps [AG-12, AG-13] + probe feeds [AI_CORRELATION_CHECK, LIMITATION_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: ANALYZE, ADVISE, CHALLENGE · forbidden: DECIDE, PROMOTE, VETO
- **evidence_requirements**: spec only; enters runtime solely through self-evolution loop (PART K)
- **probes**: required: AI_CORRELATION_CHECK, LIMITATION_CHECK · refs: tests/test_runtime_w11.py
- **health**: probe → router health
- **circuit**: CLOSED (failures=0)
- **failure_mode**: no providers ⇒ deterministic floor, council silent
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=ADVISORY ⇒ SYSTEM_DEGRADED; DETERMINISTIC_ONLY floor continues unimpaired
- **runtime**: python_lib
- **cadence**: event_driven

### AG-12 · AI Model Router · form=lib · lane=B
- **version**: router-W11
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/True/False/False
- **capabilities**: capability_routing, fallback, AI
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [health probe law] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: ANALYZE, ADVISE · forbidden: DECIDE, PROMOTE, VETO
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: health probe law · refs: PRB-20260811-AI-001, tests/test_runtime_w11.py
- **health**: probe → provider probes
- **circuit**: CLOSED (failures=0)
- **failure_mode**: all fail ⇒ DETERMINISTIC_ONLY (live-verified PRB-20260811-AI-001)
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=ADVISORY ⇒ SYSTEM_DEGRADED; DETERMINISTIC_ONLY floor continues unimpaired
- **runtime**: python_lib
- **cadence**: on_demand

### AG-13 · Consensus/Disagreement Engine · form=lib · lane=B
- **version**: compare-W11
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/True/False/False
- **capabilities**: disagreement_detection
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [AI_CORRELATION_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: ANALYZE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: AI_CORRELATION_CHECK · refs: tests/test_runtime_w11.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: conflicts recorded, never silent-averaged
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=ADVISORY ⇒ SYSTEM_DEGRADED; DETERMINISTIC_ONLY floor continues unimpaired
- **runtime**: python_lib
- **cadence**: event_driven

### AG-14 · Red Team · form=service · lane=B
- **version**: linter-W11
- **status**: PARTIAL · criticality=CRITICAL · operability impl/contract/orch/live = True/True/False/False
- **capabilities**: adversarial_lints, veto_claims
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-21
- **inputs**: agent deps [AG-21] + probe feeds [STALE_DATA_LINTER, SURVIVORSHIP_LINTER, PROVENANCE_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: CHALLENGE, VETO · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: STALE_DATA_LINTER, SURVIVORSHIP_LINTER, PROVENANCE_CHECK · refs: tests/test_runtime_w11.py, tests/test_paper_trading_v32.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: verdict enum only; may veto claims, never data
- **fallback**: on_failure=DEGRADE, retries=0, backoff_s=0 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_lib
- **cadence**: event_driven

### AG-15 · Decision Engine · form=lib · lane=A
- **version**: PT-X3-v2
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: frozen_rules, exits
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-07, AG-08, AG-09
- **inputs**: agent deps [AG-07, AG-08, AG-09] + probe feeds [DETERMINISM_PROBE, REPLAY_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: position_decision_event
- **authority**: allowed: DECIDE · forbidden: PROMOTE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): paper_trading/decision_v3.py (decide_v1 byte-frozen; gated decide); 11/11 live NO_DATA(STALE) latest cycle (W10A-17)
- **probes**: required: DETERMINISM_PROBE, REPLAY_PROBE · refs: W10A-16, W10A-17, tests/test_paper_trading_v32.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: stale/unknown ⇒ NO_DATA/INVALID; never priced fiction
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_lib
- **cadence**: per_decision

### AG-16 · Paper-Trading Agent · form=service · lane=A
- **version**: PT-BANKROLL-v2
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: entries, settlement, ledger
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-15
- **inputs**: agent deps [AG-15] + probe feeds [NUMERIC_TRACE_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: paper_trade_v2, paper_exit_v3, portfolio_ledger, position_state_event, realizable_snapshot, decision_snapshot_v2, scam_assessment, post_trade_lesson, learning_stats_snapshot
- **authority**: allowed: DECIDE · forbidden: PROMOTE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): paper_trading/engine_v3.py; conservation 20.0000000 exact every cycle (W10A-04)
- **probes**: required: NUMERIC_TRACE_CHECK · refs: W10A-04, tests/test_paper_trading_v2.py, tests/test_paper_trading_v3.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: conservation invariant exact; append-only
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_service
- **cadence**: periodic

### AG-17 · Memory Agent · form=service · lane=SHARED
- **version**: eventstore-v3-F1S1
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: event_sourcing, durability
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [REPLAY_INTEGRITY_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: all stores (guardian role)
- **authority**: allowed: OBSERVE · forbidden: DECIDE, PROMOTE, VETO
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): MEASURED post-F1-S1 (2026-08-13): paper 34 triggers/17 tables; e01 10 f1s1 guards on 5 history tables (UPDATE abort probed live); ahos_local 2 guards on control_flags; upsert state tables documented; drill/apply reports data_identical=true; tests/test_f1_s1.py; PG convergence = target (F1 plan)
- **probes**: required: REPLAY_INTEGRITY_CHECK · refs: W10A-02, W12A-F1S1-ENFORCE, W12A-F1S1-APPLY
- **health**: probe → trigger census probe
- **circuit**: CLOSED (failures=0)
- **failure_mode**: append-only triggers abort history-table violations in ALL governed stores (F1-S1 measured)
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_service
- **cadence**: continuous

### AG-18 · Learning Agent · form=service · lane=A
- **version**: lessons-v1
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: lessons, stats
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-16
- **inputs**: agent deps [AG-16] + probe feeds [OVERFIT_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: post_trade_lesson, learning_stats_snapshot
- **authority**: allowed: ANALYZE, ADVISE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: OVERFIT_CHECK · refs: tests/test_paper_trading_v3.py
- **health**: static → tests
- **circuit**: CLOSED (failures=0)
- **failure_mode**: idempotent; hypotheses never auto-promote
- **fallback**: on_failure=SKIP, retries=1, backoff_s=0 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_lib
- **cadence**: event_driven

### AG-19 · Self-Diagnostic · form=service · lane=SHARED
- **version**: pal-probe-v1
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: probes, audits
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-02
- **inputs**: agent deps [AG-02] + probe feeds [TRUST_ASSUMPTION_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: OBSERVE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: TRUST_ASSUMPTION_PROBE · refs: PRB-20260813-001..017
- **health**: probe → self
- **circuit**: CLOSED (failures=0)
- **failure_mode**: probe failures recorded with ids; claims gated on them
- **fallback**: on_failure=DEGRADE, retries=1, backoff_s=60 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_service
- **cadence**: periodic

### AG-20 · Controlled Self-Evolution · form=pipeline · lane=B
- **version**: contract-W11
- **status**: PLANNED · criticality=NON_CRITICAL · operability impl/contract/orch/live = False/True/False/False
- **capabilities**: proposals, replay, versioning
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-14, AG-18
- **inputs**: agent deps [AG-14, AG-18] + probe feeds [REGRESSION_PROBE, REPLAY_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: ADVISE · forbidden: DECIDE, PROMOTE, VETO
- **evidence_requirements**: spec only; enters runtime solely through self-evolution loop (PART K)
- **probes**: required: REGRESSION_PROBE, REPLAY_PROBE · refs: tests/test_runtime_w11.py (contract validation)
- **health**: none → none
- **circuit**: CLOSED (failures=0)
- **failure_mode**: no approval ⇒ no promotion; rollback via cards
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=ADVISORY ⇒ SYSTEM_DEGRADED; DETERMINISTIC_ONLY floor continues unimpaired
- **runtime**: pipeline
- **cadence**: event_driven

### AG-21 · Evidence/Provenance · form=lib · lane=SHARED
- **version**: sha-linked-v1
- **status**: EXISTS · criticality=CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: hashing, linkage, manifests
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [PROVENANCE_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: raw_payloads, research/data/MANIFEST.json
- **authority**: allowed: OBSERVE, CHALLENGE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): research/data/MANIFEST.json + raw join 716/716 re-verified post-t11 (W11A-01)
- **probes**: required: PROVENANCE_PROBE · refs: W10A-03, W11A-01
- **health**: probe → join coverage census
- **circuit**: CLOSED (failures=0)
- **failure_mode**: unprovenanced artifact excluded from claims
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: python_lib
- **cadence**: continuous

### AG-22 · Observability/Health · form=service · lane=B
- **version**: ledger-W11
- **status**: PARTIAL · criticality=CRITICAL · operability impl/contract/orch/live = True/True/False/False
- **capabilities**: heartbeat, run_ledger
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-17
- **inputs**: agent deps [AG-17] + probe feeds [DETERMINISM_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: data/control_plane_ledger.sqlite (future)
- **authority**: allowed: OBSERVE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: DETERMINISM_PROBE · refs: tests/test_runtime_w11.py
- **health**: probe → ledger liveness
- **circuit**: CLOSED (failures=0)
- **failure_mode**: no metrics today ⇒ PHASE_STATE snapshots only
- **fallback**: on_failure=DEGRADE, retries=1, backoff_s=30 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_lib
- **cadence**: continuous

### AG-23 · Governance/Policy · form=loop_doc · lane=SHARED
- **version**: gov-R33
- **status**: PARTIAL · criticality=CRITICAL · operability impl/contract/orch/live = False/False/False/False
- **capabilities**: laws, cards, versioning
- **owner**: human operator (approval gateway; never software — F5 law)
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [LIMITATION_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: VETO, PROMOTE · forbidden: OBSERVE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: LIMITATION_CHECK · refs: W10A-12, R-series
- **health**: none → none
- **circuit**: CLOSED (failures=0)
- **failure_mode**: law conflict ⇒ STOP + register, never silent choice
- **fallback**: on_failure=SAFE_HALT, retries=0, backoff_s=0 · boot_class=CRITICAL ⇒ SAFE_HALT semantics; floor unaffected only if non-critical path
- **runtime**: loop_doc
- **cadence**: per_decision

### AG-24 · Cost/Resource Manager · form=lib · lane=SHARED
- **version**: static-budgets
- **status**: PARTIAL · criticality=NON_CRITICAL · operability impl/contract/orch/live = True/False/False/True
- **capabilities**: budgets, rate_limits
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: ∅
- **inputs**: agent deps [∅] + probe feeds [NUMERIC_TRACE_CHECK] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: OBSERVE, ANALYZE · forbidden: DECIDE, PROMOTE
- **evidence_requirements**: promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)
- **probes**: required: NUMERIC_TRACE_CHECK · refs: W10A-12
- **health**: static → cycle reports
- **circuit**: CLOSED (failures=0)
- **failure_mode**: budget exhausted ⇒ DEFER (recorded), never overdraw
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=NON_CRITICAL ⇒ SYSTEM_DEGRADED; core pipeline continues
- **runtime**: python_lib
- **cadence**: periodic

### AG-25 · Open-Source Capability Intelligence · form=pipeline · lane=B
- **version**: spec-W12
- **status**: PLANNED · criticality=NON_CRITICAL · operability impl/contract/orch/live = False/False/False/False
- **capabilities**: github_discovery, repository_ranking, capability_extraction, license_analysis, dependency_security_analysis, architecture_comparison, benchmark_design, candidate_scoring, improvement_proposal, evidence_packaging
- **owner**: AHOS governance — promotion only via improvement_proposal_v1 → human gate
- **dependencies**: AG-14, AG-20
- **inputs**: agent deps [AG-14, AG-20] + probe feeds [LICENSE_AUDIT_PROBE, SECURITY_AUDIT_PROBE, DEPENDENCY_AUDIT_PROBE] (deps/table granularity; payload-typed IO = contract v2, F3 queue)
- **outputs**: — DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)
- **authority**: allowed: OBSERVE, ANALYZE, ADVISE · forbidden: DECIDE, PROMOTE, VETO
- **evidence_requirements**: spec only; enters runtime solely through self-evolution loop (PART K)
- **probes**: required: LICENSE_AUDIT_PROBE, SECURITY_AUDIT_PROBE, DEPENDENCY_AUDIT_PROBE · refs: W12A-OSS-1
- **health**: none → none
- **circuit**: CLOSED (failures=0)
- **failure_mode**: untrusted provenance/license/security ⇒ REJECT/UNVERIFIED; not-better ⇒ NO_INTEGRATION
- **fallback**: on_failure=SKIP, retries=0, backoff_s=0 · boot_class=ADVISORY ⇒ SYSTEM_DEGRADED; DETERMINISTIC_ONLY floor continues unimpaired
- **runtime**: pipeline
- **cadence**: event_driven
