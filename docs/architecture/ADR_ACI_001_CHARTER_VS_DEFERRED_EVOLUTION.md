# ADR-ACI-001 — Charter vs deferred autonomous evolution

**Decision ID:** ADR-ACI-001  
**Date (UTC):** 2026-09-09  
**Status:** ACCEPTED for Lane-B architecture work; operational deferral preserved  
**Reversibility:** High (docs + Lane-B contracts only; no Lane A / soak change)

## Decision

Treat `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md` as the **strategic architecture** for AGI/ACI evolution research, while `docs/NEXT_DEVELOPMENT_BACKLOG.md` remains **authoritative for operational sequencing** and continues to list **autonomous evolution** as deferred. `docs/canonical/PROJECT_STATE.md` continues to record Evolution layer as **A (OFF by doctrine)** for autonomous promotion.

Lane-B cognitive **contracts** (hypothesis/experiment/self-research/gap/sandbox) are allowed. Autonomous self-modification, Lane-A mutation, soak interruption, and auto-promotion remain forbidden.

## Context

The master evolution directive establishes AGI/ACI as long-term direction. Older living documents say:

- `docs/NEXT_DEVELOPMENT_BACKLOG.md` (2026-08-27): “Deferred (explicit — do not implement now) … autonomous evolution”
- `docs/canonical/PROJECT_STATE.md`: Evolution layer “A (OFF by doctrine)”
- `docs/architecture/SELF_EVOLUTION_LOOP.md`: AI may diagnose/propose; NEVER self-approve, NEVER touch Lane A, NEVER promote itself
- `AHOS_FINAL_STATUS.md`: SUPERSEDED — not current authority (`docs/DOC_TRUTH_MAP.md`)

Silently rewriting the backlog to “evolution is now on” would erase an operational gate (Windows soak / OV-* still in progress).

## Options

1. Overwrite backlog/PROJECT_STATE to match the Charter (rejected: destroys operational authority).
2. Ignore the Charter (rejected: no governed place for AGI/ACI architecture).
3. Dual authority with an explicit conflict record (chosen).

## Chosen approach

Option 3. Indexes (`docs/DOC_TRUTH_MAP.md`) gain a pointer to the Charter plus this ADR. `AHOS_GAP_REGISTER.md` operational rows (including M-GAP-003) are **not** rewritten. AGI/ACI gaps live in `reports/agi_aci_evolution/GAP_REGISTER.md`.

## Reason

Soak T0 (`2026-09-10 00:27:41 +03:30`, run_id `run_1788987515_7ad11528`) is an independent evidence experiment. Evolution research must stay parallel and isolated.

## Consequences

- Developers may add Lane-B cognitive contracts with tests and evidence.
- Developers may **not** enable autonomous evolution, live trading, or Lane A changes from this ADR.
- After soak, a separate human-reviewed proposal is required before calibration or M-GAP-003 closure.

## Alternatives rejected

- Fake “AGI layer” classes claiming the capability exists.
- Merging speculative cognition into `main` during soak.
- Closing M-GAP-003 because a 72h soak exists.

## Evidence

- Charter path above.
- `architecture/evolution/engine.py` human-gate tests (`tests/test_self_evolution_engine.py`).
- `architecture/cognitive/evolution_gate.py` refuses non-`B_ONLY` scopes.
- `reports/agi_aci_evolution/AUDIT_REPORT.md`
