# Critique — M13 oil scratch track (7-cycle cadence)

Date: 2026-10-18 (Tehran). PAPER_ONLY; not attached to gold soak PID.

## Change
- `oil_paper` checkpoint records `margin_event` / `margin_leverage`.
- `scripts/oil_paper_cadence.py` — N cycles on dedicated ledger; optional `--break-cycle` for UNKNOWN.
- Scratch file: `data/mission_ledger/oil_paper_scratch.jsonl` (local, not live gold ledger).

## Proof
```
pytest tests/test_oil_margin.py tests/test_oil_paper_cadence_script.py -q  → passed
python scripts/oil_paper_cadence.py --ledger data/mission_ledger/oil_paper_scratch.jsonl --cycles 7
```

## Gaps
- No judge section for oil; no 7-day OS process scheduler (owner/logon).
- Gold soak unchanged.

## Verdict
PARTIAL: separate oil mission proven offline; integration with tier gate/judge pending.
