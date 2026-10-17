# CRITIQUE — M40 treasury requests (2026-10-18)

## Acceptance checked
- A clean request is recorded and `executes` stays false.
- Replay, either daily cap, expiry, an address in the message, and the wrong network are rejected.
- The module source has no withdraw function, transaction send, or route.

## Evidence
`pytest tests/test_m40_treasury_requests.py` — 3 passed.

## Adversarial critique
| Gap | Status |
|-----|--------|
| Owner manual execution | Not built. This module stops at the request. |
| Mother-fund exception | Not modeled. Every path here is request-only. |
| Address shapes beyond the three patterns | A novel address format could pass the text scan. |

## Verdict
**M40 negative suite: PASS** for paper requests. No funds move.
