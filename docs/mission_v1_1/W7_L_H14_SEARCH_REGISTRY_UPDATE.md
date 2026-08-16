# H14+ SEARCH REGISTRY UPDATE (Deliverable L) — 2026-08-11
# Canonical data: research/SEARCH_SPACE_REGISTRY.json (machine file — this doc is the human view).

## 1. Registry state after Wave-7
- Batches: B1-pre-registered (2 cells, wave-6) + **B2-pre-registered (7 cells, wave-7)** = **9 cells total**.
- Hypothesis cards: H14–H20 added with full pre-registration payloads (hypothesis, reasoning/mechanism,
  exact feature definitions, observation cutoff, event windows, baseline, exclusions, success/failure
  bars, expected failure mode, required-data, status, registered_ts).
- Statuses: H14/H15/H18/H20 = REGISTERED-COMPUTABLE · H16/H17/H19 = REGISTERED-DATA-BLOCKED
  (each block carries its unblock requirement — Helius/QuickNode free tiers (user signup), EVM
  Transfer-log scanner (Phase-3), RSS narrative MVP (Phase-7)). Blocked cards mint NO cells.

## 2. B2 cells (computable predicates, locked constants)
B2-h14-24h-p50 · B2-h14-72h-p100 · B2-h15-24h-p50 · B2-h15-72h-p100 · B2-h18-24h-p50 ·
B2-h18-72h-p100 · B2-h20-24h-p50 — see registry JSON for exact clause lists.
Report-mode execution evidence (machinery exercised, verdicts honest):
research/reports/baseline_stats_b2_reportmode_20260811.json — 7/7 INSUFFICIENT_DATA (0 resolved
tokens; 72h barrier not yet elapsed at run time). No mining, no threshold shopping.

## 3. Engine change enabling composites
research/baseline_stats.py::evaluate_conjunction — parameterized multi-key AND cells; ops/key
whitelist + binding (injection-proof; negative tests); guards n≥200/pos≥20 unchanged (constants);
scan() dispatches legacy "condition" and new "clauses" cells from the same registry file.

## 4. What happens next (standing)
1. 72h cohort resolution ≥2026-08-14 via discovery/materialize.py (features frozen at exact join
   as_of; outcomes written only after horizon closure).
2. First REAL B2 evaluation when resolved ≥200 (≈ week of 2026-08-17); any CANDIDATE relation gets
   the full battery (time-split OOS, stability halves, budget check) BEFORE anyone says "signal".
3. Rejection is a recorded success: dead cards stay in the registry with their failure bar evidence.
