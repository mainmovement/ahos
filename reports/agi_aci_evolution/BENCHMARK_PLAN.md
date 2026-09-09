# AGI/ACI Benchmark Plan

**Status:** DOCUMENTATION_ONLY for AGI suite. P4.1 executed a **SYNTHETIC cognitive-correctness vector** (`architecture/cognitive/benchmark/`). That is not an AGI result. Several metrics FAIL.  
**Law:** Synthetic data must be labeled SYNTHETIC/SIMULATION/TEST. Real soak rows remain distinct. Do not consume soak in a way that changes experimental semantics.

## Purpose

Convert the “99.9% intelligence” aspiration into **measurable targets with methodology**, not a stored percentage.

Examples of defensible targets (not yet measured):

- Data integrity: fraction of cognitive records with provenance + typed `data_label` = 100% of records produced by `architecture/cognitive`.
- False promotion: count of HypothesisState.SUPPORTED without `experiment_id` = 0 (unit-tested).
- Fabricated scores refused: `refuse_fabricated_score` raises (unit-tested).
- Calibration: existing M-GAP-008 methodology after eligible joins > 0 — **not** this suite; wait for soak.

## Required comparisons (when a capability is later claimed improved)

1. Current AHOS baseline (this SHA + capability matrix).
2. Previous best AHOS implementation of the same surface.
3. Simple baseline (e.g. majority-unaware constant, or “always UNCERTAIN”).
4. Strong statistical baseline where applicable.
5. Relevant ML baseline where applicable.
6. External AI/tool baseline only with labeled TEST packets — never as soak truth.

## Suites (future; not executed this pass)

| ID | Question | Data label | Blocked by |
|----|----------|------------|------------|
| B-COG-01 | Hypothesis transition fail-closed | TEST | none (unit tests now) |
| B-COG-02 | Self-research does not treat Cloud sqlite as soak | TEST | none (unit tests now) |
| B-COG-03 | Closed cognitive loop lesson reuse vs NO_MEMORY | SYNTHETIC_TEST_DATA | none (`tests/test_cognitive_loop.py`) |
| B-COG-04 | P4.1 labeled retrieval/context/contradiction/learning vector | SYNTHETIC_TEST_DATA | none (`architecture/cognitive/benchmark/`) |
| B-FIN-01 | Prediction calibration vs simple baseline | REAL local soak | eligible_join_pairs_estimate=0; T+72h |
| B-FIN-02 | Hindsight vs displayed-price naive CF | TEST/REAL paper | existing hindsight module |
| B-SOC-01 | Council disagreement preserved vs majority vote | TEST | existing council tests |
| B-WM-01 | Causal/CF quality | — | ACI-GAP-002; do not fake |

## Forbidden

- Hard-coded 99.9% intelligence.
- Using soak T0 counts as proof of new cognition.
- Training/evaluating on unlabeled synthetic data presented as REAL.
- Closing M-GAP-003 from this plan.
