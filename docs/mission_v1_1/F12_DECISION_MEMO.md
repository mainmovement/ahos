# F12 — DECISION MEMO: tracked/active-cohort observation starvation (OWNER DECISION REQUIRED)
Date: 2026-08-13 ~04:1xZ · Status: **OPEN — decision rests with the owner (Lane A is frozen;
any collector change is governance-touching)** · Prepared by: Project Lead (evidence below).
Nothing in this memo touches Lane A; it is a decision artifact only.

## 1. Measured reality (all numbers from live RO queries, 2026-08-13T04:05Z)
- discovery cohort: **762 tokens / 987 observations / 0 resolved**.
- Observation density per token: **span ≥12h: 1 token of 762 · span ≥24h: 1 · ≥5 observations: 5 ·
  latest-obs >24h old: 222** (the recent ~540 are fresh only because they were discovered in
  the last day; each new token receives its initial-window snapshot(s) and then freezes).
- The lifecycle scheduler itself records the starvation honestly: gap_register =
  **826 missed snapshots** (`missed:s+15m` 223 · `missed:s+1h` 222 · `missed:s+4h` 223 ·
  `missed:s+12h` 158; expected_ts range 2026-08-11 ~16:15Z → 2026-08-12 ~04:40Z; later cohorts
  will keep registering `missed:` rows as their windows pass).
- The collector (`discovery/collect.py`) ingests ONLY new listings (`--max-new` per lane);
  no code path re-polls prices for already-known tokens.
- Consumers read ONLY stored series: `discovery/outcomes.py::compute_outcomes` resolves labels
  from `discovery_observations` alone (entry = first obs within t0+15m; each horizon h needs
  ≥2 price points in [t0, t0+h]); PT-X3-v2 exit engine likewise reads stored observations.
- 11 open v2 positions: entries 2026-08-12 07:15Z (×7) and 08:41Z (×4) ⇒ 72h horizons
  **2026-08-15 07:15Z / 08:41Z**. Since 2026-08-12 every management decision is
  `NO_DATA(STALE_OBSERVATION)` — the R-C3/PT-X3-v2 stale law (>6h ⇒ nothing priced, no fake
  settlement) is working exactly as designed. Cash $1.8984375 idle; entry gate
  QUALIFIED_SKIPPED_NO_CASH.

## 2. What happens if nothing changes (expects these truthfully at the gates)
- E-01 materialization (gate 2026-08-14 18:00Z): state machine will move first-cohort tokens
  to RESOLVED on schedule, but `compute_outcomes` will write labels ONLY where a horizon has
  ≥2 stored points — with frozen series that means mostly the 15m horizon or nothing.
  **The ≥200-resolved gate may be reached in state-count while the outcome coverage is
  statistically thin.** The baseline comparison and sufficiency audit will then read
  INSUFFICIENT_DATA for the meaningful (4h+/positive-class) cells. That is the experiment
  telling the truth, not a failure to hide.
- Track B: positions stay NO_DATA through and past their horizons; 0 exits; ≥30-closed gate
  unreachable for this cohort; trapped capital recorded open per trapped-capital law.
- Permanent loss note: past snapshot windows cannot be recovered later (a backfill would
  carry retrieved_ts ≠ window ⇒ availability-honest law rejects it). missed = missed, already
  recorded. Only FUTURE windows are salvageable.

## 3. Options (none execute without explicit owner order)
- **O1 — accept as-is.** Zero interference; statistical purity absolute. Cost: Track A resolves
  hollow for this cohort; Track B frozen; experiment horizon extends by one full new cohort
  (~72h+ after a fix) before any sufficiency verdict is even possible.
- **O2 — owner-authorized versioned observability amendment (recommended reading).** Add a
  scheduled-observation poller job (append-only `discovery_observations` rows for tokens whose
  lifecycle snapshot points are open, incl. the 11 tracked tokens), e.g. a new `--observe-active`
  path next to collect.py, DexScreener/GeckoTerminal free endpoints, rate-capped. This restores
  the protocol's OWN data requirement (exit/label decisions on FRESH prices) — it changes no
  threshold, card, decision logic, or historical row. Mandatory disclosures: registered in
  AHOS_ISSUE_REGISTER + declared in the Experimental Validation Report as a mid-experiment
  collection amendment with activation timestamp; pre/post suites; replay-parity proof that
  existing rows/labels are untouched (additive-only census). Benefit: future s+1h/4h/12h/24h/72h
  points get collected; the 11 positions can receive REAL exits at/before horizon; Track B's
  ≥30-closed path re-opens (cash returns on exits → entry gate can fire again).
  Cost/risk: ~1 endpoint call per active token per snapshot point (trivial rate); mid-cohort
  activation MUST NOT be silently merged into the statistic — the sufficiency audit will
  segment cohorts pre/post activation (survivorship/availability honesty).
- **O3 — fix for next cohort only.** Keep current cohort untouched; activate the poller from a
  declared boundary date; current first cohort stands as the "starved-collection" control —
  cleanest statistically, slowest to any Track-B evidence.

## 4. Recommendation framing (advisory; NOT a decision)
The stale-law safety (R-C3) and the gap recorder both behaved correctly — the failure is purely
observational scheduling (no autonomous scheduler in this sandbox; G-SCHED in W13 audit).
O2 with the disclosure protocol preserves evidence law while un-starving future windows; O1/O3
sacrifice this cohort's utility for maximal purity. The trade is the owner's to call.
Any approval must name: option, activation time, disclosure ack — and it will be executed as a
versioned, tested, replay-verified amendment with rollback = stop the poller (no deletions ever).

تصمیم نهایی با کاربر است.

## EXECUTION ADDENDUM (2026-08-13) — owner chose **O2**, executed with strict evidence bounds
- Approval: owner directive "DECISION: O2 — APPROVED WITH STRICT EVIDENCE BOUNDARIES" 2026-08-13.
- Root cause (code-proven): due_snapshots/sweep schedule machinery existed but had NO fetch-side
  consumer; collector ingests new listings only; no scheduler in sandbox. Repair = completing the
  existing loop, not duplicating it.
- Shipped: discovery/observe_active.py (NEW file; ZERO edits to existing Lane-A files) using the
  existing due-schedule + record_observation + PAL client; 14 tests (tests/test_observe_active.py)
  incl. red-team set; isolation run on a LIVE COPY (network-real): 6 recorded / 14 explicit
  failures; activation run on the live store: 14 recorded / 26 failures (dead tokens priced as
  no_valid_price rows — explicit, never silent), activation_ts 2026-08-13T04:30Z (1786595433.489).
- Boundary proofs (sha census, /tmp + this wave's manifests): tokens/pairs/lifecycle_events/
  gap_register/outcome_label IDENTICAL pre⇒post; observations 987→1027 and raw_payloads 224→239
  as pure appends with retrieved_ts ≥ activation only.
- Cohort separation: PRE_FIX = all rows with retrieved_ts < 1786595433.489443; POST_FIX = rows ≥
  activation (row-level marker: run reports list every obs_id; poller version observe_active:v1).
- Lane-B guardrail: engine/coverage_audit.py (5-block invariant bundle + frozen classifier;
  verdicts HEALTHY/DEGRADED/STARVING) + tests/test_coverage_audit.py; live verdict at activation:
  DEGRADED (fresh share 0.727; 580 gaps churned in last 24h — must fall as poller cadence serves
  due slots; horizon_coverage honest-null with 0 resolved).
- Status: F12 → **MITIGATED** (not "solved forever"): monitoring = coverage_audit per cycle-ish.
