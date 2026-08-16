# AHOS CANONICAL — GOVERNANCE
Doctrine + decision rules. Evidence: `AHOS_ISSUE_REGISTER.md` (single canonical register;
wave-1 long-form archived at docs/archive/ISSUES_REGISTER_wave1_longform.md).

## Principles
Observation First · Data > AI · Evidence > Assumption · Controlled Risk · Replayability · Human Gate ·
Opportunity Discovery First · Security Before Opportunity · Explainability · Provider Independence ·
Cost Efficiency · Iran-Network Resilience.

## Hard rules (each tied to enforcement)
- **Gates are math, not words**: lab gates (OOS PF bars per batch, WF/MC/stress/min-sample) enforced in code (strategy_lab/run_lab.py).
- **OOS windows are consumables**; batch-2/3 raised bar PF>1.5 (multiplicity guard, R-05).
- **No rescue-tuning**: failed hypothesis → new pre-registered card, never parameter fiddling (R-06/R-07).
- **Leakage law L1–L4** machine-enforced (feature_store + DB CHECK + AST test).
- **Change record law**: WHY/WHAT/EXPECTED/TEST/ROLLBACK in AHOS_ISSUE_REGISTER.md per change.
- **Maturity letters** on every component; bare "ready" prohibited.
- **SIMULATED vs LIVE VERIFIED** can never be conflated; probes/states labeled per environment.
- **Document hygiene**: canonical set (this dir) references detail; superseded docs marked + archived with hash;
  negative evidence is never deletable (Part XXIV).
- **Deletion needs council sign-off** (Architect+DataArch+Research+QA); autonomous deletion prohibited — archive only.

## Forbidden autonomously
Real financial transactions · live trading · paid subscriptions · irreversible deletion ·
credential changes · security-sensitive external actions.
