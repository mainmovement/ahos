# CRITIQUE — M51 self-improvement (2026-10-18)

## Acceptance checked
- One accepted proposal per cycle id, and `merge` stays false.
- A second proposal in the same cycle is refused.
- A proposal based on the loop's own output is refused.
- A target path containing gate, policy, cap, limit, or HOLD is refused.

## Evidence
`pytest tests/test_m51_improvement.py` — 2 passed.

## Adversarial critique
| Gap | Status |
|-----|--------|
| M45 lab and M50 exam feeding the proposal | Not wired. The caller supplies the target. |
| A path that changes a gate without using those words | The word list would miss it. |
| Auto-merge | The result field is false and this module has no git merge call. |

## Verdict
**M51 proposal rule: PASS.** It records a candidate and does not merge.
