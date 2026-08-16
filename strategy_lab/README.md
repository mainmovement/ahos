# AHOS STRATEGY RESEARCH LABORATORY v2.0 — CHARTER
# Treat every strategy as a hypothesis. Never tune parameters to rescue a failed candidate.

## Pipeline (binding)
Researcher → Critic → Quant Reviewer → Risk Reviewer → QA → Auditor.
No candidate becomes ACCEPTED without: Train/OOS + Walk-Forward + Monte Carlo + Stress + Registry entry.

## How to add a candidate (H10+)
1. Write the hypothesis card in `hypotheses.py` FIRST (all 10 fields). Timestamp is in git/log.
2. Implement generator in `candidates.py` — causal series ONLY (prefix tests will prove it).
3. Freeze parameters with reasoning BEFORE first run. After first OOS look → params frozen forever.
4. Run `python3 strategy_lab/run_lab.py`; registry updates automatically with verdict + evidence hash.
5. REJECTED candidates may NOT re-enter with tweaked params under the same hypothesis id.
   A materially different mechanism = NEW id (e.g., H10) with its own card and fresh OOS discipline.

## Gates (fixed)
OOS PF>1.3 · expectancy>0 · OOS DD<15% · MC(1000 sims) >70% positive · WF ≥60% profitable windows
(≥10 trades/window, ≥3 windows) · stress(2×costs) PF>1.1 · ≥30 OOS trades · stable across ≥2/3 assets,
no catastrophic asset (PF<0.8). See run_lab.GATES — changes require Auditor note in experiment log.

## Files
hypotheses.py (cards) · candidates.py (signal generators) · lab_engine.py (causal executor) ·
run_lab.py (battery) · registry.json (verdicts) · ../research/data/ (real 3.6y sets + MANIFEST) ·
../research/experiments/ (append-only logs) · ../research/reports/ (findings + telegram dispatch)

## Guarantees enforced by tests (tests/test_strategy_lab.py)
- prefix-causality of every generator on real data (3 checkpoints per generator)
- funding/OI merge proven backward-only (no future leak)
- engine determinism · hypothesis-card schema · gate verdict logic · registry schema
