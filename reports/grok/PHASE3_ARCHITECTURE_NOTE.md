# Phase 3 architecture note (Grok, 2026-10-02)

Reality ladder: DESIGN_ONLY → IMPLEMENTED → TESTED (offline self-tests) → INTEGRATED (wired into a running path) → OPERATIONAL (proven in the live runtime with evidence). Self-tests are not independent verification.

| Item | Ladder | Why not higher |
|---|---|---|
| P3-M1 `tsconfig.json` excludes `docs/archive` | TESTED | It is build configuration, so there is nothing to operate. `tsc --noEmit` is clean on Windows. |
| GM-08 mission/engineering ledger (`architecture/mission/ledger.py`) | IMPLEMENTED + TESTED | Nothing writes to it automatically, and it has not been seeded on the laptop, so it is not INTEGRATED. OPERATIONAL would need real missions recorded and verified over time. It is not a decision authority and gates nothing. |
| GM-09 AI provider status model + classifier (`architecture/ai/provider_status.py`) | IMPLEMENTED + TESTED | No runtime path (LiveCouncil/router) calls it yet, so it is not INTEGRATED. Tested only with fake providers. |
| GM-09 ledger integration (`architecture/ai/mission_guard.py`) | IMPLEMENTED + TESTED | Not called by any running process. |
| GM-09 credential-store interface (`architecture/ai/credential_store.py`) | IMPLEMENTED (interface + fakes) + TESTED | There is no real backend. |
| Windows Credential Manager backend | DESIGN_ONLY | Needs owner + security review (GM-12). It reads and writes nothing. |

Not OPERATIONAL anywhere. PAPER_ONLY. Nothing here is a decision authority.
