# EARLY-MOVEMENT H14+ RESEARCH PLAN (Deliverable B) — 2026-08-11
# Builds on: F_PUMP_EVENT_RESEARCH_SPEC (event grammar), G_BASELINE_LIFT_DESIGN (stats law),
# H_H14_GENERATION_DESIGN (registry-first law). Rank-first stays; NO score until the research gate.

## 1. Central question (locked, verbatim)
P(event | all candidates) vs P(event | feature condition) — which BEFORE-event signal combinations
produce statistically significant lift, with CIs, OOS replication, regime and robustness checks?

## 2. Registered cards (SEARCH_SPACE_REGISTRY.json, batch B2-pre-registered, 2026-08-11)
| Card | Statement (predicate cells) | State |
|---|---|---|
| H14 | volume_acceleration ≥ 2.0 AND buy_sell_imbalance_1h ≥ 0.15 | COMPUTABLE (unique-buyer = proxy, declared) |
| H15 | liquidity_growth_1h ≥ 0.10 AND txn_acceleration ≥ 1.5 | COMPUTABLE |
| H16 | top20_net_flow_1h > 0 AND liquidity_stability ≥ 0.7 | DATA-BLOCKED (holder source refuted, R-15) |
| H17 | holder growth + organic social acceleration | DATA-BLOCKED ×2 (holders + social MVP) |
| H18 | volume_acceleration ≥ 2.0 AND security_all_hard_veto_clear = 1 (concentration clause blocked) | COMPUTABLE (partial, declared) |
| H19 | narrative acceleration + txn_acceleration | DATA-BLOCKED (Phase-7 narrative feature) |
| H20 | STRICT 4-of-4 (vol+txn+liq+imbalance) AND \|price_change_1h\| < 0.05 | COMPUTABLE |

Events per cell: PRIMARY +50% @24h · SECONDARY +100% @72h (H14/H15/H18 both; H20 primary only).
Every card carries: exact feature definition, observation cutoff (as_of = first_seen+3600s locked),
event window, baseline (ALL resolved candidates incl. RUGS/DEAD/FLAT/SECURITY-FAILED — survivorship
ban), exclusion rules, success bar (train lift CI-lower>1 AND OOS lift CI-lower>1 AND time-half
stability), failure bar, expected failure mode. 7 B2 cells registered BEFORE any run (evidence:
research/reports/baseline_stats_b2_reportmode_20260811.json — all INSUFFICIENT_DATA, honest).

## 3. Mechanics now test-pinned
- evaluate_conjunction: parameterized clauses only (ops whitelisted, keys regex-validated — SQL
  injection impossible by construction; negative tests pinned). Missing feature ⇒ excluded from the
  conditioned stratum, never imputed.
- discovery/materialize.py: freezes fs_v0.2 vectors at the EXACT join as_of and labels RESOLVED
  tokens only, horizons close by wall-clock (72h/7d cannot peek). Idempotent (test-pinned).

## 4. Statistical law (unchanged + one addition)
- Guards: n≥200 per stratum, positives≥20 (constants, not runtime-settable); Wilson CIs.
- Time-split OOS only (never random split); multiplicity budget = registry cells (9 total: 2 B1 + 7 B2).
- ADDITION (Wave-7 council Quant ruling): composite cells consume EXTRA multiplicity budget —
  each H-card may mint at most the pre-registered (primary, secondary) cell pair; any new threshold
  or clause = NEW card. Relaxing H20 to ≥3-of-4 post-hoc is PROHIBITED (would be rescue-tuning).
- Liquidity-adjusted and rug-adjusted variants are REPORTED as separate descriptive columns;
  a raw +100% in an illiquid token is never reported as equivalent to a liquid +100% (F spec).

## 5. Timeline
- ≥2026-08-14: first 72h cohort exit report (descriptive-only; classes per F spec).
- ≥200 resolved (≈ week of 2026-08-17): first REAL B2 scan; CANDIDATE relations only.
- Research gate ≈2026-10-06 (E-01 ≥8 weeks): only after gate may ranking-adjacent statistics be
  discussed for promotion; a score must be EARNED (directive §4).
