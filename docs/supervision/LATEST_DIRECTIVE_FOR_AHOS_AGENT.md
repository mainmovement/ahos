# BUILD AGENT DIRECTIVE — Oversight Council v2

**Updated:** 2026-09-13T16:30Z — post W3/W4 merge wave  
**Council STATUS:** `MONITOR`  
**Build agent STATUS:** `FIX_BEFORE_CONTINUE` (Phase 1 remainder + W4 tip promotion pending human gate)  
**Vision audit:** `docs/supervision/AHOS_VISION_ALIGNMENT_AUDIT.md` ← **authority for WHAT TO BUILD**  
**Architecture:** `docs/supervision/SUPERVISION_ARCHITECTURE.md` (v2 unchanged)  
**Truth model:** `docs/supervision/AHOS_PROJECT_TRUTH_MODEL.md`

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

## OWNER SAFETY LOCKS (§20 — updated 2026-09-13)

| ID | Rule |
|----|------|
| S20-1 | Lane A — **DO NOT** touch |
| S20-2 | W4 Slice 8 — **DO NOT start** |
| S20-3 | W4 slices 2–7 → `main` — **ESCALATE_TO_HUMAN** (owner merged #103 to stack; promotion PR required) |
| S20-4 | No new identity authority |
| S20-5 | No historical mapping |
| S20-6 | No readiness upgrade claims |
| S20-7 | No fixture patch to fake green |
| S20-8 | No aesthetic-only architecture |
| S20-9 | No soak/runtime semantic interference |

---

## DO (Vision-audit path — Phase 1 only)

| ID | Task |
|----|------|
| D1 | W1.3 identity spoof hardening + test |
| D2 | Merge W2 (#95) to main — **COMPLETE** |
| D3 | DOSSIER.md + DOC_TRUTH_MAP |
| D4 | POST-FLIGHT report per PR |
| D5 | Open promotion PR: `cursor/calibration-identity-join-9500` → `main` — **HUMAN GATE** before merge |

**Phase 2 (P1 chat/TG/alerts)** — ALLOW after D1 + D3; W4 tip promotion is separate human-gated step.

## DO_NOT

- Start Slice 8; merge W4 tip to `main` without human gate
- Secrets in git; live trading; AGI/ACI claims
- Mega-PR; orphan 3D tree wiring

## BLOCK

W4 tip → `main` without human gate · Slice 8 · Lane A · readiness inflation · soak interference

## MONITOR

Agent IDLE stall — wake if no progress by next L2 cycle

## ESCALATE_TO_HUMAN

- P5 MERGE=NO vs main code conflict
- Token rotation (S-01)
- Windows soak start

---

## Launch filter

> Does this move AHOS one **real** step toward trustworthy Launch?
