# F1 RESOLUTION PLAN — append-only enforcement reality vs claim (W10 finding F1 / W11 §17)
Status: **S1 EXECUTED 2026-08-13 (path (i), owner-authorized)** — interim closure via §2(a)
ACHIEVED: triggers now exist on all three live stores; census data_identical=true; rollback
drill-proven. Final closure via §2(b) PG convergence remains TARGET/DESIGN-ONLY (host-gated).
Plan text below is preserved unmodified (append-only law); the execution is recorded in the
EXECUTION ADDENDUM at the end of this document.

## 0. The contradiction, recorded precisely (no silent fix)
Claim made in W9 (config/cognitive_principles.yaml CRYPTO-02 text + AG-17 evidence): "UPDATE/DELETE-
abort triggers on all stores".
Measured reality (audit probe W10A-02, 2026-08-13): paper_trading.sqlite = 34 triggers guarding
17/17 tables; e01_discovery.sqlite = 0 triggers; ahos_local.sqlite = 0 triggers.
W11 action taken: the CLAIM was corrected to measured truth in the registry/matrix (F1 repair by
text-truth, logged R-33). The STORES are untouched — trigger addition on Lane-A evidence stores
is governance-touching and awaits owner authorization.

## 1. Current reality (evidence)
| Store | Enforcement today | Residual protections |
|---|---|---|
| paper_trading.sqlite | 34 triggers (UPDATE/DELETE abort, 17 tables) | conservation invariants (test-pinned) |
| e01_discovery.sqlite | none (DB-level) | read-only lab law (uri mode=ro), discipline, sha-join coverage 716/716 (W11A-01), cycle reports |
| ahos_local.sqlite | none (DB-level) | trivial control_flags store |

## 2. Target reality
Single governed PostgreSQL evidence/state layer (F1 convergence) with explicit migration
boundaries — additive, reversible, row-preserving; SQLite remains the experiment's source of
truth until gates pass. Lane-A NEVER migrates mid-experiment without owner approval and a
completed parity battery. F1 closes when EITHER (a) triggers exist on all live stores (interim
closure), OR (b) PG canonical layer carries the invariant with replay parity (final closure),
whichever the owner selects — both residual paths documented below.

## 3. Migration stages (each gated, each reversible)
S0 — DONE (this wave): claim corrected; F1 registered; this plan produced.
S1 — Owner authorization for ONE of: (i) additive trigger migration on e01_discovery + ahos_local
      (DDL-only, zero row writes; guarded by before/after row-count + sha census), or
      (ii) defer triggers; rely on PG convergence.
S2 — PG schema generation (dialect translation per pg_parity_audit_w9.md; append-only triggers
      in PG) — BLOCKED on host (no Docker/PG in sandbox).
S3 — Parity battery: identical insert battery into both stores ⇒ row-count + checksum equality;
      replay one fixed cycle window through both stores.
S4 — Mirror population from SQLite snapshots (dual-read, single-write: SQLite still canonical).
S5 — Owner reviews parity + rollback drill ⇒ canonical switch decision (or indefinite coexistence).

## 4. Invariants (must hold at EVERY stage — a breach aborts the stage)
I1 No historical row is ever modified or deleted (row-count + sha256 census before/after).
I2 All 33 live table schemata map explicitly (parity matrix 33/33, no silent drops).
I3 Experiment queries keep returning byte-identical results for the frozen window.
I4 Claim honesty: docs never state "trigger-guarded" beyond measured coverage at that stage.
I5 The experiment's statistical state (0 resolved / 0 closed at plan time) is untouched by S1–S5.

## 5. Rollback
- S1(i): migration script ships its inverse (DROP TRIGGER list); all triggers additive-named
  (f1_guard_*); rollback = one script, verified on a copy first.
- S2–S4: PG side is additive; rollback = stop mirroring; SQLite never destroyed (destruction is
  not a stage anywhere).
- S5: switch decision is reversible only because snapshots pre-switch are frozen-verified.

## 6. Verification tests (planned; implemented when their stage is authorized)
- test_f1_trigger_census: live census matches the claim in docs (THIS wave implements the census
  probe as an audit function; the per-stage assertion joins CI at S1).
- test_f1_parity_battery (S3): row-count + per-table checksum equality SQLite⇄PG on fixtures.
- test_f1_no_row_rewrite (S1/S4): sha census before/after migration identical.
- test_f1_rollback_drill (S1): apply+revert on copy ⇒ schema diff empty.
Current interim enforcement in CI: registry evidence text asserts measured coverage only
(that assertion is what failed-safe during W10 and produced F1 — the system worked as designed).

## 7. EXECUTION ADDENDUM — S1 executed 2026-08-13 (owner authorization: W12 PART B directive)
- WHY: owner chose path S1(i) — additive DDL-only trigger migration on e01_discovery + ahos_local,
  conditions: append-only compatible, zero historical manipulation, regression battery
  before/after, nothing silent. All conditions met with evidence (below).
- ARTIFACTS: engine/f1_s1_migration.py (drill / apply / rollback; probe sets
  W12A-F1S1-{BEFORE,DRILL,APPLY,ENFORCE}) · reports/f1_s1_drill_20260813T025708Z.json (verdict
  SAFE on copies) · reports/f1_s1_apply_20260813T025708Z.json (verdict OK on live stores;
  census_before == census_after; row counts: tokens 569, discovery_observations 716,
  lifecycle_events 1285, gap_register 826, raw_payloads 173 — identical before/after).
- GUARDS INSTALLED (all additive-named f1s1_guard_*, all abort UPDATE and DELETE):
  e01_discovery: 10 triggers on the 5 classified history tables (discovery_observations,
  raw_payloads, gap_register, lifecycle_events, gate_summary). ahos_local: 2 triggers on
  control_flags. paper_trading: untouched — pre-existing 34 triggers / 17 tables intact
  (test-pinned). Mutable upsert-by-design tables (tokens, pairs, observation_state,
  opportunity_rank, outcome_label, security_verdicts, feature_definitions, feature_vector,
  holder_snapshot, wallet_observation) are DELIBERATELY unguarded + documented in
  engine/f1_s1_migration.py (blocking them would break the pipeline by design).
- LIVE ENFORCEMENT PROBED: UPDATE against discovery_observations aborts (W12A-F1S1-ENFORCE);
  INSERT path verified open (append unimpeded ⇒ collector-compatible).
- PIPELINE-SAFETY PROOF: the t12 standing cycle ran to completion WITH guards installed
  (research/experiments/e01_collection_t12_20260813.json; reports/paper_cycle_20260813_025748.json)
  — 638 tokens / 791 observations appended normally; zero guard interference, zero data change.
- CLAIMS UPDATED TO MEASURED TRUTH: CRYPTO-02 restored EXISTING (measured wording);
  AG-17 PARTIAL→EXISTS with evidence text citing the reports; CI pin
  test_registry_and_matrix_text_now_measured + 6 further tests in tests/test_f1_s1.py (7 total).
- ROLLBACK PATH (verified in drill): engine/f1_s1_migration.py rollback — drops the 12 f1s1_*
  triggers by name; drill proved rollback_clean=true on copies before any live apply.
- RESIDUAL: S2–S5 (PG schema, parity battery, mirror, switch decision) stay TARGET/DESIGN-ONLY —
  BLOCKED_NO_HOST (no Docker/PG in sandbox) per W12 PART O. Invariants I1–I5 held throughout:
  experiment statistical state untouched (0 resolved / 0 closed at execution time).
