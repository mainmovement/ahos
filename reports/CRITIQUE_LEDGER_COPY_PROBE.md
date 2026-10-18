# Critique — wiring probe on live ledger **copy**

Date: 2026-10-18 (Tehran). Read-only source; writes only TEMP copy.

## Command
```
python scripts/prove_wiring_on_ledger_copy.py
```

## Result (sample)
- Source: `data/mission_ledger/mission_ledger.jsonl`
- Dest: `%TEMP%\ahos_ledger_wiring_probe_*.jsonl`
- `path_oms`: ACCEPTED_PAPER
- `path.m51.merge`: false
- `lessons_keys`: includes m58_* and visible_gold
- `judge`: CLEAN on the **copy** after one synthetic cycle

## Not proven
- Live soak process bytes (PID until owner restart).
- `close_eval` non-null requires a settling cycle on copy with open position + TP.

## Verdict
PARTIAL: new wiring runs against replayed live history on a fork; not dual-writer on live file.
