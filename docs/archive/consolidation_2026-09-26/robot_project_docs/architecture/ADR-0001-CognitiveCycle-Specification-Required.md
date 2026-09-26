# ADR-0001 — CognitiveCycle Specification Required

## Status

Accepted

---

## Date

2026-07-28

---

## Context

During implementation of Deliverable #6 (CognitiveCycle), the implementation process was blocked because the approved architecture specifications (SPS v1.1, DMS v1.0, RAS v1.1, DEB v1.0) do not explicitly define the CognitiveCycle aggregate.

The implementation engineer correctly stopped implementation instead of introducing assumptions.

---

## Decision

Implementation of CognitiveCycle is postponed until a dedicated Cognitive Architecture Specification (CAS) is created and approved.

No implementation may introduce:

- Aggregate structure
- State machine
- Phase transitions
- Business invariants
- Event emission rules

unless they are explicitly defined by architecture.

---

## Consequences

Positive:

- Prevents architecture drift.
- Prevents overengineering.
- Preserves strict scope discipline.
- Keeps implementation aligned with approved specifications.

Negative:

- Domain implementation is temporarily paused until CAS is completed.

---

## Related Documents

- SPS v1.1
- DMS v1.0
- RAS v1.1
- DEB v1.0
- ARCHITECTURE_COMPLETION_ROADMAP_v1.0

---

## Decision

Accepted