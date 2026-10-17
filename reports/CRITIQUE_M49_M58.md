# CRITIQUE — M49 lessons ledger + M58.1 decision eval (2026-10-18)

## Acceptance checked
- Hash-chained append-only SQLite lesson rows (update/delete aborted).
- UNVERIFIED retrieval weight is 0 until reviewer 16 appends a review row.
- `apply_gate` returns the same limit.
- A lesson dated after `as_of` is invisible.
- An outcome timestamp that is not after the decision is refused.
- A miss files an UNVERIFIED lesson and does not move the gate limit.

## Evidence
`pytest tests/test_m49_m58_lessons.py` — 6 passed.

## Adversarial critique
| Gap | Status |
|-----|--------|
| Retrieval wired into the live gold cycle | Not done. The soak must not gain a second writer or a gate change. |
| Agent 16 is a string id, not a signed review | The permission check is the reviewer id. It is not a cryptographic signature. |
| Existing `paper_trading/lessons.py` | Left in place. This chain is the M49 record; it does not replace trade narratives. |
| Reviewed weight | Retrieval weight may become 1. Gate application stays an identity. |

## Verdict
**M49 chain + M58.1 paper scorer: PASS** for the local store and the leak rule. Live decision retrieval is a follow-on, still without gate edits.
