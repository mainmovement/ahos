# B. CURRENT E-01 AUDIT — Mission v1.1, STEP 2 — 2026-08-11
# Auditor: council roles 2 (Quant), 10 (Statistician), 11 (Backtesting), 15 (QA)

## B.1 Verdict
| Aspect | State | Evidence |
|---|---|---|
| E-01 research design (forward paper event study, ≥8w, 7 horizons) | **EXISTS (design only)** | RESEARCH_META_ANALYSIS_v1.md §Q10; DEVELOPMENT_ROADMAP Phase-4 exit; DATA_SOURCE_MATRIX §"Acquisition policy" |
| Event-class definitions (+25/+50/+100/+200% × horizons) | **PARTIAL** | defined as research questions; exact baselines/labels NOT frozen yet (froze in D + F this wave) |
| Discovery collector code | **MISSING** | 0 collector files (verified by grep/find 2026-08-11) |
| Timestamped observation store | **MISSING** | schema v1.1 covers market_data only (majors); no token/discovery tables (schema v1.2 now drafted, C §5) |
| 72h observation lifecycle | **MISSING** | state machine designed this wave (F), code not yet |
| Feature store | **MISSING** | schema designed this wave (D) |
| Leakage guardrails (feature_ts / availability_ts) | **PARTIAL** | lab_engine proves prefix-causality for research features (6 pytest); discovery features have no store yet → guardrails specced in D §4, enforced by new tests |
| n8n workflows for discovery (20/21/22) | **MISSING (by plan; Phase-5)** | not started; wave-4 verified 6 existing workflows remain untouched |

## B.2 Gap report (STEP 2 output, ranked)
| # | Gap | Severity | Closes at STEP |
|---|---|---|---|
| G1 | No PAL runtime | BLOCKER | 3u (underpinning) |
| G2 | No canonical token identity | BLOCKER | 3 |
| G3 | No timestamped observation persistence | BLOCKER | 4 |
| G4 | No 72h lifecycle engine | HIGH | 5 |
| G5 | No feature store + feature definitions | HIGH | 6 |
| G6 | No security gate runtime | HIGH (safety) | 7 |
| G7 | No outcome labeler (research dataset) | MED | 8 |
| G8 | No paper ranking surface | MED | 9 |
| G9 | Telegram Persian contract not implemented | MED | 10 |
| G10 | Iran-side provider reachability UNKNOWN | MED (ops) | user/VPS |

## B.3 What E-01 must NOT become (council red lines)
- Not a "pump score" demo (Mission §10: FEATURE STORE first, scores after data).
- Not a single-run scrape: observations must be replayable with raw payloads retained (integrity like MANIFEST).
- Not a silent-failure system: every provider error → error_state row, never a fabricated NULL-as-pass.
- Not hindsight-usable: feature vectors freeze at availability_ts (D §4 + tests).

## B.4 Minimal honest claim allowed after this wave
"AHOS E-01 collects a timestamped, provenance-stamped discovery universe with UNKNOWN discipline and a
security gate; predictive power: NOT YET EVALUATED (needs ≥8 weeks forward data per registered design)."
