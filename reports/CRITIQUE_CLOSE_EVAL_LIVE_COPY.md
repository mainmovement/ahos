# Critique — close_eval on forked **live** ledger history

Date: 2026-10-18 (Tehran).

## Command
```
python scripts/prove_wiring_on_ledger_copy.py --settle-tp
```

## Result
- `close_eval.hit`: **true** (`gold-eval-638`, weight 0 until review)
- `path.m51.merge`: false
- `judge`: **CLEAN** on TEMP copy only

## Full stack drill
```
python scripts/full_stack_copy_drill.py --settle-tp
```
- tier gate stdout: `tier=T0 measurable_pass=4/10 unmeasurable=1`

## Verdict
PARTIAL: end-to-end settle bytes proven on fork; live soak PID still old in-process code.
