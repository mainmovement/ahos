# CRITIQUE — M37 frontier slots (2026-10-18)

A locked slot and a slot at 100% budget are skipped. `purpose="order"` raises. No provider is called and no key is read.

`pytest tests/test_m37_frontier_slots.py` — 1 passed.

The registry file and a monthly cost meter are not in this slice. The selector is the fail-closed rule.
