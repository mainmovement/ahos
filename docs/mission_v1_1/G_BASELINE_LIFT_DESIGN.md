# G. BASELINE / LIFT ANALYSIS DESIGN — Wave-6 (Part X) — 2026-08-11
# Implemented: research/baseline_stats.py (+ tests). Rule: never evaluate a signal without a baseline.

## 1. Quantities (deterministic, versioned PAPER)
baseline_rate = P(event | all resolved candidates in stratum)
conditioned_rate = P(event | feature condition C)     [C pre-registered per evaluation]
lift = conditioned / baseline  (reported only when denominators exist)
precision = TP/(TP+FP) · recall = TP/(TP+FN) (event = positive label, condition = predicted-positive)
Wilson 95% CI for both rates · sample sizes printed ALWAYS · regime stratum = {chain × week} (v1).

## 2. Decision thresholds (guards — constants, documented, not tuned)
- MIN_N_STRATUM = 200 resolved · MIN_POSITIVES = 20 (per F §5) else INSUFFICIENT_DATA.
- Report lift with CI; "signal" language banned until lab-card battery survives (Part XV chain).
- Multiple-testing: every evaluation batch registers its search space (doc H registry); a batch that
  evaluates k conditions reports k and uses the prevailing batch discipline (holm option recorded).

## 3. Calibration path (locked)
Numeric probability to users only after: train-only fit → OOS replication on a NEW week-cohort →
reliability curve saved → council sign-off. Until then: ranks + bullets (unchanged from wave-5).

## 4. Implementation (this wave)
research/baseline_stats.py:
  load_outcomes(sqlite) × feature_vector(as_of = T0+1h default join) → 2×2 tables per (feature, condition,
  horizon, class) → rates/lift/Wilson → JSON report research/reports/baseline_stats_<ts>.json
  with verdict INSUFFICIENT_DATA when guards unmet (will be the honest verdict for weeks).
tests/test_baseline_stats.py: fixture cohorts (incl. a cohort KNOWN to contain lift; and one known null)
  → assert detector finds the first, refuses the second on small n, CIs behave (cover-age sanity calc).

## 5. Survivorship guard (Part XIII)
Strata ALWAYS include dead/rugged/flat/security-failed tokens (lifecycle states + veto flags are in-store
dimensions; the join never filters to survivors). Absence of negatives ⇒ report marks STRATUM_CORRUPT.
