<!-- Tehran: 2026-10-09 16:58 (UTC+3:30) | Version: v1 | Author: Asi | Reason: vet @iclosegreen quant-desk repos for AHOS -->
# @iclosegreen "six open source repos that replace a quant desk": AHOS vetting v1
Hard laws: zero cost, paper only, no live execution, no exchange keys, addenda only (no new parallel modules). Slots come from /workspace/out/DEDUP_MERGE_MAP.md.
Source of the post: an Instagram reel by iclosegreen dated Aug 26 (instagram.com/reel/DcgZhLyiZ3o). Its caption names no repos. X search_posts_all returned 0 results.
Repo data comes from the GitHub public REST API. Commit times below are Tehran (UTC+3:30), converted from UTC. Paid products (Trove, tradeinhouse.ai) are ignored.

## Verdict table
| # | Repo | License | Last commit (Tehran), stars | Win / 8 GB | Verdict / slot |
|---|---|---|---|---|---|
| 1 | github.com/shiyu-coder/Kronos | MIT | 2026-04-13 16:08 (about 6 months idle), ~40.3k | OK on CPU (mini/small/base) | ADOPT-PAPER: addendum to M15.10 (extra forecaster) + M24 regime input |
| 2 | github.com/skfolio/skfolio | BSD-3-Clause | 2026-10-09 00:24, ~2.5k | OK, pure Python | ADOPT: addendum to M24 / M28.6 HRP/ERC |
| 3 | github.com/nautechsystems/nautilus_trader | LGPL-3.0 | 2026-10-09 14:46, ~29.8k | Windows x86_64 listed (Py 3.13-3.14) | PAPER-ONLY: addendum to M28.1 / M25 backtest parity |
| 4 | github.com/hummingbot/hummingbot | Apache-2.0 | 2026-09-22 12:23, ~20.4k | UNVERIFIED | IDEAS ONLY: no install; notes to M21 |
| 5 | github.com/freqtrade/freqtrade (FreqAI built in) | GPL-3.0 | 2026-10-09 08:56, ~55.2k | Windows stated, Py 3.12+ | IDEAS + at most a separate GPL process for dry-run backtests: M28.1/M25; FreqAI ideas to M15.10 |
| 6 | UNVERIFIED which repo. Best fit: github.com/microsoft/RD-Agent | MIT | 2026-09-23 14:35, ~14.9k | Linux-only badge, so Windows is UNVERIFIED (WSL2?) | RESEARCH ONLY: addendum to M16 (University/GitHub) + M58 |

## Details
1. Kronos is a foundation model trained only on OHLCV candles, pretrained on data from 45+ exchanges.
   - Uncertainty: the README offers probabilistic sampling (T, top_p, sample_count paths). There are no native quantile intervals, so uncertainty means the spread across many sampled paths.
   - Sizes: mini 4.1M params (2048 context), small 24.7M and base 102.3M (512 context). Large (499.2M) is NOT released. All three released sizes fit on CPU in 8 GB (estimate; RAM not measured).
   - Data: a one-time weights download from Hugging Face (NeoQuasar/*), then inference runs locally.
   - Risks: maintenance is stale, and it needs a zero-shot vs. fine-tuned check. In AHOS its output must go through M28.1 DSR/PBO and M15.10 calibration before it carries any weight. It is advisory only.
2. skfolio does portfolio optimization on scikit-learn (risk parity/HRP, stress tests, factor models per the post). It runs fully local and sends no data.
   - Risk: low. It overlaps the M24 allocator / M28.6 HRP plan, so use it inside those missions instead of hand-rolling, and don't add a new allocator.
3. NautilusTrader is a Rust core with a Python control plane. The README says the same strategy code runs in backtest and live, and it documents "backtest and live differences".
   - Data: offline in backtest; venue adapters connect only if configured.
   - Risks: live adapters exist and would need exchange keys, so never configure them. It's a heavy dependency, so measure RAM on 8 GB before adopting (UNVERIFIED).
   - Use: parity checks of M25 gates against the AHOS validation_engine, in backtest/sandbox only.
4. Hummingbot runs market-making/arbitrage bots; the README says 140+ venues and $34B user volume.
   - It has a `binance_paper_trade` connector, but live use needs exchange API keys (stored in an encrypted keystore).
   - Risks: high-frequency and live-oriented, which conflicts with the no-keys law. Telemetry is UNVERIFIED.
   - Use: read its inventory-skew / spread logic for M21 risk notes only. Don't install it.
5. Freqtrade is a crypto bot with backtesting, a WebUI, Telegram control, CCXT exchange access and FreqAI (adaptive self-retraining ML). It has a Dry-Run mode.
   - Data: exchange public market data via CCXT. If Telegram is enabled, bot output goes to Telegram (conflicts with M61 / the AD-0128 token rules).
   - Risks: live trading is one config switch away. Run only with dry_run=true and no keys, never connected to Telegram.
6. Research workspace. The reel says: "you type a question in plain english, it pulls data, writes the strategy and backtests it". The repo is not named, so UNVERIFIED.
   - RD-Agent(Q) is the closest fit: LLM-driven factor/model R&D on Qlib, via LiteLLM (needs an LLM API, so only :free models per M35.1 / M37 $0 cap).
   - OpenBB is an open data platform, not a question-to-backtest agent. It is now github.com/openbq-org/OpenBB, Apache-2.0 (from its LICENSE file). It moved to OpenBQ, a non-profit, per openbb.co on 2026-10-01; last commit 2026-10-02 08:24. A data-source option for M19.
   - Qlib (github.com/microsoft/qlib, MIT, last commit 2026-10-08 13:45, ~49.2k) is the platform RD-Agent runs on.
   - Risks: LLM-written strategies must pass the M25/M28.1 gates, and research output never trades.

## License notes (importing vs. a separate process; not legal advice)
- MIT / BSD-3 / Apache-2.0 (Kronos, skfolio, Hummingbot, RD-Agent, Qlib, OpenBB): import freely. Keep the notices; Apache also has a patent clause.
- LGPL-3.0 (Nautilus): importing it unmodified as a library is fine even in non-LGPL code. If you modify Nautilus itself and distribute it, the modified library must be released under LGPL and users must be able to swap it. Private, undistributed use triggers nothing.
- GPL-3.0 (Freqtrade): `import freqtrade` into AHOS and then distribute, and the combined work must be GPL. Running it as a separate process that talks only over CLI/REST/files is usually treated as arm's length, so AHOS keeps its own license. Private, undistributed use triggers nothing.
  - Rule: keep it a separate process and never copy its code into AHOS.
- AGPL: none of the six is AGPL. If one were, network use would also trigger the copyleft.

## UNVERIFIED
- Which repo item 6 is.
- Hummingbot on Windows / 8 GB and its telemetry.
- RD-Agent on Windows.
- Real RAM use of Nautilus and Kronos on 8 GB.
- skfolio's stress-test and factor-model features (taken from the post, not checked in its docs).

Dedup: every item is an addendum to M15.10, M24/M28.6, M28.1/M25, M21, M16/M58 or M19 (map rows 14, 18-20, 22, 26). There are no new modules, and the map's own note says "zipline/bt are not needed".
