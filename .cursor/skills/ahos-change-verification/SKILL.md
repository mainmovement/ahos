---
name: ahos-change-verification
description: Final AHOS inspector — freeze, validate_imports, pytest, typecheck, lint, build, health, browser receipts, phase gates, clean tree. Invoke before claiming COMPLETE.
disable-model-invocation: true
---

# AHOS change verification

Run real commands. Never claim a gate that did not execute.

Default ladder (skip inapplicable steps, do not skip Lane A):

```bash
python3 -B scripts/freeze_lane_a.py
python3 scripts/validate_imports.py          # when Python/architecture changed
python3 -m pytest -q -p no:cacheprovider     # targeted first, then broader
npm run test:web-api-auth                    # web/auth
npm run typecheck && npm run lint && npm run build
python3 deployment/healthcheck.py            # if runtime is up
```

Native Browser for affected UI: Persian RTL, English LTR if present, console
and network errors, empty/error states.

Forbidden: weakening tests; rewriting `reports/` history; presenting VM-empty
DBs as soak evidence; marking COMPLETE with failed or skipped mandatory gates.

Phase record must include `PHASE_STATUS`, `PASS_GATES`, `FAILED_GATES`,
`BLOCKERS`, `EVIDENCE`, `TEST_RESULTS`, `REGRESSIONS`, `KNOWN_LIMITATIONS`,
`NEXT_UNLOCKED_PHASE`.
