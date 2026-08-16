# AHOS — TELEGRAM RESEARCH REPORT (Agent-05/06) — 2026-08-10
# Purpose: telegram-based research reporting test (temporary bot Sun_sniperbot, TEST ONLY).
# Mode: SIMULATED (no credentials in env) — transcript below is the exact payload that will send
# identically in REAL mode once TELEGRAM_BOT_TOKEN + TELEGRAM_ADMIN_CHAT_ID are exported.

## 1. What was tested
- Digest builder: engine/research_report_bot.py reads strategy_lab/registry.json + latest experiment log.
- Dispatch path: env-only credentials; SIMULATED transcript persisted to research/reports/telegram_dispatch.json.
- n8n delivery path: workflow ahos_12_research_report.json (weekly Sun 06:00) runs the same builder and
  audits dispatch to agent_audit_trail; failure alert path included (validated by tests/validate_n8n.py).

## 2. Simulated telegram digest (verbatim payload)
```
AHOS RESEARCH DIGEST
ts: 2026-08-10 12:14Z
data: real 3.6y (BTC/ETH/SOL, sha 7d1375cc1f52…)
gates: PF>1.3 OOS, exp>0, DD<15%, MC>70%, WF>=60%, stress PF>1.1

H1 Donchian Breakout 55/20: REJECTED (BTC 0.612 | ETH 1.229 | SOL 0.809)
H2 Bollinger z20 ±2 reversion: REJECTED (BTC 0.313 | ETH 0.219 | SOL 0.338)
H3 ATR squeeze breakout: REJECTED (BTC 0.886 | ETH 0.751 | SOL 0.796)
H4 ADX>25 pullback-to-EMA20: REJECTED (BTC 0.712 | ETH 0.672 | SOL 0.391)
H5 Extreme funding contrarian: REJECTED (BTC 0.661 | ETH 0.432 | SOL 0.313)
H6 OI expansion + price confirmation: REJECTED (BTC 3.126 | ETH 0.925 | SOL 0.926)
H7 Volume shock continuation: REJECTED (BTC 0.310 | ETH 0.747 | SOL 1.048)
H8 Order-book imbalance scalping: NOT TESTED (data-blocked)
H9 Fixed-weight composite score: REJECTED (BTC 1.383 | ETH 1.006 | SOL 0.606)

accepted: 0/8 testable | live gate: CLOSED
no parameter tuning performed · full log in research/experiments/
```

## 3. Result
- SIMULATED: PASS (message < 3800 chars, all gates text render, no secrets, no claims beyond evidence).
- REAL send: PENDING — blocked by token rotation (user action); procedure: docs/TELEGRAM_TEST_PROCEDURE.md.
- Report cadence: weekly digest (H-results) + nightly data update note (workflow 11) + hourly control plane (workflow 03).

## 4. Compliance note
Message content contains zero performance promises; all verdicts reference the experiment log hash.
This satisfies the NO CLAIM WITHOUT DATA rule for outbound communications.
