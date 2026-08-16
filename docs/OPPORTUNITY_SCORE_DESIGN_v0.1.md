# AHOS — OPPORTUNITY SCORE DESIGN v0.1 (DESIGN — Maturity A; weights NOT validated)
# LAW: numerical weights below are STARTING HYPOTHESES (score-hypothesis H→lab registration required).
# They earn calibration ONLY from E-01 forward outcome data. Until then scores are reported as RANKS
# with explanations, never as probabilities.

## Structure (two-sided, security-absolute)
Opportunity v0.1 = Σ weighted dimension scores − Σ risk penalties, then Security veto gate.

### Positive dimensions (each 0–10, documented normalization per feature)
| Dimension | w0 | Example features (all measurable from PAL data) |
|---|---|---|
| Market structure | 0.15 | pool age, mcap/FDV tier, price/volume regime vs new-pair cohort |
| Liquidity quality | 0.12 | liquidity USD, LP lock status, L/V ratio, liquidity trajectory |
| On-chain activity | 0.13 | unique buyers growth, tx acceleration, unique-maker diversity |
| Whale/smart-money | 0.13 | accumulation vs distribution, top-wallet net flow, cluster novelty |
| Social momentum | 0.10 | mention velocity, unique authors ratio (bot-filtering when possible) |
| Narrative strength | 0.10 | cross-platform propagation, news hits, theme heat (DefiLlama/news) |
| Catalyst | 0.12 | listing event, launchpad, partnership announcement (source-stamped) |
| Tokenomics | 0.08 | supply float vs unlock schedule, insider allocation flags |
| Development activity | 0.07 | commits/issues velocity (GitHub), audit presence |
| (reserve) | — | unallocated 0.00 until E-01 |

### Risk penalties (subtractive, 0–10 each)
Manipulation (wash trade, bundled wallets, fake volume heuristics) · Liquidity risk · Holder
concentration (top-10 %, Gini) · Execution risk (slippage estimate at target size) · Volatility regime.

### Security veto (hard, non-compensable — see SECURITY_SCORE_DESIGN_v0.1)
honeypot=YES · sell-restricted · blacklist-function · active mint-authority with hidden mint ·
proxy-ownership-capable-of-drain · deployer rugpull-link → **verdict = AVOID regardless of score.**

## Output contract (explainable, Persian-formatted downstream)
score_total (0–100) · per-dimension contributions · top evidence bullets · top risks ·
confidence = f(coverage, agreement, sample) capped ≤0.8 in v0.1 · recommendation ∈
{WATCH, WAIT, HIGH-RISK-ENTRY (only if user risk mode allows), AVOID} · invalidation list (threshold-tied).
System MUST be able to emit "NO OPPORTUNITY" as a first-class successful output.

## Event classes (replacing "pump")
EP[+30%,24h], EP[+50%,72h], EP[+100%,7d] (+ symmetric downside classes), measured vs detection-time price.
Probability statements exist only after E-01 calibration (logistic on train split only, per lab law).

## Validation path (binding)
1) E-01 forward collection ≥8 weeks → 2) train-only weight estimation → 3) OOS ranking quality
(Spearman IC, decile lift) → 4) multiplicity budget (PF-parallel: require IC>0.05 persistence across
weeks) → 5) only then show numeric scores to user; until then: ranks + bullets.
