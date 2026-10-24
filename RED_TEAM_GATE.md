# RED TEAM GATE: Stage 1 ($100 multi-market paper trader + Kian resilience + Telegram), 2026-10-24 Asia/Tehran

Scope reviewed: commit e285d44 on the box. Completeness baseline: SPEC_TRACE.md (122 items; REAL 16, PARTIAL 29,
PLACEHOLDER 4, CODE_PRESENT_UNVERIFIED 52, MISSING 21; weighted coverage 25%).

| Critic | Verdict | Evidence |
|---|---|---|
| R1 Quant | APPROVE (paper) | Recomputed fills: fill = quote × (1 ± slippage) exact for BTC/ETH/SOL; fee = notional × 0.10% exact; sizes come from current equity (compounding); Kelly OFF n<30 per §6; unit tests cover open → take-profit → realized PnL > 0, the kill switch and witness verdicts (3/3 pass). Objections: linear composite, no walk-forward/DSR (TS-8/TS-9 MISSING); a 0.25 entry threshold is untested. |
| R2 Data | APPROVE with caveat | Live witness for all 13 + DXY/US10Y. Brent is correctly CONFLICT (Yahoo BZ=F 111.66 vs CNBC @LCO.1 117.38, gap 5.0%) and is not traded. Caveat: Yahoo and CNBC print identical exchange prints for indices/FX/WTI (same upstream feed), so they are independent providers rather than independent price discovery. Gold B is PAXG (a token), with a 1.5% tolerance. |
| R3 News | APPROVE as filter only | 11 live RSS feeds, 295 deduped items, 2-source corroboration required, 6 h half-life decay. Keyword lexicon fixed to word boundaries after a false hit ("banks" → "ban"). Not "hundreds" of sources; the synthesized newsroom (M18) is still PLACEHOLDER and outside this stage. |
| R4 Intelligence (Kian) | APPROVE pending live check | 4 free Gemini models probed live on the laptop (flash-lite-latest OK, 3.5-flash-lite OK, 3.5-flash OK, flash-latest 503 at probe time); 429 now rotates to the next model; quota back-off 45 s instead of 600 s; 10-min answer cache; local fallback answers gold/oil with real quotes and a witness note instead of "didn't understand". The deterministic footer is removed (kept only on trade_signal and confirm-gated proposals). TS selftests 817/817 pass. Live Gemini through :3200 must be re-verified after deploy. |
| R5 Visual/UX | CONDITIONAL | /arena/markets renders the PaperTraderPanel (200, panel + Persian verdicts present). Home hero, banner, the / crash and oil-gold 404s are NOT fixed in this stage (priority 4). |
| R6 Learning | APPROVE (mechanism only) | Lessons are written only from real CLOSE rows. Weight changes are bounded [0.5×, 1.5×], need n ≥ 10 per signal, and are versioned with full history (reversible). No closes yet, so no weights have changed and nothing is shown GREEN. |
| R7 SRE/Security | APPROVE with condition | One python loop at 300 s cadence, single-instance guard script; a writer lock was added to ledger.py because the soak and the trader share the one ledger (the 2026-10-23 duplicate-seq incident). Condition: restart the soak so it picks up the lock, and measure RAM on the laptop. CVE/secret scans are still pending (priority 9). |
| R8 Discipline/completeness | CONDITIONAL | Gold soak bankroll change to $100 reverted: it broke test_gold_judge + test_a_tripped_breaker (legacy soak keeps 10k; the $100 gold desk is XAU in the new trader). | Deviation: paper_trader.py is a NEW engine beside gold_paper.py/oil_paper.py (Master Map rule 6 says "extend, never parallel"). The justification is that the legacy engines are single-market and soak-coupled; folding them in is gap G1. Lessons live in signal_lessons.jsonl instead of lessons_ledger.py (G2). MOOD_AGENT_QUEUE.md does not exist. |

## Decision: APPROVE Stage 1 for PAPER_ONLY deploy to the laptop
No real-money path exists, every price used is two-source verified, every fill is reproducible from the logged quote, fee and slippage, and nothing is styled as profitable.

