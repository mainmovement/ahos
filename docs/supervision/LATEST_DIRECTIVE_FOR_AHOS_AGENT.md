# BUILD AGENT DIRECTIVE — Oversight Council v2

**Updated:** 2026-09-12 Cycle 005 (Architecture v2)  
**STATUS:** `FIX_BEFORE_CONTINUE`  
**Architecture:** `docs/supervision/SUPERVISION_ARCHITECTURE.md`  
**Truth model:** `docs/supervision/AHOS_PROJECT_TRUTH_MODEL.md`  
**Baseline:** `docs/supervision/cycles/BASELINE_AUDIT_2026-09-12.md`

---

## PRE-FLIGHT required (before any material change)

```
Intended change | Authority surface | Reason | Expected behavior | Risks | Test plan
```

## POST-FLIGHT required (after)

```
Actual diff | Tests | Evidence artifacts | Unknowns | New risks
```

---

## OWNER SAFETY LOCKS (§20 — BLOCK until council updates)

| ID | Rule |
|----|------|
| S20-1 | Lane A — **DO NOT** touch |
| S20-2 | W4 Slice 7 — hold current state |
| S20-3 | **DO NOT merge PR #103** |
| S20-4 | **DO NOT start Slice 8** |
| S20-5 | No new identity authority |
| S20-6 | No historical mapping |
| S20-7 | No readiness upgrade claims |
| S20-8 | No fixture patch to fake green |
| S20-9 | No aesthetic-only architecture |

---

## DO (priority order)

| ID | Task |
|----|------|
| D1 | W1.3 identity spoof hardening + test |
| D2 | Merge W2 (#95) to main |
| D3 | DOSSIER.md + DOC_TRUTH_MAP |
| D4 | POST-FLIGHT report per PR |

## DO_NOT

- Merge #103, start Slice 8, expand W4 without council review
- Secrets in git; live trading; AGI/ACI claims
- Mega-PR; orphan 3D tree wiring

## BLOCK

PR #103 merge · Slice 8 · Lane A · readiness inflation · soak interference

## MONITOR

Agent IDLE stall — wake if no progress by next L2 cycle

## ESCALATE_TO_HUMAN

- P5 MERGE=NO vs main code conflict
- Token rotation (S-01)
- Windows soak start

---

## Launch filter

> Does this move AHOS one **real** step toward trustworthy Launch?
