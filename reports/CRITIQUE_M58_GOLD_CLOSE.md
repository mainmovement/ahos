# Critique — M58.1 on gold close + path cap snapshot

Date: 2026-10-18 (Tehran). PAPER_ONLY.

## Change
- `path.lessons` now includes `m58_daily_cap_pct` and `m58_cap_unchanged` (apply_gate identity on 3% daily cap).
- Every recorded close calls `evaluate_paper_decision` (long-only paper: predicted `up`, realized from PnL sign) into sidecar sqlite; losses still append trade_loss lesson.

## Proof
```
pytest tests/test_gold_lessons_read.py -q  → 2 passed
```

## Gaps
- Live soak PID until owner restart.
- M51 merge still proposal-only in path.

## Verdict
PARTIAL closed-loop: eval on close proven on scratch ledger; not proven on live bytes.