Profitability cannot be judged: 0 closed trades, and the promotion gate needs ≥ 30 closes over weeks.

## Conditions and top gaps carried to the next stages
- G1: fold the gold_paper/oil_paper desks into one engine.
- G2: merge lessons into lessons_ledger.py (M49).
- G3: HRP allocation (§7), walk-forward + DSR/PBO (§8), calibrated ensemble (§9).
- G4: on-chain whale/exchange flows, and central-bank/EIA/OPEC calendars.
- G5: arXiv q-fin → hypothesis pipeline.
- G6: news registry growing toward hundreds of sources, and the M18 synthesized newsroom.
- G7: UI priority-4 fixes.
- G8: portable G: Python/Node.
- G9: CVE/secret scans.
- G10: legacy oil_paper_once.py hardcoded 75.

## Stage 2 verdict — 2026-10-24 04:28 Tehran (box commit 082bac5, laptop dist .next_stage2)
- APPROVED for paper deploy only. HOLD.flag unchanged; PAPER_ONLY.
- Paper trader orders now routed through OMS (`ACCEPTED_PAPER` required); closes write UNVERIFIED lessons into M49 `lessons_ledger`.
- `oil_paper_once.py`: hardcoded 75/75.05 removed; live Yahoo CL=F vs TradingView/CNBC (laptop: 103.44 vs 103.27 VERIFIED).
- Red team candidates are now REAL walk-forward OOS results (1y Yahoo 1h, 6 markets, 4 rule families, costs incl.):
  24 tested / 0 survived / 24 vetoed; PBO 0.74; max DSR 0.18; only WTI OOS positive (+6% trend, +12% composite, DSR 0.03).
  => **No demonstrated edge.** The live $100 trader is an experiment, not a profitable system.
- Owner live-switch gates recomputed from evidence: 3/6 GREEN (was a fake 6/6; "85/85 missions" replaced by SPEC_TRACE REAL 16/122).
- Bridges no longer default to GREEN/ARMED_GREEN when data is missing (UNKNOWN).
- `/` crash fixed (redirect to /arena).

## Stage 3 verdict — 2026-10-24 05:25 Tehran (box commits 1a645d6, 212f250, 70331ac; laptop dist .next_stage3)

