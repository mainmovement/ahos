# Canonical overlay census (observability, not a join)

**Date:** 2026-09-09  
**Classification:** `IMPLEMENTED` / `TESTED`. Dual-store architecture is **not** redesigned.  
**Not claimed:** Python→Postgres sync, token-key unification, identity VERIFIED, BUY.

---

## Law

Python JSON (`reports/canonical_decision_read_model.json`) and TypeScript/Postgres
opportunities are **separate stores**. Canonical BUY lives only in Python.

Unmatched Command Center opportunity rows stay **`UNAVAILABLE`**. That is
fail-closed, not a bug to “fix” by inventing a join.

GeckoTerminal still stores **pool** address as `NormalizedTokenCandidate.address`.
Dexscreener/TS rows typically use the **token** address. Those keys will not
match. Changing gecko identity is a **STOP**.

---

## What this adds

`canonicalOverlayCensus` on `/api/command` (`overlayCensus`):

| Field | Meaning |
|-------|---------|
| `pythonDecisionCount` | Python read-model rows |
| `tsOpportunityCount` | Postgres opportunity rows in the snapshot |
| `matched` | TS rows whose chain+address hit a Python row |
| `unmatchedTs` | TS rows with no Python row → display UNAVAILABLE |
| `unmatchedPython` | Python rows with no TS opportunity |
| `note` | Explicit: not a join, does not mint BUY |

---

## Tests

`npm run test:canonical-read-model` — census counts + unmatched stays UNAVAILABLE.
