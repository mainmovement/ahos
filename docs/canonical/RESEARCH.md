# AHOS CANONICAL — RESEARCH (lab + evidence laws)
Detail: strategy_lab/README.md · research/reports/{RESEARCH_FINDINGS_v2.0, RESEARCH_META_ANALYSIS_v1}.md ·
reports/FINAL_EXECUTION_REPORT.md §6.

## Immutable evidence
- H1–H13: ALL REJECTED (H8 NOT TESTED — data-blocked: L2 order book). Registry: strategy_lab/registry.json.
- Frozen baseline: NO EDGE (PF 0.739/0.724/0.779) → LIVE CLOSED.
- Learnings: cost realism decides at 1h (H9: 1.38→0.93 @ 2× cost) · small-sample inflation (H10: 2.35→1.27 when n 16→31) ·
  conviction-threshold falsifiability (H11 zero-signal) · OOS windows are consumables (batch bars PF>1.5).

## Lab law
Pre-registered cards (hypothesis/mechanism/data/risk/failure-mode/status) before any run · multiplicity budget
(batch bars) · WF/MC/stress/min-sample · no rescue-tuning · rejection+reason = success.

## H14+ path (wave-6 doc H)
Discovery dataset → baseline_stats (lift with CI) → candidate relation (pre-registered) → lab card (H14+)
→ battery (train/OOS/WF/MC/stress/regime) → gate. Search space logged in research/SEARCH_SPACE_REGISTRY.json.
Small n ⇒ verdict INSUFFICIENT_DATA (never over-read).

## Data assets (governed, sha-pinned)
research/data: 3.6y BTC/ETH/SOL (31,608×3) + 6.6y BTC-ext (57,912) + funding/OI + MANIFEST{,_ext}.json ·
E-01 discovery store data/e01_discovery.sqlite (growing).
