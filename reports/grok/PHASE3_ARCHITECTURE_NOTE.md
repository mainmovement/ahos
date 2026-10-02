# Phase 3 architecture note (Grok, 2026-10-02)

Reality ladder: DESIGN_ONLY → IMPLEMENTED → TESTED (offline self-tests) → INTEGRATED (wired into a running path) → OPERATIONAL (proven in the live runtime with evidence). Self-tests are not independent verification.

| Item | Ladder | Why not higher |
|---|---|---|
| P3-M1 `tsconfig.json` excludes `docs/archive` | TESTED | It is build configuration, so there is nothing to operate. `tsc --noEmit` is clean on Windows. |
| GM-08 mission/engineering ledger (`architecture/mission/ledger.py`) | IMPLEMENTED + TESTED | Nothing writes to it automatically, and it has not been seeded on the laptop, so it is not INTEGRATED. OPERATIONAL would need real missions recorded and verified over time. It is not a decision authority and gates nothing. |
