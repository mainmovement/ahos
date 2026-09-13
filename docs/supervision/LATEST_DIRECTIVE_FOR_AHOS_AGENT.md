# BUILD AGENT DIRECTIVE — Oversight Council v2

**Updated:** 2026-09-12 — post Vision Alignment Audit  
**Council STATUS:** `MONITOR`  
**Build agent STATUS:** `FIX_BEFORE_CONTINUE` (Phase 1 only when resumed)  
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

## DO (Vision-audit path — Phase 1 only)

| ID | Task |
|----|------|
| D1 | W1.3 identity spoof hardening + test |
| D2 | Merge W2 (#95) to main |
| D3 | DOSSIER.md + DOC_TRUTH_MAP |
| D4 | POST-FLIGHT report per PR |

**Phase 2 (P1 chat/TG/alerts)** — ALLOW only after D1–D2 complete. See Vision Audit §11 FINAL BEST PATH.

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
