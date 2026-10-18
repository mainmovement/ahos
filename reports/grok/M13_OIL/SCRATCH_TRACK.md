# M13 oil paper scratch track

PAPER_ONLY. **Not** wired to `m13_gold_soak.py` (gold PID). Use a dedicated ledger file.

## One cycle
```
.venv\Scripts\python.exe scripts\oil_paper_once.py --ledger data\mission_ledger\oil_paper_scratch.jsonl
```

## Seven-day-style cadence (7 checkpoints, offline)
```
.venv\Scripts\python.exe scripts\oil_paper_cadence.py --ledger data\mission_ledger\oil_paper_scratch.jsonl --cycles 7
```

Checkpoint includes `margin_event` / `margin_leverage` (paper cap 2x). Mission id: `M13-OIL-PAPER`.
