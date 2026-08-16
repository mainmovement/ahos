# E-01 GATE-DAY PROTOCOL v1 — pre-registered judgment rules for the 2026-08-14 18:00Z gate
Status: **PRE-REGISTERED 2026-08-13 ~04:2xZ — before any gate outcome exists.** Immutability:
this file's sha256 is registered in AHOS_ISSUE_REGISTER (R-39) at pre-registration time; any
change after that moment requires a new version (E01_GATE_PROTOCOL_v2) + register entry with the
diff's reason (frozen-law §7: definitions change ⇒ NEW VERSION, never rewrite the past).
Scope: Track A gate sequence `discovery.materialize → cohort report → baseline comparison →
outcome sufficiency audit` and Track B accounting check, ending in the Experimental Validation
Report. This protocol binds INTERPRETATION only; it never changes the frozen pipeline.

## R1 — "Resolved" means resolved WITH coverage
The gate metric `≥200 resolved` is counted two ways and BOTH are reported:
- `n_resolved_state` — observation_state == RESOLVED (state machine only);
- `n_resolved_covered` — RESOLVED **and** outcome_label rows exist for the 72h horizon window.
The gate (Track A) applies to **n_resolved_covered**. A high state-count with thin coverage is
reported as hollow-coverage, not as validation.

## R2 — F12 starvation context (measured, cited, not hidden)
Collection starvation is a measured fact of this cohort (2026-08-13 measurements: only 1/762
tokens with ≥12h observation span; 826 missed scheduled snapshots recorded in gap_register;
0 fetched prices after the discovery window). The cohort report MUST segment: per-cohort
coverage profile (obs counts per snapshot point), and — if the owner later authorizes the
F12-O2 poller amendment — pre/post activation segmentation with the activation timestamp.

## R3 — INSUFFICIENT_DATA is a lawful terminal
If coverage is thin, the sufficiency audit's honest output is INSUFFICIENT_DATA. No threshold,
definition, cohort filter, or window may be adjusted to escape that verdict (§7/§23 laws).
Escaping it requires MORE DATA (future windows/cohorts), never edits.

## R4 — Baseline comparison stays pre-registered
Baseline comparison runs exactly per `docs/mission_v1_1/G_BASELINE_LIFT_DESIGN.md` with the
multiplicity budget of `research/SEARCH_SPACE_REGISTRY.json` (B1+B2; H14–H20) — no new
hypotheses may be minted on gate day; anything exploratory is tagged EXPLORATORY and excluded
from verdict strength.

## R5 — Track B gate is arithmetic, not narrative
Track B requires ≥30 closed trades + ≥1 realizable-vs-realized cost reconciliation. Today:
0 closed, 0 realized. `NO_DATA(STALE_OBSERVATION)` streaks are safety-law behavior, not exits.
The gate is reported NOT MET if 0 remains 0 — no surrogate metric is permitted.

## R6 — Deviations are evidence
Any deviation from this protocol on gate day (ordering, tooling, interpretation) is recorded
in AHOS_ISSUE_REGISTER as a protocol deviation with reason — before the result is reported.

## R7 — Sufficiency audit verdict alphabet (exactly one)
- `SUFFICIENT_FOR_EVALUATION` — coverage adequate to run the pre-registered statistical cells
  (this does NOT mean the experiment is validated; it means evaluation may proceed);
- `INSUFFICIENT_DATA` — coverage inadequate (expected under current starvation measurements);
- `INVALID_PROTOCOL` — a pipeline defect voids the window (e.g., state machine fault);
anything else is INVALID output.

## R8 — Required artifacts (the gate's evidence链)
1. materialize run report (rows moved, states, timestamps);
2. cohort report (per-cohort counts, coverage profile per R2);
3. baseline comparison output (cells populated vs INSUFFICIENT);
4. sufficiency audit JSON (verdict per R7 + the numbers behind it);
5. Experimental Validation Report — Persian summary + English artifact, explicitly carrying
   one of: NOT YET VALIDATED (with reason) / VALIDATED (only if the frozen gates are met).
All artifacts live under reports/ + research/reports/ with probe ids where applicable.

## Out of scope (recorded to prevent scope-creep on gate day)
No F12 remediation execution (owner-gated, see F12_DECISION_MEMO.md) · no Lane-B deliveries ·
no Telegram/live-anything. FIRST 72h closures are expected at the gate; 7d labels (t0+604800s)
mature 2026-08-18+ and are NOT required for the gate (recorded here to prevent later confusion).