| Critic | Verdict | Evidence |
|---|---|---|
| R1 Quant | APPROVE (paper, 0 promoted) | Pre-registered Batch-4 hypotheses H14–H22 in `strategy_lab/hypotheses.py` tested OOS in `walk_forward.py` across 14 instruments (27 new trials; 64 cumulative trials counted in trial-inflated DSR; CSCV PBO = 0.2714 vs 0.7429 in M28.1). H15 (DefiLlama USDT+USDC 7d impulse) achieved OOS +112.9% on BTC (DSR 0.20, n=36) and +119.2% on ETH (DSR 0.10, n=36) and survived `strategy_red_team.py`, but failed DSR > 0.95 -> kept at weight 0.0 (`SHADOW_FORWARD_TEST`). H19 Platt-calibrated logistic combiner (Brier skill ~0, DSR 0.13) and H20 HRP portfolio allocation (OOS Sharpe -0.01 vs EW 1.06) failed OOS -> rejected. `strategy_switch.py` stays at version 0 (0 strategies promoted). |
| R2 Data | APPROVE | Added `macro_calendar.py` (live official schedules: FOMC 56, EIA WPSR 164, BoE 16, BoJ 12 events; ECB TLS EOF & OPEC 403 honestly marked `UNAVAILABLE`, never hand-filled) and `onchain_flows.py` (Coin Metrics community BTC/ETH exchange netflows with 2-day lag guard, DefiLlama stablecoin supply, blockchain.info mempool whales >=100 BTC). Hero globe gate wired to live two-source price witness (14/15 VERIFIED on box, 13/15 on laptop). |
| R3 News | APPROVE | Added `news_registry.py` (246 candidate feeds; live-verified per host: 167 verified across 118 domains on box, 149 verified on laptop). Rewrote `news_desk.py` `build_live_newsroom()` and `export_newsroom_snapshot.py` to replace hand-written stories with live RSS ingestion + two-publisher corroboration (laptop: 90 feeds, 595 items/24h, 475 clusters, 68 corroborated stories). |
| R4 Intelligence (Kian) | APPROVE | `chat_agent.ts`, `chat_replies.ts`, and `paper_account.ts` surface `edge_status: "UNPROVEN_EDGE"` (`لبهٔ سودآوری اثبات‌نشده`), `edge_evidence`, and `shadow_signals` on every trader status/chat reply. |
| R5 Visual/UX | APPROVE | Added `DataHonestyBanner` (`ah-honesty-banner`, aligned with RTL sidebar) and red `UNPROVEN EDGE` badges across `/arena` and `/arena/markets`; added `MarketsStage3.tsx` (`ResearchPanel`, `MacroCalendarPanel`, `NewsPanel`) and redesigned `PaperTraderPanel.tsx`; replaced mock KPIs with 6 live Stage 3 KPIs; verified in headless Chrome screenshots on box and HTTP 200 on laptop `:3200`. |
| R6 Learning | APPROVE | `arxiv_scout.py` queries live `export.arxiv.org` API (45 q-fin/econ/stat papers cached in `reports/grok/M44/arxiv_scout.json`); `science_to_desk_pipeline.py` reads real arXiv, `strategy_lab/registry.json`, `strategy_switch.json`, and M49 lessons; `strategy_red_team.py` removes fake default passes and requires measured regime + perturbation survival. |
| R7 SRE/Security | APPROVE | Portable Node v24.19.0 + Python 3.11.9 staged on `G:\robat\ahos_runtime`; `ahos_launcher.ini` and `.venv/pyvenv.cfg` point to `G:\robat\ahos_runtime` (zero `C:\Users\Sniper` dependency); temp QA files moved off `C:\Users\Sniper` to `G:\robat\_deploy\sniper_cleanup`. Upgraded `certifi` (2026.10.23), `urllib3` (2.8.0), `setuptools` (84.2.1), `pip` (26.2.2) in laptop venv and box venv -> `pip-audit` 0 CVEs on both hosts. Extended `negahban.py` secret scan across 1,093 files (`findings: 0`, `CLEAN`) and recorded npm lockfile advisories (`next`, `postcss` gated by `OWNER_GATE`). |
| R8 Discipline/completeness | APPROVE | Read all remaining docs (`CLAUDE_BUILD_MISSIONS.md`, `DASHBOARD_DESIGN_SPEC.md`, `CLAUDE_DASHBOARD_2050.md` + v1.19, `CLAUDE_MISSION_AGI_RESEARCH_M70.md`, `CLAUDE_MISSION_M80_OSINT_WHITEHAT_v2.md`, `M57_M59_UNIVERSITY_TEAMS_MEMORY_ADDENDUM_v1.md`, `M53..M59`); inspected and verified all 52 `CODE_PRESENT_UNVERIFIED` rows in `SPEC_TRACE.md` (`CODE_PRESENT_UNVERIFIED = 0`; 122 items: REAL 75 [61%], PARTIAL 45 [36%], PLACEHOLDER 0, MISSING 2; weighted coverage 80%). Left all unknown-modified box files untouched and uncommitted. |

### Stage 3 Gate Decision: APPROVED for PAPER_ONLY deploy to laptop (`G:\robat`)
- Paper trader continues running with current baseline rules (`PAPER_ONLY`, `HOLD.flag` intact, `strategy_switch` v0) and explicit `UNPROVEN_EDGE` (`لبهٔ سودآوری اثبات‌نشده`) labeling everywhere.
- New signals (`exchange_netflow`, `whale_mempool`, `macro_event`, `stablecoin_impulse`) run live in shadow mode (weight 0.0) to accumulate forward OOS evidence without distorting paper fills.
