# Critique — M51 path + M58 close_eval in ledger checkpoint

Date: 2026-10-18 (Tehran). PAPER_ONLY.

## Change
- `path.m51`: structured proposal (`accepted`, `reason`, `merge`, `cycle_id`) with one proposal per cycle via `proposal_cycles`.
- `close_eval` written in the **same** checkpoint as the settle (before `_record`), not after — judge-visible bytes include M58 hit/miss.

## Proof
```
pytest tests/test_gold_close_eval_m51.py tests/test_paper_path_wire.py tests/test_gold_lessons_read.py -q
```

## Gaps
- Live soak until owner restart.
- M51 still never merges; human/Cursor review only.

## Verdict
PARTIAL: closed-loop proposal + eval on scratch ledger proven.
