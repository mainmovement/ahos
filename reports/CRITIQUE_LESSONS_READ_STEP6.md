# Critique — Step 6 lessons read (M49 → gold path)

Date: 2026-10-18 (Tehran). PAPER_ONLY; HOLD unchanged.

## Change
- `GoldPaperTrack._lessons_snapshot` reads `m49_lessons.sqlite` beside the ledger before entry sizing.
- Checkpoint `path.lessons` records visible gold lessons, reviewer-weight count, and `notional_unchanged` (apply_gate is identity).
- Unreviewed lessons stay weight 0; reviewed lessons increment `weight_one` without blocking entry.

## Proof
```
pytest tests/test_gold_lessons_read.py tests/test_paper_path_wire.py -q  → 5 passed
```

## Gaps
- Live soak PID 10564 still runs pre-wiring code until owner restart (`OWNER_ACTIONS.md`).
- Lessons do not yet feed M58.1 scorer or M51 in the same cycle (proposal slot unchanged).

## Verdict
PARTIAL integration: read loop on scratch/copy ledger proven; closed-loop improve not proven.
