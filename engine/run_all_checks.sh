#!/usr/bin/env bash
# AHOS CI regression gate — all four checks must pass (Agent-09).
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== [1/6] Data integrity audit =="
python3 engine/data_audit.py
echo "== [2/6] pytest core suite =="
python3 -m pytest tests/test_ahos.py -q
echo "== [3/6] pytest strategy-lab suite =="
python3 -m pytest tests/test_strategy_lab.py -q
echo "== [3b/6] pytest discovery-core suite (Mission v1.1) =="
python3 -m pytest tests/test_discovery.py -q
echo "== [3c/6] pytest baseline-statistics suite (Wave-6) =="
python3 -m pytest tests/test_baseline_stats.py -q
echo "== [3d/6] pytest wave-7 research suite (conjunction cells + materializer) =="
python3 -m pytest tests/test_wave7_research.py -q
echo "== [3e/6] pytest telegram-ai suite (Persian intent / AI-PAL / ledger / alerts) =="
python3 -m pytest tests/test_telegram_ai.py -q
echo "== [3f/6] pytest paper-trading lab suite (anti-bias laws) =="
python3 -m pytest tests/test_paper_trading.py -q
echo "== [3g/6] pytest paper-trading v2 suite (bankroll/scam-defense/trapped-capital) =="
python3 -m pytest tests/test_paper_trading_v2.py -q
echo "== [4/6] Workflow dry-run scenarios =="
python3 engine/dryrun_simulation.py
echo "== [5/6] Telegram protocol harness + research dispatch (SIMULATED unless env vars set) =="
python3 engine/telegram_live_test.py --simulate
python3 engine/research_report_bot.py --simulate > /dev/null
echo "== [6/6] n8n workflow structural validation (6 workflows) =="
python3 tests/validate_n8n.py
echo "ALL CHECKS GREEN — ready for Agent-10 review"
