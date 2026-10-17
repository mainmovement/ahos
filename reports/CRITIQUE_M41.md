# CRITIQUE — M41 broker key self-check (2026-10-18)

## Acceptance checked
- A mocked key with `withdraw` returns HALT.
- Missing IP lock returns HALT.
- `trade` + `read` with an IP lock returns READ.
- A path outside `broker/` returns HALT.
- The checker does not open the key file (fixture bytes unchanged).

## Evidence
`pytest tests/test_m41_broker_keys.py` — 4 passed.

## Adversarial critique
| Gap | Status |
|-----|--------|
| Live exchange permission query | Not done. There is no broker and no key in this pass. |
| Mother-fund isolated withdraw key at T4 | Not modeled. Any withdraw word halts. |
| IP lock is a boolean argument | The caller must pass it. This module does not ask an exchange. |

## Verdict
**M41 mocked fail-closed check: PASS.** A live permission pull remains out of scope.
