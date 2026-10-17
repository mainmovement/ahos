# CRITIQUE — M59.S Idea Shelf core (2026-10-18)

## Acceptance (from TEAM_QUEUE 2026-10-11)
- `core/idea_shelf/{registry,hardware,flags,ram_guard}.py`
- Single registry `config/idea_shelf.json`
- psutil probe, override, fail-safe without GPU
- RAM guard soft 80% / hard 90%, core never shed
- Tests: tier sets, shed order, core property, missing GPU safe

## Evidence
- `pytest tests/test_m59s_idea_shelf.py` — 9 tests
- `npm run test:idea-shelf` — dashboard TS rule unchanged (shared JSON)

## Adversarial critique
| Gap | Status |
|-----|--------|
| Live psutil on 8 GB laptop | Probe logs only; tier derived from RAM bands |
| Auto-install of shelf tools | Out of scope — flags are enable *decisions*, not pip |
| GPU VRAM without driver | Uses AHOS_VRAM_GB env optional; default no discrete GPU |
| Hysteresis 60s re-enable | `evaluate_ram_guard` exposes threshold constants; full timer loop deferred to M47 hook |

## Verdict
**M59.S core: PASS** for registry + probe + flags + RAM guard logic. Runtime scheduler integration = follow-on with M47.
