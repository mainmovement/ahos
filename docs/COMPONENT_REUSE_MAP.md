# AHOS — COMPONENT REUSE MAP — 2026-08-11
| New need | Reuse | Action | Maturity after |
|---|---|---|---|
| Market klines/funding/OI | engine/acquire_3yr.py + research/data | REUSE as-is | D |
| Causal event engine pattern (signal→eval→halt) | strategy_lab/lab_engine.py discipline | REUSE pattern for event evaluator | B→C |
| Gates/verdict logic (acceptance battery) | strategy_lab/run_lab.py + GATES | REUSE for E-01 outcome analysis | C |
| Data integrity gates (12 gates) | engine/data_audit.py | REUSE on every new dataset | D |
| DB schema | database/postgresql_schema.sql | EXTEND additively (v1.2: tokens, discoveries, features, events, scores, positions, alerts) | B |
| n8n skeletons + credentials externalization | workflows 01/02/03 patterns | EXTEND: 20_discovery, 21_scoring, 22_position_monitor workflows (new files) | B |
| Telegram auth/kill/audit flow | workflow 03 + bot_skeleton.py | REUSE; ADD Persian templates + NLP intake node | C→B |
| Research digest builder | engine/research_report_bot.py | REUSE for opportunity digest formatting | C |
| Telegram test harness | engine/telegram_live_test.py | REUSE; extend with Persian-payload tests | C |
| CI regression gate | engine/run_all_checks.sh | EXTEND with new suites (discovery, scoring, ux) | D |
| Rollback discipline | config/rollback_v1.0.json | REUSE pattern; per-score-version rollback entries | D |
| Hypothesis registry law | strategy_lab/charter | REUSE for score-weight hypotheses (weights = hypotheses) | D |
| Docker/VPS deployment | deployment/docker-compose.yml | REUSE as-is | B |
| Secret hygiene / env-only rules | docs/SECURITY_CHECKLIST.md | REUSE; add provider-key registry | D |

## NOT reusable (explicit)
- Baseline strategy v1.0 as production signal (no edge — evidence-locked, remains as calibration baseline).
- 83-day LBank canonical sets for anything beyond historical integrity references (superseded by 3.6y/6.6y).
