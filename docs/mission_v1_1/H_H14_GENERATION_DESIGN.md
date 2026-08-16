# H. H14+ HYPOTHESIS GENERATION DESIGN — Wave-6 (Part IX/XI) — 2026-08-11
# Law: hypotheses emerge FROM THE DATASET, not from "looks interesting". Full search space pre-registered.

## 1. Pipeline (Part XV chain, wired to existing lab)
E-01 dataset → baseline_stats scan → CANDIDATE RELATION (auto-logged, NOT a hypothesis yet) →
H-card mint (H14+: same card fields as lab law: hypothesis/reasoning/market_mechanism/required_data/
risk_model/expected_failure_mode/status + batch id) → battery (train/OOS/WF/MC/stress/regime/adversarial)
→ research gate → promotion or REJECTED record.

## 2. Guard sequence (order binding)
1. SEARCH-SPACE REGISTRY first: research/SEARCH_SPACE_REGISTRY.json — every (feature × condition ×
   horizon × class × stratum) cell evaluated, with batch id and timestamp. The registry is the
   multiplicity budget's ground truth. New search spaces require a new batch.
2. Minimum cell stats: F §5 (n≥200, positives≥20) else cell = INSUFFICIENT_DATA (never mined harder).
3. A relation may become a hypothesis card ONLY if lift CI excludes 1.0 on the training cohort AND the
   mechanism sentence passes Critic ("why would this predict, causally, before the event?").
4. OOS cohort = strictly LATER calendar weeks (time-split, never random-split here).
5. Threshold mining prohibited: conditions are the pre-registered grid (F spec) or lab-card constants.

## 3. H-card numbering & storage
Next free ids: H14… (H1–H13 immutable). Cards live in strategy_lab/hypotheses.py (same machinery,
batch=N + gates_override) — reuse, not a new lab. Rejected H-cards remain immutable evidence.

## 4. What auto-generation will NEVER do
- Never POST-hoc explain a hit after seeing its outcome (Critic template forces pre-registration fields).
- Never mutate constants after peeking (every card diff goes through council).
- Never claim predictive power from lift alone (lift = screening statistic, not evidence of edge).

## 5. Timing
First scan run is scheduled ONLY when ≥1 full 72h cohort has ≥200 resolved tokens (≈ mid-week of
2026-08-17 at current intake ≈30–60/day) — earlier runs are allowed in REPORT mode with
INSUFFICIENT_DATA verdicts to keep the machinery exercised (honest by construction).
